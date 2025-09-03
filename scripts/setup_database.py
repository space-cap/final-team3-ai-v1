import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def create_database_and_tables():
    """MySQL 데이터베이스와 테이블 생성"""
    
    # MySQL 연결 설정 (.env 파일에서 로드)
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'steve'),
        'password': os.getenv('DB_PASSWORD', 'doolman'),
        'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
        'collation': 'utf8mb4_unicode_ci'
    }
    
    connection = None
    cursor = None
    
    try:
        # MySQL 서버에 연결
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # 데이터베이스 생성
        db_name = os.getenv('DB_NAME', 'alimtalk_ai')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE {db_name}")
        
        # 사용자 템플릿 요청 테이블
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS template_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_input TEXT NOT NULL COMMENT '사용자 입력 메시지',
            business_type VARCHAR(100) COMMENT '업종',
            message_purpose VARCHAR(100) COMMENT '메시지 목적 (예: 주문확인, 배송안내 등)',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 생성된 템플릿 테이블
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS generated_templates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            request_id INT NOT NULL,
            template_content TEXT NOT NULL COMMENT '생성된 템플릿 내용',
            template_type VARCHAR(50) NOT NULL COMMENT '템플릿 유형 (기본형, 부가정보형 등)',
            compliance_score DECIMAL(3,2) COMMENT '정책 준수 점수 (0-1)',
            used_policies TEXT COMMENT '참조된 정책 문서 목록 (JSON)',
            status ENUM('draft', 'approved', 'rejected') DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES template_requests(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 정책 문서 메타데이터 테이블
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS policy_documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            document_type VARCHAR(50) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            chunk_count INT NOT NULL,
            total_chars INT NOT NULL,
            file_size_kb DECIMAL(10,2),
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        connection.commit()
        print("Database and tables created successfully.")
        
        # 정책 문서 메타데이터 삽입
        policy_data = [
            ('콘텐츠가이드', 'content-guide.jsonl', 11, 3669, 11.7),
            ('심사정책-금지사항', 'audit-blacklist.jsonl', 10, 3527, 11.2),
            ('심사정책-허용사항', 'audit-whitelist.jsonl', 4, 1493, 4.7),
            ('심사정책', 'audit-policy.jsonl', 9, 3689, 11.9),
            ('운영정책', 'operations-policy.jsonl', 9, 3116, 10.6),
            ('공용템플릿', 'public-template.jsonl', 3, 1779, 4.8),
            ('알림톡기본정책', 'infotalk-basic.jsonl', 6, 2090, 7.0)
        ]
        
        cursor.executemany("""
        INSERT INTO policy_documents (document_type, file_name, chunk_count, total_chars, file_size_kb)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        chunk_count = VALUES(chunk_count),
        total_chars = VALUES(total_chars),
        file_size_kb = VALUES(file_size_kb)
        """, policy_data)
        
        connection.commit()
        print("Policy documents metadata inserted successfully.")
        
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
    create_database_and_tables()