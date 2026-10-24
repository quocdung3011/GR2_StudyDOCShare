-- 1. Bảng lưu người dùng
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    university TEXT,
    role TEXT DEFAULT 'STUDENT',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng lưu thông tin Môn học (VD: IT3080 - Mạng máy tính)
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    course_name TEXT NOT NULL
);

-- 3. Bảng lưu Tài liệu & Thư mục (Áp dụng Phân quyền Linux)
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    storage_path TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    course_id INTEGER,
    parent_id INTEGER DEFAULT 0,       -- 0 là thư mục gốc, >0 là nằm trong folder khác
    is_directory BOOLEAN DEFAULT 0,    -- 0: là File, 1: là Folder
    permission INTEGER DEFAULT 755,    -- Phân quyền Linux (755: Công khai, 700: Riêng tư)
    download_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

-- 4. Bảng lưu Nhật ký hệ thống (Log)
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    detail TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Thêm thử 1 Môn học mẫu để test
INSERT INTO courses (course_code, course_name) VALUES ('IT3080', 'Mạng máy tính');