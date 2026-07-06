import os, base64, logging, json, hashlib
from flask import render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash # Thư viện băm mật khẩu an toàn
from PIL import Image # Thư viện kiểm tra Magic Bytes của ảnh
from SecureImageSharing import app
from .crypto_utils import generate_rsa_keys, encrypt_packet, decrypt_packet

app.secret_key = 'supersecret_fit4012'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///secure_chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

logging.basicConfig(filename='system_security.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# ==========================================
# 🛡️ BỘ LỌC KIỂM TRA BẢO MẬT FILE ĐA LỚP
# ==========================================
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # Giới hạn tối đa 10MB mỗi file

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_real_image(file_stream):
    try:
        img = Image.open(file_stream)
        img.verify() 
        file_stream.seek(0) # Trả con trỏ file về vị trí đầu tiên sau khi kiểm tra xong
        return True
    except Exception:
        return False

def get_file_size(file_stream):
    file_stream.seek(0, os.SEEK_END)
    size = file_stream.tell()
    file_stream.seek(0)
    return size

# ==========================================
# 📊 CẤU TRÚC DATABASE (THÊM CỘT MẬT KHẨU)
# ==========================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(255)) # Lưu trữ mật khẩu dạng băm an toàn
    pub_key = db.Column(db.LargeBinary)
    priv_key = db.Column(db.LargeBinary)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50))
    receiver = db.Column(db.String(50))
    is_image = db.Column(db.Boolean, default=False)
    content = db.Column(db.Text) 

# ==========================================
# 🔐 HỆ THỐNG XÁC THỰC TÀI KHOẢN (AUTH SYSTEM)
# ==========================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            return render_template('login.html', error="Tài khoản và mật khẩu không được để trống!", mode="register")
            
        if User.query.filter_by(username=username).first():
            return render_template('login.html', error="Tên đăng nhập đã tồn tại trên hệ thống!", mode="register")
            
        # Tạo cặp khóa RSA và băm mật khẩu bảo mật
        priv, pub = generate_rsa_keys()
        hashed_pw = generate_password_hash(password)
        
        new_user = User(username=username, password_hash=hashed_pw, pub_key=pub, priv_key=priv)
        db.session.add(new_user)
        db.session.commit()
        logging.info(f"Đăng ký thành công & Cấp khóa RSA cho: {username}")
        
        return render_template('login.html', success="Đăng ký thành công! Mời bạn đăng nhập.", mode="login")
    return render_template('login.html', mode="register")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        # Kiểm tra sự tồn tại và đối chiếu chuỗi băm mật khẩu
        if user and check_password_hash(user.password_hash, password):
            session['username'] = username
            return redirect(url_for('chat'))
        else:
            return render_template('login.html', error="Tài khoản hoặc mật khẩu không chính xác!", mode="login")
            
    return render_template('login.html', mode="login")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/chat')
def chat():
    if 'username' not in session: return redirect(url_for('login'))
    users = User.query.filter(User.username != session['username']).all()
    return render_template('chat.html', current_user=session['username'], users=users)

