# Medical ETL System - Enterprise-Lite MVP

A production-ready ETL system for organizing medical records from healthcare practices into structured patient repositories with comprehensive audit logging and a web-based review queue.

## 🏗️ Architecture

The system consists of two main components:

1. **Router Service** - Python CLI that processes files and organizes them by patient
2. **Review Queue UI** - Flask web application for managing unmapped files and monitoring ETL runs

### Key Features

- ✅ **Smart Patient Identification** - Roster matching, filename parsing, folder structure analysis
- ✅ **Duplicate Detection** - Hash-based deduplication with configurable policies
- ✅ **Module Classification** - Automatic categorization (labs, imaging, notes, reports)
- ✅ **PHI-Safe Logging** - Redaction of sensitive data in logs
- ✅ **Audit Trail** - Complete PostgreSQL-backed audit logging with provenance tracking
- ✅ **Review Queue** - Web UI for handling unmapped files and bad DOB corrections
- ✅ **Dry-Run & Canary Modes** - Safe testing before production runs
- ✅ **YAML Configuration** - Per-practice customization without code changes

## 📁 Project Structure

```
medical-etl-mvp/
├── router_service/              # ETL Engine
│   ├── universal_router.py      # Main CLI
│   ├── lib/                     # Core libraries
│   │   ├── identity.py          # Patient identification
│   │   ├── modules.py           # Module/category detection
│   │   ├── dedupe.py            # Duplicate detection
│   │   ├── copier.py            # Safe file operations
│   │   ├── logger.py            # CSV + SQL logging
│   │   └── security.py          # PHI redaction & hashing
│   └── configs/                 # YAML configurations
│       ├── default.yml
│       └── practice_morse.yml
├── review_ui/                   # Flask Web Application
│   ├── app.py                   # Main Flask app
│   └── templates/
│       └── index.html           # Review Queue dashboard
├── dw/                          # Database schema
│   └── schema.sql               # PostgreSQL tables
└── tests/                       # Test data
    ├── sample_roster.xlsx       # Sample patient roster
    └── sample_source/           # Sample files to process
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database (optional - for full ETL system)

### Quick Start

The Review Queue UI is already running at **http://localhost:5000**

View the dashboard to see:
- Overall statistics (total files, copied, unmapped, errors)
- Recent ETL runs
- Unmapped files requiring review
- Files with bad DOB
- Complete audit trail

### Running the Router (ETL Engine)

#### Dry Run (Default - No Files Copied)

```bash
python router_service/universal_router.py \
  --src ./tests/sample_source \
  --dst ./output/patients \
  --config router_service/configs/practice_morse.yml \
  --log ./logs \
  --db-url $DATABASE_URL
```

#### Real Run (Actually Copy Files)

```bash
python router_service/universal_router.py \
  --src ./tests/sample_source \
  --dst ./output/patients \
  --config router_service/configs/practice_morse.yml \
  --log ./logs \
  --db-url $DATABASE_URL \
  --real
```

#### Canary Mode (Test First 100 Files)

```bash
python router_service/universal_router.py \
  --src ./tests/sample_source \
  --dst ./output/patients \
  --config router_service/configs/practice_morse.yml \
  --log ./logs \
  --db-url $DATABASE_URL \
  --canary 100 \
  --real
```

## ⚙️ Configuration

Each practice can have its own YAML configuration file. See `router_service/configs/practice_morse.yml` for a complete example.

### Key Configuration Sections

**Patient Identification**
```yaml
identity:
  roster:
    type: excel
    path: "./tests/sample_roster.xlsx"
    autodetect_headers: true
    hints:
      last: ["last", "last_name", "surname"]
      first: ["first", "first_name", "given"]
      dob: ["dob", "date_of_birth", "birth"]
```

**Module Detection**
```yaml
module_detection:
  folder_keywords:
    labs: ["lab", "labs", "pathology"]
    imaging: ["xray", "ct", "mri", "imaging"]
    notes: ["note", "progress", "encounter"]
  filename_patterns:
    labs: [".*\\bLAB\\b.*"]
