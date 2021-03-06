from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "default"
    admin_email: str
    token: str
    database_url: str

    class Config:
        import os
        is_prod = os.environ.get('IS_HEROKU', None)

        if is_prod is None:
            env_file = ".env"