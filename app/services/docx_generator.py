from io import BytesIO
from typing import Dict
from uuid import UUID
from docx import Document
from app.models import NDAType, FieldsENG, FieldsRuEn
from app.services.minio_service import minio_service


class DOCXGenerator:
    TEMPLATE_MAP = {
        NDAType.ENG: "PT MITRA - NDA_eng.docx",
        NDAType.RU_EN: "PT MITRA - NDA_rus_eng.docx"
    }

    FIELD_MAPPING_ENG = {
        "POINT 1": "effective_date",
        "POINT 2": "company_name",
        "POINT 3": "country",
        "POINT 4": "registration_number",
        "POINT 5": "signatory_name",
        "POINT 5.1": "signatory_title",
        "POINT 6": "address",
        "POINT 7": "email"
    }

    FIELD_MAPPING_RU_EN = {
        "POINT 1": "effective_date",
        "POINT 2": "company_name_en",
        "POINT 3": "company_name_ru",
        "POINT 4": "country_en",
        "POINT 5": "country_ru",
        "POINT 6": "registration_number",
        "POINT 7": "signatory_name_en",
        "POINT 7.1": "signatory_title_en",
        "POINT 8": "signatory_name_ru",
        "POINT 9": "address_en",
        "POINT 10": "address_ru",
        "POINT 11": "email"
    }

    def __init__(self):
        pass

    def _get_field_mapping(self, nda_type: NDAType) -> Dict[str, str]:
        if nda_type == NDAType.ENG:
            return self.FIELD_MAPPING_ENG
        elif nda_type == NDAType.RU_EN:
            return self.FIELD_MAPPING_RU_EN
        else:
            raise ValueError(f"Unknown NDA type: {nda_type}")

    def _replace_placeholders(self, doc: Document, fields: Dict, mapping: Dict[str, str]) -> None:
        replacements = {
            f"[{placeholder}]": str(fields[field_name])
            for placeholder, field_name in mapping.items()
            if field_name in fields and fields[field_name] is not None
        }

        def replace_in_paragraph(paragraph):
            full_text = paragraph.text
            for placeholder, value in replacements.items():
                if placeholder in full_text:
                    full_text = full_text.replace(placeholder, value)

            if full_text != paragraph.text:
                paragraph.clear()
                paragraph.add_run(full_text)

        for paragraph in doc.paragraphs:
            replace_in_paragraph(paragraph)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        replace_in_paragraph(paragraph)

    def generate(self, nda_id: UUID, nda_type: NDAType, fields: Dict) -> bytes:
        template_name = self.TEMPLATE_MAP.get(nda_type)
        if not template_name:
            raise ValueError(f"No template found for NDA type: {nda_type}")

        template_bytes = minio_service.get_template(template_name)
        
        doc = Document(BytesIO(template_bytes))
        
        field_mapping = self._get_field_mapping(nda_type)
        
        self._replace_placeholders(doc, fields, field_mapping)
        
        output = BytesIO()
        doc.save(output)
        output.seek(0)
        
        return output.read()


docx_generator = DOCXGenerator()
