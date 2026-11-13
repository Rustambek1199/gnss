import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'uz-gnss-meteo-chang-production-key-2026')
    DATA_DIR = os.path.join(BASE_DIR, 'app', 'data')
    STATIC_DIR = os.path.join(BASE_DIR, 'app', 'static')
    TEMPLATES_DIR = os.path.join(BASE_DIR, 'app', 'templates')
    
    # Parquet Data Paths
    GNSS_DATA_PATH = os.path.join(DATA_DIR, 'gnss_data.parquet')
    CHANG_DATA_PATH = os.path.join(DATA_DIR, 'chang_data.parquet')
    
    # Cache / Pre-generated Images
    SIM_IMAGE_PATH = os.path.join(STATIC_DIR, 'img', 'green_barrier_sim.png')
    
    # Server defaults
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
