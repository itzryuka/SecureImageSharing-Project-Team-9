# 🔐 Hệ thống Gửi Ảnh Bảo Mật Gắn Watermark (FIT4012 Upgrade)

<h2 align="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
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
        <img src="aiotlab_logo.png" alt="AIoTLab Logo" width="170"/>
        <img src="fitdnu_logo.png" alt="AIoTLab Logo" width="180"/>
        <img src="dnu_logo.png" alt="DaiNam University Logo" width="200"/>
    </p>

[![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn)

</div>

## 📌 Giới thiệu
Dự án này là sản phẩm của bài tập lớn học phần **FIT4012 - Nhập môn An toàn bảo mật thông tin**, chủ đề **Secure System Upgrade Challenge (Đề tài 9)**. 

Hệ thống cung cấp nền tảng Web Chat Real-time cho phép **gửi ảnh gắn watermark** với các cơ chế bảo vệ được nâng cấp hoàn toàn so với phiên bản cũ:
- Nâng cấp từ thuật toán cũ (DES) lên **AES-GCM (Mã hóa có xác thực)**.
- Tự động sinh và quản lý cặp khóa **RSA-OAEP 2048-bit** cho mỗi người dùng.
- Gắn **Watermark chéo mờ (Diagonal)** tự động scale theo kích thước ảnh, chống cắt xén.
- Đóng gói chuẩn **Metadata** (gồm: `image_id`, `owner_id`, `receiver_id`, `watermark_hash`, `timestamp`, `nonce`) để chống tấn công Replay.
- Tự động phát hiện gói tin bị sửa đổi trên đường truyền và cung cấp **Công cụ Giám định ảnh** độc lập.

## 🧠 Công nghệ sử dụng

| Thành phần | Mô tả |
| :-- | :-- |
| **Python 3.10+** | Ngôn ngữ xử lý Backend |
| **Flask** | Web framework API & Routing |
| **Cryptography** | Thư viện mật mã chuẩn (AES-GCM, RSA-OAEP) |
| **Pillow (PIL)** | Xử lý ảnh và chèn Watermark |
| **SQLite** | Cơ sở dữ liệu (Flask-SQLAlchemy) |
| **HTML/CSS/JS** | Giao diện Chat Real-time (Polling API) |

## 🎯 Tính năng chính & Nâng cấp (So với bản cũ)

- ✅ **Giao diện Chat Real-time:** Hoạt động mượt mà dựa theo các app nhắn tin.
- ✅ **Mã hóa có xác thực:** Khắc phục nhược điểm của DES, AES-GCM tự động phát hiện thay đổi (MAC Tag).
- ✅ **Bảo vệ Watermark kép:** Watermark lặp chéo toàn ảnh + Băm SHA-256 lưu vào Metadata.
- ✅ **So sánh trực quan:** Tự động hiển thị Modal (cửa sổ nổi) so sánh ảnh Gốc và ảnh đã xử lý ngay khi gửi.
- ✅ **Tính năng Giám định:** Cho phép người dùng tải ảnh về, nếu cố tình dùng Paint xóa watermark hoặc crop ảnh, công cụ sẽ phát hiện ngay lập tức.
- ✅ **Hệ thống Ghi Log (Logging):** Tự động ghi lại lịch sử tạo watermark, mã hóa, giải mã, và các cảnh báo bảo mật vào file `system_security.log`.

## 🔐 Quy trình bảo mật cốt lõi

1. **Sinh khóa:** Người dùng đăng nhập lần đầu, hệ thống tự cấp cặp khóa RSA công khai/bí mật.
2. **Xử lý Ảnh:** Server nhận ảnh gốc, chèn Watermark chéo với độ mờ (alpha=70), tính mã băm (SHA-256).
3. **Đóng gói Metadata:** Khởi tạo Nonce, Timestamp, Hash, ID để chống Replay Attack.
4. **Mã hóa dữ liệu:** Sử dụng Session Key (AES-256) mã hóa cụm `[Metadata + Ảnh Watermark]` qua chế độ GCM.
5. **Khóa Session Key:** Dùng Public Key (RSA) của người nhận để bọc Session Key lại.
6. **Truyền tải:** Gói tin `Nonce | Encrypted_Key | Ciphertext` được lưu vào CSDL và đẩy đến người nhận.
7. **Giải mã & Kiểm chứng:** - Người nhận dùng Private Key giải mã lấy Session Key.
    - AES-GCM giải mã Ciphertext và **tự động xác thực MAC Tag** (Văng lỗi nếu bị sửa).
    - So khớp Timestamp, Hash để đảm bảo toàn vẹn tuyệt đối.
  
## 🧪 Các kịch bản Kiểm thử bảo mật (Đã Pass)

1. **Gửi ảnh hợp lệ:** Luồng gửi/nhận diễn ra bình thường, giải mã thành công.
2. **Sửa Ciphertext:** Bấm nút *👾 Giả lập Hacker can thiệp*, Sử dụng Db Browser for SQLite để test, hệ thống lập tức báo lỗi đỏ chặn hình ảnh.
3. **Crop/Sửa ảnh sau giải mã:** Tải ảnh về, crop lại, đưa vào *Công cụ Giám định Ảnh* -> Báo lỗi Fake.
4. **Xóa Watermark:** Dùng tẩy xóa chữ watermark, đưa vào *Công cụ Giám định Ảnh* -> Hash không khớp, báo lỗi.
5. **Sai người nhận:** Can thiệp DB đổi ID người nhận, hệ thống từ chối mở khóa RSA.

## 📂 Cấu trúc thư mục

```text
📁 SecureChatApp/
├── app.py                 # File chạy Server Flask & API endpoints
├── crypto_utils.py        # Module xử lý Lõi mật mã (AES, RSA, Watermark, Hash)
├── runserver.py           # File khởi chạy & tự động mở trình duyệt (Visual Studio)
├── requirements.txt       # Danh sách thư viện cần thiết
├── system_security.log    # File ghi lại toàn bộ nhật ký hệ thống (Tự động sinh)
├── secure_chat.db         # Database SQLite (Tự động sinh)
└── templates/             
    ├── login.html         # Giao diện Đăng nhập / Cấp khóa
    └── chat.html          # Giao diện Chat Real-time & Giám định ảnh
```

## 🚀 Chạy ứng dụng

### 1. Cài thư viện:
```bash
pip install -r requirements.txt
```

> File `requirements.txt` gồm:
```
Flask>=2.2.3
Flask-SQLAlchemy
cryptography
Pillow
```

### 2. Chạy server:
Nếu dùng Visual Studio: Bấm F5 để chạy dự án.
```bash
python runserver.py
```
Trình duyệt sẽ tự động mở trang web tại địa chỉ: http://localhost:5000

### 3. Hướng dẫn kết nối LAN (Chat 2 máy):
1. Máy Server (Máy chạy code) cài đặt Radmin VPN và tạo một Network.

2. Máy Client kết nối vào Network đó.

3. Trên máy Client, mở trình duyệt và truy cập: http://[IP_Radmin_Máy_Server]:5000

### 4. Kết nối khi không sử dụng RadminVPN:
1. Kết nối cả 2 máy tính vào cùng một mạng Wi-Fi.

2. Trên máy đóng vai trò làm Server, mở lại cmd, gõ ipconfig để xem IPv4 Address mới.

3. Khởi chạy lại Server bằng Visual Studio (bấm F5).

4. Người dùng ở máy 2 nhập địa chỉ IP mới kèm port http://[IPv4_CUA_MAY_SERVER]:5000 lên trình duyệt để truy cập bình thường.

## 📚 Tài liệu tham khảo
1. ** Cryptography Package (Python): **
   [https://cryptography.io/en/latest/](https://cryptography.io/en/latest/)

2. **Authenticated Encryption (AES-GCM): **
   [https://en.wikipedia.org/wiki/Galois/Counter_Mode](https://en.wikipedia.org/wiki/Galois/Counter_Mode)

3. **Pillow (Image Processing): **
   [https://pillow.readthedocs.io/](https://pillow.readthedocs.io/)

4. **Flask Documentation: **
   [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)

5. **DES (Data Encryption Standard) – Wikipedia**  
   [https://en.wikipedia.org/wiki/Data_Encryption_Standard](https://en.wikipedia.org/wiki/Data_Encryption_Standard)

6. **SHA-2 (SHA-512) – Wikipedia**  
   [https://en.wikipedia.org/wiki/SHA-2](https://en.wikipedia.org/wiki/SHA-2)

7. **RSA Algorithm – Wikipedia**  
   [https://en.wikipedia.org/wiki/RSA_(cryptosystem)](https://en.wikipedia.org/wiki/RSA_(cryptosystem))
