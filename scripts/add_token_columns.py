import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def add_token_usage_columns():
    """generated_templates 테이블에 토큰 사용량 컬럼 추가"""
    
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
        cursor = connection.cursor()
        
        # 토큰 사용량 컬럼들 추가
        columns_to_add = [
            "ADD COLUMN prompt_tokens INT DEFAULT 0 COMMENT '프롬프트 토큰 수'",
            "ADD COLUMN completion_tokens INT DEFAULT 0 COMMENT '생성된 토큰 수'", 
            "ADD COLUMN total_tokens INT DEFAULT 0 COMMENT '총 토큰 수'",
            "ADD COLUMN token_cost DECIMAL(10,6) DEFAULT 0.000000 COMMENT '토큰 비용 (USD)'"
        ]
        
        for column in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE generated_templates {column}")
                print(f"Added column: {column}")
            except Error as e:
                if "Duplicate column name" in str(e):
                    print(f"Column already exists: {column}")
                else:
                    print(f"Error adding column {column}: {e}")
        
        # 토큰 사용량 통계 테이블 생성
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS token_usage_stats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            total_requests INT DEFAULT 0,
            total_prompt_tokens INT DEFAULT 0,
            total_completion_tokens INT DEFAULT 0,
            total_tokens INT DEFAULT 0,
            total_cost DECIMAL(10,6) DEFAULT 0.000000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_date (date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        connection.commit()
        print("Token usage columns and statistics table created successfully.")
        
    except Error as e:
        print(f"MySQL Error: {e}")
        if connection:
            connection.rollback()
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    add_token_usage_columns()