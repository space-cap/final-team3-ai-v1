# 환경 설정 가이드

## 📋 환경변수 설정

프로젝트의 모든 설정은 `.env` 파일을 통해 관리됩니다.

### 1. .env 파일 생성

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음과 같이 설정하세요:

```bash
# OpenAI API 설정
OPENAI_API_KEY=sk-proj-your-openai-api-key-here

# MySQL 데이터베이스 설정
DB_HOST=localhost
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=alimtalk_ai
DB_CHARSET=utf8mb4
```

### 2. 설정 항목 상세 설명

#### OpenAI API 설정
- **OPENAI_API_KEY**: OpenAI GPT-4o-mini 모델 사용을 위한 API 키
  - [OpenAI 플랫폼](https://platform.openai.com/)에서 발급
  - `sk-proj-`로 시작하는 프로젝트 API 키 권장

#### MySQL 데이터베이스 설정
- **DB_HOST**: MySQL 서버 호스트 (기본값: `localhost`)
- **DB_USER**: MySQL 사용자명
- **DB_PASSWORD**: MySQL 비밀번호  
- **DB_NAME**: 데이터베이스 이름 (기본값: `alimtalk_ai`)
- **DB_CHARSET**: 문자 인코딩 (기본값: `utf8mb4`)

### 3. .env.example 참조

프로젝트에 포함된 `.env.example` 파일을 참조하여 설정하세요:

```bash
cp .env.example .env
# 이후 .env 파일의 값들을 실제 값으로 변경
```

## 🔐 보안 주의사항

### 1. .env 파일 보안
- `.env` 파일은 **절대 Git에 커밋하지 마세요**
- `.gitignore`에 `.env` 파일이 포함되어 있는지 확인
- API 키와 비밀번호 등 민감한 정보 포함

### 2. API 키 관리
- OpenAI API 키는 사용량 제한 설정 권장
- 정기적으로 API 키 회전 (rotation) 실행
- 개발/운영 환경별로 다른 API 키 사용

### 3. 데이터베이스 보안
- 강력한 비밀번호 사용
- 데이터베이스 사용자 권한 최소화
- 프로덕션 환경에서는 SSL 연결 사용

## 🏗️ 환경별 설정

### 개발 환경
```bash
# .env.development
OPENAI_API_KEY=sk-proj-development-key
DB_HOST=localhost
DB_USER=dev_user
DB_PASSWORD=dev_password
DB_NAME=alimtalk_ai_dev
DB_CHARSET=utf8mb4
```

### 운영 환경
```bash
# .env.production
OPENAI_API_KEY=sk-proj-production-key
DB_HOST=your-production-db-host
DB_USER=prod_user
DB_PASSWORD=strong-production-password
DB_NAME=alimtalk_ai
DB_CHARSET=utf8mb4
```

### 테스트 환경
```bash
# .env.test
OPENAI_API_KEY=sk-proj-test-key
DB_HOST=localhost
DB_USER=test_user
DB_PASSWORD=test_password
DB_NAME=alimtalk_ai_test
DB_CHARSET=utf8mb4
```

## 📦 종속성 확인

환경 설정 후 다음 패키지들이 올바르게 설치되어 있는지 확인하세요:

```bash
pip install python-dotenv  # 환경변수 로드
pip install mysql-connector-python  # MySQL 연결
pip install openai  # OpenAI API 클라이언트
```

## 🔍 환경 설정 검증

### 1. 환경변수 로드 확인
```python
from dotenv import load_dotenv
import os

load_dotenv()

# 환경변수 확인
print("OpenAI API Key loaded:", bool(os.getenv('OPENAI_API_KEY')))
print("DB Host:", os.getenv('DB_HOST'))
print("DB Name:", os.getenv('DB_NAME'))
```

### 2. MySQL 연결 테스트
```bash
python scripts/setup_database.py
```

성공 메시지가 출력되면 MySQL 설정이 올바릅니다:
```
Database and tables created successfully.
Policy documents metadata inserted successfully.
```

### 3. OpenAI API 연결 테스트
```bash
python app/core/template_generator.py
```

성공 메시지 출력 예시:
```
Template generator initialized with 52 policy chunks
Generated Template (New Format):
Title: 교육 특강안내
Variables: 5
Content length: 677
Success! Template generated with new format.
```

## 🚨 문제 해결

### 1. MySQL 연결 오류
```
MySQL Error: Access denied for user
```
**해결책**: DB 사용자명과 비밀번호 확인

### 2. OpenAI API 오류  
```
OpenAI API 오류: Incorrect API key provided
```
**해결책**: OPENAI_API_KEY 값 확인 및 재설정

### 3. 환경변수 로드 실패
```
KeyError: 'OPENAI_API_KEY'
```
**해결책**: 
- `.env` 파일 경로 확인
- `load_dotenv()` 호출 확인
- 환경변수명 오타 확인

## 🔄 환경 초기화

완전히 새로운 환경에서 시작하는 경우:

```bash
# 1. 가상환경 활성화
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac

# 2. 패키지 설치
pip install -r requirements.txt

# 3. .env 파일 설정
cp .env.example .env
# .env 파일 편집하여 실제 값 입력

# 4. 데이터베이스 초기화
python scripts/setup_database.py

# 5. FAISS 벡터 DB 생성 (처음 한 번만)
python scripts/create_faiss_vectors.py

# 6. 서버 실행
python main.py
```

이제 http://localhost:8000 에서 API가 정상 작동합니다! 🎉