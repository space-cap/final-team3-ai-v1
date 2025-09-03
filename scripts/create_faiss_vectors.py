import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path

def load_all_chunks():
    """모든 JSONL 파일에서 청크 데이터 로드"""
    data_dir = Path("data/cleaned_v4")
    all_chunks = []
    
    jsonl_files = list(data_dir.glob("*.jsonl"))
    
    for file_path in jsonl_files:
        print(f"Loading {file_path.name}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                chunk = json.loads(line.strip())
                all_chunks.append(chunk)
    
    return all_chunks

def create_faiss_index(chunks, model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'):
    """FAISS 인덱스 생성"""
    print(f"Loading sentence transformer model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # 텍스트 추출
    texts = [chunk['content'] for chunk in chunks]
    print(f"Encoding {len(texts)} chunks...")
    
    # 임베딩 생성
    embeddings = model.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')
    
    # FAISS 인덱스 생성
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # 내적 유사도 사용
    
    # 벡터 정규화 (cosine similarity를 위해)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    
    print(f"Created FAISS index with {index.ntotal} vectors, dimension: {dimension}")
    return index, model

def save_index_and_metadata(index, chunks, output_dir="data/vectors"):
    """인덱스와 메타데이터 저장"""
    os.makedirs(output_dir, exist_ok=True)
    
    # FAISS 인덱스 저장
    index_path = os.path.join(output_dir, "policy_chunks.faiss")
    faiss.write_index(index, index_path)
    print(f"FAISS index saved to {index_path}")
    
    # 메타데이터 저장 (청크 정보)
    metadata = []
    for i, chunk in enumerate(chunks):
        metadata.append({
            'index': i,
            'chunk_id': chunk['chunk_id'],
            'content': chunk['content'],
            'metadata': chunk['metadata']
        })
    
    metadata_path = os.path.join(output_dir, "chunks_metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"Metadata saved to {metadata_path}")
    
    return index_path, metadata_path

def main():
    print("Starting FAISS vector database creation...")
    
    # 데이터 로드
    chunks = load_all_chunks()
    print(f"Loaded {len(chunks)} chunks from cleaned_v4 data")
    
    # FAISS 인덱스 생성
    index, model = create_faiss_index(chunks)
    
    # 저장
    index_path, metadata_path = save_index_and_metadata(index, chunks)
    
    # 테스트 검색
    print("\nTesting search functionality...")
    test_query = "알림톡 템플릿 승인 거부 사유"
    query_embedding = model.encode([test_query])
    query_embedding = np.array(query_embedding).astype('float32')
    faiss.normalize_L2(query_embedding)
    
    k = 3
    scores, indices = index.search(query_embedding, k)
    
    print(f"\nTest query: '{test_query}'")
    print("Top 3 results:")
    for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
        chunk = chunks[idx]
        print(f"\n{i+1}. Score: {score:.4f}")
        print(f"   Source: {chunk['metadata']['source_file']}")
        print(f"   Content: {chunk['content'][:100]}...")
    
    print(f"\nFAISS vector database created successfully!")
    print(f"Index: {index_path}")
    print(f"Metadata: {metadata_path}")

if __name__ == "__main__":
    main()