import os
import customtkinter as ctk
from tkinter import messagebox, filedialog
from client.network import NetworkClient

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, session_token, current_user, on_logout):
        super().__init__(parent)
        self.session_token = session_token
        self.current_user = current_user
        self.on_logout = on_logout
        self.current_parent_id = 0

        self.setup_ui()

    def setup_ui(self):
        # Top Bar
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        self.search_entry = ctk.CTkEntry(top_frame, placeholder_text="Nhập tên tài liệu...", width=500)
        self.search_entry.pack(side="left", padx=10, pady=10)

        btn_search = ctk.CTkButton(top_frame, text="Tìm Kiếm", command=self.search_files, width=100)
        btn_search.pack(side="left", padx=5)

        btn_refresh = ctk.CTkButton(top_frame, text="Làm Mới", fg_color="gray", command=self.load_files, width=80)
        btn_refresh.pack(side="left", padx=5)

        # Sidebar
        sidebar = ctk.CTkFrame(self, width=200)
        sidebar.pack(side="left", fill="y", padx=10, pady=(0, 10))

        role_color = "red" if self.current_user['role'] == "ADMIN" else ("green" if self.current_user['role'] == "STUDENT" else "gray")
        lbl_user = ctk.CTkLabel(sidebar, text=f"👤 {self.current_user['username']}\nRole: {self.current_user['role']}", font=("Arial", 14, "bold"), text_color=role_color)
        lbl_user.pack(pady=20)

        if self.current_user['role'] != "GUEST":
            btn_new_folder = ctk.CTkButton(sidebar, text="+ Tạo Thư Mục", fg_color="orange", hover_color="darkorange", command=self.show_create_folder_dialog)
            btn_new_folder.pack(pady=8, padx=10, fill="x")

            btn_upload = ctk.CTkButton(sidebar, text="⬆ Upload Tài Liệu", fg_color="green", hover_color="darkgreen", command=self.upload_file)
            btn_upload.pack(pady=8, padx=10, fill="x")
        else:
            lbl_guest_note = ctk.CTkLabel(sidebar, text="⚠️ Vui lòng đăng nhập\nđể Upload & Download", font=("Arial", 11, "italic"), text_color="orange")
            lbl_guest_note.pack(pady=10)

        btn_logout = ctk.CTkButton(sidebar, text="🚪 Đăng Xuất", fg_color="darkred", command=self.on_logout)
        btn_logout.pack(side="bottom", pady=20, padx=10, fill="x")

        # Main Area
        self.main_frame = ctk.CTkScrollableFrame(self, label_text="Danh Sách Tài Liệu Học Tập")
        self.main_frame.pack(side="right", fill="both", expand=True, padx=10, pady=(0, 10))

        self.load_files()

    def load_files(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        res = NetworkClient.send_request("LIST_FILES", {"parent_id": self.current_parent_id}, token=self.session_token)
        if res and res.get("status") == 200:
            files = res.get("payload", {}).get("files", [])

            if self.current_parent_id != 0:
                btn_back = ctk.CTkButton(self.main_frame, text="⬅ Quay lại Thư mục gốc", fg_color="gray", command=self.go_back_root)
                btn_back.pack(anchor="w", pady=(0, 10))

            if not files:
                lbl_empty = ctk.CTkLabel(self.main_frame, text="Thư mục này chưa có tài liệu nào.", font=("Arial", 14, "italic"))
                lbl_empty.pack(pady=20)
                return

            user_role = self.current_user.get("role", "GUEST")
            current_uid = self.current_user.get("id", 0)

            for f in files:
                card = ctk.CTkFrame(self.main_frame)
                card.pack(fill="x", pady=5, padx=5)

                icon = "📁" if f["is_directory"] else "📄"
                perm_text = "🔒 Private" if f["permission"] == 700 else "🌐 Public"
                lbl_info = ctk.CTkLabel(card, text=f"{icon} {f['title']}  |  Đăng bởi: {f['owner_name']}  |  {perm_text}", font=("Arial", 13))
                lbl_info.pack(side="left", padx=10, pady=10)

                # 1. Nút Mở Folder
                if f["is_directory"]:
                    btn_open = ctk.CTkButton(card, text="Mở", width=60, height=25, fg_color="darkblue", command=lambda fid=f["id"]: self.open_folder(fid))
                    btn_open.pack(side="right", padx=5)

                # 2. Nút Download (Khách Guest không có quyền Tải Về)
                if not f["is_directory"] and user_role != "GUEST":
                    btn_download = ctk.CTkButton(card, text="Tải Về", width=60, height=25, command=lambda fid=f["id"]: self.download_file(fid))
                    btn_download.pack(side="right", padx=5)

                # 3. Phân quyền Quản trị:
                #    - Nếu user là ADMIN: Thấy đầy đủ nút Xóa / Sửa / Chmod của MỌI file.
                #    - Nếu user là STUDENT: Chỉ thấy nút Xóa / Sửa / Chmod của FILE CHÍNH MÌNH ĐĂNG.
                #    - Nếu user là GUEST: Không thấy nút quản trị nào.
                is_admin = (user_role == "ADMIN")
                is_owner = (user_role == "STUDENT" and f["owner_id"] == current_uid)

                if is_admin or is_owner:
                    btn_del = ctk.CTkButton(card, text="❌ Xóa", width=50, height=25, fg_color="red", hover_color="darkred", command=lambda fid=f["id"]: self.delete_node(fid))
                    btn_del.pack(side="right", padx=5)

                    btn_rename = ctk.CTkButton(card, text="✏ Đổi tên", width=65, height=25, fg_color="orange", hover_color="darkorange", command=lambda fid=f["id"], old_t=f["title"]: self.rename_node(fid, old_t))
                    btn_rename.pack(side="right", padx=5)

                    new_perm = 700 if f["permission"] == 755 else 755
                    btn_chmod = ctk.CTkButton(card, text="Riêng tư" if f["permission"] == 755 else "Công khai", width=70, height=25, fg_color="purple", hover_color="indigo", command=lambda fid=f["id"], p=new_perm: self.chmod_node(fid, p))
                    btn_chmod.pack(side="right", padx=5)

    def open_folder(self, folder_id):
        self.current_parent_id = folder_id
        self.load_files()

    def go_back_root(self):
        self.current_parent_id = 0
        self.load_files()

    def show_create_folder_dialog(self):
        dialog = ctk.CTkInputDialog(text="Nhập tên thư mục mới:", title="Tạo Thư Mục")
        folder_name = dialog.get_input()
        if folder_name:
            res = NetworkClient.send_request("CREATE_FOLDER", {"folder_name": folder_name, "parent_id": self.current_parent_id}, token=self.session_token)
            if res and res.get("status") == 200:
                self.load_files()
            else:
                messagebox.showerror("Lỗi", res.get("message"))

    def upload_file(self):
        """Mở cửa sổ điền thông tin phân loại trước khi Upload"""
        # 1. Mở cửa sổ Pop-up
        upload_window = ctk.CTkToplevel(self)
        upload_window.title("Upload & Phân Loại Tài Liệu")
        upload_window.geometry("400x420")
        upload_window.resizable(False, False)
        upload_window.grab_set()  # Giữ tiêu điểm trên cửa sổ này

        # Tên môn học / Mã môn
        lbl_course = ctk.CTkLabel(upload_window, text="Môn học / Mã môn (VD: IT3080 - Mạng máy tính):", font=("Arial", 12, "bold"))
        lbl_course.pack(padx=20, pady=(15, 5), anchor="w")
        entry_course = ctk.CTkEntry(upload_window, placeholder_text="Nhập tên môn học...", width=360)
        entry_course.pack(padx=20, pady=5)

        # Mô tả ngắn
        lbl_desc = ctk.CTkLabel(upload_window, text="Mô tả ngắn / Ghi chú tài liệu:", font=("Arial", 12, "bold"))
        lbl_desc.pack(padx=20, pady=(10, 5), anchor="w")
        entry_desc = ctk.CTkEntry(upload_window, placeholder_text="VD: Đề thi giữa kỳ 2023, Slide chương 2...", width=360)
        entry_desc.pack(padx=20, pady=5)

        # Chọn File
        selected_file_path = [""]  # Dùng list để lưu biến tham chiếu

        lbl_file = ctk.CTkLabel(upload_window, text="File tài liệu:", font=("Arial", 12, "bold"))
        lbl_file.pack(padx=20, pady=(10, 5), anchor="w")

        lbl_file_name = ctk.CTkLabel(upload_window, text="Chưa chọn file nào", font=("Arial", 11, "italic"), text_color="gray")
        lbl_file_name.pack(padx=20, pady=2)

        def choose_file():
            path = filedialog.askopenfilename(title="Chọn file tài liệu học tập")
            if path:
                selected_file_path[0] = path
                lbl_file_name.configure(text=os.path.basename(path), text_color="green")

        btn_choose = ctk.CTkButton(upload_window, text="📁 Chọn File từ máy tính", fg_color="gray", command=choose_file, width=360)
        btn_choose.pack(padx=20, pady=5)

        # Nút xác nhận Upload
        def confirm_upload():
            file_path = selected_file_path[0]
            course_name = entry_course.get().strip()
            description = entry_desc.get().strip()

            if not file_path:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn file tài liệu!")
                return

            upload_window.destroy()  # Đóng cửa sổ popup

            # Gọi helper Network để upload kèm metadata phân loại
            res = NetworkClient.upload_file(
                file_path=file_path,
                parent_id=self.current_parent_id,
                token=self.session_token,
                course_name=course_name,
                description=description
            )

            if res and res.get("status") == 200:
                messagebox.showinfo("Thành công", res.get("message"))
                self.load_files()
            else:
                messagebox.showerror("Lỗi", res.get("message") if res else "Upload thất bại")

        btn_confirm = ctk.CTkButton(upload_window, text="🚀 XÁC NHẬN UPLOAD", fg_color="green", hover_color="darkgreen", command=confirm_upload, width=360)
        btn_confirm.pack(padx=20, pady=(20, 10))

    def download_file(self, file_id):
        save_path = filedialog.asksaveasfilename(title="Chọn nơi lưu file")
        if not save_path:
            return
        res = NetworkClient.download_file(file_id, save_path, self.session_token)
        if res and res.get("status") == 200:
            messagebox.showinfo("Thành công", "Tải tài liệu về máy thành công!")
        else:
            messagebox.showerror("Lỗi", res.get("message") if res else "Lỗi download")

    def delete_node(self, node_id):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa?"):
            res = NetworkClient.send_request("DELETE_NODE", {"node_id": node_id}, token=self.session_token)
            if res and res.get("status") == 200:
                self.load_files()

    def rename_node(self, node_id, old_title):
        dialog = ctk.CTkInputDialog(text=f"Nhập tên mới cho '{old_title}':", title="Đổi Tên")
        new_title = dialog.get_input()
        if new_title:
            res = NetworkClient.send_request("RENAME_NODE", {"node_id": node_id, "new_title": new_title}, token=self.session_token)
            if res and res.get("status") == 200:
                self.load_files()

    def chmod_node(self, node_id, new_permission):
        res = NetworkClient.send_request("CHMOD_NODE", {"node_id": node_id, "permission": new_permission}, token=self.session_token)
        if res and res.get("status") == 200:
            self.load_files()

    def search_files(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            self.load_files()
            return
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        res = NetworkClient.send_request("SEARCH_FILES", {"keyword": keyword}, token=self.session_token)
        if res and res.get("status") == 200:
            files = res.get("payload", {}).get("files", [])
            for f in files:
                card = ctk.CTkFrame(self.main_frame)
                card.pack(fill="x", pady=5, padx=5)
                lbl_info = ctk.CTkLabel(card, text=f"📄 {f['title']}  |  Đăng bởi: {f['owner_name']}", font=("Arial", 13))
                lbl_info.pack(side="left", padx=10, pady=10)
                if self.current_user["role"] != "GUEST":
                    btn_download = ctk.CTkButton(card, text="Tải Về", width=60, height=25, command=lambda fid=f["id"]: self.download_file(fid))
                    btn_download.pack(side="right", padx=5)