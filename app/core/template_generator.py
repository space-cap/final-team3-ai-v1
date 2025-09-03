import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import mysql.connector
from typing import List, Dict, Tuple, Optional
import openai
from datetime import datetime
import os
from dotenv import load_dotenv
import re

class AlimTalkTemplateGenerator:
    def __init__(self, 
                 faiss_index_path="data/vectors/policy_chunks.faiss",
                 metadata_path="data/vectors/chunks_metadata.json",
                 model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        
        # .env 파일 로드
        load_dotenv()
        
        # OpenAI API 설정
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # FAISS 인덱스와 메타데이터 로드
        self.index = faiss.read_index(faiss_index_path)
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        # 임베딩 모델 로드
        self.embedding_model = SentenceTransformer(model_name)
        
        # MySQL 연결 설정
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'steve'),
            'password': os.getenv('DB_PASSWORD', 'doolman'),
            'database': os.getenv('DB_NAME', 'alimtalk_ai'),
            'charset': os.getenv('DB_CHARSET', 'utf8mb4')
        }
        
        print(f"Template generator initialized with {self.index.ntotal} policy chunks")

    def search_relevant_policies(self, query: str, top_k: int = 5) -> List[Dict]:
        """사용자 쿼리와 관련된 정책 문서 검색"""
        # 쿼리 임베딩
        query_embedding = self.embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # 검색 실행
        scores, indices = self.index.search(query_embedding, top_k)
        
        # 결과 포맷팅
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.metadata):
                chunk_data = self.metadata[idx]
                results.append({
                    'content': chunk_data['content'],
                    'metadata': chunk_data['metadata'],
                    'score': float(score)
                })
        
        return results

    def generate_template(self, user_input: str, business_type: str = "", message_purpose: str = "", user_id: int = 123) -> Dict:
        """사용자 입력을 기반으로 알림톡 템플릿 생성 (새로운 형식)"""
        
        # 관련 정책 검색
        search_query = f"{user_input} {business_type} {message_purpose}"
        relevant_policies = self.search_relevant_policies(search_query)
        
        # 정책 컨텍스트 구성
        policy_context = self._build_policy_context(relevant_policies)
        
        # OpenAI로 템플릿 생성
        template_result = self._generate_with_openai(user_input, business_type, message_purpose, policy_context)
        
        # 변수 추출
        variables = self._extract_variables(template_result['template_content'])
        
        # 템플릿 코드 생성
        template_code = self._generate_template_code(business_type, message_purpose)
        
        # 최종 결과 구성
        result = {
            "id": 1,
            "userId": user_id,
            "categoryId": 9101,  # 일반 카테고리
            "title": template_result['title'],
            "content": self._format_template_content(
                template_code=template_code,
                template_content=template_result['template_content'],
                variables=variables,
                compliance_notes=template_result['compliance_notes']
            ),
            "imageUrl": None,
            "type": "MESSAGE",
            "buttons": [],
            "variables": variables,
            "industries": [business_type] if business_type else [],
            "purposes": [message_purpose] if message_purpose else [],
            "token_usage": template_result.get('token_usage', {})
        }
        
        return result

    def _determine_template_type(self, user_input: str, policies: List[Dict]) -> str:
        """사용자 입력과 정책을 기반으로 템플릿 타입 결정"""
        # 단순한 규칙 기반으로 템플릿 타입 결정
        if "버튼" in user_input or "링크" in user_input or "확인" in user_input:
            return "부가정보형"
        elif "이미지" in user_input or "사진" in user_input:
            return "이미지형"
        elif "주문" in user_input or "배송" in user_input or "결제" in user_input:
            return "정보형"
        else:
            return "기본형"

    def _build_policy_context(self, policies: List[Dict]) -> str:
        """정책 문서들을 컨텍스트로 구성"""
        context_parts = []
        for policy in policies:
            context_parts.append(f"[{policy['metadata']['document_type']}]\n{policy['content']}")
        return "\n\n".join(context_parts)

    def _build_generation_prompt(self, user_input: str, business_type: str, 
                               message_purpose: str, policy_context: str, template_type: str) -> str:
        """템플릿 생성을 위한 프롬프트 구성"""
        
        prompt = f"""Generate KakaoTalk AlimTalk template.

User Request: {user_input}
Business Type: {business_type}
Message Purpose: {message_purpose}
Template Type: {template_type}

Policy Context:
{policy_context}

Rules:
1. Must comply with above policy content
2. Never include prohibited expressions
3. Structure according to {template_type} type
4. Write in natural Korean
5. Use variables in format: #{{variable_name}}

AlimTalk Template:"""

        return prompt

    def _generate_with_openai(self, user_input: str, business_type: str, message_purpose: str, policy_context: str) -> Dict:
        """OpenAI API를 사용하여 템플릿 생성 (토큰 사용량 추적 포함)"""
        
        prompt = f"""당신은 카카오 알림톡 템플릿 전문가입니다. 다음 요청에 따라 정책을 준수하는 알림톡 템플릿을 생성해주세요.

사용자 요청: {user_input}
업종: {business_type}
메시지 목적: {message_purpose}

참고할 카카오 알림톡 정책:
{policy_context}

요구사항:
1. 위 정책을 반드시 준수해야 합니다
2. 변수는 #{{변수명}} 형태로 표시하세요
3. 자연스러운 한국어로 작성하세요
4. 수신거부 링크를 포함하세요
5. 야간 전송 제한을 안내하세요
6. 정보통신망법을 준수하세요

응답 형식 (JSON):
{{
    "title": "템플릿 제목 (첫 줄 일부)",
    "template_content": "실제 알림톡 템플릿 내용",
    "compliance_notes": "정책 준수 관련 참고사항"
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in KakaoTalk AlimTalk template creation, specialized in Korean business communication and compliance."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # 토큰 사용량 추출
            token_usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
                'token_cost': self._calculate_token_cost(response.usage)
            }
            
            # JSON 응답 파싱
            content = response.choices[0].message.content
            # JSON 블록 추출
            if '```json' in content:
                json_content = content.split('```json')[1].split('```')[0].strip()
            elif '{' in content and '}' in content:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                json_content = content[json_start:json_end]
            else:
                json_content = content
            
            result = json.loads(json_content)
            # 토큰 사용량 정보 추가
            result['token_usage'] = token_usage
            return result
            
        except Exception as e:
            print(f"OpenAI API 오류: {e}")
            # 기본 템플릿 반환 (토큰 사용량 0)
            return {
                "title": f"{business_type} 알림톡 템플릿",
                "template_content": f"""안녕하세요, #{{고객명}}님.

