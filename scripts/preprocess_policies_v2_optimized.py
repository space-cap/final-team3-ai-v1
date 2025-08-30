"""
최적화된 policies_v2 마크다운 전처리 스크립트
- 텍스트 정규화 및 정제
- 중복 공백, 특수문자 처리
- 구조적 마크다운 요소 보존
- 한국어 텍스트 최적화
- 불필요한 메타데이터 제거
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

class OptimizedPolicyPreprocessor:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 처리 통계
        self.stats = {
            "processed_files": 0,
            "total_chars_original": 0,
            "total_chars_cleaned": 0,
            "processing_date": datetime.now().isoformat()
        }

    def clean_text_content(self, content: str) -> str:
        """텍스트 내용 정제"""
        
        # 1. 연속된 공백, 탭을 단일 공백으로 변경
        content = re.sub(r'[ \t]+', ' ', content)
        
        # 2. 연속된 개행을 최대 2개로 제한
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 3. 줄 시작/끝의 공백 제거 (마크다운 구조 보존)
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 마크다운 헤더, 리스트, 코드블록은 구조 보존
            if re.match(r'^#{1,6}\s', line) or \
               re.match(r'^[\s]*[-*+]\s', line) or \
               re.match(r'^[\s]*\d+\.\s', line) or \
               re.match(r'^```', line) or \
               re.match(r'^[\s]*\|', line):
                cleaned_lines.append(line.rstrip())
            else:
                cleaned_lines.append(line.strip())
        
        content = '\n'.join(cleaned_lines)
        
        # 4. 특수 문자 정규화
        # 전각 문자를 반각으로 변경
        content = content.replace('　', ' ')  # 전각 공백
        content = content.replace('＊', '*')
        content = content.replace('－', '-')
        
        # 5. 불필요한 마크다운 요소 정리
        # 빈 테이블 행 제거
        content = re.sub(r'\|\s*\|\s*\|\s*\n', '', content)
        
        # 6. 연속된 구분선(***) 정리
        content = re.sub(r'(\*{3,}\n?){2,}', '***\n', content)
        
        # 7. 시작/끝 공백 제거
        content = content.strip()
        
        return content

    def extract_metadata(self, content: str, filename: str) -> Dict:
        """파일 메타데이터 추출"""
        lines = content.split('\n')
        
        # 헤더 구조 분석
        headers = []
        for i, line in enumerate(lines):
            header_match = re.match(r'^(#{1,6})\s+(.+)', line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                headers.append({
                    "level": level,
                    "title": title,
                    "line": i + 1
                })
        
        # 문서 특성 분석
        char_count = len(content)
        line_count = len(lines)
        word_count = len(content.split())
        
        # 한국어 문장 수 추정
        korean_sentences = len(re.findall(r'[가-힣][^.!?]*[.!?]', content))
        
        # 주요 키워드 추출 (정책 문서용)
        policy_keywords = []
        keyword_patterns = [
            r'(승인|검토|심사|허가)',
            r'(거부|반려|금지|제한)',
            r'(템플릿|양식|형식)',
            r'(정책|규정|규칙|기준)',
            r'(광고|홍보|마케팅)',
            r'(개인정보|민감정보)',
        ]
        
        for pattern in keyword_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            policy_keywords.extend(matches)
        
        return {
            "filename": filename,
            "headers": headers,
            "stats": {
                "char_count": char_count,
                "line_count": line_count,
                "word_count": word_count,
                "korean_sentences": korean_sentences,
                "header_count": len(headers)
            },
            "policy_keywords": list(set(policy_keywords)),
            "document_type": self._classify_document_type(content, filename)
        }

    def _classify_document_type(self, content: str, filename: str) -> str:
        """문서 유형 분류"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        if 'audit' in filename_lower or '심사' in content_lower:
            return 'audit_policy'
        elif 'guide' in filename_lower or '가이드' in content_lower:
            return 'content_guide'
        elif 'operation' in filename_lower or '운영' in content_lower:
            return 'operation_policy'
        elif 'template' in filename_lower or '템플릿' in content_lower:
            return 'template_guide'
        elif 'infotalk' in filename_lower:
            return 'infotalk_policy'
        else:
            return 'general_policy'

    def process_file(self, file_path: Path) -> Tuple[str, Dict]:
        """단일 파일 처리"""
        print(f"처리 중: {file_path.name}")
        
        # 원본 파일 읽기
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except UnicodeDecodeError:
            # UTF-8로 읽기 실패 시 다른 인코딩 시도
            with open(file_path, 'r', encoding='cp949') as f:
                original_content = f.read()
        
        # 통계 업데이트
        self.stats["total_chars_original"] += len(original_content)
        
        # 텍스트 정제
        cleaned_content = self.clean_text_content(original_content)
        
        # 메타데이터 추출
        metadata = self.extract_metadata(cleaned_content, file_path.name)
        
        # 통계 업데이트
        self.stats["total_chars_cleaned"] += len(cleaned_content)
        
        reduction_percentage = ((len(original_content) - len(cleaned_content)) / len(original_content)) * 100
        print(f"  - 원본: {len(original_content):,}자 → 정제: {len(cleaned_content):,}자")
        print(f"  - 압축률: {reduction_percentage:.1f}%")
        
        return cleaned_content, metadata

    def save_cleaned_file(self, content: str, metadata: Dict, original_filename: str):
        """정제된 파일 저장"""
        
        # 파일명에서 확장자 제거
        base_name = Path(original_filename).stem
        
        # 정제된 마크다운 파일 저장
        cleaned_file = self.output_dir / f"{base_name}_cleaned.md"
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 메타데이터 JSON 파일 저장
        metadata_file = self.output_dir / f"{base_name}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return cleaned_file, metadata_file

    def process_all_files(self):
        """모든 마크다운 파일 처리"""
        md_files = list(self.input_dir.glob("*.md"))
        
        if not md_files:
            print(f"'{self.input_dir}' 폴더에서 .md 파일을 찾을 수 없습니다.")
            return
        
        print(f"총 {len(md_files)}개의 .md 파일을 처리합니다.\n")
        
        all_metadata = []
        
        for md_file in md_files:
            try:
                # 파일 처리
                cleaned_content, metadata = self.process_file(md_file)
                
                # 파일 저장
                cleaned_file, metadata_file = self.save_cleaned_file(
                    cleaned_content, metadata, md_file.name
                )
                
                all_metadata.append(metadata)
                self.stats["processed_files"] += 1
                
                print(f"  [완료] 저장: {cleaned_file.name}, {metadata_file.name}\n")
                
            except Exception as e:
                print(f"  [오류] 발생 - {md_file.name}: {str(e)}\n")
                continue
        
        # 전체 통계 저장
        self._save_processing_stats(all_metadata)
        
        print("=" * 50)
        print("처리 완료!")
        print(f"처리된 파일 수: {self.stats['processed_files']}")
        print(f"원본 총 문자 수: {self.stats['total_chars_original']:,}")
        print(f"정제 후 총 문자 수: {self.stats['total_chars_cleaned']:,}")
        
        if self.stats['total_chars_original'] > 0:
            total_reduction = ((self.stats['total_chars_original'] - self.stats['total_chars_cleaned']) 
                             / self.stats['total_chars_original']) * 100
            print(f"전체 압축률: {total_reduction:.1f}%")
        
        print(f"출력 디렉토리: {self.output_dir}")

    def _save_processing_stats(self, all_metadata: List[Dict]):
        """처리 통계 저장"""
        stats_file = self.output_dir / "processing_summary.json"
        
        summary = {
            "processing_stats": self.stats,
            "files_metadata": all_metadata,
            "document_types": {},
            "total_keywords": {}
        }
        
        # 문서 유형별 통계
        for metadata in all_metadata:
            doc_type = metadata.get("document_type", "unknown")
            summary["document_types"][doc_type] = summary["document_types"].get(doc_type, 0) + 1
        
        # 전체 키워드 통계
        for metadata in all_metadata:
            for keyword in metadata.get("policy_keywords", []):
                summary["total_keywords"][keyword] = summary["total_keywords"].get(keyword, 0) + 1
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"처리 통계 저장: {stats_file}")

def main():
    """메인 실행 함수"""
    input_dir = "data/policies_v2"
    output_dir = "data/cleaned_v3"
    
    print("카카오 알림톡 정책 문서 전처리 시작")
    print(f"입력 디렉토리: {input_dir}")
    print(f"출력 디렉토리: {output_dir}")
    print("-" * 50)
    
    # 전처리기 초기화 및 실행
    preprocessor = OptimizedPolicyPreprocessor(input_dir, output_dir)
    preprocessor.process_all_files()

if __name__ == "__main__":
    main()