from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "default"
    admin_email: str
    token: str

    class Config:
        env_file = ".env"