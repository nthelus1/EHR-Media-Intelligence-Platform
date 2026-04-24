import pytest
from datetime import date

from ingestion.cleaner import (
    normalize_mrn,
    normalize_date,
    normalize_gender,
    normalize_name,
    normalize_record_type,
    record_fingerprint,
)


def test_mrn_strips_non_digits_and_pads():
    logs = []
    assert normalize_mrn("MRN-00042", logs) == "00000042"

def test_mrn_empty_string_sentinel():
    logs = []
    assert normalize_mrn("", logs) == "00000000"

def test_mrn_already_correct_no_log():
    logs = []
    normalize_mrn("00001234", logs)
    assert logs == []

def test_date_slash_format():
    logs = []
    assert normalize_date("01/15/1990", "dob", logs) == date(1990, 1, 15)

def test_date_null_returns_none():
    logs = []
    assert normalize_date("null", "dob", logs) is None

def test_date_unparseable_returns_none():
    logs = []
    assert normalize_date("not-a-date", "dob", logs) is None

def test_gender_male_variants():
    logs = []
    for raw in ("m", "M", "Male", "1", "man"):
        assert normalize_gender(raw, logs) == "male"

def test_gender_female_variants():
    logs = []
    for raw in ("f", "F", "Female", "2", "woman"):
        assert normalize_gender(raw, logs) == "female"

def test_gender_unknown_fallback():
    logs = []
    assert normalize_gender("ZZZZ", logs) == "unknown"

def test_name_title_case():
    logs = []
    assert normalize_name("john", "first_name", logs) == "John"

def test_name_strips_whitespace():
    logs = []
    assert normalize_name("  SMITH  ", "last_name", logs) == "Smith"

def test_record_type_lab_variants():
    logs = []
    for raw in ("lab", "laboratory", "Labs", "bloodwork"):
        assert normalize_record_type(raw, logs) == "lab"

def test_duplicate_fingerprint():
    rec = {"mrn": "00001234", "name": "Jane"}
    assert record_fingerprint(rec) == record_fingerprint(rec)

def test_different_records_different_fingerprint():
    r1 = {"mrn": "00001234"}
    r2 = {"mrn": "00009999"}
    assert record_fingerprint(r1) != record_fingerprint(r2)