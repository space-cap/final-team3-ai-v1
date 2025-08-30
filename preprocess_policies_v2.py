import os
import re
import json
from typing import List, Dict, Any
from pathlib import Path

class PolicyPreprocessor:
    def __init__(self, input_dir: str = "data/policies_v2", output_dir: str = "data/cleaned_v2"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_metadata(self, content: str, filename: str) -> Dict[str, Any]:
        """파일 내용에서 메타데이터를 추출합니다."""
        metadata = {
            "source_file": filename,
            "total_length": len(content),
            "sections": [],
            "policy_type": self._classify_policy_type(filename),
            "main_topics": []
        }
        
        # 섹션 헤더 추출 (## 또는 ### 로 시작하는 제목들)
        section_pattern = r'^(#{1,3})\s+(.+)$'
        sections = re.findall(section_pattern, content, re.MULTILINE)
        
        for level, title in sections:
            metadata["sections"].append({
                "level": len(level),
                "title": title.strip(),
                "type": self._classify_section_type(title)
            })
        
        # 주요 토픽 추출
        metadata["main_topics"] = self._extract_main_topics(content, filename)
        
        return metadata
    
    def _classify_policy_type(self, filename: str) -> str:
        """파일명을 기반으로 정책 유형을 분류합니다."""
        if "content-guide" in filename:
            return "template_guide"
        elif "infotalk-audit" in filename and "black" in filename:
            return "blacklist_policy"
        elif "infotalk-audit" in filename and "white" in filename:
            return "whitelist_policy"
        elif "infotalk-audit" in filename:
            return "audit_policy"
        elif "infotalk-operations" in filename:
            return "operation_policy"
        elif "infotalk-publictemplate" in filename:
            return "public_template"
        elif "infotalk" in filename:
            return "basic_policy"
        else:
            return "general_policy"
    
    def _classify_section_type(self, title: str) -> str:
        """섹션 제목을 기반으로 섹션 유형을 분류합니다."""
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in ["가이드", "guide", "제작", "작성"]):
            return "guide"
        elif any(keyword in title_lower for keyword in ["심사", "기준", "승인", "반려"]):
            return "review_criteria"
        elif any(keyword in title_lower for keyword in ["블랙리스트", "불가", "금지", "제한"]):
            return "prohibited"
        elif any(keyword in title_lower for keyword in ["화이트리스트", "가능", "허용"]):
            return "allowed"
        elif any(keyword in title_lower for keyword in ["예시", "example", "샘플"]):
            return "example"
        elif any(keyword in title_lower for keyword in ["정보성", "메시지", "알림톡"]):
            return "message_type"
        elif any(keyword in title_lower for keyword in ["운영", "발송", "유의사항"]):
            return "operation"
        else:
            return "general"
    
    def _extract_main_topics(self, content: str, filename: str) -> List[str]:
        """내용에서 주요 토픽을 추출합니다."""
        topics = []
        
        # 파일별 주요 키워드 정의
        topic_keywords = {
            "content-guide": ["메시지 유형", "카드 유형", "템플릿", "포맷"],
            "infotalk-audit": ["심사 기준", "정보성 메시지", "승인", "반려"],
            "infotalk-audit-black": ["블랙리스트", "발송 불가", "금지", "제한"],
            "infotalk-audit-white": ["화이트리스트", "발송 가능", "허용"],
            "infotalk-operations": ["발송 유의사항", "운영정책", "가이드"],
            "infotalk-publictemplate": ["공용 템플릿", "변수", "표준화"],
            "infotalk": ["알림톡", "정보성 메시지", "비즈니스 채널"]
        }
        
        # 파일명에 맞는 키워드 찾기
        for key, keywords in topic_keywords.items():
            if key in filename:
                topics.extend(keywords)
                break
        
        # 내용에서 자주 언급되는 키워드 추가
        common_keywords = ["알림톡", "템플릿", "메시지", "발송", "심사", "승인", "가이드"]
        for keyword in common_keywords:
            if keyword in content and keyword not in topics:
                keyword_count = content.count(keyword)
                if keyword_count > 3:  # 3번 이상 언급된 키워드만 추가
                    topics.append(keyword)
        
        return list(set(topics))  # 중복 제거
    
    def chunk_content(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """내용을 적절한 크기로 청킹합니다."""
        chunks = []
        
        # 섹션별로 분할
        sections = self._split_by_sections(content)
        
        for i, section in enumerate(sections):
            section_content = section["content"].strip()
            if not section_content:
                continue
                
            # 섹션이 너무 길면 더 작게 분할
            if len(section_content) > 1500:
                sub_chunks = self._split_long_section(section_content, section["title"], section.get("level", 2))
                for j, sub_chunk in enumerate(sub_chunks):
                    chunks.append({
                        "chunk_id": f"section_{i}_sub_{j}",
                        "content": sub_chunk,
                        "section_title": section["title"],
                        "section_type": self._classify_section_type(section["title"]),
                        "section_level": section.get("level", 2),
                        "is_subsection": True,
                        "chunk_length": len(sub_chunk),
                        "metadata": metadata
                    })
            else:
                chunks.append({
                    "chunk_id": f"section_{i}",
                    "content": section_content,
                    "section_title": section["title"],
                    "section_type": self._classify_section_type(section["title"]),
                    "section_level": section.get("level", 2),
                    "is_subsection": False,
                    "chunk_length": len(section_content),
                    "metadata": metadata
                })
        
        return chunks
    
    def _split_by_sections(self, content: str) -> List[Dict[str, Any]]:
        """내용을 섹션별로 분할합니다."""
        sections = []
        
        # 헤더 패턴으로 분할
        section_pattern = r'^(#{1,3})\s+(.+)$'
        lines = content.split('\n')
        
        current_section = {"title": "", "content": "", "level": 1}
        
        for line in lines:
            header_match = re.match(section_pattern, line)
            
            if header_match:
                # 이전 섹션 저장
                if current_section["content"].strip():
                    sections.append(current_section.copy())
                
                # 새 섹션 시작
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                current_section = {
                    "title": title,
                    "content": line + '\n',
                    "level": level
                }
            else:
                current_section["content"] += line + '\n'
        
        # 마지막 섹션 저장
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections
    
    def _split_long_section(self, content: str, title: str, level: int) -> List[str]:
        """긴 섹션을 더 작은 청크로 분할합니다."""
        chunks = []
        
        # 단락별로 먼저 분할
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        current_chunk = f"{'#' * level} {title}\n\n"
        
        for paragraph in paragraphs:
            # 청크가 너무 길어지면 새로운 청크 시작
            if len(current_chunk + paragraph) > 1200:
                if len(current_chunk.strip()) > len(f"{'#' * level} {title}"):
                    chunks.append(current_chunk.strip())
                current_chunk = f"{'#' * level} {title}\n\n{paragraph}\n\n"
            else:
                current_chunk += paragraph + '\n\n'
        
        # 마지막 청크 추가
        if len(current_chunk.strip()) > len(f"{'#' * level} {title}"):
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [content]
    
    def process_file(self, file_path: Path) -> Dict[str, Any]:
        """단일 파일을 처리합니다."""
        print(f"Processing {file_path.name}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 메타데이터 추출
        metadata = self.extract_metadata(content, file_path.name)
        
        # 청킹
        chunks = self.chunk_content(content, metadata)
        
        result = {
            "source_file": file_path.name,
            "metadata": metadata,
            "chunks": chunks,
            "total_chunks": len(chunks),
            "processing_info": {
                "original_length": len(content),
                "avg_chunk_length": sum(chunk["chunk_length"] for chunk in chunks) / len(chunks) if chunks else 0
            }
        }
        
        return result
    
    def process_all_files(self) -> Dict[str, Any]:
        """모든 파일을 처리합니다."""
        all_results = {}
        
        # .md 파일들만 처리
        md_files = list(self.input_dir.glob("*.md"))
        print(f"Found {len(md_files)} markdown files to process")
        
        for file_path in md_files:
            try:
                result = self.process_file(file_path)
                all_results[file_path.stem] = result
                
                # 개별 파일 결과 저장
                output_file = self.output_dir / f"{file_path.stem}_processed.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"  → Saved to {output_file.name}")
                
            except Exception as e:
                print(f"Error processing {file_path.name}: {e}")
                continue
        
        # 전체 요약 저장
        summary = {
            "total_files_processed": len(all_results),
            "total_chunks": sum(result["total_chunks"] for result in all_results.values()),
            "files": {
                name: {
                    "chunks": result["total_chunks"],
                    "policy_type": result["metadata"]["policy_type"],
                    "main_topics": result["metadata"]["main_topics"],
                    "avg_chunk_length": result["processing_info"]["avg_chunk_length"]
                }
                for name, result in all_results.items()
            },
            "policy_types": list(set(result["metadata"]["policy_type"] for result in all_results.values()))
        }
        
        summary_file = self.output_dir / "processing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\nProcessing Summary:")
        print(f"  Total files processed: {summary['total_files_processed']}")
        print(f"  Total chunks created: {summary['total_chunks']}")
        print(f"  Policy types: {', '.join(summary['policy_types'])}")
        print(f"  Summary saved to: {summary_file.name}")
        
        return all_results

if __name__ == "__main__":
    processor = PolicyPreprocessor()
    results = processor.process_all_files()