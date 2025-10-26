# Medical ETL System - Complete Architecture

## 📊 System Overview

This is an **Enterprise-Lite Medical File Router** that processes healthcare files and organizes them into structured patient repositories. The system follows a **Bronze-Silver-Gold data pipeline** architecture with HIPAA-compliant security.

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEDICAL ETL SYSTEM                            │
│                                                                  │
│  Source Files (ZIP/Folder) → Router → Patient Folders + DB      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture Layers

### 1. **Input Layer** (Bronze)
Raw medical files from various sources.

```
Source Inputs:
├── ZIP files (automatically extracted)
├── Folder structures
└── Individual files (.pdf, .tif, .xlsx, etc.)
```

### 2. **Processing Layer** (Silver)
Intelligent routing and organization.

```
Router Service:
├── Patient Identification
├── Module Detection (labs, imaging, notes)
├── Deduplication
├── File Copying
└── Audit Logging
```

### 3. **Output Layer** (Gold)
Organized patient repositories + data warehouse.

```
Outputs:
├── Patient Folders (organized by name + DOB)
│   ├── Labs/
│   ├── Imaging/
│   ├── Notes/
│   └── Reports/
├── PostgreSQL Data Warehouse (fact/dimension tables)
└── CSV Audit Logs
```

---

## 🔍 How Patient Identification Works

### **The Problem**: Files go to "unmapped" when system can't identify which patient they belong to.

### **Solution 1: Roster File (Recommended)**

Provide a patient roster Excel file with columns:

| last_name | first_name | dob        |
|-----------|------------|------------|
| Smith     | John       | 1980-05-15 |
| Johnson   | Mary       | 1975-03-20 |

**Configuration:**
```json
{
  "mapping": {
    "identity": {
      "roster": {
        "path": "C:/path/to/roster.xlsx"
      }
    }
  }
}
```

### **Solution 2: Filename Patterns**

Structure your source files with patient names in filenames or folders:

**Good Filename Patterns:**
```
✓ Smith_John_1980-05-15_lab_report.pdf
✓ Johnson, Mary 03-20-1975/xray.tif
✓ Brown_Patricia/labs/blood_work.pdf
```

**System Extracts:**
- Last Name: Smith, Johnson, Brown
- First Name: John, Mary, Patricia
- DOB: 1980-05-15, 1975-03-20 (if available)

### **Solution 3: Mapping File**

Create a mapping file that tells the system how to identify patients:

**JSON Format:**
```json
{
  "identity": {
    "roster": {
      "path": "C:/path/to/roster.xlsx",
      "hints": {
        "last": ["last_name", "surname", "last"],
        "first": ["first_name", "given_name", "first"],
        "dob": ["date_of_birth", "dob", "birthdate"]
      }
    }
  },
  "module_mappings": {
    "laboratory": "Labs",
    "radiology": "Imaging",
    "clinical_notes": "Notes"
  }
}
```

---

## 📁 Directory Structure

```
medical-etl/
├── router_service/           # Core file routing engine
│   ├── lib/
│   │   ├── identity.py      # Patient identification logic
│   │   ├── modules.py       # Module detection (labs/imaging/notes)
│   │   ├── dedupe.py        # Duplicate file detection
│   │   ├── copier.py        # Safe file copying
│   │   ├── logger.py        # Audit logging (CSV + DB)
│   │   └── security.py      # PHI redaction & security
│   ├── configs/
│   │   ├── default.yml      # Default configuration
│   │   └── practice_*.yml   # Per-practice configs
│   └── universal_router.py  # Main CLI router
│
├── review_ui/               # Flask web UI
│   ├── app.py              # REST API + web interface
│   ├── templates/          # HTML templates
│   └── static/             # CSS/JS assets
│
├── dw/
│   └── schema.sql          # PostgreSQL data warehouse schema
│
└── logs/                   # Audit logs (auto-generated)
```

---

## 🔄 Processing Flow

```
┌──────────────┐
│ 1. INGEST    │  ZIP or folder input
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 2. EXTRACT   │  Unzip if needed (with security checks)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 3. IDENTIFY  │  Match file → patient
│              │  • Check roster
│              │  • Parse filename
│              │  • Validate DOB
└──────┬───────┘
       │
       ├─── Patient Found ──────┐
       │                        │
       └─── Not Found ──────────┤
                                ▼
                         ┌──────────────┐
                         │  UNMAPPED    │
                         └──────────────┘
       │
       ▼
┌──────────────┐
│ 4. CLASSIFY  │  Determine module (labs/imaging/notes)
│              │  • Folder keywords
│              │  • Filename patterns
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 5. DEDUPE    │  Check if file already exists
│              │  • SHA256 hash
│              │  • Size + module match
└──────┬───────┘
       │
       ├─── Duplicate ──────────┤
       │                        ▼
       │                  ┌──────────────┐
       │                  │   SKIP       │
       │                  └──────────────┘
       │
       ▼
┌──────────────┐
│ 6. COPY      │  Safe copy to destination
│              │  • Create patient folder
│              │  • Create module subfolder
│              │  • Copy file (read-only source)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 7. LOG       │  Audit trail
│              │  • CSV logs
│              │  • PostgreSQL FACT_FileProcessing
│              │  • PHI redaction
└──────────────┘
```

---

## 🗄️ Database Schema

### **Fact Tables** (Transaction Data)
- `FACT_FileProcessing` - Every file operation logged
  - RunID, SessionKey, timestamps
  - Source/destination paths
  - Patient info, module, action
  - File hash, size, provenance

