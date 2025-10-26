# 🏗️ Medical ETL System - Complete Architecture Guide

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Complete Data Flow](#complete-data-flow)
3. [Patient Identification Pipeline](#patient-identification-pipeline)
4. [Module Classification](#module-classification)
5. [Configuration System](#configuration-system)
6. [Database Architecture](#database-architecture)
7. [Security Architecture](#security-architecture)
8. [API Request Lifecycle](#api-request-lifecycle)
9. [Why Files Go to "Unmapped"](#why-files-go-to-unmapped)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MEDICAL ETL SYSTEM                               │
│                                                                      │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐     │
│  │   REST API   │──────│    Router    │──────│  PostgreSQL  │     │
│  │  (Flask UI)  │      │   Service    │      │   Warehouse  │     │
│  └──────────────┘      └──────────────┘      └──────────────┘     │
│         │                      │                      │            │
│         │                      │                      │            │
│    ┌────▼────┐          ┌─────▼──────┐        ┌─────▼──────┐    │
│    │ Postman │          │ File Logic │        │ Audit Logs │    │
│    │ Testing │          │ • Identity │        │ CSV Files  │    │
│    └─────────┘          │ • Modules  │        └────────────┘    │
│                         │ • Dedupe   │                           │
│                         │ • Security │                           │
│                         └────────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Components

1. **review_ui/app.py** - Flask web server + REST API
2. **router_service/** - Core file processing engine
   - `universal_router.py` - Main orchestrator
   - `lib/identity.py` - Patient identification
   - `lib/modules.py` - File classification
   - `lib/dedupe.py` - Duplicate detection
   - `lib/copier.py` - Safe file operations
   - `lib/logger.py` - Audit logging
   - `lib/security.py` - PHI redaction
3. **dw/schema.sql** - PostgreSQL data warehouse
4. **router_service/configs/** - YAML configurations

---

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: API REQUEST                                                  │
└─────────────────────────────────────────────────────────────────────┘
           │
           │  POST /api/process
           │  {
           │    "source": "C:/input/files.zip",
           │    "dest": "C:/output",
           │    "mapping": {...}
           │  }
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: SECURITY VALIDATION (review_ui/app.py)                       │
│  • API key check (if enabled)                                        │
│  • Path validation (prevent traversal)                               │
│  • ZIP safety checks                                                 │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: ZIP EXTRACTION (if source is .zip)                          │
│                                                                      │
│  for each file in ZIP:                                              │
│    ├─ Skip directories                                              │
│    ├─ Validate path (no ../)                                        │
│    ├─ Extract to temp folder                                        │
│    └─ Verify final location                                         │
│                                                                      │
│  temp_dir/ ← All files extracted here                               │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: CONFIGURATION MERGE                                          │
│                                                                      │
│  Base Config (default.yml)                                          │
│       ↓                                                              │
│  + Practice Config (if specified)                                   │
│       ↓                                                              │
│  + API Mapping (from request)                                       │
│       ↓                                                              │
│  = Final Runtime Config                                             │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: INITIALIZE ROUTER (universal_router.py)                     │
│                                                                      │
│  UniversalRouter                                                     │
│    ├─ Load PatientIdentity (with roster)                           │
│    ├─ Load ModuleDetector                                           │
│    ├─ Load DedupeManager                                            │
│    ├─ Load SafeCopier                                               │
│    └─ Load AuditLogger                                              │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 6: SCAN SOURCE FILES                                           │
│                                                                      │
│  Walk directory tree:                                               │
│    for each file:                                                   │
│      ├─ Check extension (.pdf, .tif, etc)                          │
│      ├─ Check max_depth                                             │
│      ├─ Check exclude patterns                                      │
│      └─ Add to processing queue                                     │
│                                                                      │
│  Found: 150 files                                                   │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 7: PROCESS EACH FILE                                           │
│                                                                      │
│  FOR EACH FILE:                                                     │
│    ├─ Identify Patient ──────────────┐                             │
│    ├─ Classify Module                │                             │
│    ├─ Check Duplicates               │                             │
│    ├─ Copy File                      │                             │
│    └─ Log Transaction                │                             │
│                                       │                             │
│  (See detailed flows below)          │                             │
└──────────────────────────────────────┼─────────────────────────────┘
                                        │
                                        ▼
                        [PATIENT IDENTIFICATION FLOW]
```

---

## Patient Identification Pipeline

### 🔍 This is WHERE Files Get "Unmapped"!

```
┌─────────────────────────────────────────────────────────────────────┐
│ FILE: C:/input/Smith_John/lab_report.pdf                            │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: EXTRACT PATIENT INFO FROM FILENAME/PATH                     │
│ (identity.py → identify_from_filename)                              │
│                                                                      │
│  Filename: "Smith_John/lab_report.pdf"                             │
│  Patterns tried:                                                    │
│    ✓ ([A-Z][a-z]+)[_\s,]+([A-Z][a-z]+)[\s_]*([\d\-/]+)            │
│    ✓ (\w+),\s*(\w+)\s+([\d\-/]+)                                   │
│                                                                      │
│  Match found: Smith_John                                            │
│    last: "Smith"                                                    │
│    first: "John"                                                    │
│    dob: None (no date in filename)                                  │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: LOOKUP IN PATIENT ROSTER                                    │
│ (identity.py → load_roster → self.roster)                          │
│                                                                      │
│  🔴 CRITICAL STEP - THIS IS WHERE IT FAILS!                        │
│                                                                      │
│  Config says: roster.path = null                                    │
│  Result: self.roster = {} (empty dictionary)                       │
│                                                                      │
│  Trying to find patient key:                                        │
│    patient_key = "smith_john" (normalized)                         │
│    roster.get("smith_john") → None ❌                              │
│                                                                      │
│  IF roster.path WAS SET:                                            │
│    roster.xlsx loaded:                                              │
│      {"smith_john_1980-05-15": {                                    │
│         "last": "Smith",                                            │
│         "first": "John",                                            │
│         "dob": "1980-05-15"                                         │
│      }}                                                             │
│    roster.get("smith_john") → Fuzzy match found ✓                  │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: DECISION TREE                                               │
│                                                                      │
│  Patient found in roster?                                           │
│    ├─ YES → Use roster data (full name + DOB)                      │
│    │         Continue to Module Classification                      │
│    │                                                                 │
│    └─ NO  → Check if filename had valid patient info               │
│         ├─ Has Last + First name?                                  │
│         │   ├─ YES → Use filename data                             │
│         │   │         (but less reliable, no DOB verification)     │
│         │   │                                                        │
│         │   └─ NO  → ⚠️ FILE GOES TO "UNMAPPED" FOLDER            │
│         │                                                            │
│         └─ Current case: "Smith", "John", no DOB                   │
│              Roster empty → Can't verify                            │
│              → UNMAPPED ❌                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Patient Identification Code Flow

```python
# identity.py - PatientIdentity class

def __init__(self, roster_path=None, config=None):
    self.roster = {}  # Empty initially
    self.config = config or {}
    
    if roster_path:  # ← roster_path is None from config!
        self.load_roster(roster_path)  # Never called!

def load_roster(self, roster_path):
    """Load patient roster from Excel"""
    wb = openpyxl.load_workbook(roster_path)
    # ... parse Excel rows ...
    for row in data_rows:
        patient = self._parse_roster_row(row, headers, header_map)
        patient_key = self._make_patient_key(
            patient['last'], 
            patient['first'], 
            patient['dob']
        )
        self.roster[patient_key] = patient
        # Result: self.roster = {
        #   "smith_john_1980-05-15": {...},
        #   "johnson_mary_1975-03-20": {...}
        # }

def identify_patient(self, file_path, folder_path):
    """Main identification logic"""
    
    # Step 1: Try filename parsing
    candidate = self.identify_from_filename(filename, folder_path)
    # Returns: {"last": "Smith", "first": "John", "dob": None}
    
    # Step 2: Try roster lookup
    if candidate:
        patient_key = self._make_patient_key(
            candidate['last'], 
            candidate['first'], 
            candidate.get('dob')
        )
        # patient_key = "smith_john"
        
        # 🔴 THE CRITICAL LOOKUP
        if patient_key in self.roster:
            return self.roster[patient_key]  # ✓ Found
        
        # Fuzzy match without DOB
        for key, patient in self.roster.items():
            if candidate['last'] == patient['last'] and \
               candidate['first'] == patient['first']:
                return patient  # ✓ Matched
        
        # 🔴 ROSTER IS EMPTY - NO MATCHES POSSIBLE
        # Falls through to "unmapped"
    
    return None  # ❌ UNMAPPED
```

---

## Module Classification

```
┌─────────────────────────────────────────────────────────────────────┐
│ FILE: lab_report.pdf                                                │
│ PATH: C:/input/Smith_John/labs/lab_report.pdf                      │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: CHECK FOLDER KEYWORDS (modules.py)                          │
│                                                                      │
│  Folder path: "Smith_John/labs"                                     │
│                                                                      │
│  Config: module_detection.folder_keywords:                          │
│    labs: ["lab", "labs", "laboratory", "pathology"]                │
│    imaging: ["xray", "ct", "mri", "radiology"]                     │
│    notes: ["note", "notes", "clinical"]                            │
│                                                                      │
│  Check each folder part:                                            │
│    "labs" contains "lab" → Match! ✓                                │
│                                                                      │
│  Result: module = "Labs"                                            │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: CHECK FILENAME PATTERNS (if no folder match)               │
│                                                                      │
│  Filename: "lab_report.pdf"                                         │
│                                                                      │
│  Config: module_detection.filename_patterns:                        │
│    labs: [".*\\bLAB\\b.*", ".*\\bPATH\\b.*"]                       │
│    imaging: [".*\\bXRAY\\b.*", ".*\\bCT\\b.*"]                     │
│                                                                      │
│  Regex match on "lab_report.pdf":                                   │
│    .*\bLAB\b.* → Matches "LAB" → ✓                                 │
│                                                                      │
│  Result: module = "Labs" (confirmed)                               │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: DEFAULT MODULE                                              │
│                                                                      │
│  If no matches found:                                               │
│    module = "General" (catch-all)                                  │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ FINAL DESTINATION PATH                                              │
│                                                                      │
│  dest/                                                              │
│    └─ Smith, John 05-15-1980/                                       │
│        └─ Labs/                                                     │
│            └─ lab_report.pdf                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Configuration System

### Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 1: default.yml (Base Configuration)                           │
│                                                                      │
│  practice_id: "DEFAULT_Practice"                                    │
│  naming:                                                             │
│    patient_folder: "{Last}, {First} {DOB_MM}-{DOB_DD}-{DOB_YYYY}"  │
│  identity:                                                           │
│    roster:                                                           │
│      type: excel                                                    │
│      path: null  ← 🔴 DEFAULT IS NULL                              │
│  module_detection:                                                   │
│    folder_keywords:                                                 │
│      labs: ["lab", "labs"]                                         │
└─────────────────────────────────────────────────────────────────────┘
           │
           │ Merge ↓
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 2: practice_config.yml (Optional Override)                    │
│                                                                      │
│  practice_id: "ABC_Medical"                                         │
│  identity:                                                           │
│    roster:                                                           │
│      path: "C:/configs/abc_patients.xlsx"  ← Overrides null        │
└─────────────────────────────────────────────────────────────────────┘
           │
           │ Merge ↓
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 3: API Mapping (Runtime Override)                             │
│                                                                      │
│  POST /api/process                                                  │
│  {                                                                   │
│    "mapping": {                                                     │
│      "identity": {                                                  │
│        "roster": {                                                  │
│          "path": "C:/temp/patients.xlsx"  ← Final override         │
│        }                                                            │
│      }                                                              │
│    }                                                                │
│  }                                                                  │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ FINAL RUNTIME CONFIG                                                │
│                                                                      │
│  practice_id: "ABC_Medical"                                         │
│  naming:                                                             │
│    patient_folder: "{Last}, {First} {DOB_MM}-{DOB_DD}-{DOB_YYYY}"  │
│  identity:                                                           │
│    roster:                                                           │
│      type: excel                                                    │
│      path: "C:/temp/patients.xlsx"  ← FINAL VALUE                  │
│  module_detection: (from default.yml)                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Config Merge Code

```python
# universal_router.py

def _merge_configs(base, override):
    """Deep merge configurations"""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result

# Load sequence:
base_config = yaml.load(open('default.yml'))
practice_config = yaml.load(open('practice_ABC.yml'))
api_mapping = request.json.get('mapping', {})

config = _merge_configs(base_config, practice_config)
config = _merge_configs(config, api_mapping)
```

---

## Database Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PostgreSQL Data Warehouse                        │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐
│    FACT TABLES           │
│  (Transaction Data)      │
└──────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ FACT_FileProcessing                                                  │
├─────────────────────────────────────────────────────────────────────┤
│ FileProcessingID (PK)    │ Auto-increment                            │
│ RunID                    │ Batch execution ID                        │
│ SessionKey               │ Unique session identifier                 │
│ ProcessedTimestamp       │ When processed                            │
│ SourceFilePath           │ Original file location (REDACTED)         │
│ DestinationFilePath      │ Final file location (REDACTED)            │
│ FileName                 │ File name (PHI redacted)                  │
│ PatientID_FK             │ → DIM_Patient                             │
│ ModuleID_FK              │ → DIM_Module                              │
│ ActionTaken              │ copied/skipped/error                      │
│ FileHash                 │ SHA256 hash                               │
│ FileSizeBytes            │ File size                                 │
│ ProvenanceSource         │ roster/filename/manual                    │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐
│   DIMENSION TABLES       │
│   (Master Data)          │
└──────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ DIM_Patient                                                          │
├─────────────────────────────────────────────────────────────────────┤
│ PatientID (PK)           │ Auto-increment                            │
│ LastName                 │ REDACTED in logs                          │
│ FirstName                │ REDACTED in logs                          │
│ DateOfBirth              │ REDACTED in logs                          │
│ PatientKey               │ Normalized key (smith_john_1980-05-15)    │
│ SourceRoster             │ Which roster file                         │
│ CreatedDate              │ When added to system                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ DIM_Module                                                           │
├─────────────────────────────────────────────────────────────────────┤
│ ModuleID (PK)            │ Auto-increment                            │
│ ModuleName               │ Labs, Imaging, Notes, Reports             │
│ ModuleDescription        │ Human readable description                │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐
│   REFERENCE TABLES       │
└──────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ REF_MappingConfiguration                                             │
├─────────────────────────────────────────────────────────────────────┤
│ MappingID (PK)           │ Auto-increment                            │
│ FolderPattern            │ Keyword to match                          │
│ ModuleID_FK              │ → DIM_Module                              │
│ Priority                 │ Match priority                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ AUDIT_HIPAALog                                                       │
├─────────────────────────────────────────────────────────────────────┤
│ AuditID (PK)             │ Auto-increment                            │
│ Timestamp                │ When accessed                             │
│ UserID                   │ Who accessed (if applicable)              │
│ ActionType               │ SELECT/INSERT/UPDATE                      │
│ TableAccessed            │ Which table                               │
│ RecordID                 │ Which record                              │
│ IPAddress                │ Where from                                │
└─────────────────────────────────────────────────────────────────────┘

Relationships:
  FACT_FileProcessing.PatientID_FK ────→ DIM_Patient.PatientID
  FACT_FileProcessing.ModuleID_FK ─────→ DIM_Module.ModuleID
  REF_MappingConfiguration.ModuleID_FK → DIM_Module.ModuleID
```

---

## Security Architecture

### PHI Redaction Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ ORIGINAL DATA                                                        │
│                                                                      │
│  File: C:/input/Smith_John_1980-05-15/lab_report.pdf               │
│  Patient: Smith, John (DOB: 1980-05-15)                            │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ REDACTION PROCESS (security.py → SecurityManager)                   │
│                                                                      │
│  Patterns to redact:                                                │
│    1. Names: [A-Z][a-z]+ [A-Z][a-z]+                               │
│    2. DOB: \d{4}-\d{2}-\d{2}, \d{2}/\d{2}/\d{4}                    │
│    3. SSN: \d{3}-\d{2}-\d{4}                                        │
│    4. MRN: MRN[\s:]*\d+                                             │
│                                                                      │
│  Processing text:                                                   │
│    "Smith, John (DOB: 1980-05-15)"                                  │
│         │      │           │                                         │
│         ▼      ▼           ▼                                         │
│    [NAME], [NAME] (DOB: [DATE])                                     │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ REDACTED OUTPUT (for CSV logs, database logs)                       │
│                                                                      │
│  File: C:/input/[NAME]_[NAME]_[DATE]/lab_report.pdf                │
│  Patient: [NAME], [NAME] (DOB: [DATE])                             │
└─────────────────────────────────────────────────────────────────────┘
```

### ZIP Extraction Security

```
┌─────────────────────────────────────────────────────────────────────┐
│ INPUT: malicious.zip                                                │
│                                                                      │
│  Contents:                                                          │
│    ├─ normal_file.pdf                                              │
│    ├─ ../../etc/passwd     ← Path traversal attack                │
│    └─ symlink → /secret    ← Symlink escape                        │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ SECURITY CHECK #1: Pre-Extraction Validation                       │
│                                                                      │
│  for member in zip_file:                                            │
│    if member.is_dir():                                              │
│      skip  # Directories not needed                                │
│                                                                      │
│    member_path = normalize(join(temp_dir, member.name))            │
│    member_path_real = realpath(member_path)                        │
│                                                                      │
│    if not member_path_real.startswith(temp_dir_real):              │
│      raise Error("Path traversal detected!")                       │
│                                                                      │
│  Result:                                                            │
│    ✓ normal_file.pdf → Allow                                       │
│    ✗ ../../etc/passwd → BLOCKED (path escapes temp_dir)           │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ SECURITY CHECK #2: Safe Extraction                                  │
│                                                                      │
│  with zip.open(member) as source:                                   │
│    with open(target_path, 'wb') as target:                         │
│      shutil.copyfileobj(source, target)                            │
│                                                                      │
│  # Direct file copy - no symlinks created                          │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ SECURITY CHECK #3: Post-Extraction Validation                       │
│                                                                      │
│  final_path_real = realpath(extracted_file)                        │
│                                                                      │
│  if not final_path_real.startswith(temp_dir_real):                 │
│    os.unlink(extracted_file)  # Delete file                        │
│    raise Error("Symlink attack detected!")                         │
│                                                                      │
│  Result:                                                            │
│    ✓ normal_file.pdf → Safe                                        │
│    ✗ symlink → DELETED and ERROR raised                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## API Request Lifecycle

### Complete POST /api/process Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ CLIENT (Postman)                                                     │
│                                                                      │
│  POST http://localhost:5000/api/process                             │
│  Headers: { "X-API-Key": "secret123" }                             │
│  Body: {                                                            │
│    "source": "C:/input/files.zip",                                 │
│    "dest": "C:/output",                                             │
│    "dry_run": false,                                                │
│    "mapping": { ... }                                               │
│  }                                                                  │
└─────────────────────────────────────────────────────────────────────┘
           │ HTTP POST
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ FLASK SERVER (review_ui/app.py)                                     │
│                                                                      │
│  @app.route('/api/process', methods=['POST'])                       │
│  def process_files():                                               │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: Authentication Check                                        │
│                                                                      │
│  api_key = os.getenv('API_KEY')                                     │
│  if api_key:                                                        │
│    request_key = request.headers.get('X-API-Key')                  │
│    if request_key != api_key:                                       │
│      return {"error": "Unauthorized"}, 401                         │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Parse Request Parameters                                    │
│                                                                      │
│  data = request.get_json()                                          │
│  source = data.get('source')                                        │
│  dest = data.get('dest')                                            │
│  dry_run = data.get('dry_run', False)                              │
│  mapping = data.get('mapping')                                      │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: Validate Paths                                              │
│                                                                      │
│  if not os.path.exists(source):                                     │
│    return {"error": "Source not found"}, 400                       │
│                                                                      │
│  if '..' in source or '..' in dest:                                │
│    return {"error": "Path traversal detected"}, 400                │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: Handle ZIP Extraction (if applicable)                       │
│                                                                      │
│  if source.endswith('.zip'):                                        │
│    temp_dir = tempfile.mkdtemp()                                    │
│    extract_zip_safely(source, temp_dir)                            │
│    source = temp_dir                                                │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: Parse Mapping File                                          │
│                                                                      │
│  if isinstance(mapping, str):                                       │
│    if mapping.endswith('.json'):                                    │
│      mapping = json.load(open(mapping))                            │
│    elif mapping.endswith('.xlsx'):                                  │
│      mapping = parse_excel_mapping(mapping)                        │
│    elif mapping.endswith('.csv'):                                   │
│      mapping = parse_csv_mapping(mapping)                          │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 6: Load and Merge Configurations                               │
│                                                                      │
│  base_config = yaml.load('router_service/configs/default.yml')     │
│  runtime_config = merge_configs(base_config, mapping)              │
│                                                                      │
│  # Extract roster path                                             │
│  roster_path = runtime_config.get('identity', {})                  │
│                             .get('roster', {})                      │
│                             .get('path')                            │
│                                                                      │
│  # 🔴 IF roster_path IS NONE, ROSTER WON'T LOAD!                  │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 7: Initialize UniversalRouter                                  │
│                                                                      │
│  router = UniversalRouter(                                          │
│    source=source,                                                   │
│    dest=dest,                                                       │
│    config=runtime_config,                                           │
│    dry_run=dry_run                                                  │
│  )                                                                  │
│                                                                      │
│  Inside UniversalRouter.__init__:                                   │
│    self.identity = PatientIdentity(                                │
│      roster_path=roster_path,  ← None or actual path               │
│      config=config                                                 │
│    )                                                                │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 8: Process Files                                               │
│                                                                      │
│  stats = router.process()                                           │
│                                                                      │
│  Returns:                                                           │
│  {                                                                  │
│    "processed": 150,                                                │
│    "copied": 142,                                                   │
│    "skipped": 3,                                                    │
│    "unmapped": 4,   ← Files with no patient match                  │
│    "errors": 1,                                                     │
│    "run_id": "RUN_20251026_143022"                                 │
│  }                                                                  │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 9: Cleanup and Return                                          │
│                                                                      │
│  if temp_dir:                                                       │
│    shutil.rmtree(temp_dir)  # Delete extracted ZIP files           │
│                                                                      │
│  return jsonify({                                                   │
│    "status": "success",                                             │
│    "stats": stats,                                                  │
│    "log_file": "logs/RUN_20251026_143022.csv"                      │
│  })                                                                 │
└─────────────────────────────────────────────────────────────────────┘
           │ HTTP 200 OK
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ CLIENT RECEIVES RESPONSE                                             │
│                                                                      │
│  {                                                                  │
│    "status": "success",                                             │
│    "stats": { ... },                                                │
│    "log_file": "logs/RUN_20251026_143022.csv"                      │
│  }                                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Why Files Go to "Unmapped"

### Root Cause Analysis

```
┌─────────────────────────────────────────────────────────────────────┐
│ YOUR SITUATION                                                       │
│                                                                      │
│  You have patient data:                                             │
│    - Smith, John (1980-05-15)                                       │
│    - Johnson, Mary (1975-03-20)                                     │
│                                                                      │
│  But files still go to "unmapped" folder                            │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ THE PROBLEM: Configuration Mismatch                                 │
│                                                                      │
│  router_service/configs/default.yml line 10:                        │
│                                                                      │
│    identity:                                                        │
│      roster:                                                        │
│        type: excel                                                  │
│        path: null  ← 🔴 THIS IS WHY!                               │
│                                                                      │
│  The system doesn't know WHERE your patient data is!                │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ WHAT HAPPENS AT RUNTIME                                             │
│                                                                      │
│  1. System loads default.yml                                        │
│  2. roster.path = null                                              │
│  3. PatientIdentity.__init__(roster_path=None)                     │
│  4. self.roster = {} (empty dictionary)                            │
│  5. For each file:                                                  │
│     - Parse filename: "Smith_John"                                  │
│     - Lookup in roster: roster.get("smith_john") → None            │
│     - No match found                                                │
│     - File → unmapped/ ❌                                           │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ THE FIX: Provide Roster Path                                        │
│                                                                      │
│  Option 1: In API request                                           │
│    {                                                                │
│      "mapping": {                                                   │
│        "identity": {                                                │
│          "roster": {                                                │
│            "path": "C:/path/to/patients.xlsx"                      │
│          }                                                          │
│        }                                                            │
│      }                                                              │
│    }                                                                │
│                                                                      │
│  Option 2: Create practice config                                  │
│    router_service/configs/practice_myoffice.yml:                   │
│      identity:                                                      │
│        roster:                                                      │
│          path: "C:/configs/patients.xlsx"                          │
│                                                                      │
│  Option 3: Edit default.yml (not recommended)                      │
│    Change line 10 to actual path                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Decision Tree: Patient Identification

```
                        START
                          │
                          ▼
                ┌──────────────────┐
                │ Load Config      │
                │ roster.path = ?  │
                └────────┬─────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
         path=null                path="C:/..."
            │                         │
            ▼                         ▼
    ┌───────────────┐        ┌──────────────────┐
    │ roster = {}   │        │ Load Excel       │
    │ (EMPTY)       │        │ Parse patients   │
    └───────┬───────┘        │ roster = {...}   │
            │                └────────┬─────────┘
            │                         │
            │                         │
            └─────────┬───────────────┘
                      │
                      ▼
            ┌──────────────────┐
            │ Process File:    │
            │ "Smith_John.pdf" │
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ Parse Filename   │
            │ last: "Smith"    │
            │ first: "John"    │
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ Lookup in Roster │
            │ key="smith_john" │
            └────────┬─────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   roster={}                 roster={...}
        │                         │
        ▼                         ▼
┌───────────────┐      ┌──────────────────────┐
│ No match      │      │ Found!               │
│ patient=None  │      │ patient={            │
└───────┬───────┘      │   "last": "Smith",   │
        │              │   "first": "John",   │
        │              │   "dob": "1980-..."  │
        │              │ }                    │
        │              └──────────┬───────────┘
        │                         │
        ▼                         ▼
┌───────────────┐      ┌──────────────────────┐
│ UNMAPPED      │      │ Classify Module      │
│ dest/         │      │ Copy to:             │
│  unmapped/    │      │ dest/                │
│   Smith_...   │      │  Smith, John.../     │
└───────────────┘      │   Labs/...           │
                       └──────────────────────┘
```

---

## Summary

### Critical Flow for Your Case

```
YOU NEED TO DO THIS:
═══════════════════════════════════════════════════════════════

1. Create Excel file: C:/patients.xlsx
   
   | last_name | first_name | dob        |
   |-----------|------------|------------|
   | Smith     | John       | 1980-05-15 |
   | Johnson   | Mary       | 1975-03-20 |

2. Send API request:

   POST http://localhost:5000/api/process
   {
     "source": "C:/input/files.zip",
     "dest": "C:/output",
     "dry_run": false,
     "mapping": {
       "identity": {
         "roster": {
           "path": "C:/patients.xlsx"  ← THIS IS THE KEY!
         }
       }
     }
   }

3. System will now:
   ✓ Load roster from C:/patients.xlsx
   ✓ Match "Smith_John" → Smith, John (1980-05-15)
   ✓ Match "Johnson_Mary" → Johnson, Mary (1975-03-20)
   ✓ Copy files to correct patient folders
   ✓ No more "unmapped" files!
```

That's the complete architecture! The root cause is simple: **the system needs to be told WHERE your patient roster is located**.
