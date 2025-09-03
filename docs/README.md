# 카카오 알림톡 템플릿 자동 생성 AI 서비스 문서

## 📚 문서 목차

이 폴더에는 카카오 알림톡 템플릿 자동 생성 AI 서비스의 모든 기술 문서가 포함되어 있습니다.

### 🏗️ 아키텍처 및 기술 문서
- **[architecture-flow.md](./architecture-flow.md)** - 시스템 아키텍처 및 데이터 플로우 상세 분석
- **[development-process.md](./development-process.md)** - 단계별 개발 과정 및 기술적 구현 세부사항

## 🔍 문서별 주요 내용

### 1. Architecture & Flow (architecture-flow.md)
- 📊 **시스템 아키텍처 다이어그램**
  - 컴포넌트 간 관계도
  - 데이터 플로우 차트
  - 기술 스택별 역할 분석

- 🔄 **처리 플로우 상세**
  - RAG 검색 과정
  - OpenAI API 호출 플로우  
  - 템플릿 후처리 과정

- 🧩 **주요 컴포넌트 설명**
  - FAISS 벡터 DB 구조
  - MySQL 데이터베이스 스키마
  - FastAPI 서비스 레이어

### 2. Development Process (development-process.md)
- 📅 **단계별 개발 타임라인**
  - Phase 1: 프로젝트 분석
  - Phase 2: 인프라 구축
  - Phase 3: AI 엔진 개발
  - Phase 4: 출력 형식 구현
  - Phase 5: API 서비스 개발
  - Phase 6: 클라이언트 개발

- 🔧 **기술적 과제 해결 과정**
  - 인코딩 문제 해결
  - OpenAI API JSON 파싱 개선
  - FAISS 벡터 검색 최적화

- 📈 **성능 및 품질 지표**
  - 벡터 검색 성능 분석
  - API 응답 시간 측정
  - 시스템 안정성 평가

## 🚀 빠른 시작 가이드

### 전체 시스템 이해하기
1. **[architecture-flow.md](./architecture-flow.md)** 먼저 읽어보세요
   - 시스템 전체 구조 파악
   - 데이터 흐름 이해
   - 각 컴포넌트 역할 확인

2. **[development-process.md](./development-process.md)** 개발 과정 학습
   - 구현 단계별 상세 내용
   - 기술적 의사결정 배경
   - 코드 구현 방법론

### 개발자를 위한 추가 리소스

#### 📁 프로젝트 구조
```
docs/
├── README.md                    # 이 파일
├── architecture-flow.md         # 시스템 아키텍처 및 플로우
└── development-process.md       # 개발 과정 상세 문서
```

#### 🔗 관련 파일 참조
- **루트 디렉토리**: `../README_FINAL.md` - 사용자용 최종 가이드
- **API 문서**: http://localhost:8000/docs (서버 실행 시)
- **테스트 클라이언트**: `../test_client.html`

## 🎯 문서 활용 가이드

### 👥 대상자별 추천 문서

#### **프로젝트 매니저**
- [architecture-flow.md](./architecture-flow.md) - 시스템 아키텍처
- [development-process.md](./development-process.md) - 개발 단계 및 일정

#### **개발자**  
- [development-process.md](./development-process.md) - 구현 세부사항
- [architecture-flow.md](./architecture-flow.md) - 기술 스택 및 플로우

#### **운영자**
- [architecture-flow.md](./architecture-flow.md) - 성능 최적화 포인트
- [development-process.md](./development-process.md) - 배포 및 운영 가이드

### 🔄 문서 업데이트 정책

이 문서들은 시스템 변경사항에 따라 지속적으로 업데이트됩니다.

- **주요 기능 추가 시**: 아키텍처 문서 업데이트
- **성능 개선 시**: 개발 과정 문서 개선 사항 추가  
- **버그 수정 시**: 해결 과정 문서화

## ❓ 추가 지원

### 기술 문의
- **GitHub Issues**: 프로젝트 저장소의 Issues 탭
- **코드 리뷰**: Pull Request를 통한 개선 제안

### 문서 기여
문서 개선이나 추가 정보가 필요한 경우:
1. 해당 문서 파일을 직접 수정
2. Pull Request 생성
3. 리뷰 및 머지 과정

---

이 문서들을 통해 카카오 알림톡 템플릿 자동 생성 AI 서비스의 전체적인 이해와 효과적인 개발/운영이 가능합니다. 📚✨