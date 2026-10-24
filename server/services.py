import os
import uuid
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.protocol import Protocol
from server.database import get_db_connection, hash_password

STORAGE_DIR = os.path.join(os.path.dirname(__file__), 'storage')
os.makedirs(STORAGE_DIR, exist_ok=True)

SESSIONS = {}

def log_activity(user_id, action, detail, ip_address="127.0.0.1"):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (user_id, action, detail, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, action, f"[{ip_address}] {detail}"))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[LOG ERROR] {e}")

def handle_register(data):
    username = data.get("username")
    password = data.get("password")
    full_name = data.get("full_name", "")
    university = data.get("university", "")

    if not username or not password:
        return Protocol.create_response(400, "Tên đăng nhập và mật khẩu không được để trống!")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return Protocol.create_response(400, "Tên đăng nhập đã tồn tại!")

    pwd_hash = hash_password(password)
    cursor.execute(
        "INSERT INTO users (username, password_hash, full_name, university, role) VALUES (?, ?, ?, ?, 'STUDENT')",
        (username, pwd_hash, full_name, university)
    )
    conn.commit()
    conn.close()
    return Protocol.create_response(200, "Đăng ký thành công! Bạn có thể đăng nhập ngay.")

def handle_login(data):
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return Protocol.create_response(400, "Vui lòng nhập đầy đủ thông tin!")

    conn = get_db_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    cursor.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (username, pwd_hash))
    user = cursor.fetchone()
    conn.close()

    if user:
        session_token = str(uuid.uuid4())
        user_info = {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "university": user["university"],
            "role": user["role"]
        }
        SESSIONS[session_token] = user_info
        log_activity(user["id"], "LOGIN", f"User '{username}' đăng nhập thành công")
        return Protocol.create_response(200, "Đăng nhập thành công!", {"token": session_token, "user": user_info})
    else:
        return Protocol.create_response(401, "Sai tên đăng nhập hoặc mật khẩu!")

def handle_list_files(data, user_info):
    parent_id = data.get("parent_id", 0)
    user_id = user_info.get("id", 0) if user_info else 0

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, u.full_name as owner_name 
        FROM documents d
        JOIN users u ON d.owner_id = u.id
        WHERE d.parent_id = ? AND (d.permission >= 755 OR d.owner_id = ?)
        ORDER BY d.is_directory DESC, d.title ASC
    ''', (parent_id, user_id))
    
    rows = cursor.fetchall()
    conn.close()
    
    files_list = [dict(row) for row in rows]
    return Protocol.create_response(200, "Thành công", {"files": files_list})

def handle_create_folder(data, user_info):
    folder_name = data.get("folder_name")
    parent_id = data.get("parent_id", 0)

    if not folder_name:
        return Protocol.create_response(400, "Tên thư mục không được để trống!")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO documents (title, file_name, storage_path, owner_id, parent_id, is_directory, permission)
        VALUES (?, ?, '', ?, ?, 1, 755)
    ''', (folder_name, folder_name, user_info['id'], parent_id))
    conn.commit()
    conn.close()
    
    log_activity(user_info['id'], "CREATE_FOLDER", f"Tạo thư mục '{folder_name}'")
    return Protocol.create_response(200, "Tạo thư mục thành công!")

