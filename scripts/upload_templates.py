import os
import sys
from pathlib import Path
from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

TEMPLATES = [
    "PT MITRA - NDA_eng.docx",
    "PT MITRA - NDA_rus_eng.docx"
]


def upload_templates():
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
        print(f"✓ Bucket '{MINIO_BUCKET}' created")
    else:
        print(f"✓ Bucket '{MINIO_BUCKET}' already exists")

    templates_dir = Path(__file__).parent.parent / "app" / "templates"
    
    if not templates_dir.exists():
        print(f"✗ Templates directory not found: {templates_dir}")
        print("Please create 'app/templates/' and add NDA template files:")
        for template in TEMPLATES:
            print(f"  - {template}")
        sys.exit(1)

    for template_name in TEMPLATES:
        template_path = templates_dir / template_name
        
        if not template_path.exists():
            print(f"⚠ Template not found: {template_name}")
            continue
        
        try:
            client.fput_object(
                MINIO_BUCKET,
                f"templates/{template_name}",
                str(template_path),
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            print(f"✓ Uploaded: {template_name}")
        except S3Error as e:
            print(f"✗ Failed to upload {template_name}: {e}")

    print("\n✓ Template upload complete!")


if __name__ == "__main__":
    upload_templates()
