from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import date


class AuditLog(BaseModel):
    field: str
    original: str
    normalized: str
    reason: str


class PatientRecord(BaseModel):
    mrn: str = Field(..., description="Zero-padded 8-digit Medical Record Number")
    first_name: str
    last_name: str
    dob: Optional[date] = None
    gender: Literal["male", "female", "other", "unknown"] = "unknown"
    record_type: Literal["lab", "imaging", "discharge_summary", "note", "unknown"]
    record_date: Optional[date] = None
    content: str = Field(..., description="Raw text content of the clinical document")
    source_format: Literal["json", "csv"]
    source_file: str
    audit_log: list[AuditLog] = Field(default_factory=list)

    @field_validator("mrn")
    @classmethod
    def mrn_must_be_8_digits(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 8:
            raise ValueError(f"MRN '{v}' must be exactly 8 digits after normalization")
        return v

    @field_validator("gender")
    @classmethod
    def gender_must_be_valid(cls, v: str) -> str:
        allowed = {"male", "female", "other", "unknown"}
        if v not in allowed:
            raise ValueError(f"Gender '{v}' is not a valid FHIR gender code")
        return v