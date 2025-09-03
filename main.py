#!/usr/bin/env python3
"""
카카오 알림톡 템플릿 자동 생성 AI 서비스
심플한 메인 실행 파일
"""

import uvicorn
from app.api.main import app

if __name__ == "__main__":
    print("Starting AlimTalk Template Generator API Server...")
    print("API Documentation available at: http://localhost:8000/docs")
    print("Health check at: http://localhost:8000/health")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000
    )