#!/usr/bin/env python3
"""
JSON 파일을 문서 타입별 JSONL 파일로 분리
"""

import json
from pathlib import Path
from collections import defaultdict

def main():
    """JSON을 문서 타입별 JSONL로 분리"""
    input_file = Path("data/cleaned_v4/processed_chunks.json")
    output_dir = Path("data/cleaned_v4")
    
    # JSON 파일 읽기
    with open(input_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    # 문서 타입별로 그룹화
    doc_groups = defaultdict(list)
    
    for chunk in chunks:
        doc_type = chunk["metadata"]["document_type"]
        doc_groups[doc_type].append(chunk)
    
    # 파일명 매핑
    filename_mapping = {
        "콘텐츠가이드": "content-guide.jsonl",
        "알림톡기본정책": "infotalk-basic.jsonl", 
        "심사정책": "audit-policy.jsonl",
        "심사정책-금지사항": "audit-blacklist.jsonl",
        "심사정책-허용사항": "audit-whitelist.jsonl",
        "운영정책": "operations-policy.jsonl",
        "공용템플릿": "public-template.jsonl"
    }
    
    # 각 문서 타입별로 JSONL 파일 생성
    file_stats = {}
    
    for doc_type, chunks_list in doc_groups.items():
        filename = filename_mapping.get(doc_type, f"{doc_type}.jsonl")
        output_file = output_dir / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for chunk in chunks_list:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
        
        file_stats[filename] = {
            "document_type": doc_type,
            "chunk_count": len(chunks_list),
            "total_chars": sum(chunk["metadata"]["char_count"] for chunk in chunks_list),
            "file_size_kb": round(output_file.stat().st_size / 1024, 1)
        }
        
        print(f"Created: {filename} ({len(chunks_list)} chunks)")
    
    # 분리 통계 저장
    split_stats = {
        "total_files_created": len(file_stats),
        "total_chunks": sum(stat["chunk_count"] for stat in file_stats.values()),
        "file_details": file_stats
    }
    
    stats_file = output_dir / "split_statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(split_stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 분리 완료 ===")
    print(f"생성된 JSONL 파일: {len(file_stats)}개")
    print(f"총 청크 수: {split_stats['total_chunks']}")
    
    print(f"\n=== 파일별 상세 ===")
    for filename, stats in file_stats.items():
        print(f"{filename}: {stats['chunk_count']}개 청크, {stats['file_size_kb']}KB")

if __name__ == "__main__":
    main()