import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "clave-secreta-de-desarrollo")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://app:123qwe@db:5432/movies_database",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Auth0: sin https:// en el dominio
    AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
    AUTH0_AUDIENCE = os.environ.get("AUTH0_AUDIENCE", "")
    AUTH0_CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "")


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    AUTH0_DOMAIN = "test-tenant.us.auth0.com"
    AUTH0_AUDIENCE = "todoapp-api"
    AUTH0_CLIENT_ID = "test-client-id"