def handle_search_files(data, user_info):
    keyword = data.get("keyword", "").strip()
    user_id = user_info.get("id", 0) if user_info else 0

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, u.full_name as owner_name 
        FROM documents d
        JOIN users u ON d.owner_id = u.id
        WHERE (d.title LIKE ? OR d.file_name LIKE ? OR d.course_name LIKE ? OR d.description LIKE ?) 
          AND d.is_directory = 0
          AND (d.permission >= 755 OR d.owner_id = ?)
        ORDER BY d.created_at DESC
    ''', (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", user_id))
    
    rows = cursor.fetchall()
    conn.close()
    
    if user_id > 0:
        log_activity(user_id, "SEARCH", f"Tìm kiếm từ khóa: '{keyword}'")
        
    return Protocol.create_response(200, "Tìm kiếm thành công", {"files": [dict(row) for row in rows]})

def handle_delete_node(data, user_info):
    node_id = data.get("node_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (node_id,))
    doc = cursor.fetchone()

    if not doc:
        conn.close()
        return Protocol.create_response(404, "Tài liệu không tồn tại!")

    # BẮT ĐẦU KIỂM TRA QUYỀN:
    # Admin xóa được mọi thứ. Sinh viên chỉ xóa được file do mình đăng.
    is_admin = user_info.get("role") == "ADMIN"
    is_owner = doc["owner_id"] == user_info.get("id")

    if not (is_admin or is_owner):
        conn.close()
        return Protocol.create_response(403, "Bạn không có quyền xóa tài liệu của người khác!")

    if not doc["is_directory"] and os.path.exists(doc["storage_path"]):
        try:
            os.remove(doc["storage_path"])
        except Exception:
            pass

    cursor.execute("DELETE FROM documents WHERE id = ?", (node_id,))
    conn.commit()
    conn.close()
    log_activity(user_info['id'], "DELETE", f"Xóa file/folder ID: {node_id}")
    return Protocol.create_response(200, "Xóa thành công!")

def handle_rename_node(data, user_info):
    node_id = data.get("node_id")
    new_title = data.get("new_title", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (node_id,))
    doc = cursor.fetchone()

    if not doc:
        conn.close()
        return Protocol.create_response(404, "Tài liệu không tồn tại!")

    is_admin = user_info.get("role") == "ADMIN"
    is_owner = doc["owner_id"] == user_info.get("id")

    if not (is_admin or is_owner):
        conn.close()
        return Protocol.create_response(403, "Bạn không có quyền đổi tên tài liệu này!")

    cursor.execute("UPDATE documents SET title = ? WHERE id = ?", (new_title, node_id))
    conn.commit()
    conn.close()
    log_activity(user_info['id'], "RENAME", f"Đổi tên ID {node_id} -> '{new_title}'")
    return Protocol.create_response(200, "Đổi tên thành công!")

def handle_chmod_node(data, user_info):
    node_id = data.get("node_id")
    permission = data.get("permission", 755)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (node_id,))
    doc = cursor.fetchone()

    if not doc or (doc["owner_id"] != user_info["id"] and user_info["role"] != "ADMIN"):
        conn.close()
        return Protocol.create_response(403, "Không có quyền đổi mức chia sẻ!")

    cursor.execute("UPDATE documents SET permission = ? WHERE id = ?", (permission, node_id))
    conn.commit()
    conn.close()
    log_activity(user_info['id'], "CHMOD", f"Đổi permission ID {node_id} -> {permission}")
    return Protocol.create_response(200, "Đổi phân quyền thành công!")

def handle_upload_file(client_socket, data, user_info):
    file_name = data.get("file_name")
    file_size = data.get("file_size", 0)
    parent_id = data.get("parent_id", 0)
    course_name = data.get("course_name", "").strip()
    description = data.get("description", "").strip()

    if not file_name or file_size <= 0:
        client_socket.sendall(Protocol.create_response(400, "File không hợp lệ!"))
        return

    unique_file_name = f"{str(uuid.uuid4())[:8]}_{file_name}"
    save_path = os.path.join(STORAGE_DIR, unique_file_name)

    client_socket.sendall(Protocol.create_response(200, "READY"))

    received_bytes = 0
    try:
        with open(save_path, "wb") as f:
            while received_bytes < file_size:
                chunk_size = min(64 * 1024, file_size - received_bytes)
                chunk = client_socket.recv(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                received_bytes += len(chunk)

        # Lưu thêm course_name và description vào Database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tạo tiêu đề đẹp hiển thị kèm môn học nếu có
        display_title = f"[{course_name}] {file_name}" if course_name else file_name

        cursor.execute('''
            INSERT INTO documents (title, file_name, file_size, storage_path, owner_id, parent_id, is_directory, permission, course_name, description)
            VALUES (?, ?, ?, ?, ?, ?, 0, 755, ?, ?)
        ''', (display_title, file_name, file_size, save_path, user_info['id'], parent_id, course_name, description))
        conn.commit()
        conn.close()

        log_activity(user_info['id'], "UPLOAD", f"Upload file '{file_name}' - Môn: '{course_name}'")
        client_socket.sendall(Protocol.create_response(200, f"Upload file '{file_name}' thành công!"))
    except Exception as e:
        client_socket.sendall(Protocol.create_response(500, f"Lỗi lưu trữ: {e}"))

def handle_download_file(client_socket, data, user_info):
    file_id = data.get("file_id")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ? AND is_directory = 0", (file_id,))
    doc = cursor.fetchone()

    user_id = user_info.get("id", 0) if user_info else 0
    if not doc or (doc["permission"] < 755 and doc["owner_id"] != user_id):
        conn.close()
        client_socket.sendall(Protocol.create_response(403, "Không có quyền tải tài liệu này!"))
        return

    cursor.execute("UPDATE documents SET download_count = download_count + 1 WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

    file_path = doc["storage_path"]
    if not os.path.exists(file_path):
        client_socket.sendall(Protocol.create_response(404, "File không tồn tại!"))
        return

    client_socket.sendall(Protocol.create_response(200, "START_DOWNLOAD", {
        "file_name": doc["file_name"],
        "file_size": doc["file_size"]
    }))

    client_socket.recv(1024)

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(64 * 1024)
            if not chunk:
                break
            client_socket.sendall(chunk)

    if user_id > 0:
        log_activity(user_id, "DOWNLOAD", f"Tải file '{doc['file_name']}'")