{user_input}와 관련하여 안내드립니다.

#{{내용}}

문의사항이 있으시면 연락 주시기 바랍니다.

감사합니다.
#{{업체명}}

수신거부: #{{수신거부링크}}""",
                "compliance_notes": "정보통신망법을 준수하여 작성된 템플릿입니다.",
                "token_usage": {
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0,
                    'token_cost': 0.0
                }
            }
    
    def _calculate_token_cost(self, usage) -> float:
        """GPT-4o-mini 토큰 비용 계산"""
        # GPT-4o-mini 가격 (2024년 기준)
        # Input: $0.000150 per 1K tokens
        # Output: $0.000600 per 1K tokens
        input_cost = (usage.prompt_tokens / 1000) * 0.000150
        output_cost = (usage.completion_tokens / 1000) * 0.000600
        return round(input_cost + output_cost, 6)

    def _extract_variables(self, template_content: str) -> List[Dict]:
        """템플릿에서 변수 추출"""
        # #{변수명} 패턴 찾기
        pattern = r'#\{([^}]+)\}'
        variables_found = re.findall(pattern, template_content)
        
        variables = []
        for i, var_name in enumerate(set(variables_found), 1):
            variables.append({
                "id": i,
                "variableKey": var_name,
                "placeholder": f"#{{{var_name}}}",
                "inputType": "TEXT"
            })
        
        return variables

    def _generate_template_code(self, business_type: str, message_purpose: str) -> str:
        """템플릿 코드 생성"""
        business_code = business_type.replace(" ", "").replace("-", "")[:10] if business_type else "일반"
        purpose_code = message_purpose.replace(" ", "").replace("-", "")[:10] if message_purpose else "안내"
        return f"{business_code}_{purpose_code}"

    def _format_template_content(self, template_code: str, template_content: str, variables: List[Dict], compliance_notes: str) -> str:
        """템플릿 콘텐츠를 마크다운 형식으로 포맷"""
        
        # 변수 목록 생성
        variable_list = ""
        if variables:
            variable_list = "\n**변수:**\n\n"
            for var in variables:
                var_example = self._get_variable_example(var['variableKey'])
                variable_list += f"*   {var['placeholder']}: {var['variableKey']} (예: {var_example})\n"
        
        content = f"""## 알림톡 템플릿

**템플릿 코드:** {template_code}

**템플릿 내용:**

{template_content}
{variable_list}
**참고사항:**

*   {compliance_notes}
*   야간 시간 (21시 ~ 익일 8시)에는 전송되지 않습니다.
*   수신거부 링크를 통해 언제든지 수신을 거부할 수 있습니다.
"""
        return content

    def _get_variable_example(self, variable_key: str) -> str:
        """변수별 예시 값 제공"""
        examples = {
            "고객명": "홍길동",
            "업체명": "㈜패스트캠퍼스",
            "수신거부링크": "https://example.com/unsubscribe",
            "일시": "2025년 9월 5일 (금) 20시",
            "장소": "서울 강남구 역삼로 186, 6층",
            "주문번호": "20250905001",
            "금액": "25,000원",
            "배송상태": "배송중",
            "내용": "상세 내용"
        }
        
        for key, example in examples.items():
            if key in variable_key:
                return example
        
        return "예시 값"

    def _calculate_compliance_score(self, template: str, policies: List[Dict]) -> float:
        """생성된 템플릿의 정책 준수 점수 계산"""
        # 간단한 점수 계산 로직
        score = 1.0
        
        # 금지어 체크
        prohibited_words = ["ad", "marketing", "discount", "event", "benefit"]
        for word in prohibited_words:
            if word.lower() in template.lower():
                score -= 0.1
        
        # 길이 체크 (기본형 90자 제한)
        if len(template) > 90:
            score -= 0.2
        
        return max(0.0, min(1.0, score))

    def save_to_database(self, user_input: str, business_type: str, message_purpose: str, 
                        template_result: Dict) -> int:
        """생성된 템플릿을 데이터베이스에 저장 (토큰 사용량 포함)"""
        connection = None
        cursor = None
        
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            # 요청 정보 저장
            cursor.execute("""
                INSERT INTO template_requests (user_input, business_type, message_purpose)
                VALUES (%s, %s, %s)
            """, (user_input, business_type, message_purpose))
            
            request_id = cursor.lastrowid
            
            # 토큰 사용량 정보 추출
            token_usage = template_result.get('token_usage', {})
            
            # 생성된 템플릿 저장 (토큰 사용량 포함)
            cursor.execute("""
                INSERT INTO generated_templates 
                (request_id, template_content, template_type, compliance_score, used_policies,
                 prompt_tokens, completion_tokens, total_tokens, token_cost)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request_id,
                template_result.get('content', ''),  # 마크다운 형식 전체 콘텐츠
                template_result.get('type', 'MESSAGE'),
                1.0,  # 기본 컴플라이언스 점수
                json.dumps(template_result.get('industries', []), ensure_ascii=False),
                token_usage.get('prompt_tokens', 0),
                token_usage.get('completion_tokens', 0),
                token_usage.get('total_tokens', 0),
                token_usage.get('token_cost', 0.0)
            ))
            
            # 일일 토큰 사용량 통계 업데이트
            self._update_daily_token_stats(cursor, token_usage)
            
            connection.commit()
            return request_id
            
        except Exception as e:
            print(f"Database error: {e}")
            if connection:
                connection.rollback()
            return -1
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def _update_daily_token_stats(self, cursor, token_usage: Dict):
        """일일 토큰 사용량 통계 업데이트"""
        try:
            from datetime import date
            today = date.today()
            
            cursor.execute("""
                INSERT INTO token_usage_stats 
                (date, total_requests, total_prompt_tokens, total_completion_tokens, total_tokens, total_cost)
                VALUES (%s, 1, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                total_requests = total_requests + 1,
                total_prompt_tokens = total_prompt_tokens + %s,
                total_completion_tokens = total_completion_tokens + %s,
                total_tokens = total_tokens + %s,
                total_cost = total_cost + %s
            """, (
                today,
                token_usage.get('prompt_tokens', 0),
                token_usage.get('completion_tokens', 0),
                token_usage.get('total_tokens', 0),
                token_usage.get('token_cost', 0.0),
                token_usage.get('prompt_tokens', 0),
                token_usage.get('completion_tokens', 0),
                token_usage.get('total_tokens', 0),
                token_usage.get('token_cost', 0.0)
            ))
        except Exception as e:
            print(f"Token stats update error: {e}")

# 사용 예시
if __name__ == "__main__":
    generator = AlimTalkTemplateGenerator()
    
    # 테스트
    result = generator.generate_template(
        user_input="마케팅 특강 안내 메시지를 보내고 싶어요",
        business_type="교육",
        message_purpose="특강안내"
    )
    
    print("Generated Template (New Format):")
    print("Title:", result.get('title', 'N/A'))
    print("Variables:", len(result.get('variables', [])))
    print("Content length:", len(result.get('content', '')))
    print("Success! Template generated with new format.")