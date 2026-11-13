import os
from app import create_app

# Lokal test va dasturlash uchun
app = create_app('development')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    print("=" * 60)
    print(" 🚀 Uz-GNSS & Chang Monitoring Tizimi (Lokal rejim)")
    print(f" 🌐 Asosiy sahifa (GNSS): http://localhost:{port}/gnss")
    print(f" 🏜️ Chang tahlili:       http://localhost:{port}/chang")
    print("=" * 60)
    app.run(host=host, port=port, debug=False)
