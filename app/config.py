import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    BEHIND_PROXY = os.environ.get("BEHIND_PROXY", "0") == "1"
    AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
    AUTH0_AUDIENCE = os.environ.get("AUTH0_AUDIENCE", "")
    AUTH0_CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "")
    AUTH0_CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET", "")
    LOCAL_JWT_SECRET_KEY = os.environ.get("LOCAL_JWT_SECRET_KEY", "")
    LOCAL_JWT_EXPIRES_MINUTES = int(
        os.environ.get("LOCAL_JWT_EXPIRES_MINUTES", "60")
    )
    LOCAL_JWT_ISSUER = os.environ.get(
        "LOCAL_JWT_ISSUER", "lacarta-jwt-local"
    )

class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    AUTH0_DOMAIN = "test-tenant.us.auth0.com"
    AUTH0_AUDIENCE = "test-api"
    AUTH0_CLIENT_ID = "test-client"
    AUTH0_CLIENT_SECRET = "test-client-secret"
    LOCAL_JWT_SECRET_KEY = "test-local-jwt-secret-at-least-32-bytes-long"
    LOCAL_JWT_EXPIRES_MINUTES = 5
