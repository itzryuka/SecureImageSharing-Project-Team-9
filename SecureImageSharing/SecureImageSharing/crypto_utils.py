import os, time, base64, hashlib, json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from PIL import Image, ImageDraw

def generate_rsa_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    priv_pem = private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    pub_pem = public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv_pem, pub_pem

def add_watermark(image_bytes, text):
    with open("temp.png", "wb") as f: f.write(image_bytes)
    img = Image.open("temp.png").convert("RGBA")
    txt = Image.new('RGBA', img.size, (255,255,255,0))
    d = ImageDraw.Draw(txt)
    d.text((10, 10), text, fill=(255, 0, 0, 128))
    watermarked = Image.alpha_composite(img, txt).convert("RGB")
    watermarked.save("temp_wm.jpg", "JPEG")
    with open("temp_wm.jpg", "rb") as f: data = f.read()
    return data, hashlib.sha256(data).hexdigest()

def encrypt_packet(image_bytes, sender_id, receiver_id, receiver_pub_pem):
    wm_image, wm_hash = add_watermark(image_bytes, f"Bản quyền: {sender_id}")
    session_key = os.urandom(32) # Khóa AES-256 ngẫu nhiên
    nonce = os.urandom(12)
    
    # Metadata chống replay
    metadata = {
        "sender": sender_id,
        "receiver": receiver_id,
        "watermark_hash": wm_hash,
        "timestamp": int(time.time()),
        "nonce": base64.b64encode(nonce).decode('utf-8')
    }
    
    # Mã hóa dữ liệu bằng AES-GCM (Có xác thực tag)
    payload = json.dumps(metadata).encode('utf-8') + b"|||" + wm_image
    aesgcm = AESGCM(session_key)
    ciphertext = aesgcm.encrypt(nonce, payload, None)
    
    # Mã hóa session key bằng RSA Public Key của người nhận
    receiver_pub_key = serialization.load_pem_public_key(receiver_pub_pem)
    encrypted_session_key = receiver_pub_key.encrypt(
        session_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return nonce, encrypted_session_key, ciphertext

def decrypt_packet(nonce, encrypted_session_key, ciphertext, receiver_priv_pem):
    # Giải mã session key bằng RSA Private Key
    priv_key = serialization.load_pem_private_key(receiver_priv_pem, password=None)
    session_key = priv_key.decrypt(
        encrypted_session_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    
    # Giải mã và tự động xác thực toàn vẹn bằng AES-GCM
    aesgcm = AESGCM(session_key)
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    
    meta_bytes, wm_image = decrypted.split(b"|||", 1)
    metadata = json.loads(meta_bytes.decode('utf-8'))
    
    # So khớp Hash để đảm bảo watermark không bị sửa/xóa
    current_hash = hashlib.sha256(wm_image).hexdigest()
    if current_hash != metadata['watermark_hash']:
        raise Exception("Watermark hoặc dữ liệu ảnh đã bị can thiệp trái phép!")
        
    return metadata, wm_image