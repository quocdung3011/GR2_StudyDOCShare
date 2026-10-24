import socket
import threading
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.protocol import Protocol
from server.database import init_db
from server.services import (
    SESSIONS, handle_register, handle_login, handle_list_files,
    handle_create_folder, handle_search_files, handle_delete_node,
    handle_rename_node, handle_chmod_node, handle_upload_file, handle_download_file
)

HOST = '0.0.0.0'
PORT = 2100

def handle_client(client_socket, client_address):
    print(f"[*] [MỚI] Client kết nối từ: {client_address}")
    try:
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            
            request = Protocol.parse_message(data)
            if not request:
                client_socket.sendall(Protocol.create_response(400, "Gói tin không hợp lệ!"))
                continue
            
            action = request.get("action")
            req_data = request.get("data", {})
            token = request.get("token")
            user_info = SESSIONS.get(token)

            if action == "REGISTER":
                client_socket.sendall(handle_register(req_data))
                continue
            elif action == "LOGIN":
                client_socket.sendall(handle_login(req_data))
                continue

            login_required = ["CREATE_FOLDER", "UPLOAD_FILE", "DELETE_NODE", "RENAME_NODE", "CHMOD_NODE"]
            if action in login_required and not user_info:
                client_socket.sendall(Protocol.create_response(401, "Bạn cần đăng nhập để thực hiện chức năng này!"))
                continue

            if action == "LIST_FILES":
                client_socket.sendall(handle_list_files(req_data, user_info))
            elif action == "SEARCH_FILES":
                client_socket.sendall(handle_search_files(req_data, user_info))
            elif action == "CREATE_FOLDER":
                client_socket.sendall(handle_create_folder(req_data, user_info))
            elif action == "DELETE_NODE":
                client_socket.sendall(handle_delete_node(req_data, user_info))
            elif action == "RENAME_NODE":
                client_socket.sendall(handle_rename_node(req_data, user_info))
            elif action == "CHMOD_NODE":
                client_socket.sendall(handle_chmod_node(req_data, user_info))
            elif action == "UPLOAD_FILE":
                handle_upload_file(client_socket, req_data, user_info)
                continue
            elif action == "DOWNLOAD_FILE":
                handle_download_file(client_socket, req_data, user_info)
                continue
            else:
                client_socket.sendall(Protocol.create_response(404, "Lệnh không hỗ trợ."))

    except Exception as e:
        print(f"[LỖI] Client {client_address}: {e}")
    finally:
        client_socket.close()
        print(f"[-] [RỜI MẠNG] Client {client_address} ngắt kết nối.")

def main():
    init_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"=== SERVER STUDYDOCSHARE ĐÃ KHỞI ĐỘNG CỔNG {PORT} ===")

    while True:
        client_socket, client_address = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        thread.start()

if __name__ == "__main__":
    main()