# EHR Media Intelligence Platform

AI-powered pipeline that ingests raw EHR data, cleans and normalizes it to HL7 FHIR R4.

## Setup

pip install -r requirements.txt

## Run Tests

pytest tests/ -v

## Run Pipeline

python main.py

## Project Structure

ehr_pipeline/
  ingestion/
    models.py      - Pydantic schemas
    cleaner.py     - Normalization functions
    ingestor.py    - JSON and CSV parsers
  tests/
    test_cleaner.py - Unit tests
  data/
    sample_messy.json
    sample_messy.csv

## Design Decisions

- Pydantic v2 for validation and audit logging
- dateutil for flexible date parsing
- MD5 fingerprinting for duplicate detection
- Pure functions in cleaner.py for easy testing