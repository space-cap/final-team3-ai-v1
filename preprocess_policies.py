#!/usr/bin/env python3
"""
카카오 알림톡 정책 문서 전처리 스크립트
RAG 시스템을 위한 문서 정리 및 정제
"""

import re
import html
import os
from pathlib import Path


def clean_markdown_content(content):
    """마크다운 콘텐츠 정리"""
    
    # 1. GitBook 마크업 제거
    content = re.sub(r'\{% hint.*?%\}', '', content, flags=re.MULTILINE)
    content = re.sub(r'\{% endhint %\}', '', content)
    content = re.sub(r'\{% tabs.*?%\}', '', content)
    content = re.sub(r'\{% tab.*?%\}', '', content)
    content = re.sub(r'\{% endtab.*?%\}', '', content)
    content = re.sub(r'\{% endtabs.*?%\}', '', content)
    content = re.sub(r'\{% content-ref.*?%\}', '', content)
    content = re.sub(r'\{% endcontent-ref %\}', '', content)
    
    # 2. HTML 태그 제거
    content = re.sub(r'<figure>.*?</figure>', '', content, flags=re.DOTALL)
    content = re.sub(r'<figcaption>.*?</figcaption>', '', content, flags=re.DOTALL)
    content = re.sub(r'<img[^>]*>', '', content)
    content = re.sub(r'<mark[^>]*>(.*?)</mark>', r'\1', content)
    content = re.sub(r'<[^>]+>', '', content)
    
    # 3. HTML 엔티티 디코딩
    content = html.unescape(content)
    content = content.replace('&#x26;', '&')
    content = content.replace('\\n', '\n')
    content = content.replace('\\\n', '\n')
    content = content.replace('\\-', '-')
    content = content.replace('\\(', '(')
    content = content.replace('\\)', ')')
    
    # 4. GitBook 링크 패턴 제거
    content = re.sub(r'\[.*?\]\(https://.*?gitbook\.io.*?\)', '', content)
    content = re.sub(r'https://.*?gitbook\.io[^\s\)]*', '', content)
    
    # 5. 불필요한 문자열 제거
    content = re.sub(r'alt=.*?token=[^\s"]*', '', content)
    content = re.sub(r'\?alt=media.*?token=[^\s"]*', '', content)
    content = re.sub(r'files\.gitbook\.io[^\s]*', '', content)
    
    # 6. 연속된 빈 줄 정리 (3개 이상의 연속 빈 줄을 2개로)
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    # 7. 특수 문자 정리
    content = re.sub(r'[◀▶►☞]', '', content)
    
    # 8. 앞뒤 공백 제거
    content = content.strip()
    
    return content


def preprocess_policy_file(input_path, output_path):
    """개별 정책 파일 전처리"""
    try:
        # 파일 읽기
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 전처리 실행
        cleaned_content = clean_markdown_content(content)
        
        # 정리된 내용 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"[OK] 전처리 완료: {input_path.name} -> {output_path.name}")
        
    except Exception as e:
        print(f"[ERROR] 전처리 실패: {input_path.name} - {str(e)}")


def main():
    """메인 실행 함수"""
    # 경로 설정
    policies_dir = Path("data/policies")
    cleaned_dir = Path("data/cleaned")
    
    # 출력 디렉토리 생성
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    
    # 모든 .md 파일 처리
    md_files = list(policies_dir.glob("*.md"))
    
    if not md_files:
        print("[ERROR] data/policies/ 폴더에 .md 파일이 없습니다.")
        return
    
    print(f"[INFO] {len(md_files)}개의 정책 문서 전처리 시작...")
    print("-" * 50)
    
    for md_file in md_files:
        output_file = cleaned_dir / md_file.name
        preprocess_policy_file(md_file, output_file)
    
    print("-" * 50)
    print(f"[SUCCESS] 전처리 완료! {len(md_files)}개 파일이 data/cleaned/ 폴더에 저장되었습니다.")


if __name__ == "__main__":
    main()