# Universal Medical File Processor

**TL;DR:** This tool is universal and portable. All paths are parameterized. Pass a source location (folder or ZIP), and the app auto-discovers files and infers patient identity from filenames/folders. If roster/mapping isn't provided, system continues with filename/folder parsing.

## 🌟 Universal Behavior Guarantee

✅ **Fully parameterized** - All paths come from user input (CLI flags or API JSON)  
✅ **Optional mapping/roster** - System sets `mapping_mode = "none"` and proceeds with filename/folder parsing if not supplied  
✅ **Universal input** - Accepts directory or ZIP, any file types, any date formats, international characters  
✅ **Source is read-only** - Never modify/delete originals, all outputs go under dest  
✅ **Dry-run first** - `dry_run: true` computes everything and writes logs without copying  

## 📋 API Contract

### Endpoint: `POST /api/process`

**Request Body (JSON):**
```json
{
  "source": "{{source_path}}",
  "dest": "{{dest_path}}",
  "dry_run": false,
  "roster": null,
  "mapping": null,
  "options": {
    "duplicate_policy": "size_and_module",
    "output_root_style": "container", 
    "skip_placeholder_dobs": ["01-01-1900","1900-01-01"]
  }
}
```

- `roster`: optional path to CSV/XLSX. If omitted → treated as null
- `mapping`: optional path to JSON alias map. If omitted → treated as null and mapping mode becomes "none"
- `options`: optional fine-tuning

**Successful Response:**
```json
{
  "status": "ok",
  "mapping_mode": "none",
  "discovery": { "files": 283711, "zip_expanded": 1 },
  "matched_patients": 2419,
  "unmapped": 318,
  "duplicates": 77,
  "dry_run": false,
  "logs": {
    "summary_csv": "{{log_path}}/run_summary.csv",
    "details_csv": "{{log_path}}/run_events.csv"
  }
}
```

## 🚀 Usage Examples

### A) Pure Auto Mode (no mapping/roster):
```json
{
  "source": "{{source_path}}",
  "dest": "{{dest_path}}",
  "dry_run": false
}
```
**Expected:** `"mapping_mode": "none"` and the engine parses names/DOBs from file/folder names.

### B) Roster Only (header auto-detection):
```json
{
  "source": "{{source_path}}",
  "dest": "{{dest_path}}",
  "dry_run": true,
  "roster": "/path/to/practice_roster.csv"
}
```

### C) Roster + Mapping Aliases:
```json
{
  "source": "/path/to/batch_files.zip",
  "dest": "/path/to/organized_batch",
  "dry_run": false,
  "roster": "/path/to/practice_roster.csv",
  "mapping": "/path/to/column_aliases.json",
  "options": { "duplicate_policy": "size_and_module" }
}
```

## 🎯 Detection Order

### 1. Roster Match (if provided)
- Normalize headers via mapping aliases if present; else auto-detect common synonyms (LastName/lname/surname, etc.)
- Fuzzy match file name → patient (by Last, First, DOB; tolerate punctuation & separators)

### 2. Filename/Folder Inference (always available)
**Patterns supported:**
- `Lastname_Firstname_YYYY-MM-DD_*`
- `Firstname Lastname - module (MM/DD/YYYY)`
- `DOE,J,LAB_04221988.*`
- `{module}_{last}_{first}.*`

Extract last, first, dob. If DOB missing, mark `dob_status = "missing"` but still route by name.

### 3. Fallbacks & Flags
- Placeholder DOBs (e.g., 01-01-1900) → treat as unknown, not a real DOB
- If both roster and filename inference disagree → prefer roster but log a conflict event

## ⚠️ Validation & Error Messages

| Scenario | Message |
|----------|---------|
| **No mapping/roster** | `mapping_mode set to "none". Proceeding with filename/folder inference.` |
| **Mapping file missing** | `mapping_mode: "file_missing" — mapping not found at "<path>". Falling back to auto alias detection.` |
| **Roster unreadable** | `roster_status: "unavailable" — Could not read roster "<path>". Continuing in filename-only mode.` |
| **No patients inferred** | `inference_status: "no_matches" — Unable to extract name/DOB from provided files. Provide a roster or adjust filename patterns.` |
| **ZIP source** | `discovery: "zip_detected" — Expanding zip to temp workspace (read-only source preserved).` |

## 💻 CLI Contract

```bash
# Interactive (prompts for paths; never hardcodes)
python universal_medical_processor.py

# Command-line mode
python universal_medical_processor.py \
  --source "/path/to/medical_dataset.zip" \
  --dest   "/path/to/organized_patients" \
  --dry-run false
  # --roster "/path/to/roster.csv"           (optional)
  # --mapping "/path/to/column_aliases.json" (optional)
```

## 🏥 API Health Check

**GET `/health`**
```json
{
  "status": "ready",
  "mapping_mode_default": "none",
  "hardcoded_paths": false,
  "version": "1.0.0",
  "universal": true,
  "portable": true
}
```

## 📁 Supported Filename Patterns

✅ `Doe_John_1988-04-22_clinicaldocuments.pdf` → Pattern 1: Lastname_Firstname_YYYY-MM-DD_*  
✅ `John Doe - clinicaldocuments (1988-04-22).pdf` → Pattern 2: Firstname Lastname - module (MM/DD/YYYY)  
✅ `DOE,J,LAB_04221988.pdf` → Pattern 3: DOE,J,LAB_04221988.*  
✅ `john doe 04-22-1988 labs.pdf` → Pattern 4: lastname firstname MM-DD-YYYY  
✅ `MRN12345_Lee_Min_2001-01-09_CT.jpg` → Pattern 5: MRN prefix  
✅ `García_María_1995-10-14_clinical.txt` → International characters supported  
✅ `O'Neil_Aoife_1992-12-05_results.pdf` → Apostrophes and special characters  

## 🌟 Why "Don't Assign Mapping" by Default?

- **Portability**: Hardcoding mapping/paths ties the app to one developer's machine
- **Resilience**: Real datasets arrive with unknown headers; defaulting to `mapping = none` and falling back to auto-detection keeps runs unblocked
- **Clarity**: Surfacing `mapping_mode: "none"` in responses/logs tells the user exactly which path the engine chose

## 📝 Plain English Summary

We don't hard-code any paths or column mappings. You provide source (folder or ZIP) and dest, and the app will auto-discover files and infer patient identity from filenames and folder names. If no roster or mapping is supplied, we explicitly set `mapping_mode = "none"` and proceed with filename/folder parsing (regex heuristics). If a roster or mapping is provided, we use them to increase match accuracy while preserving the read-only source. This design ensures the tool runs universally on any system without local path assumptions.

## 🎉 Getting Started

### 1. Start the API Server
```bash
python universal_api.py
```

### 2. Test with Postman
```
POST http://localhost:8080/api/process
{
  "source": "/path/to/medical_dataset.zip",
  "dest": "/path/to/organized_files",
  "dry_run": false
}
```

### 3. Check Health
```
GET http://localhost:8080/health
```

### 4. Use CLI Mode
```bash
python universal_medical_processor.py
# Follow the prompts
```

---

**One-liner to remember:** *"Point it at any medical dataset and it adapts automatically - no configuration needed, no assumptions made, just works."* 🚀