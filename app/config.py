from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "nda"
    MINIO_SECURE: bool = False
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_EXTENSIONS: str = "pdf,doc,docx,zip"
    PRESIGNED_URL_EXPIRY_SECONDS: int = 900

    # Mail Settings
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    ADMIN_EMAIL: str # Recipient for lead emails

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def allowed_extensions(self) -> set:
        return set(self.ALLOWED_FILE_EXTENSIONS.split(","))


settings = Settings()
