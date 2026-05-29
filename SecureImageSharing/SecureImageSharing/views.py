import os, base64, logging, json
from flask import render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from SecureImageSharing import app
from .crypto_utils import generate_rsa_keys, encrypt_packet, decrypt_packet

app.secret_key = 'supersecret_fit4012'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///secure_chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

logging.basicConfig(filename='system_security.log', level=logging.INFO, format='%(asctime)s - %(message)s')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    pub_key = db.Column(db.LargeBinary)
    priv_key = db.Column(db.LargeBinary)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50))
    receiver = db.Column(db.String(50))
    is_image = db.Column(db.Boolean, default=False)
    content = db.Column(db.Text) 

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if not user:
            priv, pub = generate_rsa_keys()
            user = User(username=username, pub_key=pub, priv_key=priv)
            db.session.add(user)
            db.session.commit()
            logging.info(f"Đăng ký & Cấp khóa RSA cho User: {username}")
        session['username'] = username
        return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/chat')
def chat():
    if 'username' not in session: return redirect(url_for('login'))
    users = User.query.filter(User.username != session['username']).all()
    return render_template('chat.html', current_user=session['username'], users=users)

@app.route('/api/send', methods=['POST'])
def api_send():
    sender = session['username']
    receiver = request.form['receiver']
    text = request.form.get('text', '')
    file = request.files.get('file')
    
    if file:
        recv_user = User.query.filter_by(username=receiver).first()
        nonce, enc_key, cipher = encrypt_packet(file.read(), sender, receiver, recv_user.pub_key)
        packet = f"{base64.b64encode(nonce).decode()}|{base64.b64encode(enc_key).decode()}|{base64.b64encode(cipher).decode()}"
        msg = Message(sender=sender, receiver=receiver, is_image=True, content=packet)
    else:
        msg = Message(sender=sender, receiver=receiver, is_image=False, content=text)
    
    db.session.add(msg)
    db.session.commit()
    return jsonify({"status": "success"})

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
                result.append({"sender": m.sender, "is_image": False, "content": f"<b style='color:red;'>[LỖI: {str(e)}]</b>"})
        elif m.is_image and m.sender == sender:
            result.append({"sender": m.sender, "is_image": False, "content": "[Bạn đã gửi một ảnh mã hóa an toàn]"})
        else:
            result.append({"sender": m.sender, "is_image": False, "content": m.content})
            
    return jsonify(result)

# Khởi tạo DB khi chạy
with app.app_context():
    db.create_all()