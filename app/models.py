from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID, uuid4


class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    details: str
    website_url: Optional[str] = None  # Honeypot field


class NDAType(str, Enum):
    ENG = "eng"
    RU_EN = "ru_en"


class NDAStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    SIGNED_UPLOADED = "signed_uploaded"
    SUBMITTED = "submitted"


class FieldsENG(BaseModel):
    effective_date: str = Field(..., description="DD.MM.YYYY")
    company_name: str = Field(..., description="Full registered company name")
    country: str = Field(..., description="Country of incorporation")
    registration_number: str = Field(..., description="Registration number")
    signatory_name: str = Field(..., description="Authorized signatory name")
    signatory_title: str = Field(..., description="Authorized signatory title")
    address: str = Field(..., description="Full registered address")
    email: EmailStr = Field(..., description="Contact email")


class FieldsRuEn(BaseModel):
    effective_date: str = Field(..., description="DD.MM.YYYY")
    company_name_en: str
    company_name_ru: str
    country_en: str
    country_ru: str
    registration_number: str
    signatory_name_en: str
    signatory_title_en: str
    signatory_name_ru: str
    address_en: str
    address_ru: str
    email: EmailStr


class NDACreateRequest(BaseModel):
    type: NDAType
    fields: Dict


class NDAMetadata(BaseModel):
    nda_id: UUID = Field(default_factory=uuid4)
    type: NDAType
    status: NDAStatus = NDAStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    fields: Dict
    files: Dict[str, Any] = Field(default_factory=lambda: {"generated": {}, "signed": []})


class NDAResponse(BaseModel):
    nda_id: UUID
    type: NDAType
    status: NDAStatus
    created_at: datetime


class NDADownloadResponse(BaseModel):
    presigned_url: str
    expires_in_seconds: int


class NDAUploadResponse(BaseModel):
    nda_id: UUID
    status: NDAStatus
    message: str
