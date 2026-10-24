import json

class Protocol:
    @staticmethod
    def create_request(action, data=None, token=None):
        """Đóng gói yêu cầu từ Client thành định dạng JSON Byte Stream"""
        payload = {
            "action": action,
            "token": token,
            "data": data or {}
        }
        return json.dumps(payload).encode('utf-8')

    @staticmethod
    def create_response(status, message, payload=None):
        """Đóng gói phản hồi từ Server thành định dạng JSON Byte Stream"""
        response = {
            "status": status,
            "message": message,
            "payload": payload or {}
        }
        return json.dumps(response).encode('utf-8')

    @staticmethod
    def parse_message(raw_bytes):
        """Giải mã gói tin JSON từ dòng Byte"""
        try:
            return json.loads(raw_bytes.decode('utf-8'))
        except Exception:
            return None