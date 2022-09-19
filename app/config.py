import os
import sys

from pydantic import BaseSettings


class Settings(BaseSettings):
    github_username: str | None 
    github_token: str | None
    postgres_user: str
    postgres_password: str
    postgres_server: str = "db"
    postgres_port: int = 5432
    postgres_db: str

    class Config:
        case_sensitive = False
        env_file = ".env" if "pytest" not in sys.modules else ".env.test"
        env_file_encoding = "utf-8"


settings = Settings()
