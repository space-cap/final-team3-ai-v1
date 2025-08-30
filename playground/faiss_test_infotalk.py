#!/usr/bin/env python3
"""
FAISS 벡터 DB 테스트 스크립트
infotalk-basic.jsonl 파일을 사용하여 FAISS 인덱스 생성 및 검색 테스트

필수 패키지:
pip install faiss-cpu sentence-transformers
"""

import json
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
import time

class FAISSVectorDB:
    """FAISS 벡터 데이터베이스 클래스"""
    
    def __init__(self, model_name: str = "jhgan/ko-sbert-nli"):
        """
        FAISS 벡터 DB 초기화
        
        Args:
            model_name: 한국어 문장 임베딩 모델명
        """
        print(f"임베딩 모델 로딩: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = None  # 벡터 차원 (모델 로딩 후 결정)
        self.index = None      # FAISS 인덱스
        self.documents = []    # 원본 문서 저장
        self.chunk_ids = []    # 청크 ID 저장
        
    def load_jsonl(self, file_path: str) -> List[Dict[str, Any]]:
        """
        JSONL 파일에서 문서 데이터 로딩
        
        Args:
            file_path: JSONL 파일 경로
            
        Returns:
            List[Dict]: 문서 청크 리스트
        """
        documents = []
        
        print(f"JSONL 파일 로딩: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    chunk = json.loads(line.strip())
                    documents.append(chunk)
                except json.JSONDecodeError as e:
                    print(f"JSON 파싱 에러 (라인 {line_num}): {e}")
                    continue
        
        print(f"총 {len(documents)}개 문서 청크 로딩 완료")
        return documents
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        텍스트 리스트를 벡터 임베딩으로 변환
        
        Args:
            texts: 임베딩할 텍스트 리스트
            
        Returns:
            np.ndarray: 임베딩 벡터 배열 (n_texts, embedding_dim)
        """
        print(f"{len(texts)}개 텍스트 임베딩 생성 중...")
        start_time = time.time()
        
        # 문장 임베딩 생성
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # numpy 배열로 변환 및 float32 타입으로 변경 (FAISS 요구사항)
        embeddings = np.array(embeddings, dtype=np.float32)
        
        end_time = time.time()
        print(f"임베딩 생성 완료: {end_time - start_time:.2f}초")
        print(f"임베딩 차원: {embeddings.shape[1]}")
        
        return embeddings
    
    def build_index(self, embeddings: np.ndarray, index_type: str = "flat"):
        """
        FAISS 인덱스 구축
        
        Args:
            embeddings: 임베딩 벡터 배열
            index_type: 인덱스 타입 ("flat", "ivf", "hnsw")
        """
        self.dimension = embeddings.shape[1]
        n_vectors = embeddings.shape[0]
        
        print(f"FAISS 인덱스 구축 중... (타입: {index_type})")
        
        if index_type == "flat":
            # L2 거리 기반 Flat 인덱스 (정확하지만 느림)
            self.index = faiss.IndexFlatL2(self.dimension)
            
        elif index_type == "ivf":
            # IVF (Inverted File) 인덱스 (빠르지만 근사치)
            nlist = min(100, n_vectors // 4)  # 클러스터 수
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            
            # 훈련 필요 (클러스터링을 위해)
            print(f"IVF 인덱스 훈련 중... (nlist={nlist})")
            self.index.train(embeddings)
            
        elif index_type == "hnsw":
            # HNSW (Hierarchical Navigable Small World) 인덱스
            M = 16  # 연결 수
            self.index = faiss.IndexHNSWFlat(self.dimension, M)
            
        else:
            raise ValueError(f"지원하지 않는 인덱스 타입: {index_type}")
        
        # 벡터 추가
        print("벡터 인덱스에 추가 중...")
        self.index.add(embeddings)
        
        print(f"인덱스 구축 완료: {self.index.ntotal}개 벡터")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        유사도 검색 수행
        
        Args:
            query: 검색 쿼리
            k: 반환할 상위 결과 수
            
        Returns:
            List[Dict]: 검색 결과 리스트
        """
        if self.index is None:
            raise ValueError("인덱스가 구축되지 않았습니다.")
        
        print(f"검색 쿼리: '{query}'")
        
        # 쿼리 임베딩 생성
        query_embedding = self.model.encode([query])
        query_embedding = np.array(query_embedding, dtype=np.float32)
        
        # 유사도 검색
        distances, indices = self.index.search(query_embedding, k)
        
        # 결과 포맷팅
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.documents):  # 유효한 인덱스 확인
                result = {
                    'rank': i + 1,
                    'chunk_id': self.chunk_ids[idx],
                    'distance': float(distance),
                    'similarity': 1 / (1 + distance),  # 거리를 유사도로 변환
                    'content': self.documents[idx]['content'],
                    'metadata': self.documents[idx]['metadata']
                }
                results.append(result)
        
        return results
    
    def save_index(self, index_path: str, metadata_path: str):
        """
        인덱스와 메타데이터를 파일로 저장
        
        Args:
            index_path: FAISS 인덱스 저장 경로
            metadata_path: 메타데이터 저장 경로
        """
        print(f"인덱스 저장 중: {index_path}")
        faiss.write_index(self.index, index_path)
        
        print(f"메타데이터 저장 중: {metadata_path}")
        metadata = {
            'documents': self.documents,
            'chunk_ids': self.chunk_ids,
            'dimension': self.dimension,
            'model_name': self.model.get_sentence_embedding_dimension()
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print("저장 완료")


def main():
    """메인 테스트 함수"""
    print("=== FAISS 벡터 DB 테스트 시작 ===\n")
    
    # 1. FAISS 벡터 DB 초기화
    vector_db = FAISSVectorDB(model_name="jhgan/ko-sbert-nli")
    
    # 2. JSONL 파일 로딩
    jsonl_path = "data/cleaned_v4/infotalk-basic.jsonl"
    if not Path(jsonl_path).exists():
        print(f"에러: 파일이 존재하지 않습니다: {jsonl_path}")
        return
    
    documents = vector_db.load_jsonl(jsonl_path)
    if not documents:
        print("에러: 로딩된 문서가 없습니다.")
        return
    
    # 3. 문서 데이터 준비
    print("\n문서 데이터 준비 중...")
    texts = []
    chunk_ids = []
    
    for doc in documents:
        texts.append(doc['content'])
        chunk_ids.append(doc['chunk_id'])
        vector_db.documents.append(doc)
    
    vector_db.chunk_ids = chunk_ids
    
    # 4. 임베딩 생성
    print("\n=== 임베딩 생성 ===")
    embeddings = vector_db.create_embeddings(texts)
    
    # 5. FAISS 인덱스 구축
    print("\n=== FAISS 인덱스 구축 ===")
    vector_db.build_index(embeddings, index_type="flat")
    
    # 6. 검색 테스트
    print("\n=== 검색 테스트 ===")
    test_queries = [
        "알림톡이란 무엇인가요?",
        "템플릿 심사 기준",
        "광고성 메시지 금지",
        "개인정보 보호",
        "카카오톡 채널 개설 방법"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        results = vector_db.search(query, k=3)
        
        if results:
            print(f"상위 {len(results)}개 검색 결과:")
            for result in results:
                print(f"\n[{result['rank']}위] 청크 ID: {result['chunk_id']}")
                print(f"유사도: {result['similarity']:.4f}")
                print(f"내용: {result['content'][:100]}...")
                print(f"섹션: {result['metadata']['section'][:50]}...")
        else:
            print("검색 결과가 없습니다.")
    
    # 7. 인덱스 저장 (선택적)
    print(f"\n=== 인덱스 저장 ===")
    save_option = input("인덱스를 저장하시겠습니까? (y/n): ").strip().lower()
    if save_option == 'y':
        index_path = "playground/infotalk_faiss.index"
        metadata_path = "playground/infotalk_metadata.json"
        vector_db.save_index(index_path, metadata_path)
    
    # 8. 성능 정보 출력
    print(f"\n=== 성능 정보 ===")
    print(f"총 문서 수: {len(documents)}")
    print(f"임베딩 차원: {embeddings.shape[1]}")
    print(f"인덱스 타입: Flat L2")
    print(f"모델: jhgan/ko-sbert-nli")
    
    print("\n=== 테스트 완료 ===")


if __name__ == "__main__":
    # 필요한 패키지 설치 확인
    try:
        import faiss
        import sentence_transformers
        print("필요한 패키지가 모두 설치되어 있습니다.")
    except ImportError as e:
        print(f"에러: 필요한 패키지가 설치되지 않았습니다: {e}")
        print("다음 명령어로 설치하세요:")
        print("pip install faiss-cpu sentence-transformers")
        exit(1)
    
    main()