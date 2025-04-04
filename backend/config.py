import os
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# API Configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8000))

# Rate Limiter Configuration
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 60))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv('RATE_LIMIT_MAX_REQUESTS', 20))

# Redis Cache Configuration
REDIS_CACHE_EXPIRE_SECONDS = int(os.getenv('REDIS_CACHE_EXPIRE_SECONDS', 86400))
REDIS_CACHE_MAX_KEYS = int(os.getenv('REDIS_CACHE_MAX_KEYS', 1000))

# SSL Configuration
SSL_KEYFILE = os.getenv('SSL_KEYFILE')
SSL_CERTFILE = os.getenv('SSL_CERTFILE')