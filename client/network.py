import socket
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.protocol import Protocol

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 2100

class NetworkClient:
    @staticmethod
    def send_request(action, data=None, token=None):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((SERVER_HOST, SERVER_PORT))
            
            req_bytes = Protocol.create_request(action, data, token)
            client.sendall(req_bytes)
            
            res_bytes = client.recv(4096)
            response = Protocol.parse_message(res_bytes)
            client.close()
            return response
        except Exception as e:
            return {"status": 500, "message": f"Không thể kết nối tới Server: {e}"}

    @staticmethod
    def upload_file(file_path, parent_id, token, course_name="", description=""):
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((SERVER_HOST, SERVER_PORT))

            # Bổ sung course_name và description vào JSON request
            req_bytes = Protocol.create_request("UPLOAD_FILE", {
                "file_name": file_name,
                "file_size": file_size,
                "parent_id": parent_id,
                "course_name": course_name,
                "description": description
            }, token=token)
            client.sendall(req_bytes)

            res_bytes = client.recv(4096)
            res = Protocol.parse_message(res_bytes)

            if res and res.get("status") == 200:
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(64 * 1024)
                        if not chunk:
                            break
                        client.sendall(chunk)

                done_bytes = client.recv(4096)
                done_res = Protocol.parse_message(done_bytes)
                client.close()
                return done_res
            client.close()
            return res
        except Exception as e:
            return {"status": 500, "message": f"Lỗi truyền file: {e}"}

    @staticmethod
    def download_file(file_id, save_path, token):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((SERVER_HOST, SERVER_PORT))

            req_bytes = Protocol.create_request("DOWNLOAD_FILE", {"file_id": file_id}, token=token)
            client.sendall(req_bytes)

            res_bytes = client.recv(4096)
            res = Protocol.parse_message(res_bytes)

            if res and res.get("status") == 200:
                file_size = res.get("payload", {}).get("file_size", 0)
                client.sendall(b"ACK")

                received_bytes = 0
                with open(save_path, "wb") as f:
                    while received_bytes < file_size:
                        chunk_size = min(64 * 1024, file_size - received_bytes)
                        chunk = client.recv(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        received_bytes += len(chunk)

                client.close()
                return {"status": 200, "message": "Tải file thành công!"}
            client.close()
            return res
        except Exception as e:
            return {"status": 500, "message": f"Lỗi download: {e}"}