# ==========================================
# ✉️ ENDPOINT XỬ LÝ GỬI TIN NHẮN CHỮ & ẢNH
# ==========================================
@app.route('/api/send', methods=['POST'])
def api_send():
    sender = session['username']
    receiver = request.form['receiver']
    text = request.form.get('text', '').strip()
    file = request.files.get('file')
    
    # LUỒNG XỬ LÝ 1: GỬI FILE ẢNH BẢO MẬT
    if file and file.filename != '':
        file_size = get_file_size(file)

        # Lớp 1: Chặn file quá dung lượng (Chống tấn công DoS ổ đĩa)
        if file_size > MAX_FILE_SIZE:
            logging.warning(f"[{sender}] Cảnh báo: Gửi file quá lớn vượt mức 10MB.")
            return jsonify({"status": "error", "msg": "❌ HỆ THỐNG CHẶN: Dung lượng file ảnh vượt quá giới hạn 10MB!"})

        # Lớp 2: Kiểm tra đuôi mở rộng Whitelist
        if not allowed_file(file.filename):
            logging.warning(f"[{sender}] Cảnh báo: Sai định dạng đuôi file ({file.filename}).")
            return jsonify({"status": "error", "msg": "❌ HỆ THỐNG CHẶN: Định dạng không được phép! Chỉ chấp nhận .jpg, .jpeg, .png"})

        # Lớp 3: Quét Magic Bytes bên trong nội dung (Chống ngụy trang Webshell/Trojan bằng đuôi giả)
        if not is_real_image(file):
            logging.warning(f"[{sender}] Cảnh báo nguy hiểm: Phát hiện cấu trúc tệp giả mạo Header bức ảnh từ người dùng.")
            return jsonify({"status": "error", "msg": "❌ NGUY HIỂM: Hệ thống phát hiện cấu trúc file giả mạo hoặc chứa mã độc độc hại!"})

        # Vượt qua bộ lọc an toàn thành công -> Đọc dữ liệu byte và tiến hành mã hóa gắn Watermark
        file_bytes = file.read()
        recv_user = User.query.filter_by(username=receiver).first()
        
        wm_image, nonce, enc_key, cipher = encrypt_packet(file_bytes, sender, receiver, recv_user.pub_key)
        
        packet = f"{base64.b64encode(nonce).decode()}|{base64.b64encode(enc_key).decode()}|{base64.b64encode(cipher).decode()}"
        msg = Message(sender=sender, receiver=receiver, is_image=True, content=packet)
        logging.info(f"[{sender}] Đã gửi gói tin ảnh mã hóa thành công cho [{receiver}]")
        db.session.add(msg)
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "original_img": base64.b64encode(file_bytes).decode(),
            "watermarked_img": base64.b64encode(wm_image).decode()
        })
        
    # LUỒNG XỬ LÝ 2: GỬI TIN NHẮN VĂN BẢN THƯỜNG (PLAIN TEXT)
    elif text != '':
        msg = Message(sender=sender, receiver=receiver, is_image=False, content=text)
        db.session.add(msg)
        db.session.commit()
        return jsonify({"status": "success"})
        
    return jsonify({"status": "error", "msg": "Nội dung gửi trống!"})

# Các API dữ liệu phía dưới giữ nguyên (api_messages, verify_image)
@app.route('/api/messages/<receiver>')
def api_messages(receiver):
    sender = session['username']
    msgs = Message.query.filter(
        ((Message.sender == sender) & (Message.receiver == receiver)) | 
        ((Message.sender == receiver) & (Message.receiver == sender))
    ).order_by(Message.id).all()
    
    result = []
    for m in msgs:
        if m.is_image and m.receiver == sender:
            try:
                parts = m.content.split("|")
                nonce, enc_key, cipher = base64.b64decode(parts[0]), base64.b64decode(parts[1]), base64.b64decode(parts[2])
                user = User.query.filter_by(username=sender).first()
                meta, img_bytes = decrypt_packet(nonce, enc_key, cipher, user.priv_key)
                img_b64 = base64.b64encode(img_bytes).decode()
                result.append({"sender": m.sender, "is_image": True, "content": img_b64, "meta": meta})
            except Exception as e:
                result.append({"sender": m.sender, "is_image": False, "content": f"<b style='color:red;'>[LỖI GIẢI MÃ: {str(e)}]</b>"})
        elif m.is_image and m.sender == sender:
            result.append({"sender": m.sender, "is_image": False, "content": "[Bạn đã gửi một ảnh mã hóa an toàn]"})
        else:
            result.append({"sender": m.sender, "is_image": False, "content": m.content})
            
    return jsonify(result)

@app.route('/api/verify_image', methods=['POST'])
def verify_image():
    file = request.files.get('file')
    original_hash = request.form.get('original_hash')
    
    if not file or not original_hash:
        return jsonify({"status": "error", "msg": "Thiếu file hoặc mã băm!"})
        
    img_bytes = file.read()
    current_hash = hashlib.sha256(img_bytes).hexdigest()
    
    if current_hash == original_hash:
        return jsonify({"status": "success", "msg": "✅ ẢNH NGUYÊN VẸN: Khớp mã băm, Watermark chưa bị can thiệp."})
    else:
        return jsonify({"status": "error", "msg": "❌ CẢNH BÁO: Ảnh đã bị Crop, chỉnh sửa hoặc xóa Watermark!"})

with app.app_context():
    db.create_all()