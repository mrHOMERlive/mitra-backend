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
