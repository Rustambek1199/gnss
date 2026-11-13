# 🌐 Uz-GNSS & Chang Monitoring Tizimi (Production Web App)

O'zbekiston hududidagi GNSS meteorologik stansiyalari orqali atmosferadagi suv bug'i (PWV), troposfera kechikishlari (ZTD), yog'in xavfi, konvektiv bo'ronlar, sun'iy yomg'ir qulayligi va chang-to'zon xavfini monitoring qilish hamda sun'iy intellekt (AI) yordamida bashorat qilish platformasi.

---

## ⚡ Asosiy Imkoniyatlar

1. **🌐 Interaktiv 3D Yer Shari (Globe 3D):**
   - Three.js va Globe.gl asosida real vaqtli 3D Yer Shari.
   - O'zbekiston GNSS tarmog'idagi barcha stansiyalar uchun 3D mayoqlar, radar to'lqinlari va ob-havo belgilari.
   - 3D va 2D (OpenStreetMap / Esri sun'iy yo'ldosh) xarita o'rtasida bir zumda almashish.
2. **🌧️ Meteorologik & Sun'iy Yomg'ir Monitoringi:**
   - Troposfera parametrlari (ZTD, ZHD, ZWD, PWV), bosim va namlik tahlili.
   - Bulut ekish (cloud seeding) uchun optimal vaqtlar, konvektiv sharoitlar va traektoriyalar hisobi.
   - AccuWeather uslubidagi soatlik ob-havo lentasi.
