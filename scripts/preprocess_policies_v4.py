#!/usr/bin/env python3
"""
정책 문서 전처리 스크립트 v4
data/policies_v2의 모든 .md 파일을 RAG 시스템용으로 전처리
"""

import os
import json
import re
from typing import List, Dict, Any
from pathlib import Path
import hashlib

def clean_text(text: str) -> str:
    """불필요한 텍스트 제거 및 정제"""
    # 이미지 참조 제거
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'<img.*?>', '', text, flags=re.IGNORECASE)
    
    # 표 마크다운 정리 (표 구분선 제거)
    text = re.sub(r'\|[\s\-\|:]+\|', '', text)
    
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    
    # 연속된 공백 및 줄바꿈 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    # 마크다운 헤더 표시 간소화
    text = re.sub(r'^#{1,6}\s', '', text, flags=re.MULTILINE)
    
    # 불필요한 특수문자 제거
    text = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ.,!?():\-\[\]{}]', '', text)
    
    return text.strip()

def extract_keywords(text: str, filename: str) -> List[str]:
    """텍스트에서 키워드 추출"""
    keywords = []
    
    # 파일명 기반 키워드
    file_keywords = {
        'infotalk': ['알림톡', 'InfoTalk'],
        'content-guide': ['콘텐츠가이드', '템플릿작성', '가이드'],
        'audit': ['심사', '검수', '승인'],
        'operations': ['운영정책', '정책'],
        'publictemplate': ['공용템플릿', '템플릿'],
        'black-list': ['금지어', '블랙리스트', '제한사항'],
        'white-list': ['허용', '화이트리스트', '승인']
    }
    
    for key, words in file_keywords.items():
        if key in filename:
            keywords.extend(words)
    
    # 텍스트 내 주요 키워드 추출
    keyword_patterns = [
        r'알림톡|InfoTalk',
        r'템플릿|template',
        r'심사|검수|승인|approval',
        r'정책|policy|가이드|guide',
        r'콘텐츠|content',
        r'발송|전송|send',
        r'채널|channel',
        r'사업자|business',
        r'API',
        r'메시지|message'
    ]
    
    for pattern in keyword_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords.extend([match for match in matches if match not in keywords])
    
    return list(set(keywords))[:5]  # 최대 5개 키워드

def get_document_type(filename: str) -> str:
    """파일명 기반 문서 타입 결정"""
    if 'content-guide' in filename:
        return '콘텐츠가이드'
    elif 'audit' in filename:
        if 'black-list' in filename:
            return '심사정책-금지사항'
        elif 'white-list' in filename:
            return '심사정책-허용사항'
        else:
            return '심사정책'
    elif 'operations' in filename:
        return '운영정책'
    elif 'publictemplate' in filename:
        return '공용템플릿'
    elif 'infotalk' in filename:
        return '알림톡기본정책'
    else:
        return '기타정책'

def extract_section_from_text(text: str) -> str:
    """텍스트에서 섹션명 추출"""
    # 첫 번째 문장이나 주요 키워드를 섹션으로 사용
    first_line = text.split('\n')[0].strip()
    if len(first_line) > 50:
        first_line = first_line[:50] + '...'
    
    if not first_line:
        return '본문'
    
    return first_line

def semantic_chunk_text(text: str, min_chars: int = 200, max_chars: int = 400) -> List[str]:
    """의미 단위 기반 텍스트 청킹"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # 현재 청크에 문장을 추가했을 때의 길이 체크
        potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
        
        if len(potential_chunk) <= max_chars:
            current_chunk = potential_chunk
        else:
            # 현재 청크가 최소 길이를 만족하면 추가
            if len(current_chunk) >= min_chars:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                # 최소 길이를 만족하지 않으면 계속 추가 (최대 길이 초과하더라도)
                current_chunk = potential_chunk
    
    # 마지막 청크 처리
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def process_markdown_file(file_path: Path) -> List[Dict[str, Any]]:
    """마크다운 파일 처리하여 청크들 생성"""
    print(f"Processing: {file_path.name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 텍스트 정제
    cleaned_content = clean_text(content)
    
    # 의미 단위 청킹
    chunks = semantic_chunk_text(cleaned_content)
    
    # 청크별 메타데이터 생성
    chunk_data = []
    filename_base = file_path.stem
    doc_type = get_document_type(filename_base)
    
    for i, chunk_text in enumerate(chunks):
        if len(chunk_text.strip()) < 50:  # 너무 짧은 청크 제외
            continue
            
        chunk_id = f"{filename_base}_{i+1:03d}"
        keywords = extract_keywords(chunk_text, filename_base)
        section = extract_section_from_text(chunk_text)
        
        chunk_data.append({
            "chunk_id": chunk_id,
            "content": chunk_text.strip(),
            "metadata": {
                "source_file": file_path.name,
                "section": section,
                "keywords": keywords,
                "document_type": doc_type,
                "char_count": len(chunk_text),
                "chunk_index": i + 1
            }
        })
    
    return chunk_data

def main():
    """메인 처리 함수"""
    input_dir = Path("data/policies_v2")
    output_dir = Path("data/cleaned_v4")
    
    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_chunks = []
    file_stats = {}
    
    # 모든 .md 파일 처리
    md_files = list(input_dir.glob("*.md"))
    print(f"Found {len(md_files)} markdown files to process")
    
    for md_file in md_files:
        chunks = process_markdown_file(md_file)
        all_chunks.extend(chunks)
        
        file_stats[md_file.name] = {
            "chunk_count": len(chunks),
            "total_chars": sum(chunk["metadata"]["char_count"] for chunk in chunks),
            "avg_chunk_length": sum(chunk["metadata"]["char_count"] for chunk in chunks) // len(chunks) if chunks else 0
        }
    
    # 전체 결과를 JSON 파일로 저장
    output_file = output_dir / "processed_chunks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    
    # 통계 정보 저장
    stats = {
        "total_files": len(md_files),
        "total_chunks": len(all_chunks),
        "total_characters": sum(chunk["metadata"]["char_count"] for chunk in all_chunks),
        "average_chunk_length": sum(chunk["metadata"]["char_count"] for chunk in all_chunks) // len(all_chunks) if all_chunks else 0,
        "file_statistics": file_stats,
        "document_types": list(set(chunk["metadata"]["document_type"] for chunk in all_chunks))
    }
    
    stats_file = output_dir / "processing_statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 전처리 완료 ===")
    print(f"총 파일 수: {stats['total_files']}")
    print(f"총 청크 수: {stats['total_chunks']}")
    print(f"평균 청크 길이: {stats['average_chunk_length']}자")
    print(f"총 문자 수: {stats['total_characters']:,}")
    print(f"결과 파일: {output_file}")
    print(f"통계 파일: {stats_file}")
    
    print(f"\n=== 파일별 통계 ===")
    for filename, stat in file_stats.items():
        print(f"{filename}: {stat['chunk_count']}개 청크, 평균 {stat['avg_chunk_length']}자")

if __name__ == "__main__":
    main()