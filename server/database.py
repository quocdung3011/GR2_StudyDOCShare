import sqlite3
import hashlib
import os

# Đường dẫn file DB nằm trong thư mục data/
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'studocu_mini.db')

def get_db_connection():
    """Kết nối CSDL SQLite"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Băm mật khẩu SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    """Khởi tạo cấu trúc các bảng CSDL"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        university TEXT,
        role TEXT DEFAULT 'STUDENT',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT NOT NULL,
        course_name TEXT NOT NULL
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        storage_path TEXT NOT NULL,
        owner_id INTEGER NOT NULL,
        course_id INTEGER,
        course_name TEXT DEFAULT '',    -- Bổ sung Tên/Mã môn học
        description TEXT DEFAULT '',    -- Bổ sung Mô tả ngắn
        parent_id INTEGER DEFAULT 0,
        is_directory BOOLEAN DEFAULT 0,
        permission INTEGER DEFAULT 755,
        download_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES users(id)
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        detail TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # Tự tạo account Admin mặc định
    pwd_admin = hash_password("admin123")
    cursor.execute('''
        INSERT OR IGNORE INTO users (id, username, password_hash, full_name, university, role)
        VALUES (1, 'admin', ?, 'Quản Trị Viên', 'Hệ Thống', 'ADMIN')
    ''', (pwd_admin,))
    
    conn.commit()
    conn.close()
    print("[DB] Kiểm tra và khởi tạo Cơ sở dữ liệu thành công!")