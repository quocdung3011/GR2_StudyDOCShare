import customtkinter as ctk
from tkinter import messagebox
from client.network import NetworkClient

class AuthView(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.on_login_success = on_login_success

        self.tabview = ctk.CTkTabview(self, width=400, height=500)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_login = self.tabview.add("Đăng Nhập")
        self.tab_register = self.tabview.add("Đăng Ký")

        self.setup_login_tab()
        self.setup_register_tab()

    def setup_login_tab(self):
        title = ctk.CTkLabel(self.tab_login, text="ĐĂNG NHẬP", font=("Arial", 22, "bold"))
        title.pack(pady=(20, 15))

        self.login_user = ctk.CTkEntry(self.tab_login, placeholder_text="Tên đăng nhập", width=280)
        self.login_user.pack(pady=8)

        self.login_pass = ctk.CTkEntry(self.tab_login, placeholder_text="Mật khẩu", show="*", width=280)
        self.login_pass.pack(pady=8)

        btn_login = ctk.CTkButton(self.tab_login, text="Đăng Nhập", command=self.handle_login, width=280)
        btn_login.pack(pady=10)

        btn_guest = ctk.CTkButton(self.tab_login, text="🚶 Vào xem với tư cách Khách (Guest)", fg_color="transparent", border_width=1, text_color="gray", command=self.handle_guest, width=280)
        btn_guest.pack(pady=10)

    def setup_register_tab(self):
        title = ctk.CTkLabel(self.tab_register, text="ĐĂNG KÝ TÀI KHOẢN", font=("Arial", 20, "bold"))
        title.pack(pady=(10, 15))

        self.reg_user = ctk.CTkEntry(self.tab_register, placeholder_text="Tên đăng nhập (*)", width=280)
        self.reg_user.pack(pady=8)

        self.reg_pass = ctk.CTkEntry(self.tab_register, placeholder_text="Mật khẩu (*)", show="*", width=280)
        self.reg_pass.pack(pady=8)

        self.reg_name = ctk.CTkEntry(self.tab_register, placeholder_text="Họ và tên", width=280)
        self.reg_name.pack(pady=8)

        self.reg_uni = ctk.CTkEntry(self.tab_register, placeholder_text="Trường ĐH (VD: ĐHBK Hà Nội)", width=280)
        self.reg_uni.pack(pady=8)

        btn_register = ctk.CTkButton(self.tab_register, text="Đăng Ký Ngay", fg_color="green", hover_color="darkgreen", command=self.handle_register, width=280)
        btn_register.pack(pady=20)

    def handle_login(self):
        username = self.login_user.get().strip()
        password = self.login_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin!")
            return

        res = NetworkClient.send_request("LOGIN", {"username": username, "password": password})
        if res and res.get("status") == 200:
            payload = res.get("payload", {})
            self.on_login_success(payload.get("token"), payload.get("user"))
        else:
            messagebox.showerror("Thất bại", res.get("message") if res else "Lỗi không xác định")

    def handle_guest(self):
        guest_user = {"id": 0, "username": "Guest", "full_name": "Khách Vãng Lai", "university": "Chưa đăng nhập", "role": "GUEST"}
        self.on_login_success(None, guest_user)

    def handle_register(self):
        username = self.reg_user.get().strip()
        password = self.reg_pass.get().strip()
        if not username or not password:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập Tên đăng nhập và Mật khẩu!")
            return

        res = NetworkClient.send_request("REGISTER", {
            "username": username, "password": password,
            "full_name": self.reg_name.get().strip(),
            "university": self.reg_uni.get().strip()
        })
        if res and res.get("status") == 200:
            messagebox.showinfo("Thành công", res.get("message"))
            self.tabview.set("Đăng Nhập")
        else:
            messagebox.showerror("Thất bại", res.get("message") if res else "Lỗi không xác định")