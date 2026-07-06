# 🔐 Hệ thống Gửi Ảnh Bảo Mật Gắn Watermark (FIT4012)

<h2 align="center">
    <a href="[https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)">
    🎓 Faculty of Information Technology (DaiNam University)
    </a>
</h2>
<br>
<h2 align="center">
    CRYPTOGRAPHY AND CYBER SECURITY
</h2>
<br>
<div align="center">
    <p align="center">
        <img src="fitdnu_logo.png" alt="FIT Logo" width="180"/>
        <img src="dnu_logo.png" alt="DaiNam University Logo" width="200"/>
    </p>

[![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn)

</div>

## 📌 Giới thiệu
Dự án này là sản phẩm của bài tập lớn học phần **FIT4012 - Nhập môn An toàn bảo mật thông tin**, chủ đề **Secure System Upgrade Challenge (Đề tài 9)**. 

Hệ thống cung cấp nền tảng Web Chat Real-time tập trung chuyên sâu vào việc **chia sẻ ảnh bảo mật (Secure Image)** với các cơ chế phòng thủ đa lớp:
- **Xác thực người dùng an toàn:** Đăng ký/Đăng nhập với mật khẩu được băm (Password Hashing).
- **Phòng thủ Đa lớp (Defense in Depth):** Quét Input đầu vào để chống mã độc (Giới hạn 10MB, Whitelist, soi Magic Bytes).
- **Mã hóa E2EE:** Nâng cấp từ thuật toán cũ (DES) lên **AES-GCM (Mã hóa có xác thực)** kết hợp tự động quản lý cặp khóa **RSA-OAEP 2048-bit** cho mỗi người dùng.
- **Watermark & Metadata:** Gắn **Watermark chéo mờ (Diagonal)** tự động scale theo kích thước ảnh, đóng gói Metadata chống Replay Attack và chống cắt xén.

## 🧠 Công nghệ sử dụng

| Thành phần | Mô tả |
| :-- | :-- |
| **Python 3.10+** | Ngôn ngữ xử lý Backend |
| **Flask & Werkzeug** | Web framework API & Băm mật khẩu (Security) |
| **Cryptography** | Thư viện mật mã chuẩn (AES-GCM, RSA-OAEP) |
| **Pillow (PIL)** | Phân tích cấu trúc Byte ảnh và chèn Watermark |
| **SQLite** | Cơ sở dữ liệu nội bộ (Flask-SQLAlchemy) |
| **HTML/CSS/JS** | Giao diện Chat Real-time (Fetch API) |

## 🎯 Tính năng chính

- ✅ **Hệ thống Xác thực (Auth):** Mã hóa mật khẩu bảo mật, không lưu plain-text trong Database, cấp phát tự động khóa RSA khi đăng ký.
- ✅ **Kiểm duyệt Input Đầu vào:** Đánh chặn mã độc ở cửa ngõ. Giới hạn dung lượng ảnh **tối đa 10MB**, kiểm tra Whitelist và dùng Pillow để soi cấu trúc Magic Bytes, từ chối mọi file `.exe` hay Shell giả mạo đuôi `.jpg`.
- ✅ **Giao diện Chat Real-time:** Hoạt động mượt mà, chuyên biệt cho việc chia sẻ hình ảnh bí mật.
- ✅ **Mã hóa có xác thực:** Khắc phục nhược điểm của thuật toán cũ, AES-GCM tự động phát hiện thay đổi (MAC Tag).
- ✅ **So sánh trực quan:** Tự động hiển thị Modal (cửa sổ nổi) so sánh ảnh Gốc và ảnh đã xử lý ngay khi gửi.
- ✅ **Tính năng Giám định:** Người dùng tải ảnh về, nếu cố tình dùng Paint xóa watermark hoặc crop ảnh, công cụ sẽ phát hiện ngay lập tức.
- ✅ **Hệ thống Ghi Log (Logging):** Tự động ghi lại lịch sử tạo watermark, các nỗ lực tấn công bằng file mã độc vào file `system_security.log`.

## 🔐 Quy trình bảo mật cốt lõi

1. **Sinh khóa & Băm mật khẩu:** Đăng ký tài khoản, hệ thống băm mật khẩu và tự cấp cặp khóa RSA công khai/bí mật.
2. **Kiểm tra File (Filter):** Soi dung lượng (<10MB), soi đuôi file, soi Magic Bytes. Hủy gói tin nếu có rủi ro.
3. **Xử lý Ảnh:** Chèn Watermark chéo với độ mờ (alpha=70), tính mã băm (SHA-256).
4. **Đóng gói Metadata:** Khởi tạo Nonce, Timestamp, Hash, ID để chống Replay Attack.
5. **Mã hóa dữ liệu:** Sử dụng Session Key (AES-256) mã hóa cụm `[Metadata + Ảnh Watermark]` qua chế độ GCM.
6. **Khóa Session Key:** Dùng Public Key (RSA) của người nhận để bọc Session Key lại.
7. **Giải mã & Kiểm chứng:** - Người nhận dùng Private Key giải mã lấy Session Key.
   - AES-GCM giải mã Ciphertext và **tự động xác thực MAC Tag** (Báo lỗi nếu DB bị can thiệp).
   - So khớp Timestamp, Hash để đảm bảo toàn vẹn tuyệt đối.
  
## 🧪 Các kịch bản Kiểm thử bảo mật (Đã Pass)

1. **Input Validation (Đánh chặn cửa ngõ):** Tải lên file mã độc giả mạo đuôi `.jpg` hoặc file siêu nặng > 10MB -> Hệ thống từ chối mã hóa, báo lỗi trực tiếp trên giao diện.
2. **Database Tampering (Trộm dữ liệu):** Sử dụng DB Browser for SQLite sửa người nhận từ B thành C -> Người dùng C không thể giải mã, hệ thống từ chối mở khóa RSA.
3. **Sửa Ciphertext:** Can thiệp làm sai lệch mã hóa trong DB -> Hệ thống AES-GCM báo lỗi giải mã do sai MAC Tag.
4. **Crop/Sửa ảnh sau giải mã:** Tải ảnh về, crop lại, đưa vào *Công cụ Giám định Ảnh* -> Báo lỗi Fake.
5. **Xóa Watermark:** Dùng tẩy xóa chữ watermark, đưa vào *Công cụ Giám định Ảnh* -> Hash không khớp, báo lỗi.

## 📂 Cấu trúc thư mục

```text
📁 SecureImageSharing_Project/
├── runserver.py           # File khởi chạy Server chính
├── requirements.txt       # Danh sách thư viện cần thiết
├── system_security.log    # File ghi lại toàn bộ nhật ký hệ thống (Tự động sinh)
└── SecureImageSharing/              
    ├── views.py           # Bộ não xử lý API, Auth và Kiểm duyệt File
    ├── crypto_utils.py    # Module xử lý Lõi mật mã (AES, RSA, Watermark, Hash)
    ├── secure_chat.db     # Database SQLite (Tự động sinh)
    └── templates/             
        ├── login.html     # Giao diện Đăng ký / Đăng nhập
        └── chat.html      # Giao diện Chat Real-time & Giám định ảnh
```

## 🚀 Hướng dẫn Chạy ứng dụng

### 1. Cài đặt thư viện yêu cầu:
Mở Terminal/CMD và chạy lệnh:
```bash
pip install -r requirements.txt
```

### 2. Cách chạy bằng VS Code (Visual Studio Code - Bản Xanh)
1. Chuột phải vào thư mục dự án chọn **"Open with Code"** (Hoặc mở VS Code lên và kéo thả thư mục dự án vào).
2. Mở cửa sổ Terminal tích hợp trong VS Code bằng phím tắt: `` Ctrl + ` `` (Nút backtick bên dưới nút Esc).
3. Tại Terminal, gõ lệnh sau và ấn Enter:
```bash
python runserver.py
```
4. Trình duyệt sẽ tự động bật lên ở địa chỉ `http://localhost:5000`.

*(Lưu ý: Nếu bạn sử dụng Visual Studio bản Tím, chỉ cần mở file `.sln` hoặc `.pyproj` và ấn `F5`)*.

### 3. Hướng dẫn kết nối LAN (Chat 2 máy):
1. Máy Server (Máy chạy code) cài đặt **Radmin VPN** và tạo một Network.
2. Máy Client tải Radmin VPN và kết nối vào Network đó.
3. Trên máy Client, mở trình duyệt và truy cập: `http://[IP_Radmin_Máy_Server]:5000`

### 4. Kết nối mạng nội bộ (LAN / Wi-Fi) không dùng phần mềm:
1. Kết nối cả 2 máy tính vào cùng chung một mạng Wi-Fi (hoặc cắm chung router mạng LAN).
2. Trên máy Server, mở CMD gõ `ipconfig` để lấy địa chỉ **IPv4 Address** (VD: `192.168.1.5`).
3. Khởi chạy Server.
4. Máy thứ 2 truy cập: `http://[IPv4_CUA_MAY_SERVER]:5000` để bắt đầu nhắn tin.

## 📚 Tài liệu tham khảo
1. **Cryptography Package (Python)** [https://cryptography.io/en/latest/](https://cryptography.io/en/latest/)
2. **Authenticated Encryption (AES-GCM)** [https://en.wikipedia.org/wiki/Galois/Counter_Mode](https://en.wikipedia.org/wiki/Galois/Counter_Mode)
3. **Pillow (Image Processing & Validation)** [https://pillow.readthedocs.io/](https://pillow.readthedocs.io/)
4. **Flask Documentation** [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
5. **Werkzeug Security (Password Hashing)** [https://werkzeug.palletsprojects.com/](https://werkzeug.palletsprojects.com/)
6. **RSA Algorithm – Wikipedia** [https://en.wikipedia.org/wiki/RSA_(cryptosystem)](https://en.wikipedia.org/wiki/RSA_(cryptosystem))
