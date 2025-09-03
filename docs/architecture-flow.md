# 카카오 알림톡 템플릿 자동 생성 AI 서비스 아키텍처 및 처리 플로우

## 📋 목차
1. [시스템 아키텍처](#시스템-아키텍처)
2. [데이터 플로우](#데이터-플로우)
3. [주요 컴포넌트](#주요-컴포넌트)
4. [처리 과정 상세](#처리-과정-상세)
5. [API 플로우](#api-플로우)

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │   FastAPI       │    │  OpenAI GPT-4   │
│  (test_client.  │◄──►│    Server       │◄──►│      API        │
│     html)       │    │  (app/api)      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Template Gen.   │
                       │ (app/core)      │
                       └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
            ┌─────────────┐ ┌─────────┐ ┌─────────┐
            │   MySQL     │ │ FAISS   │ │ Policy  │
            │ Database    │ │ Vector  │ │  Docs   │
            │             │ │   DB    │ │(cleaned_│
            └─────────────┘ └─────────┘ │   v4)   │
                                        └─────────┘
```

## 🔄 데이터 플로우

### 1. 전처리 단계 (사전 준비)
```
정책 문서 (data/policies_v2) 
    ▼
전처리 스크립트 (preprocess_policies_v4.py)
    ▼
정제된 청크 (data/cleaned_v4/*.jsonl)
    ▼
FAISS 벡터화 (create_faiss_vectors.py)
    ▼
벡터 DB 저장 (data/vectors/)
```

### 2. 런타임 플로우
```
사용자 요청 (HTTP POST)
    ▼
FastAPI 엔드포인트 (/generate-template)
    ▼
AlimTalkTemplateGenerator.generate_template()
    ▼
┌─ RAG 검색 (FAISS) ─┐    ┌─ OpenAI API 호출 ─┐
│ 1. 쿼리 임베딩      │    │ 1. 프롬프트 구성   │
│ 2. 유사도 검색      │◄──►│ 2. GPT-4o-mini    │
│ 3. 정책 문서 추출   │    │ 3. 템플릿 생성     │
└────────────────────┘    └───────────────────┘
    ▼
템플릿 후처리
    ▼
JSON 응답 생성
    ▼
클라이언트 응답
```

## 🧩 주요 컴포넌트

### 1. 데이터 레이어
- **MySQL Database** (`alimtalk_ai`)
  - `template_requests`: 사용자 요청 저장
  - `generated_templates`: 생성된 템플릿 저장
  - `policy_documents`: 정책 문서 메타데이터

- **FAISS Vector DB**
  - `policy_chunks.faiss`: 정책 문서 벡터 인덱스
  - `chunks_metadata.json`: 청크 메타데이터

### 2. 핵심 서비스 레이어
- **AlimTalkTemplateGenerator** (`app/core/template_generator.py`)
  - RAG 기반 정책 검색
  - OpenAI API 연동
  - 템플릿 생성 및 후처리

### 3. API 레이어
- **FastAPI Application** (`app/api/main.py`)
  - RESTful API 엔드포인트
  - 요청/응답 모델 정의
  - CORS 설정

### 4. 클라이언트 레이어
- **Web Test Client** (`test_client.html`)
  - 사용자 친화적 인터페이스
  - 실시간 API 테스트

## 📊 처리 과정 상세

### Phase 1: 초기화
```python
# 1. 환경 설정 로드
load_dotenv()
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 2. FAISS 인덱스 로드
index = faiss.read_index("data/vectors/policy_chunks.faiss")

# 3. 임베딩 모델 로드
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
```

### Phase 2: RAG 검색
```python
# 1. 쿼리 구성
search_query = f"{user_input} {business_type} {message_purpose}"

# 2. 임베딩 생성
query_embedding = embedding_model.encode([search_query])

# 3. 유사도 검색
scores, indices = index.search(query_embedding, top_k=5)

# 4. 관련 정책 문서 추출
relevant_policies = [metadata[idx] for idx in indices[0]]
```

### Phase 3: 템플릿 생성
```python
# 1. 프롬프트 구성
prompt = f"""
당신은 카카오 알림톡 템플릿 전문가입니다.

사용자 요청: {user_input}
참고 정책: {policy_context}

JSON 형식으로 응답:
{{
    "title": "템플릿 제목",
    "template_content": "실제 템플릿 내용", 
    "compliance_notes": "준수 사항"
}}
"""

# 2. OpenAI API 호출
response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "AlimTalk expert..."},
        {"role": "user", "content": prompt}
    ]
)

# 3. 응답 파싱
template_result = json.loads(response.choices[0].message.content)
```

### Phase 4: 후처리
```python
# 1. 변수 추출
variables = extract_variables(template_content)

# 2. 템플릿 코드 생성
template_code = f"{business_type}_{message_purpose}"

# 3. 마크다운 포맷팅
formatted_content = format_template_content(
    template_code, template_content, variables, compliance_notes
)

# 4. 최종 JSON 구성
result = {
    "id": 1,
    "userId": user_id,
    "categoryId": 9101,
    "title": template_result['title'],
    "content": formatted_content,
    "variables": variables,
    "industries": [business_type],
    "purposes": [message_purpose]
}
```

## 🌐 API 플로우

### 엔드포인트별 처리 플로우

#### 1. `POST /generate-template`
```
HTTP Request
    ▼
Request Validation (Pydantic)
    ▼
AlimTalkTemplateGenerator.generate_template()
    ▼
┌─ RAG Search ─┐    ┌─ OpenAI Generation ─┐
│ Policy Docs  │    │ Template Content    │
└──────────────┘    └────────────────────┘
    ▼
Template Formatting
    ▼
Response (TemplateResponse Model)
    ▼
JSON Response to Client
```

#### 2. `POST /search-policies`
```
HTTP Request
    ▼
Query Validation
    ▼
FAISS Vector Search
    ▼
Metadata Retrieval
    ▼
PolicySearchResponse
    ▼
JSON Response
```

#### 3. `POST /generate-and-save`
```
Template Generation (위와 동일)
    ▼
MySQL Database Insert
    ▼
Response with DB Record ID
```

## 🔧 기술 스택별 역할

### 1. **OpenAI GPT-4o-mini**
- 자연스러운 한국어 템플릿 생성
- 정책 컨텍스트 기반 준수 템플릿 작성
- JSON 구조화된 응답 생성

### 2. **FAISS (Facebook AI Similarity Search)**
- 정책 문서 벡터 검색
- 코사인 유사도 기반 관련 문서 추출
- 실시간 RAG 검색 지원

### 3. **Sentence Transformers**
- 다국어 지원 임베딩 모델
- 한국어 특화 벡터 생성
- 의미적 유사도 계산

### 4. **FastAPI**
- 고성능 비동기 API 서버
- 자동 API 문서 생성 (OpenAPI/Swagger)
- Pydantic 기반 데이터 검증

### 5. **MySQL**
- 사용자 요청 및 생성 결과 영구 저장
- 템플릿 버전 관리
- 메타데이터 추적

## 📈 성능 최적화 포인트

### 1. 벡터 검색 최적화
- FAISS IndexFlatIP 사용 (내적 유사도)
- L2 정규화를 통한 코사인 유사도 계산
- 상위 K개 결과만 검색하여 속도 향상

### 2. OpenAI API 최적화
- Temperature 0.3으로 일관성 있는 결과
- Max tokens 1500으로 응답 크기 제한
- 시스템 프롬프트로 전문성 부여

### 3. 메모리 효율성
- 전역 생성기 인스턴스 재사용
- FAISS 인덱스 메모리 로드
- 임베딩 모델 캐싱

## 🛡️ 보안 및 컴플라이언스

### 1. API 보안
- CORS 설정으로 크로스 도메인 제어
- 환경변수를 통한 민감 정보 관리
- 입력 데이터 검증 (Pydantic)

### 2. 정책 준수
- RAG를 통한 실제 정책 문서 참조
- 컴플라이언스 점수 계산
- 금지어 및 규정 준수 체크

### 3. 데이터 보호
- MySQL 연결 풀링 및 자동 해제
- 트랜잭션 롤백 처리
- 민감 정보 로깅 방지

이 아키텍처는 확장 가능하고 유지보수가 용이하도록 모듈화되어 있으며, 각 컴포넌트가 명확한 책임을 가지도록 설계되었습니다.