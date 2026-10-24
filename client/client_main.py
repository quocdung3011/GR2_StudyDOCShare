import customtkinter as ctk
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.views.auth_view import AuthView
from client.views.dashboard_view import DashboardView

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("StudyDocShare - Chia sẻ Tài liệu Học tập")
        self.geometry("450x550")
        self.resizable(False, False)

        self.show_auth()

    def show_auth(self):
        if hasattr(self, 'dashboard_view'):
            self.dashboard_view.pack_forget()

        self.geometry("450x550")
        self.auth_view = AuthView(self, on_login_success=self.show_dashboard)
        self.auth_view.pack(fill="both", expand=True)

    def show_dashboard(self, session_token, current_user):
        self.auth_view.pack_forget()
        self.geometry("950x600")
        self.dashboard_view = DashboardView(self, session_token, current_user, on_logout=self.show_auth)
        self.dashboard_view.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = App()
    app.mainloop()