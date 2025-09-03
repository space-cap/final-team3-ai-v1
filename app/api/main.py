from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import sys
import os

# 현재 파일의 경로를 기준으로 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from app.core.template_generator import AlimTalkTemplateGenerator

# FastAPI 앱 생성
app = FastAPI(
    title="AlimTalk Template Generator API",
    description="카카오 알림톡 템플릿 자동 생성 AI 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 템플릿 생성기 인스턴스
generator = None

@app.on_event("startup")
async def startup_event():
    """앱 시작시 템플릿 생성기 초기화"""
    global generator
    try:
        generator = AlimTalkTemplateGenerator()
        print("AlimTalk Template Generator initialized successfully")
    except Exception as e:
        print(f"Failed to initialize template generator: {e}")

# 요청/응답 모델 정의
class TemplateRequest(BaseModel):
    user_input: str
    business_type: Optional[str] = ""
    message_purpose: Optional[str] = ""

class PolicySearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class Variable(BaseModel):
    id: int
    variableKey: str
    placeholder: str
    inputType: str

class TemplateResponse(BaseModel):
    id: int
    userId: int
    categoryId: int
    title: str
    content: str
    imageUrl: Optional[str] = None
    type: str = "MESSAGE"
    buttons: List = []
    variables: List[Variable]
    industries: List[str]
    purposes: List[str]

class PolicySearchResponse(BaseModel):
    results: List[Dict]
    total_found: int

# API 엔드포인트
@app.get("/")
async def root():
    """API 상태 확인"""
    return {"message": "AlimTalk Template Generator API", "status": "active"}

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "generator_initialized": generator is not None,
        "api_version": "1.0.0"
    }

@app.post("/generate-template", response_model=TemplateResponse)
async def generate_template(request: TemplateRequest):
    """알림톡 템플릿 생성"""
    if not generator:
        raise HTTPException(status_code=500, detail="Template generator not initialized")
    
    try:
        result = generator.generate_template(
            user_input=request.user_input,
            business_type=request.business_type,
            message_purpose=request.message_purpose
        )
        
        return TemplateResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template generation failed: {str(e)}")

@app.post("/search-policies", response_model=PolicySearchResponse)
async def search_policies(request: PolicySearchRequest):
    """정책 문서 검색"""
    if not generator:
        raise HTTPException(status_code=500, detail="Template generator not initialized")
    
    try:
        results = generator.search_relevant_policies(
            query=request.query,
            top_k=request.top_k
        )
        
        return PolicySearchResponse(
            results=results,
            total_found=len(results)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy search failed: {str(e)}")

@app.post("/generate-and-save")
async def generate_and_save_template(request: TemplateRequest):
    """템플릿 생성 후 데이터베이스에 저장"""
    if not generator:
        raise HTTPException(status_code=500, detail="Template generator not initialized")
    
    try:
        # 템플릿 생성
        result = generator.generate_template(
            user_input=request.user_input,
            business_type=request.business_type,
            message_purpose=request.message_purpose
        )
        
        # 데이터베이스에 저장
        request_id = generator.save_to_database(
            user_input=request.user_input,
            business_type=request.business_type,
            message_purpose=request.message_purpose,
            template_result=result
        )
        
        return {
            "request_id": request_id,
            "template_result": result,
            "saved": request_id > 0
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template generation and save failed: {str(e)}")

@app.get("/template-types")
async def get_template_types():
    """사용 가능한 템플릿 타입 목록"""
    return {
        "template_types": [
            {"type": "기본형", "description": "기본적인 알림 메시지"},
            {"type": "부가정보형", "description": "버튼이나 추가 정보가 포함된 메시지"},
            {"type": "정보형", "description": "주문, 배송 등 구조화된 정보 메시지"},
            {"type": "이미지형", "description": "이미지가 포함된 메시지"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)