### **Dimension Tables** (Master Data)
- `DIM_Patient` - Patient master list
- `DIM_Module` - Medical modules (labs, imaging)
- `REF_MappingConfiguration` - Folder→Module rules
- `REF_FileManifest` - File inventory

### **Audit Tables**
- `AUDIT_HIPAALog` - HIPAA compliance audit trail

---

## 🌐 REST API Architecture

### **Endpoint:** `POST /api/process`

```
Request ──────┐
              ▼
    ┌──────────────────┐
    │  Flask API       │
    │  (review_ui)     │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Parse Request    │
    │ • source         │
    │ • dest           │
    │ • dry_run        │
    │ • mapping        │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Security Checks  │
    │ • API key (opt)  │
    │ • Path validation│
    │ • ZIP safety     │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Extract ZIP      │
    │ (if applicable)  │
    │ • Symlink check  │
    │ • Path traversal │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Parse Mapping    │
    │ (if provided)    │
    │ • JSON/Excel/CSV │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ UniversalRouter  │
    │ Process files    │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Return Response  │
    │ • run_id         │
    │ • stats          │
    │ • log_file       │
    └──────────────────┘
```

---

## 🛠️ Configuration System

### **Hierarchical Config**
```
Default Config (default.yml)
  └─> Override with Practice Config (practice_XYZ.yml)
      └─> Override with Mapping File (from API)
```

### **Key Configuration Sections**

1. **Identity** - How to find patients
   ```yaml
   identity:
     roster:
       path: "roster.xlsx"
       hints:
         last: ["last_name", "surname"]
         first: ["first_name", "given"]
         dob: ["date_of_birth", "dob"]
   ```

2. **Naming** - How to format output
   ```yaml
   naming:
     patient_folder: "{Last}, {First} {DOB_MM}-{DOB_DD}-{DOB_YYYY}"
   ```

3. **Module Detection** - How to classify files
   ```yaml
   module_detection:
     folder_keywords:
       labs: ["lab", "laboratory", "pathology"]
       imaging: ["xray", "ct", "mri", "radiology"]
   ```

4. **Safety** - Security settings
   ```yaml
   safety:
     source_readonly_check: true
     dry_run_default: true
   ```

---

## 🔒 Security Features

### **1. PHI Redaction**
All logs automatically redact:
- Patient names
- Dates of birth
- SSN patterns
- MRN patterns

### **2. ZIP Security**
- Path traversal protection
- Symlink attack prevention
- Dual validation (before + after extraction)

### **3. Network Security**
- Localhost-only binding by default
- Optional API key authentication
- HTTPS ready (via reverse proxy)

### **4. File Safety**
- Source files NEVER modified (read-only)
- Temp file cleanup in finally blocks
- SHA256 hash verification

---

## 📊 Statistics & Monitoring

### **Processing Stats**
```json
{
  "processed": 150,    // Total files scanned
  "copied": 142,       // Successfully copied
  "skipped": 3,        // Duplicates
  "unmapped": 4,       // No patient match
  "errors": 1          // Processing errors
}
```

### **Available Endpoints**
- `GET /api/stats` - Overall statistics
- `GET /api/unmapped` - Files needing review
- `GET /api/bad-dob` - Invalid dates of birth
- `GET /api/duplicates` - Duplicate files
- `GET /api/audit` - Full audit trail

---

## 🚀 Usage Patterns

### **Pattern 1: With Roster File**
```json
POST /api/process
{
  "source": "C:/input/dataset.zip",
  "dest": "C:/output/organized",
  "dry_run": false,
  "mapping": {
    "identity": {
      "roster": {
        "path": "C:/config/patients.xlsx"
      }
    }
  }
}
```

### **Pattern 2: Filename-Based**
Source structure:
```
source/
├── Smith_John_1980-05-15/
│   ├── lab_report.pdf
│   └── xray.tif
└── Johnson_Mary_1975-03-20/
    └── blood_work.xlsx
```

### **Pattern 3: Custom Mapping**
```json
{
  "source": "C:/input",
  "dest": "C:/output",
  "mapping": "C:/config/custom_mapping.json"
}
```

---

## 🐛 Troubleshooting

### **Problem: All files go to "unmapped"**

**Causes:**
1. ❌ No roster file provided
2. ❌ Filenames don't match expected patterns
3. ❌ Folder structure doesn't contain patient names

**Solutions:**
1. ✅ Provide a roster file with patient list
2. ✅ Rename files to include patient names
3. ✅ Create custom mapping file
4. ✅ Check configuration hints match your Excel columns

### **Problem: Files not classified correctly**

**Causes:**
1. ❌ Module keywords don't match folder names
2. ❌ Filename patterns not recognized

**Solutions:**
1. ✅ Add custom keywords to config:
   ```json
   {
     "module_detection": {
       "folder_keywords": {
         "labs": ["laboratory", "bloodwork", "urinalysis"]
       }
     }
   }
   ```

---

## 📈 Performance

- **Throughput**: ~100 files/second (SSD)
- **Memory**: Minimal (streaming operations)
- **CPU**: Multi-threaded capable
- **Database**: Batch inserts for efficiency

---

## 🎯 Next Steps

1. **Create Patient Roster** - Excel file with patient list
2. **Configure Mapping** - JSON file with your specific rules
3. **Test with Dry Run** - Verify before real processing
4. **Review Unmapped** - Use web UI to handle edge cases
5. **Production Run** - Process your actual data

