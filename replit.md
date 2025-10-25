# Medical ETL System - Enterprise-Lite MVP

## Project Overview

This is a production-ready Medical ETL (Extract, Transform, Load) system designed for healthcare practices to organize and audit medical records. The system automatically processes files from various sources, identifies patients, classifies documents by type, detects duplicates, and organizes everything into structured patient folders with comprehensive audit logging.

**Status:** Production-Ready MVP v1.0.0  
**Last Updated:** October 25, 2025  
**Compliance:** HIPAA-friendly with PHI-safe logging

## Architecture

### Two-Component System

1. **Router Service** (Python CLI)
   - Processes files and organizes them by patient
   - Smart patient identification using rosters and filename patterns
   - Duplicate detection with hash-based policies
   - Module classification (labs, imaging, notes, reports)
   - Comprehensive CSV + PostgreSQL logging

2. **Review Queue UI** (Flask Web App)
   - Currently running on port 5000
   - Dashboard for monitoring ETL runs
   - Unmapped file triage
   - Bad DOB correction workflow
   - Complete audit trail viewer
   - API endpoints for reprocessing

## Recent Changes

### October 25, 2025 - Initial MVP Implementation
- Created complete router service with 6 core libraries
- Implemented PostgreSQL database schema with 5 tables
- Built Flask Review Queue UI with Bootstrap dashboard
- Added PHI-safe logging with automatic redaction
- Created sample test data and comprehensive documentation
- Set up workflow to run Review Queue on port 5000

## Project Structure

```
.
├── router_service/          # ETL Engine
│   ├── universal_router.py  # Main CLI orchestrator
│   ├── lib/                 # Core processing libraries
│   │   ├── identity.py      # Patient ID resolution
│   │   ├── modules.py       # Document classification
│   │   ├── dedupe.py        # Duplicate detection
│   │   ├── copier.py        # Safe file operations
│   │   ├── logger.py        # CSV + SQL logging
│   │   └── security.py      # PHI redaction & hashing
│   └── configs/             # YAML configurations
│       ├── default.yml      # Default settings
│       └── practice_morse.yml # Sample practice config
├── review_ui/               # Web Application
│   ├── app.py               # Flask server
│   └── templates/
│       └── index.html       # Review Queue dashboard
├── dw/                      # Database
│   └── schema.sql           # PostgreSQL schema
└── tests/                   # Test Data
    ├── sample_roster.xlsx   # Patient roster
    └── sample_source/       # Sample files
```

## Database Schema

### Tables Created
- **DIM_Patient** - Patient master data with demographics
- **FACT_FileProcessing** - Append-only file processing events
- **REF_MappingConfiguration** - Versioned practice configurations
- **REF_FileManifest** - File integrity manifests per session
- **AUDIT_HIPAALog** - HIPAA-compliant audit trail

All tables include proper indexing for performance.

## Key Features

### Smart Patient Identification (5-Level Strategy)
1. Roster exact match
2. Filename pattern parsing
3. Folder structure analysis
4. Fuzzy roster matching
5. Heuristic fallback

### Security & Compliance
- PHI redaction in logs (SSN, MRN patterns)
- SHA-256 content hashing for integrity
- UTC timestamps throughout
- Provenance tracking with unique IDs
- Config versioning with hashes
- Tamper-evident audit chain (foundation for future enhancement)

### Operational Modes
- **Dry Run** (default): Preview actions without copying files
- **Real Run**: Execute file copies with full logging
- **Canary Mode**: Test on first N files before full run

## User Preferences

None configured yet. The system uses sensible defaults for:
- Folder naming: `LastName, FirstName MM-DD-YYYY`
- Module detection based on keywords and patterns
- Duplicate policy: same_size_same_module

## How to Use

### View the Review Queue Dashboard
The web UI is already running at **http://localhost:5000**

### Run the ETL Router

**Test with sample data (dry run):**
```bash
python router_service/universal_router.py \
  --src ./tests/sample_source \
  --dst ./output/patients \
  --config router_service/configs/practice_morse.yml \
  --log ./logs \
  --db-url $DATABASE_URL
```

**Real run:**
Add `--real` flag to actually copy files

**Canary run:**
Add `--canary 100` to process only first 100 files

### Configuration

Each practice has a YAML config file defining:
- Patient roster location and column mappings
- Module detection rules (folder keywords, filename patterns)
- Duplicate detection policy
- File extension whitelist/blacklist
- Performance settings (workers, hash sizes)
- Logging preferences

## API Endpoints

- `GET /` - Review Queue dashboard
- `GET /api/stats` - Overall statistics
- `GET /api/recent-runs` - Recent ETL runs
- `GET /api/unmapped` - Files needing patient assignment
- `GET /api/bad-dob` - Files with invalid dates
- `GET /api/audit` - Complete audit trail
- `POST /api/reprocess/file` - Reprocess single file
- `POST /api/reprocess/patient` - Reprocess patient's files
- `GET /health` - Health check

## Action Types

Files are processed with one of these actions:
- `COPY` - Successfully copied to patient folder
- `SKIP_DUP` - Skipped as duplicate
- `MOVE_TO_UNMAPPED` - Patient not identified
- `MOVE_TO_BAD_DOB` - Invalid date of birth
- `ERROR` - Processing error

## Environment Variables

Available automatically in Replit:
- `DATABASE_URL` - PostgreSQL connection string
- `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` - DB connection details
- `SESSION_SECRET` - Flask session secret

## Testing

Sample test data included:
- 5 patients in `tests/sample_roster.xlsx`
- Sample files in `tests/sample_source/`

## Next Phase Roadmap

### Phase 2 Features (Not in MVP)
- OCR processing for scanned documents
- FHIR/HL7v2/CDA interoperability mappings
- DICOM header parsing for medical imaging
- Advanced data quality framework with validation rules
- Document classification ML
- Content-addressed storage with signed manifests
- Enhanced de-identification with reversible tokenization

### Quick Wins for Production
1. Add TLS/SSL for web UI
2. Implement user authentication (RBAC)
3. Add Prometheus metrics endpoint
4. Create reprocess job queue with workers
5. Add email/webhook notifications
6. Implement retention policies
7. Add DR backup procedures

## Development Notes

### Technology Stack
- **Language:** Python 3.11
- **Web Framework:** Flask 3.1
- **Database:** PostgreSQL
- **Config Format:** YAML
- **Logging:** CSV + PostgreSQL dual-write
- **Frontend:** Bootstrap 5 + Vanilla JS
- **Deployment:** Gunicorn-ready

### Code Organization
- Modular library structure for easy testing
- Type hints throughout for maintainability
- PHI-safe logging enforced at the library level
- Configuration-driven behavior (no hard-coded paths)

### Database Patterns
- Append-only fact tables for audit trail
- Slowly-changing dimensions for patient data
- Indexed for common query patterns
- Views for SSIS/reporting integration

## Troubleshooting

**Database connection issues:**
- Check `$DATABASE_URL` environment variable
- Verify PostgreSQL is running: `GET /health`

**Files not processing:**
- Check roster file path in config
- Verify file extensions in whitelist
- Review logs in `./logs/etl_log_*.csv`

**Unmapped files:**
- Use Review Queue UI to triage
- Check patient roster for matches
- Verify filename patterns in config

## Credits

Built following enterprise-ready ETL best practices:
- Bronze-Silver-Gold data pipeline
- Provenance tracking and lineage
- HIPAA-friendly audit logging
- Configuration-driven extensibility
