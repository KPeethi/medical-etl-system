# How to Fix "All Files Going to Unmapped"

## 🔍 Why Files Are Unmapped

The system can't identify which patient each file belongs to because:

1. **No Roster File** - The config has `roster: path: null`
2. **Filenames Don't Match Patterns** - Files like `random_doc.pdf` don't have patient names
3. **No Patient Information** - Folders/files lack patient identifiers

---

## ✅ Solution 1: Provide a Patient Roster (BEST)

### Step 1: Create Patient Roster Excel File

Create an Excel file `patients.xlsx`:

| last_name | first_name | dob        |
|-----------|------------|------------|
| Smith     | John       | 1980-05-15 |
| Johnson   | Mary       | 1975-03-20 |
| Brown     | Patricia   | 1985-03-15 |

### Step 2: Use in Your API Request

```json
POST http://localhost:5000/api/process
{
  "source": "C:/Users/kulka/Downloads/All_5_Dummy_Datasets/Dataset4_JSON_SelfMapping.zip",
  "dest": "C:/Users/kulka/Downloads/All_5_Dummy_Datasets/dataset4slove_final",
  "dry_run": false,
  "mapping": {
    "identity": {
      "roster": {
        "type": "excel",
        "path": "C:/Users/kulka/Downloads/patients.xlsx",
        "hints": {
          "last": ["last_name", "surname", "last"],
          "first": ["first_name", "given_name", "first"],
          "dob": ["date_of_birth", "dob", "birthdate"]
        }
      }
    }
  }
}
```

---

## ✅ Solution 2: Structure Your Source Files with Patient Names

### Good File/Folder Naming

**Option A: Patient Folders**
```
source/
├── Smith_John_1980-05-15/
│   ├── lab_report.pdf
│   ├── xray.tif
│   └── notes.docx
├── Johnson_Mary_1975-03-20/
│   ├── blood_work.xlsx
│   └── imaging.tif
```

**Option B: Filenames with Patient Info**
```
source/
├── Smith_John_1980-05-15_lab_report.pdf
├── Smith_John_1980-05-15_xray.tif
├── Johnson_Mary_1975-03-20_blood_work.xlsx
```

**Option C: Comma Format**
```
source/
├── Smith, John 05-15-1980/
│   └── labs/
│       └── report.pdf
```

### Patterns the System Recognizes

1. `LastName_FirstName_YYYY-MM-DD`
2. `LastName, FirstName MM-DD-YYYY`
3. `LastName_FirstName` (without DOB)

---

## ✅ Solution 3: Create a Custom Mapping File

### For JSON Format

Create `mapping.json`:

```json
{
  "identity": {
    "roster": {
      "path": "C:/path/to/your/roster.xlsx"
    }
  },
  "module_detection": {
    "folder_keywords": {
      "labs": ["laboratory", "lab", "bloodwork", "pathology"],
      "imaging": ["radiology", "xray", "x-ray", "ct", "mri", "tif"],
      "notes": ["clinical", "progress", "encounter", "visit"],
      "reports": ["report", "summary", "findings"]
    },
    "filename_patterns": {
      "labs": [".*lab.*", ".*blood.*", ".*urine.*"],
      "imaging": [".*xray.*", ".*ct.*", ".*mri.*"]
    }
  }
}
```

### For Excel/CSV Format

Create `mapping.xlsx` or `mapping.csv`:

| pattern          | module  |
|------------------|---------|
| laboratory       | Labs    |
| radiology        | Imaging |
| clinical_notes   | Notes   |
| lab_results      | Labs    |
| pathology_report | Labs    |

---

## 🧪 Test Your Configuration

### Step 1: Dry Run First

```json
POST http://localhost:5000/api/process
{
  "source": "C:/your/test/folder",
  "dest": "C:/output/test",
  "dry_run": true,
  "mapping": "C:/config/mapping.json"
}
```

### Step 2: Check Response

```json
{
  "stats": {
    "processed": 10,
    "copied": 8,
    "unmapped": 2,    // ← Should be 0 or very low
    "skipped": 0,
    "errors": 0
  }
}
```

### Step 3: Review Unmapped Files

```
GET http://localhost:5000/api/unmapped
```

This shows which files couldn't be mapped and why.

---

## 📋 Example: Complete Working Configuration

### Your Dataset Structure
```
Dataset4_JSON_SelfMapping/
└── Export/
    ├── demographics_index.json    // Contains patient info
    ├── labs/
    │   └── file1.pdf
    └── imaging/
        └── file2.tif
```

### Mapping File (demographics_mapping.json)
```json
{
  "identity": {
    "roster": {
      "type": "json",
      "path": "C:/Users/kulka/Downloads/All_5_Dummy_Datasets/Dataset4_JSON_SelfMapping/Export/demographics_index.json",
      "mapping": {
        "last_name": "surname",
        "first_name": "given_name",
        "dob": "date_of_birth"
      }
    }
  },
  "module_detection": {
    "folder_keywords": {
      "labs": ["lab", "labs", "laboratory"],
      "imaging": ["imaging", "radiology", "xray"]
    }
  }
}
```

### API Request
```json
POST http://localhost:5000/api/process
{
  "source": "C:/Users/kulka/Downloads/All_5_Dummy_Datasets/Dataset4_JSON_SelfMapping.zip",
  "dest": "C:/Users/kulka/Downloads/All_5_Dummy_Datasets/dataset4slove_final",
  "dry_run": false,
  "mapping": "C:/Users/kulka/Downloads/demographics_mapping.json"
}
```

---

## 🎯 Quick Fix Checklist

- [ ] Create patient roster Excel file with last_name, first_name, dob columns
- [ ] Save roster to accessible location (e.g., `C:/config/patients.xlsx`)
- [ ] Create mapping JSON file pointing to roster
- [ ] Test with `dry_run: true` first
- [ ] Check `/api/unmapped` endpoint to see what's missing
- [ ] Adjust configuration based on unmapped files
- [ ] Run real processing with `dry_run: false`

---

## 💡 Pro Tips

1. **Start Small**: Test with 5-10 files first before processing thousands
2. **Check Logs**: Review the CSV log files in `./logs/` folder
3. **Use Web UI**: Visit `http://localhost:5000` to see dashboard with stats
4. **Incremental Approach**: Process in batches, review unmapped, adjust config, repeat

---

## 🆘 Still Having Issues?

Share this information:
1. Sample of your source file/folder names
2. Sample of your patient roster (anonymized)
3. Current response from `/api/stats`
4. Output from `/api/unmapped`

This will help diagnose the exact issue!
