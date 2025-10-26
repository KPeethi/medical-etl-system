# Your Exact Postman Request

## ✅ Copy This Into Postman

### Method: POST
### URL: `http://localhost:5000/api/process`

### Headers:
```
Content-Type: application/json
```

### Body (raw JSON):

## Option 1: If You Have demographics_index.json File

```json
{
  "source": "C:/Users/kulka/Downloads/All_5_Dummy_Datasets/dataset4slove_final/Dataset, Jsonselfmapping/Dataset4_JSON_SelfMapping.zip",
  "dest": "C:/Users/kulka/Downloads/All_5_Dummy_Datasets/organized_output",
  "dry_run": false,
  "mapping": {
    "identity": {
      "roster": {
        "type": "json",
        "path": "C:/Users/kulka/Downloads/All_5_Dummy_Datasets/dataset4slove_final/Dataset, Jsonselfmapping/Dataset4_JSON_SelfMapping.zip/Export/demographics_index.json"
      }
    }
  }
}
```

## Option 2: If You Need to Create a Patient Roster

**First, create this Excel file at:** `C:/Users/kulka/Downloads/patients.xlsx`

| last_name | first_name | dob        |
|-----------|------------|------------|
| Smith     | John       | 1980-05-15 |
| Johnson   | Mary       | 1975-03-20 |

**Then use this request:**

```json
{
  "source": "C:/Users/kulka/Downloads/All_5_Dummy_Datasets/dataset4slove_final/Dataset, Jsonselfmapping/Dataset4_JSON_SelfMapping.zip/Export",
  "dest": "C:/Users/kulka/Downloads/All_5_Dummy_Datasets/organized_output",
  "dry_run": false,
  "mapping": {
    "identity": {
      "roster": {
        "type": "excel",
        "path": "C:/Users/kulka/Downloads/patients.xlsx"
      }
    }
  }
}
```

## Option 3: Process the Export Folder Directly (Not ZIP)

If you've already extracted the ZIP:

```json
{
  "source": "C:/Users/kulka/Downloads/All_5_Dummy_Datasets/dataset4slove_final/Dataset, Jsonselfmapping/Export",
  "dest": "C:/Users/kulka/Downloads/All_5_Dummy_Datasets/organized_output",
  "dry_run": false,
  "mapping": {
    "identity": {
      "roster": {
        "type": "excel",
        "path": "C:/Users/kulka/Downloads/patients.xlsx"
      }
    }
  }
}
```

---

## After Sending the Request

You should see this response:

```json
{
  "status": "success",
  "stats": {
    "processed": 12,
    "copied": 12,      ← All files matched!
    "unmapped": 0,     ← No more unmapped!
    "skipped": 0,
    "errors": 0
  },
  "run_id": "RUN_20251026_...",
  "log_file": "logs/RUN_20251026_....csv"
}
```

And your dashboard will show:
- **Copied: 12** (instead of 0)
- **Unmapped: 0** (instead of 12)

---

## What You Need to Tell Me:

**Do you have a `demographics_index.json` file in your Export folder?**
- If YES → Use Option 1
- If NO → Use Option 2 (create Excel roster first)

**Check if this file exists:**
`C:\Users\kulka\Downloads\All_5_Dummy_Datasets\dataset4slove_final\Dataset, Jsonselfmapping\Dataset4_JSON_SelfMapping.zip\Export\demographics_index.json`

Tell me: **Does that file exist?**
