"""
고도화된 RAG용 데이터 전처리 스크립트
- 의미 기반 청킹 (섹션 경계 우선, 800자 목표, 100자 오버랩)
- 계층적 메타데이터 생성
- 다중 표현 생성 (original, summarized, keywords, question_variants)
- 컨텍스트 보존 (prev_content, next_content 포함)
- 한국어 검색 최적화용 키워드 추출
"""

import os
import json
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import hashlib

@dataclass
class EnhancedChunk:
    id: str
    document_name: str
    chunk_index: int
    content: Dict[str, Any]  # original, summarized, keywords, question_variants
    metadata: Dict[str, Any]  # hierarchy, semantic_tags, relationships
    context: Dict[str, Any]   # prev_content, next_content
    char_count: int
    created_at: str

class AdvancedRAGPreprocessor:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 청킹 설정
        self.target_chunk_size = 800
        self.overlap_size = 100
        
        # 한국어 의미 단위 패턴
        self.section_patterns = [
            r'^#{1,6}\s+.*$',  # 마크다운 헤더
            r'^\d+\.\s+.*$',   # 번호 리스트
            r'^-\s+.*$',       # 불릿 포인트
            r'.*[.!?]\s*$',    # 문장 끝
            r'.*:\s*$',        # 콜론으로 끝나는 라인
        ]
        
        # 의미 태그 키워드 매핑
        self.semantic_keywords = {
            "정책": ["정책", "규정", "규칙", "기준", "원칙", "방침"],
            "승인": ["승인", "검토", "심사", "허가", "인가", "통과"],
            "거부": ["거부", "반려", "금지", "제한", "불가", "차단"],
            "템플릿": ["템플릿", "양식", "형식", "포맷", "서식"],
            "내용": ["내용", "텍스트", "메시지", "문구", "문장"],
            "이미지": ["이미지", "사진", "그림", "이미지", "첨부"],
            "광고": ["광고", "홍보", "마케팅", "프로모션", "캠페인"],
            "개인정보": ["개인정보", "프라이버시", "민감정보", "개인식별"],
            "금융": ["금융", "대출", "투자", "보험", "카드", "결제"],
            "의료": ["의료", "건강", "병원", "치료", "약품", "질병"]
        }

    def read_markdown_file(self, file_path: Path) -> str:
        """마크다운 파일 읽기"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def extract_hierarchy(self, content: str) -> Dict[str, Any]:
        """문서 계층 구조 추출"""
        lines = content.split('\n')
        hierarchy = []
        current_section = None
        
        for i, line in enumerate(lines):
            # 헤더 패턴 매칭
            header_match = re.match(r'^(#{1,6})\s+(.*)', line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                hierarchy.append({
                    "level": level,
                    "title": title,
                    "line_number": i + 1,
                    "type": "header"
                })
                current_section = title
            
            # 번호 리스트 패턴 매칭
            elif re.match(r'^\d+\.\s+', line):
                hierarchy.append({
                    "level": 99,  # 리스트 아이템은 낮은 우선순위
                    "title": line.strip(),
                    "line_number": i + 1,
                    "type": "list_item",
                    "parent_section": current_section
                })
        
        return {
            "structure": hierarchy,
            "total_sections": len([h for h in hierarchy if h["type"] == "header"]),
            "depth": max([h["level"] for h in hierarchy if h["type"] == "header"], default=0)
        }

    def semantic_chunking(self, content: str, hierarchy: Dict) -> List[Dict]:
        """의미 기반 청킹"""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            line_size = len(line)
            
            # 섹션 경계 확인
            is_section_boundary = any(re.match(pattern, line) for pattern in self.section_patterns)
            
            # 청크 크기가 목표를 초과하거나 섹션 경계인 경우
            if (current_size + line_size > self.target_chunk_size and current_chunk) or \
               (is_section_boundary and current_chunk and current_size > 200):
                
                # 현재 청크 저장
                chunks.append({
                    "content": '\n'.join(current_chunk),
                    "size": current_size,
                    "start_line": i - len(current_chunk) + 1,
                    "end_line": i
                })
                
                # 오버랩을 위해 마지막 몇 줄 보존
                overlap_lines = []
                overlap_size = 0
                for j in range(len(current_chunk) - 1, -1, -1):
                    if overlap_size + len(current_chunk[j]) <= self.overlap_size:
                        overlap_lines.insert(0, current_chunk[j])
                        overlap_size += len(current_chunk[j])
                    else:
                        break
                
                current_chunk = overlap_lines
                current_size = overlap_size
            
            current_chunk.append(line)
            current_size += line_size
            i += 1
        
        # 마지막 청크 처리
        if current_chunk:
            chunks.append({
                "content": '\n'.join(current_chunk),
                "size": current_size,
                "start_line": i - len(current_chunk) + 1,
                "end_line": i
            })
        
        return chunks

    def extract_semantic_tags(self, content: str) -> List[str]:
        """의미 태그 추출"""
        tags = []
        content_lower = content.lower()
        
        for tag, keywords in self.semantic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                tags.append(tag)
        
        return tags

    def generate_keywords(self, content: str) -> List[str]:
        """한국어 키워드 추출"""
        # 단순한 키워드 추출 (실제 구현시 형태소 분석기 사용 권장)
        keywords = []
        
        # 한글 명사 패턴 추출 (2-8자)
        korean_nouns = re.findall(r'[가-힣]{2,8}', content)
        
        # 빈도 기반 필터링
        word_freq = {}
        for word in korean_nouns:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 상위 빈도 단어들을 키워드로 선정
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:20] if freq > 1]
        
        return keywords

    def generate_summary(self, content: str) -> str:
        """요약 생성 (단순한 추출 기반)"""
        sentences = re.split(r'[.!?]\s*', content)
        
        # 첫 번째와 마지막 문장, 그리고 가장 긴 문장들 선택
        if len(sentences) <= 3:
            return content[:200] + "..." if len(content) > 200 else content
        
        summary_parts = [sentences[0]]  # 첫 문장
        
        # 가장 긴 문장 추가
        longest_sentence = max(sentences[1:-1], key=len, default="")
        if longest_sentence and longest_sentence not in summary_parts:
            summary_parts.append(longest_sentence)
        
        # 마지막 문장 추가
        if sentences[-1] and sentences[-1] not in summary_parts:
            summary_parts.append(sentences[-1])
        
        summary = ". ".join(summary_parts)
        return summary[:300] + "..." if len(summary) > 300 else summary

    def generate_question_variants(self, content: str) -> List[str]:
        """질문 변형 생성"""
        questions = []
        
        # 내용 기반 질문 패턴
        if "금지" in content or "제한" in content:
            questions.append("무엇이 금지되나요?")
            questions.append("어떤 제한사항이 있나요?")
        
        if "승인" in content or "허가" in content:
            questions.append("승인 조건은 무엇인가요?")
            questions.append("어떻게 승인받을 수 있나요?")
        
        if "템플릿" in content:
            questions.append("템플릿 작성 방법은?")
            questions.append("템플릿 규칙은 무엇인가요?")
        
        # 일반적인 질문 추가
        keywords = self.generate_keywords(content)
        if keywords:
            questions.append(f"{keywords[0]}에 대해 알려주세요")
            questions.append(f"{keywords[0]}와 관련된 정책은?")
        
        return questions[:5]  # 최대 5개

    def get_context(self, chunks: List[Dict], current_index: int) -> Dict[str, str]:
        """이전/다음 컨텍스트 추출"""
        context = {"prev_content": "", "next_content": ""}
        
        if current_index > 0:
            prev_chunk = chunks[current_index - 1]
            context["prev_content"] = prev_chunk["content"][-200:] + "..."
        
        if current_index < len(chunks) - 1:
            next_chunk = chunks[current_index + 1]
            context["next_content"] = "..." + next_chunk["content"][:200]
        
        return context

    def process_file(self, file_path: Path) -> List[EnhancedChunk]:
        """파일 처리"""
        print(f"처리 중: {file_path.name}")
        
        # 파일 읽기
        content = self.read_markdown_file(file_path)
        
        # 계층 구조 추출
        hierarchy = self.extract_hierarchy(content)
        
        # 의미 기반 청킹
        chunks = self.semantic_chunking(content, hierarchy)
        
        enhanced_chunks = []
        
        for i, chunk_data in enumerate(chunks):
            chunk_content = chunk_data["content"]
            
            # 다중 표현 생성
            content_representations = {
                "original": chunk_content,
                "summarized": self.generate_summary(chunk_content),
                "keywords": self.generate_keywords(chunk_content),
                "question_variants": self.generate_question_variants(chunk_content)
            }
            
            # 메타데이터 생성
            metadata = {
                "document_hierarchy": hierarchy,
                "semantic_tags": self.extract_semantic_tags(chunk_content),
                "start_line": chunk_data["start_line"],
                "end_line": chunk_data["end_line"],
                "relationships": {
                    "has_previous": i > 0,
                    "has_next": i < len(chunks) - 1,
                    "position_in_document": f"{i+1}/{len(chunks)}"
                }
            }
            
            # 컨텍스트 추출
            context = self.get_context(chunks, i)
            
            # 고유 ID 생성
            content_hash = hashlib.md5(chunk_content.encode('utf-8')).hexdigest()
            chunk_id = f"{file_path.stem}_{i:03d}_{content_hash[:8]}"
            
            enhanced_chunk = EnhancedChunk(
                id=chunk_id,
                document_name=file_path.name,
                chunk_index=i,
                content=content_representations,
                metadata=metadata,
                context=context,
                char_count=len(chunk_content),
                created_at="2024-12-20T00:00:00Z"
            )
            
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks

    def save_to_jsonl(self, chunks: List[EnhancedChunk], output_file: Path):
        """JSONL 형태로 저장"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                json_line = json.dumps(asdict(chunk), ensure_ascii=False, separators=(',', ':'))
                f.write(json_line + '\n')

    def process_all_files(self):
        """모든 마크다운 파일 처리"""
        md_files = list(self.input_dir.glob("*.md"))
        
        if not md_files:
            print(f"'{self.input_dir}' 폴더에서 .md 파일을 찾을 수 없습니다.")
            return
        
        all_chunks = []
        file_stats = {}
        
        for md_file in md_files:
            try:
                chunks = self.process_file(md_file)
                all_chunks.extend(chunks)
                
                file_stats[md_file.name] = {
                    "chunks_count": len(chunks),
                    "total_chars": sum(chunk.char_count for chunk in chunks),
                    "avg_chunk_size": sum(chunk.char_count for chunk in chunks) // len(chunks) if chunks else 0
                }
                
                print(f"  - {len(chunks)}개 청크 생성, 평균 크기: {file_stats[md_file.name]['avg_chunk_size']}자")
                
            except Exception as e:
                print(f"오류 발생 - {md_file.name}: {str(e)}")
                continue
        
        # 결과 저장
        if all_chunks:
            output_file = self.output_dir / "enhanced_chunks.jsonl"
            self.save_to_jsonl(all_chunks, output_file)
            
            # 통계 정보 저장
            stats = {
                "total_files": len(md_files),
                "total_chunks": len(all_chunks),
                "total_characters": sum(chunk.char_count for chunk in all_chunks),
                "avg_chunk_size": sum(chunk.char_count for chunk in all_chunks) // len(all_chunks),
                "file_details": file_stats,
                "processing_date": "2024-12-20T00:00:00Z"
            }
            
            stats_file = self.output_dir / "processing_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            print(f"\n=== 처리 완료 ===")
            print(f"총 {len(all_chunks)}개 청크가 생성되어 {output_file}에 저장되었습니다.")
            print(f"통계 정보: {stats_file}")
            print(f"평균 청크 크기: {stats['avg_chunk_size']}자")
        
        else:
            print("처리된 청크가 없습니다.")

def main():
    # 경로 설정
    input_dir = "data/policies"
    output_dir = "data/enhanced_chunks"
    
    # 전처리기 초기화 및 실행
    preprocessor = AdvancedRAGPreprocessor(input_dir, output_dir)
    preprocessor.process_all_files()

if __name__ == "__main__":
    main()