3. **🏜️ Chang-To'zon Xavfi & AI Bashorati:**
   - Navoiy va Buxoro viloyatlari bo'yicha tuproq namligi va shamol parametrlari.
   - Random Forest AI modeli orqali xavfni jonli bashorat qilish.
   - Yashil to'siqlar (daraxtzorlar) bo'ylab qum ko'chishini kamaytirish bo'yicha 2D difuziya-adveksiya simulyatsiyasi (darhol ko'rinadi).

---

## 💾 Ma'lumotlar Optimizatsiyasi (Data Compression)

- **Oldingi holat:** 72 ta og'ir `.txt` fayllar (~36 MB) + 6 ta NetCDF `.nc` fayllar (~13 MB) = **Jami ~49 MB**.
- **Yangi Production holat:**
  - `gnss_data.parquet` — 527,000 dan ortiq yozuv `zstd` algoritmi bilan siqildi: **atigi 7.0 MB**!
  - `chang_data.parquet` — barcha ERA5 va meteo ko'rsatkichlar: **atigi 26 KB**!
  - NetCDF (`xarray`, `netcdf4`) kabi yuzlab megabaytlik og'ir kutubxonalarga bog'liqlik butunlay olib tashlandi.
  - Ma'lumotlarni o'qish tezligi **10 barobar** oshirildi (0.05 soniya).

---

## 📂 Loyiha Tuzilishi (Project Layout)

```
gnss/
├── app/                        # Asosiy dastur paketi
│   ├── __init__.py             # Application Factory (create_app)
│   ├── config.py               # Muhit sozlamalari (Dev, Prod)
│   ├── routes/                 # Web va API marshrutlari
│   │   ├── __init__.py
│   │   ├── gnss_routes.py      # /gnss, /api/gnss_data, /api/gnss_hourly
│   │   └── chang_routes.py     # /chang, /api/data, /api/predict, /api/simulate
│   ├── services/               # Biznes mantiq va hisob-kitoblar
│   │   ├── __init__.py
│   │   ├── gnss_service.py     # GNSS tahlili, Open-Meteo jonli sinxronizatsiya
│   │   └── chang_service.py    # AI Random Forest modeli, yashil to'siq simulyatsiyasi
│   ├── templates/              # HTML shablonlar
│   │   ├── gnss.html           # 3D Yer Shari + GNSS monitoring interfeysi
│   │   └── index.html          # Chang bo'roni paneli
│   ├── static/                 # Statik resurslar (Lokal va oflayn ishlaydi)
│   │   ├── css/style.css
│   │   ├── js/
│   │   │   ├── globe.gl.min.js # 3D Yer Shari dvigateli
│   │   │   └── app.js
│   │   └── img/
│   │       ├── earth-night.jpg       # Tungi yer sferasi
│   │       ├── earth-blue-marble.jpg # Kunduzgi yer sferasi
│   │       ├── night-sky.png         # Yulduzli fazo
│   │       └── green_barrier_sim.png # Tayyor simulyatsiya grafigi
│   └── data/                   # Optimizatsiya qilingan ma'lumotlar
│       ├── gnss_data.parquet   # 527k GNSS yozuvlari (7.0 MB)
│       └── chang_data.parquet  # Chang tahlili yozuvlari (26 KB)
├── run.py                      # Lokal ishga tushirish (Development)
├── wsgi.py                     # Production kirish nuqtasi (Gunicorn / uWSGI)
├── gunicorn.conf.py            # Gunicorn production server sozlamalari
├── Procfile                    # Bulutli xostinglar uchun (Render, Railway, Heroku)
├── requirements.txt            # Python kutubxonalari
├── Dockerfile                  # Konteyner yaratish fayli
├── docker-compose.yml          # Docker Compose orqali ishga tushirish
├── .env.example                # Muhit o'zgaruvchilari namunasi
└── README.md                   # Qo'llanma
```

---

## 🚀 Ishga Tushirish Bo'yicha Qo'llanma

### 1. Lokal kompyuterda ishga tushirish:

```bash
# 1. Virtual muhit yaratish va faollashtirish
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 2. Kerakli kutubxonalarni o'rnatish
pip install -r requirements.txt

# 3. Serverni ishga tushirish
python run.py
```
Brauzerda oching:
- **GNSS Monitoring (3D Yer Shari):** `http://localhost:5000/gnss`
- **Chang Bo'roni Tahlili:** `http://localhost:5000/chang`

---

### 2. Docker orqali ishga tushirish:

```bash
# Docker Compose bilan bir buyruqda qurish va fonda ishga tushirish:
docker compose up -d --build
```
To'xtatish uchun:
```bash
docker compose down
```

---

### 3. Haqiqiy Linux VPS Serverga o'rnatish (Ubuntu / Debian):

#### A. Paketlar va kodni yuklash:
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nginx git
cd /var/www
git clone <sizning-repo-linki> gnss
cd gnss
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### B. Systemd servis yaratish (`/etc/systemd/system/gnss.service`):
```ini
[Unit]
Description=Uz-GNSS Production Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/gnss
Environment="PATH=/var/www/gnss/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/var/www/gnss/venv/bin/gunicorn --config gunicorn.conf.py wsgi:application

[Install]
WantedBy=multi-user.target
```
Servisni ishga tushirish:
```bash
sudo systemctl daemon-reload
sudo systemctl start gnss
sudo systemctl enable gnss
```

#### C. Nginx konfiguratsiyasi (`/etc/nginx/sites-available/gnss`):
```nginx
server {
    listen 80;
    server_name sizning-domeningiz.uz; # yoki server IP manzili

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/gnss/app/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```
Nginx-ni faollashtirish:
```bash
sudo ln -s /etc/nginx/sites-available/gnss /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### 4. Bulutli xostinglarga yuklash (Render / Railway):
Loyiha ichidagi `Procfile` tufayli **Render.com** yoki **Railway.app** ga GitHub orqali ulanganda, u avtomatik ravishda Python loyihasi sifatida aniqlanadi va `gunicorn wsgi:application` orqali ishga tushadi. Hech qanday qo'shimcha murakkab sozlash talab etilmaydi!

---

## 🛠️ Litsenziya va Mualliflik
Ushbu tizim O'zbekiston hududida GNSS meteorologiyasi va chang-to'zon xavfini monitoring qilish uchun ishlab chiqilgan.
