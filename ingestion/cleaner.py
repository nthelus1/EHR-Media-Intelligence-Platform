from __future__ import annotations
import re
import hashlib
import json
from datetime import date
from typing import Optional

from dateutil import parser as dateparser

from .models import AuditLog


def normalize_mrn(raw: str, audit_log: list[AuditLog]) -> str:
    stripped = re.sub(r"\D", "", raw)

    if not stripped:
        stripped = "00000000"
        audit_log.append(AuditLog(
            field="mrn", original=raw, normalized=stripped,
            reason="MRN contained no digits; replaced with sentinel 00000000"
        ))
        return stripped

    padded = stripped.zfill(8)
    if padded != raw:
        audit_log.append(AuditLog(
            field="mrn", original=raw, normalized=padded,
            reason="MRN stripped of non-digits and zero-padded to 8 chars"
        ))
    return padded


def normalize_date(raw: str, field_name: str, audit_log: list[AuditLog]) -> Optional[date]:
    if not raw or raw.strip().lower() in ("", "n/a", "null", "none", "unknown"):
        audit_log.append(AuditLog(
            field=field_name, original=raw, normalized="null",
            reason=f"Empty or sentinel value for {field_name}; set to null"
        ))
        return None

    try:
        parsed = dateparser.parse(raw, dayfirst=False).date()
        iso = str(parsed)
        if iso != raw.strip():
            audit_log.append(AuditLog(
                field=field_name, original=raw, normalized=iso,
                reason=f"Date '{raw}' standardized to ISO-8601 ({iso})"
            ))
        return parsed
    except (ValueError, OverflowError, TypeError):
        audit_log.append(AuditLog(
            field=field_name, original=raw, normalized="null",
            reason=f"Could not parse '{raw}' as a date; set to null"
        ))
        return None


_GENDER_MAP: dict[str, str] = {
    "m": "male", "male": "male", "1": "male", "man": "male",
    "f": "female", "female": "female", "2": "female", "woman": "female",
    "o": "other", "other": "other", "non-binary": "other",
    "nb": "other", "nonbinary": "other",
    "u": "unknown", "unknown": "unknown", "": "unknown",
    "n/a": "unknown", "null": "unknown", "none": "unknown",
    "not specified": "unknown",
}

def normalize_gender(raw: str, audit_log: list[AuditLog]) -> str:
    key = raw.strip().lower()
    normalized = _GENDER_MAP.get(key, "unknown")

    if normalized != raw:
        reason = (
            f"Gender '{raw}' mapped to FHIR code '{normalized}'"
            if key in _GENDER_MAP
            else f"Gender '{raw}' not recognised; defaulted to 'unknown'"
        )
        audit_log.append(AuditLog(
            field="gender", original=raw, normalized=normalized, reason=reason
        ))
    return normalized


_RECORD_TYPE_MAP: dict[str, str] = {
    "lab": "lab", "laboratory": "lab", "lab result": "lab",
    "labs": "lab", "bloodwork": "lab",
    "imaging": "imaging", "radiology": "imaging", "xray": "imaging",
    "x-ray": "imaging", "mri": "imaging", "ct": "imaging",
    "discharge": "discharge_summary",
    "discharge summary": "discharge_summary",
    "discharge note": "discharge_summary",
    "note": "note", "clinical note": "note", "progress note": "note",
}

def normalize_record_type(raw: str, audit_log: list[AuditLog]) -> str:
    key = raw.strip().lower()
    normalized = _RECORD_TYPE_MAP.get(key, "unknown")
    if normalized != raw:
        audit_log.append(AuditLog(
            field="record_type", original=raw, normalized=normalized,
            reason=f"Record type '{raw}' mapped to canonical value '{normalized}'"
        ))
    return normalized


def normalize_name(raw: str, field_name: str, audit_log: list[AuditLog]) -> str:
    cleaned = " ".join(raw.strip().split()).title()
    if cleaned != raw:
        audit_log.append(AuditLog(
            field=field_name, original=raw, normalized=cleaned,
            reason="Name whitespace stripped and title-cased"
        ))
    return cleaned


def record_fingerprint(raw_dict: dict) -> str:
    serialized = json.dumps(raw_dict, sort_keys=True, default=str)
    return hashlib.md5(serialized.encode()).hexdigest()