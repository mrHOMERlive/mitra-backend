from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, status
from typing import Optional
from fastapi.responses import Response
from app.models import (
    NDACreateRequest, NDAUploadResponse, NDAMetadata, NDAStatus, NDAType
)
from app.services.minio_service import minio_service
from app.services.docx_generator import docx_generator
from app.config import settings


router = APIRouter(prefix="/nda", tags=["NDA"])


@router.post("/generate")
async def generate_and_download_nda(
    request: NDACreateRequest,
    nda_id: Optional[str] = Query(None, description="Existing NDA ID to reuse")
):
    """
    Генерирует NDA и возвращает DOCX файл.
    
    Workflow для билингвальной формы:
    1. Нажатие "Download Bilingual NDA" -> POST /nda/generate (type=ru_en)
       Получаете NDA ID в заголовке X-NDA-ID и сохраняете на фронте
    
    2. Нажатие "Download ENG NDA" -> POST /nda/generate?nda_id={saved_id} (type=eng)
       Используется тот же NDA ID, оба документа в одной папке
    
    Возвращает:
    - DOCX файл для скачивания
    - X-NDA-ID в заголовке
    """
    if nda_id:
        try:
            nda_uuid = UUID(nda_id)
            metadata = minio_service.get_metadata(nda_uuid)
            
            if not metadata:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"NDA with id {nda_id} not found"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid NDA ID format"
            )
    else:
        metadata = NDAMetadata(
            type=request.type,
            status=NDAStatus.DRAFT,
            fields=request.fields
        )
    
    try:
        docx_bytes = docx_generator.generate(
            nda_id=metadata.nda_id,
            nda_type=request.type,
            fields=request.fields
        )
        
        docx_path = minio_service.save_generated_docx_by_type(
            metadata.nda_id, 
            docx_bytes, 
            request.type
        )
        
        metadata.status = NDAStatus.GENERATED
        if "generated" not in metadata.files:
            metadata.files["generated"] = {}
        metadata.files["generated"][str(request.type.value)] = docx_path
        minio_service.save_metadata(metadata)
        
        filename = f"NDA_{request.type}_{metadata.nda_id}.docx"
        
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-NDA-ID": str(metadata.nda_id),
                "Access-Control-Expose-Headers": "X-NDA-ID"
            }
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate NDA: {str(e)}"
        )


@router.post("/{nda_id}/upload-signed")
async def upload_signed_nda(nda_id: UUID, file: UploadFile = File(...)):
    """
    Загружает подписанный NDA файл.
    Кнопка фронтенда: "Upload Signed NDA"
    
    Параметры:
    - nda_id: UUID полученный из заголовка X-NDA-ID при генерации
    - file: подписанный файл (PDF/DOC/DOCX/ZIP)
    """
    metadata = minio_service.get_metadata(nda_id)
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NDA with id {nda_id} not found"
        )
    
    if metadata.status == NDAStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot upload signed NDA before generating it"
        )
    
    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed: {', '.join(settings.allowed_extensions)}"
        )
    
    file_data = await file.read()
    file_size = len(file_data)
    
    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        signed_filename = f"NDA_SIGNED_{timestamp}.{file_ext}"
        
        signed_path = minio_service.save_signed_file(nda_id, file_data, signed_filename)
        
        if "signed" not in metadata.files:
            metadata.files["signed"] = []
        metadata.files["signed"].append(signed_path)
        metadata.status = NDAStatus.SIGNED_UPLOADED
        
        minio_service.save_metadata(metadata)
        
        return NDAUploadResponse(
            nda_id=nda_id,
            status=metadata.status,
            message="Signed NDA uploaded successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload signed NDA: {str(e)}"
        )


@router.post("/{nda_id}/submit")
async def submit_nda(nda_id: UUID):
    """
    Финальная отправка NDA.
    Кнопка фронтенда: "Submit NDA"
    
    Параметры:
    - nda_id: UUID полученный из заголовка X-NDA-ID при генерации
    """
    metadata = minio_service.get_metadata(nda_id)
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NDA with id {nda_id} not found"
        )
    
    if metadata.status != NDAStatus.SIGNED_UPLOADED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit NDA: signed file must be uploaded first"
        )
    
    try:
        metadata.status = NDAStatus.SUBMITTED
        minio_service.save_metadata(metadata)
        
        return NDAUploadResponse(
            nda_id=nda_id,
            status=metadata.status,
            message="NDA submitted successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit NDA: {str(e)}"
        )
