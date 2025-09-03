import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def check_database_data():
    """데이터베이스 테이블의 데이터 상태 확인"""
    
    # MySQL 연결 설정 (.env 파일에서 로드)
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'steve'),
        'password': os.getenv('DB_PASSWORD', 'doolman'),
        'database': os.getenv('DB_NAME', 'alimtalk_ai'),
        'charset': os.getenv('DB_CHARSET', 'utf8mb4')
    }
    
    connection = None
    cursor = None
    
    try:
        # MySQL 서버에 연결
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)
        
        print("=== Database Connection Success ===")
        
        # template_requests 테이블 확인
        cursor.execute("SELECT COUNT(*) as count FROM template_requests")
        requests_count = cursor.fetchone()
        print(f"template_requests table count: {requests_count['count']}")
        
        # 최근 요청 5개 확인
        cursor.execute("SELECT * FROM template_requests ORDER BY created_at DESC LIMIT 5")
        recent_requests = cursor.fetchall()
        
        if recent_requests:
            print("\nRecent Requests:")
            for req in recent_requests:
                print(f"  ID: {req['id']}, Input: {req['user_input'][:50]}..., Created: {req['created_at']}")
        else:
            print("\nNo requests found!")
        
        # generated_templates 테이블 확인
        cursor.execute("SELECT COUNT(*) as count FROM generated_templates")
        templates_count = cursor.fetchone()
        print(f"\ngenerated_templates table count: {templates_count['count']}")
        
        # 최근 템플릿 5개 확인
        cursor.execute("""
            SELECT gt.id, gt.template_type, gt.prompt_tokens, gt.completion_tokens, 
                   gt.total_tokens, gt.token_cost, gt.created_at
            FROM generated_templates gt 
            ORDER BY gt.created_at DESC 
            LIMIT 5
        """)
        recent_templates = cursor.fetchall()
        
        if recent_templates:
            print("\nRecent Templates:")
            for tpl in recent_templates:
                print(f"  ID: {tpl['id']}, Type: {tpl['template_type']}, "
                      f"Tokens: {tpl['total_tokens']}, Cost: ${tpl['token_cost']}, "
                      f"Created: {tpl['created_at']}")
        else:
            print("\nNo templates found!")
        
        # token_usage_stats 테이블 확인
        cursor.execute("SELECT COUNT(*) as count FROM token_usage_stats")
        stats_count = cursor.fetchone()
        print(f"\ntoken_usage_stats table count: {stats_count['count']}")
        
        # 최근 통계 확인
        cursor.execute("SELECT * FROM token_usage_stats ORDER BY date DESC LIMIT 3")
        recent_stats = cursor.fetchall()
        
        if recent_stats:
            print("\nRecent Token Usage Stats:")
            for stat in recent_stats:
                print(f"  Date: {stat['date']}, Requests: {stat['total_requests']}, "
                      f"Tokens: {stat['total_tokens']}, Cost: ${stat['total_cost']}")
        else:
            print("\nNo token stats found!")
        
        # 테이블 구조 확인
        print("\ngenerated_templates table structure:")
        cursor.execute("DESCRIBE generated_templates")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col['Field']}: {col['Type']} ({col['Null']}, {col['Key']})")
            
    except Error as e:
        print(f"❌ MySQL 오류: {e}")
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    check_database_data()