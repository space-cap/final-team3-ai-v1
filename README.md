프로젝트 주제 : 카카오 알림톡 템플릿 자동 생성 AI 서비스 개발
프로젝트 제작 배경 : 소상공인들이 카카오 알림톡을 활용한 고객 관리를 시도할 때 가장 큰 어려움 중 하나는 까다로운 템플릿 승인 정책입니다. 수십 페이지에 달하는 가이드라인을 일일이 숙지하고 준수하기 어렵기 때문에, 많은 소상공인이 메시지 작성 단계에서부터 포기하거나 정책 위반으로 반려되는 경험을 합니다. 이는 소상공인의 효과적인 마케팅 활동을 방해하는 주요 진입 장벽이 됩니다.
본 프로젝트는 이 문제를 해결하기 위해, 사용자가 원하는 메시지 내용을 입력하면 AI가 카카오 알림톡 정책에 완벽하게 부합하는 템플릿을 자동으로 생성해주는 서비스를 개발하고자 합니다. 이를 통해 소상공인은 복잡한 정책을 고민할 필요 없이, 쉽고 빠르게 템플릿을 만들어 승인받고 마케팅에 활용할 수 있게 됩니다.

AI: LangChain, 에이전트(Agent), 도구(Tools), RAG, LangGraph, FAISS(Facebook AI Similarity Search)
DB: MySQL 8.4

카카오 알림톡 템플릿 자동 생성 AI 서비스를 위한 **폴더 구조**

## 폴더 구조

```
kakao-template-bot/
│
├── app/                          # 메인 애플리케이션
│   ├── __init__.py
│   ├── main.py                   # FastAPI 엔트리포인트
│   ├── api/                      # API 라우터
│   │   ├── __init__.py
│   │   ├── chat.py              # 챗봇 API 엔드포인트
│   │   └── template.py          # 템플릿 관련 API
│   │
│   ├── core/                     # 핵심 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── chatbot.py           # LangChain 챗봇 로직
│   │   ├── template_generator.py # 템플릿 생성 로직
│   │   └── policy_validator.py   # 카카오 정책 검증 로직
│   │
│   ├── services/                 # 서비스 레이어
│   │   ├── __init__.py
│   │   ├── rag_service.py       # RAG 구현
│   │   └── vector_service.py    # FAISS 벡터 검색
│   │
│   ├── models/                   # 데이터 모델
│   │   ├── __init__.py
│   │   ├── database.py          # MySQL 연결 설정
│   │   ├── template.py          # 템플릿 모델
│   │   └── chat_history.py      # 채팅 기록 모델
│   │
│   └── utils/                    # 유틸리티
│       ├── __init__.py
│       ├── config.py            # 설정 파일
│       └── helpers.py           # 도우미 함수
│
├── data/                         # 데이터 파일
│   ├── policies/                 # 카카오 정책 문서
│   │   ├── guideline.txt
│   │   └── policy_rules.json
│   │
│   ├── vectors/                  # FAISS 벡터 데이터
│   │   └── policy_vectors.index
│   │
│   └── templates/                # 샘플 템플릿
│       └── approved_samples.json
│
├── frontend/                     # 프론트엔드 (선택적)
│   ├── static/                   # CSS, JS
│   └── templates/                # HTML 템플릿
│
├── tests/                        # 테스트 코드
│   ├── test_chatbot.py
│   ├── test_template_generator.py
│   └── test_api.py
│
├── scripts/                      # 유틸리티 스크립트
│   ├── setup_db.py              # 데이터베이스 초기화
│   ├── load_policies.py         # 정책 데이터 로드
│   └── create_vectors.py        # FAISS 벡터 생성
│
├── requirements.txt              # 패키지 의존성
├── docker-compose.yml           # Docker 설정
├── .env.example                 # 환경변수 예시
├── .gitignore
└── README.md
```

## 핵심 파일 역할

### **app/core/ 디렉토리**

- **chatbot.py**: LangChain 기반 대화형 챗봇 구현
- **template_generator.py**: 사용자 입력을 카카오 정책에 맞는 템플릿으로 변환
- **policy_validator.py**: 생성된 템플릿의 정책 준수 여부 검증

### **app/services/ 디렉토리**

- **rag_service.py**: 정책 문서에서 관련 정보 검색 및 컨텍스트 제공
- **vector_service.py**: FAISS를 활용한 벡터 검색 및 유사도 매칭

### **data/ 디렉토리**

- **policies/**: 카카오 알림톡 가이드라인을 텍스트/JSON 형태로 저장
- **vectors/**: 전처리된 정책 데이터의 FAISS 인덱스 파일
- **templates/**: 승인받은 템플릿 샘플 데이터

## 주요 기술 스택별 구현 위치

- **LangChain**: `app/core/chatbot.py`에서 대화 플로우 관리
- **RAG**: `app/services/rag_service.py`에서 정책 문서 검색
- **LangGraph**: `app/core/template_generator.py`에서 템플릿 생성 워크플로우
- **FAISS**: `app/services/vector_service.py`에서 벡터 검색
- **MySQL**: `app/models/`에서 데이터베이스 모델 정의

## 개발 시작 순서

1. **환경 설정**: `requirements.txt`, `.env` 파일 작성
2. **데이터 준비**: 카카오 정책 문서를 `data/policies/`에 저장
3. **벡터 생성**: `scripts/create_vectors.py`로 FAISS 인덱스 생성
4. **핵심 로직**: `app/core/` 디렉토리부터 개발 시작
5. **API 구현**: `app/api/` 디렉토리에서 REST API 개발
6. **테스트**: `tests/` 디렉토리에서 단위 테스트