```

**Duplicate Detection**
```yaml
dedupe_policy: "same_size_same_module"  # Options: same_size_same_module, strict_hash, size_only
```

**Performance**
```yaml
performance:
  workers: 24
  quick_hash_bytes: 4194304  # 4MB for quick hash
```

## 📊 Database Schema

The system uses PostgreSQL with the following tables:

- **DIM_Patient** - Patient master data
- **FACT_FileProcessing** - Append-only file processing events
- **REF_MappingConfiguration** - Versioned practice configurations
- **REF_FileManifest** - File integrity manifests per session
- **AUDIT_HIPAALog** - HIPAA-compliant audit trail with integrity chain

All tables are automatically created on first run.

## 🔒 Security Features

- **PHI Redaction** - Automatic redaction of SSN, MRN in logs
- **UTC Timestamps** - All timestamps in UTC for consistency
- **Content Hashing** - SHA-256 hashing for file integrity
- **Provenance Tracking** - Complete lineage from source to destination
- **Config Versioning** - Each run logs its configuration hash

## 📈 Monitoring & Operations

### Review Queue Dashboard

Access the web UI at **http://localhost:5000** to:

1. **Monitor ETL Runs** - View recent runs with statistics
2. **Triage Unmapped Files** - Review files that couldn't be matched to patients
3. **Fix Bad DOB** - Correct invalid date of birth entries
4. **Audit Trail** - Track all file processing events
5. **Health Check** - Verify database connectivity at `/health`

### API Endpoints

- `GET /api/stats` - Overall statistics
- `GET /api/recent-runs` - Recent ETL runs
- `GET /api/unmapped` - Unmapped files
- `GET /api/bad-dob` - Files with invalid DOB
- `GET /api/audit` - Audit trail
- `POST /api/reprocess/file` - Reprocess single file
- `POST /api/reprocess/patient` - Reprocess patient's files

### Log Files

CSV logs are written to the specified log directory with format:
```
etl_log_<run_id>.csv
```

Each log includes:
- Run ID, Session Key, Event Time (UTC)
- Source path, Destination path, Action, Reason
- Patient info, Module, File metadata
- Provenance ID, Config hash, Content hash

## 🎯 Workflow

1. **Discover** - Recursively scan source directory
2. **Identify** - Match files to patients using roster + patterns
3. **Classify** - Determine module (labs, imaging, notes, etc.)
4. **Deduplicate** - Check for duplicate files
5. **Organize** - Copy to patient folders: `LastName, FirstName MM-DD-YYYY/module/`
6. **Log** - Record all actions to CSV + PostgreSQL
7. **Review** - Use web UI to handle unmapped files

## 🧪 Testing

Sample test data is included in `tests/`:

- `sample_roster.xlsx` - Sample patient roster with 5 patients
- `sample_source/` - Sample files to process

Run a test:
```bash
python router_service/universal_router.py \
  --src ./tests/sample_source \
  --dst ./test_output \
  --config router_service/configs/practice_morse.yml \
  --real
```

## 📝 Action Types

- `COPY` - File successfully copied to patient folder
- `SKIP_DUP` - Skipped as duplicate
- `MOVE_TO_UNMAPPED` - Could not identify patient
- `MOVE_TO_BAD_DOB` - Invalid date of birth
- `ERROR` - Processing error

## 🔄 Future Enhancements (Phase 2)

- OCR processing for scanned documents
- FHIR/HL7v2/CDA interoperability
- DICOM header parsing for medical imaging
- Advanced data quality framework
- Document classification ML
- Content-addressed storage
- Enhanced de-identification

## 📚 Dependencies

- Flask - Web framework
- PyYAML - Configuration management
- openpyxl - Excel roster parsing
- psycopg2-binary - PostgreSQL connector
- py7zr - Archive extraction
- Gunicorn - Production WSGI server

## 🤝 Support

For issues or questions, check the audit logs in the Review Queue UI or examine the CSV logs in the configured log directory.

---

**Version:** 1.0.0  
**Status:** Production-Ready MVP  
**Compliance:** HIPAA-friendly with PHI-safe logging
