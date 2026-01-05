import json
from io import BytesIO
from typing import Optional
from uuid import UUID
from minio import Minio
from minio.error import S3Error
from app.config import settings
from app.models import NDAMetadata, NDAType


class MinIOService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise Exception(f"MinIO bucket error: {str(e)}")

    def _get_meta_path(self, nda_id: UUID) -> str:
        return f"nda/{nda_id}/meta.json"

    def _get_generated_path(self, nda_id: UUID) -> str:
        return f"nda/{nda_id}/nda_generated/NDA_{nda_id}.docx"

    def _get_signed_path(self, nda_id: UUID, filename: str) -> str:
        return f"nda/{nda_id}/nda_signed/{filename}"

    def save_metadata(self, metadata: NDAMetadata) -> None:
        meta_path = self._get_meta_path(metadata.nda_id)
        meta_json = metadata.model_dump_json(indent=2)
        
        self.client.put_object(
            self.bucket_name,
            meta_path,
            BytesIO(meta_json.encode()),
            length=len(meta_json.encode()),
            content_type="application/json"
        )

    def get_metadata(self, nda_id: UUID) -> Optional[NDAMetadata]:
        meta_path = self._get_meta_path(nda_id)
        
        try:
            response = self.client.get_object(self.bucket_name, meta_path)
            data = json.loads(response.read().decode())
            return NDAMetadata(**data)
        except S3Error:
            return None
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()

    def save_generated_docx(self, nda_id: UUID, docx_bytes: bytes) -> str:
        docx_path = self._get_generated_path(nda_id)
        
        self.client.put_object(
            self.bucket_name,
            docx_path,
            BytesIO(docx_bytes),
            length=len(docx_bytes),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        return docx_path
    
    def save_generated_docx_by_type(self, nda_id: UUID, docx_bytes: bytes, nda_type: NDAType) -> str:
        """Сохраняет DOCX документ с указанием типа (eng или ru_en)"""
        docx_path = f"nda/{nda_id}/nda_generated/NDA_{nda_type}_{nda_id}.docx"
        
        self.client.put_object(
            self.bucket_name,
            docx_path,
            BytesIO(docx_bytes),
            length=len(docx_bytes),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        return docx_path

    def get_presigned_url(self, object_path: str, expiry_seconds: Optional[int] = None) -> str:
        if expiry_seconds is None:
            expiry_seconds = settings.PRESIGNED_URL_EXPIRY_SECONDS
        
        from datetime import timedelta
        url = self.client.presigned_get_object(
            self.bucket_name,
            object_path,
            expires=timedelta(seconds=expiry_seconds)
        )
        return url

    def save_signed_file(self, nda_id: UUID, file_data: bytes, filename: str) -> str:
        signed_path = self._get_signed_path(nda_id, filename)
        
        self.client.put_object(
            self.bucket_name,
            signed_path,
            BytesIO(file_data),
            length=len(file_data),
            content_type="application/octet-stream"
        )
        
        return signed_path

    def get_template(self, template_name: str) -> bytes:
        template_path = f"templates/{template_name}"
        
        try:
            response = self.client.get_object(self.bucket_name, template_path)
            data = response.read()
            return data
        except S3Error as e:
            raise FileNotFoundError(f"Template '{template_name}' not found in MinIO: {str(e)}")
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()


minio_service = MinIOService()
