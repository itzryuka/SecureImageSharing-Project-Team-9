import os
import threading
import webbrowser
from SecureImageSharing import app

def open_browser():
    # Tự động mở link này trên máy của bạn
    webbrowser.open_new("http://localhost:5000/")

if __name__ == '__main__':
    HOST = '0.0.0.0'
    PORT = 5000
    
    # Hẹn 1.5 giây sau khi bật Server thì tự động gọi trình duyệt lên
    threading.Timer(1.5, open_browser).start()
    
    # use_reloader=False để tránh trình duyệt bị mở thành 2 tab
    app.run(HOST, PORT, debug=True, use_reloader=False)