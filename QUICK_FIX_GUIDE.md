# Quick Fix: Why You See No Data

## Your Current Situation

Looking at your dashboard:
- **Total Files: 12**
- **Copied: 0** ← Nothing was copied!
- **Unmapped: 12** ← All files failed to match patients
- **Errors: 0**
- **Recent Runs tab: EMPTY**

## Why This Happened

You processed 12 files, but **ALL 12 went to "unmapped"** because the system doesn't know which patient they belong to.

## The Root Cause

Your configuration file has no patient roster:

```yaml
# router_service/configs/default.yml (line 10)
identity:
  roster:
    path: null  ← THIS IS THE PROBLEM!
```

Without a roster file, the system can't match files to patients, so everything goes to the "unmapped" folder.

---

## ✅ SOLUTION: 3 Simple Steps

### Step 1: Create Patient Roster Excel File

Create a file called `patients.xlsx` with this data:

| last_name | first_name | dob        |
|-----------|------------|------------|
| Smith     | John       | 1980-05-15 |
| Johnson   | Mary       | 1975-03-20 |

**Important:** Make sure the column headers are exactly: `last_name`, `first_name`, `dob`

### Step 2: Send This Postman Request

```
POST http://localhost:5000/api/process
Content-Type: application/json

{
  "source": "C:/your/input/folder",
  "dest": "C:/your/output/folder",
  "dry_run": true,
  "mapping": {
    "identity": {
      "roster": {
        "path": "C:/patients.xlsx"
      }
    }
  }
}
```

**Replace:**
- `C:/your/input/folder` with your actual source folder
- `C:/your/output/folder` with where you want files organized

### Step 3: Check Results

After running the request, you should see:
```json
{
  "status": "success",
  "stats": {
    "processed": 12,
    "copied": 12,     ← All files matched!
    "unmapped": 0,    ← No more unmapped!
    "skipped": 0,
    "errors": 0
  }
}
```

---

## What If My Files Don't Have Patient Names?

If your source files are named like:
- `document1.pdf`
- `report.xlsx`
- `scan.tif`

The system **cannot** identify which patient they belong to from the filename alone. You need **ONE** of:

1. **Patient roster file** (recommended) - Maps files to patients via metadata
2. **Rename files** to include patient names:
   - `Smith_John_1980-05-15_document1.pdf`
   - `Johnson_Mary_1975-03-20_report.xlsx`
3. **Organize in patient folders**:
   ```
   source/
   ├── Smith_John/
   │   └── document1.pdf
   └── Johnson_Mary/
       └── report.xlsx
   ```

---

## Example with Your Dataset

Based on your dataset structure:
```
/path/to/medical_dataset.zip
```

**If you have a demographics_index.json file**, here's the request:

```json
POST http://localhost:5000/api/process
{
  "source": "/path/to/medical_dataset.zip",
  "dest": "/path/to/organized_output",
  "dry_run": false,
  "mapping": {
    "identity": {
      "roster": {
        "type": "json",
        "path": "/path/to/demographics_index.json"
      }
    }
  }
}
```

---

## Why "Recent Runs" Tab is Empty

The Recent Runs tab shows empty because:
1. No data in the database yet (first run)
2. Or the database table hasn't been created

After you successfully process files with the roster configuration, this tab will show your processing history.

---

## Need Help?

**Tell me:**
1. Where are your source files located? (full path)
2. Do you have a patient roster file? (Yes/No)
3. If yes, where is it? (full path)

I'll give you the exact Postman request to copy and paste!
