# 카카오 알림톡 템플릿 자동 생성 AI 서비스

## 완성된 기능들

### 1. MySQL 데이터베이스 ✅
- **위치**: `scripts/setup_database.py`
- **테이블**: 
  - `template_requests`: 사용자 요청 저장
  - `generated_templates`: 생성된 템플릿 저장
  - `policy_documents`: 정책 문서 메타데이터
- **실행**: `python scripts/setup_database.py`

### 2. FAISS 벡터 데이터베이스 ✅
- **위치**: `scripts/create_faiss_vectors.py`
- **데이터**: `data/cleaned_v4/` 의 52개 정책 청크
- **저장**: `data/vectors/policy_chunks.faiss`, `data/vectors/chunks_metadata.json`
- **실행**: `python scripts/create_faiss_vectors.py`

### 3. RAG 기반 템플릿 생성기 ✅
- **위치**: `app/core/template_generator.py`
- **기능**:
  - 정책 문서 검색 (FAISS 기반)
  - 템플릿 타입 자동 결정
  - 정책 준수 점수 계산
  - 데이터베이스 저장
- **테스트**: `python app/core/template_generator.py`

### 4. FastAPI 웹 API ✅
- **위치**: `app/api/main.py`
- **엔드포인트**:
  - `GET /`: API 상태 확인
  - `GET /health`: 헬스 체크
  - `POST /generate-template`: 템플릿 생성
  - `POST /search-policies`: 정책 검색
  - `POST /generate-and-save`: 템플릿 생성 후 DB 저장
  - `GET /template-types`: 템플릿 타입 목록
- **문서**: http://localhost:8000/docs

### 5. 웹 테스트 클라이언트 ✅
- **위치**: `test_client.html`
- **기능**: 브라우저에서 API 테스트 가능

## 실행 방법

### 1. 환경 준비
```bash
# 가상환경 활성화
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac

# 패키지 설치
pip install -r requirements.txt
```

### 2. 데이터베이스 설정 (한번만 실행)
```bash
python scripts/setup_database.py
```

### 3. FAISS 벡터 DB 생성 (한번만 실행)
```bash
python scripts/create_faiss_vectors.py
```

### 4. API 서버 실행
```bash
python main.py
```

### 5. 테스트
- 브라우저에서 `test_client.html` 열기
- 또는 http://localhost:8000/docs 에서 API 테스트

## API 사용 예시

### 템플릿 생성
```bash
curl -X POST "http://localhost:8000/generate-template" \
-H "Content-Type: application/json" \
-d '{
  "user_input": "주문 확인 메시지를 보내고 싶어요",
  "business_type": "온라인쇼핑몰",
  "message_purpose": "주문확인"
}'
```

### 정책 검색
```bash
curl -X POST "http://localhost:8000/search-policies" \
-H "Content-Type: application/json" \
-d '{
  "query": "알림톡 승인 기준",
  "top_k": 3
}'
```

## 프로젝트 구조
```
final-team3-ai-v1/
├── app/
│   ├── core/
│   │   └── template_generator.py     # RAG 기반 템플릿 생성기
│   └── api/
│       └── main.py                   # FastAPI 웹 API
├── scripts/
│   ├── setup_database.py             # MySQL DB 설정
│   └── create_faiss_vectors.py       # FAISS 벡터 DB 생성
├── data/
│   ├── cleaned_v4/                   # 전처리된 정책 데이터 (52개 청크)
│   └── vectors/                      # FAISS 인덱스 및 메타데이터
├── main.py                           # API 서버 실행
├── test_client.html                  # 웹 테스트 클라이언트
└── requirements.txt                  # Python 패키지 목록
```

## 기술 스택
- **AI/ML**: LangChain, FAISS, sentence-transformers
- **DB**: MySQL 8.4
- **API**: FastAPI, Uvicorn
- **기타**: Python 3.13

## 주요 특징
1. **RAG 기반**: 52개 정책 문서 청크를 활용한 검색 증강 생성
2. **정책 준수**: 자동 컴플라이언스 점수 계산
3. **심플한 구조**: 전문가 수준의 간단하고 효율적인 구현
4. **확장 가능**: 모듈화된 구조로 쉬운 기능 추가

## 데이터베이스 정보
- **Host**: localhost
- **User**: steve
- **Password**: doolman
- **Database**: alimtalk_ai

모든 구성 요소가 정상 작동하며, 카카오 알림톡 정책에 맞는 템플릿을 자동 생성할 수 있습니다.