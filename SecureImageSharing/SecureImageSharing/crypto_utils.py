import os, time, base64, hashlib, json, uuid, logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from PIL import Image, ImageDraw, ImageFont

def generate_rsa_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    priv_pem = private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    pub_pem = public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv_pem, pub_pem

def add_watermark(image_bytes, text):
    # Lưu tạm ảnh gốc để Pillow xử lý
    with open("temp.png", "wb") as f:
        f.write(image_bytes)
        
    img = Image.open("temp.png").convert("RGBA")
    width, height = img.size
    
    # 1. Tạo một layer trong suốt LỚN HƠN ảnh gốc (gấp 2 lần)
    # Mục đích: Để khi xoay 45 độ, các góc ảnh không bị hụt watermark
    layer_size = max(width, height) * 2
    txt_layer = Image.new('RGBA', (layer_size, layer_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)
    
    # 2. Cấu hình Font chữ (Tự động scale to/nhỏ theo kích thước ảnh)
    font_size = int(max(width, height) / 30)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
        
    # Tính kích thước của 1 cụm chữ
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # 3. Vẽ chữ lặp lại thành dạng lưới (Grid) trên layer
    spacing_x = text_w + 100  # Khoảng cách ngang giữa các chữ
    spacing_y = text_h + 100  # Khoảng cách dọc giữa các chữ
    
    # Màu chữ: (R, G, B, Alpha). Alpha = 70 để tạo độ mờ xuyên thấu
    text_color = (255, 255, 255, 70) 
    
    for x in range(0, layer_size, spacing_x):
        for y in range(0, layer_size, spacing_y):
            draw.text((x, y), text, font=font, fill=text_color)
            
    # 4. Xoay toàn bộ layer chữ một góc 45 độ (Cắt chéo)
    txt_layer = txt_layer.rotate(45, resample=Image.BICUBIC)
    
    # 5. Cắt (Crop) layer watermark về đúng kích thước của ảnh gốc (Lấy phần trung tâm)
    left = (layer_size - width) // 2
    top = (layer_size - height) // 2
    txt_layer_cropped = txt_layer.crop((left, top, left + width, top + height))
    
    # 6. Ghép (Overlay) layer chữ mờ lên trên ảnh gốc
    watermarked = Image.alpha_composite(img, txt_layer_cropped).convert("RGB")
    watermarked.save("temp_wm.jpg", "JPEG", quality=95)
    
    # Đọc lại ảnh đã gắn watermark để trả về mã hóa
    with open("temp_wm.jpg", "rb") as f:
        data = f.read()
        
    return data, hashlib.sha256(data).hexdigest()

def encrypt_packet(image_bytes, sender_id, receiver_id, receiver_pub_pem):
    image_id = str(uuid.uuid4().hex)[:8] # Tạo ID ngẫu nhiên cho ảnh
    wm_image, wm_hash = add_watermark(image_bytes, f"Bản quyền: {sender_id}")
    
    # [YÊU CẦU 5]: Ghi log quá trình tạo watermark
    logging.info(f"[WATERMARK] Đã tạo watermark thành công cho ảnh {image_id} - Hash: {wm_hash}")

    session_key = os.urandom(32) 
    nonce = os.urandom(12)
    
    # [YÊU CẦU 1]: Chuẩn hóa cấu trúc Metadata
    metadata = {
        "image_id": image_id,
        "owner_id": sender_id,
        "receiver_id": receiver_id,
        "watermark_hash": wm_hash,
        "timestamp": int(time.time()),
        "nonce": base64.b64encode(nonce).decode('utf-8')
    }

    #THÊM DÒNG NÀY ĐỂ DEBUG
    print(f"Debug Metadata: {json.dumps(metadata, indent=4)}")
    
    # [YÊU CẦU 2]: Mã hóa bằng cơ chế có xác thực (AES-GCM)
    payload = json.dumps(metadata).encode('utf-8') + b"|||" + wm_image
    aesgcm = AESGCM(session_key)
    ciphertext = aesgcm.encrypt(nonce, payload, None)
    
    receiver_pub_key = serialization.load_pem_public_key(receiver_pub_pem)
    encrypted_session_key = receiver_pub_key.encrypt(
        session_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    # Trả về thêm wm_image để Frontend lấy dữ liệu so sánh
    return wm_image, nonce, encrypted_session_key, ciphertext

def decrypt_packet(nonce, encrypted_session_key, ciphertext, receiver_priv_pem):
    priv_key = serialization.load_pem_private_key(receiver_priv_pem, password=None)
    session_key = priv_key.decrypt(
        encrypted_session_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    
    aesgcm = AESGCM(session_key)
    # [YÊU CẦU 3]: Tự động văng lỗi nếu Ciphertext bị sửa đổi (Đặc tính của AES-GCM)
    try:
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception:
        raise Exception("Dữ liệu đã bị sửa đổi trên đường truyền (Sai MAC Tag)!")
        
    meta_bytes, wm_image = decrypted.split(b"|||", 1)
    metadata = json.loads(meta_bytes.decode('utf-8'))
    
    current_hash = hashlib.sha256(wm_image).hexdigest()
    # [YÊU CẦU 3]: Kiểm tra lại tính toàn vẹn của Watermark/Ảnh
    if current_hash != metadata['watermark_hash']:
        logging.warning(f"[CẢNH BÁO] Phát hiện watermark/ảnh bị can thiệp trái phép! ID: {metadata['image_id']}")
        raise Exception("Watermark hoặc dữ liệu ảnh đã bị can thiệp trái phép!")
        
    # [YÊU CẦU 5]: Ghi log quá trình xác minh watermark
    logging.info(f"[WATERMARK] Xác minh thành công ảnh {metadata['image_id']} - Hash khớp hợp lệ.")
        
    return metadata, wm_image