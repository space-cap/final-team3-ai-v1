## notebooks/ 폴더 활용 예시

### **주요 노트북 파일별 용도**

- **01_data_exploration.ipynb**: 카카오 정책 문서 구조 분석, 데이터 전처리 실험
- **02_policy_analysis.ipynb**: 정책 규칙 패턴 분석, 키워드 추출 테스트
- **03_rag_testing.ipynb**: RAG 파이프라인 구성 및 검색 성능 테스트
- **04_template_generation.ipynb**: 템플릿 자동 생성 로직 프로토타이핑
- **05_langchain_experiments.ipynb**: LangChain 체인 구성 및 프롬프트 튜닝
- **06_faiss_vectorstore.ipynb**: FAISS 인덱스 생성/검색 성능 테스트
- **playground.ipynb**: 빠른 아이디어 테스트 및 디버깅용

### **개발 워크플로우**

1. **notebooks/**에서 프로토타이핑 및 실험
2. 검증된 로직을 **app/core/**로 모듈화
3. **tests/**에서 단위 테스트 작성
4. **app/api/**에서 API로 서비스화
