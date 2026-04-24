from __future__ import annotations
import csv
import json
import sys
from pathlib import Path
from typing import Optional

from .cleaner import (
    normalize_mrn,
    normalize_date,
    normalize_gender,
    normalize_name,
    normalize_record_type,
    record_fingerprint,
)
from .models import AuditLog, PatientRecord


def _parse_json(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("patients", "records", "results", "data", "entries"):
            if key in raw and isinstance(raw[key], list):
                return raw[key]
        return [raw]
    raise ValueError(f"Unexpected JSON structure in {path}")


def _parse_csv(path: Path) -> list[dict]:
    records = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({k.strip(): v.strip() for k, v in row.items()})
    return records


def _get(record: dict, *keys: str, default: str = "") -> str:
    for key in keys:
        val = record.get(key, "")
        if val and str(val).strip().lower() not in ("null", "none", "n/a"):
            return str(val).strip()
    return default


def _clean_record(
    raw: dict,
    source_format: str,
    source_file: str,
) -> Optional[PatientRecord]:
    audit_log: list[AuditLog] = []

    raw_mrn = _get(raw, "mrn", "MRN", "patient_id", "patientId", "id")
    mrn = normalize_mrn(raw_mrn, audit_log)

    raw_first = _get(raw, "first_name", "firstName", "given_name", "givenName", "first")
    raw_last = _get(raw, "last_name", "lastName", "family_name", "familyName", "last", "surname")
    first_name = normalize_name(raw_first, "first_name", audit_log)
    last_name = normalize_name(raw_last, "last_name", audit_log)

    raw_dob = _get(raw, "dob", "DOB", "date_of_birth", "dateOfBirth", "birthdate", "birth_date")
    dob = normalize_date(raw_dob, "dob", audit_log)

    raw_gender = _get(raw, "gender", "sex", "Gender", "Sex", default="unknown")
    gender = normalize_gender(raw_gender, audit_log)

    raw_type = _get(raw, "record_type", "recordType", "type", "document_type", "documentType", default="unknown")
    record_type = normalize_record_type(raw_type, audit_log)

    raw_rdate = _get(raw, "record_date", "recordDate", "date", "encounter_date", "encounterDate", "service_date")
    record_date = normalize_date(raw_rdate, "record_date", audit_log)

    content = _get(raw, "content", "text", "notes", "body", "report_text", "reportText", default="[no content]")

    try:
        return PatientRecord(
            mrn=mrn,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            gender=gender,
            record_type=record_type,
            record_date=record_date,
            content=content,
            source_format=source_format,
            source_file=source_file,
            audit_log=audit_log,
        )
    except Exception as exc:
        print(f"[WARN] Skipping record (MRN raw='{raw_mrn}'): {exc}", file=sys.stderr)
        return None


def ingest(path: str | Path) -> list[PatientRecord]:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".json":
        raw_records = _parse_json(path)
        fmt = "json"
    elif suffix in (".csv", ".txt"):
        raw_records = _parse_csv(path)
        fmt = "csv"
    else:
        raise ValueError(f"Unsupported file format: '{suffix}'. Expected .json, .csv, or .txt")

    seen_fingerprints: set[str] = set()
    cleaned: list[PatientRecord] = []
    dup_count = 0
    skip_count = 0

    for raw in raw_records:
        fp = record_fingerprint(raw)
        if fp in seen_fingerprints:
            dup_count += 1
            print(f"[DEDUP] Skipping duplicate record: {raw}", file=sys.stderr)
            continue
        seen_fingerprints.add(fp)

        record = _clean_record(raw, source_format=fmt, source_file=str(path))
        if record is None:
            skip_count += 1
        else:
            cleaned.append(record)

    print(
        f"[INGEST] {path.name}: "
        f"{len(raw_records)} raw → "
        f"{len(cleaned)} cleaned, "
        f"{dup_count} duplicates skipped, "
        f"{skip_count} invalid skipped"
    )
    return cleaned