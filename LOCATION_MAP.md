## EXACT LOCATION MAP - C:\Users\kulka\Downloads

### 📍 **Main Directory Structure:**
```
C:\Users\kulka\Downloads\
├── 📁 Dataset1_ClassicExcelMap\           ← **YOUR TARGET DATASET**
│   ├── 📄 demographics.xlsx              (Excel mapping file)
│   ├── 📄 README.txt                     (Dataset information)
│   └── 📁 Export\
│       ├── 📁 ClinicalDocuments\
│       │   ├── 📄 clinicaldocument_1001.pdf
│       │   ├── 📄 clinicaldocument_1002.pdf
│       │   └── ... (more PDF files)
│       └── 📁 LabResults\
│           ├── 📄 labresult_1001.png
│           ├── 📄 labresult_1002.png
│           └── ... (more image files)
│
├── 📁 ETL\                               ← **YOUR ETL SYSTEM**
│   ├── 📁 medical_etl_system\            ← **MAIN SYSTEM DIRECTORY**
│   │   ├── 📄 main.py                   (Main processor)
│   │   ├── 📄 dataset1_solution.py      (Dataset1 processor)
│   │   ├── 📄 process_dataset1.py       (Processing script)
│   │   ├── 📁 config\
│   │   │   └── 📄 config.py             (Configuration settings)
│   │   ├── 📁 modules\
│   │   │   ├── 📄 etl_logger.py         (Logging system)
│   │   │   ├── 📄 file_organizer.py     (File organization)
│   │   │   ├── 📄 excel_manager.py      (Excel handling)
│   │   │   └── ... (other modules)
│   │   ├── 📁 data\                     ← **EXCEL TEMPLATES**
│   │   │   ├── 📄 Patient_Mapping_Template.xlsx
│   │   │   └── 📄 Dataset1_Mapping_Demo.xlsx
│   │   ├── 📁 logs\                     ← **LOG FILES LOCATION**
│   │   │   └── 📄 Texas_Houston_100920252140.log
│   │   └── 📁 temp\                     (Temporary files)
│   │
│   ├── 📁 processed_datasets\            ← **OUTPUT DESTINATION**
│   │   └── 📁 Dataset1_Output\          (Will be created when processing)
│   │
│   └── 📁 .venv\                        (Python virtual environment)
│       └── 📁 Scripts\
│           └── 📄 python.exe            (Python interpreter)
│
├── 📁 All_5_Dummy_Datasets\
├── 📁 state_practice_sample\
├── 📁 messy_export_dataset\
└── ... (other directories and files)
```

### 🎯 **Key Paths for Dataset1_ClassicExcelMap Processing:**

#### **Source Dataset:**
```
C:\Users\kulka\Downloads\Dataset1_ClassicExcelMap\
```

#### **ETL System Location:**
```
C:\Users\kulka\Downloads\ETL\medical_etl_system\
```

#### **Configuration Files:**
- **Main Config**: `C:\Users\kulka\Downloads\ETL\medical_etl_system\config\config.py`
- **Log Settings**: Lines 80-95 (smart naming and rotation)
- **Directory Settings**: Lines 12-16 (LOGS_DIR, TEMP_DIR, DATA_DIR)

#### **Log Files Location:**
```
C:\Users\kulka\Downloads\ETL\medical_etl_system\logs\
```
- **Format**: `{state}_{practice}_{mmddyyyyhhmm}_{run_type}_part{n}.log`
- **Example**: `Texas_Houston_100920252140_real_run_part1.log`

#### **Destination Path (Output):**
```
C:\Users\kulka\Downloads\ETL\processed_datasets\Dataset1_Output\
```
- **Patient Folders**: `John_Doe_1985-05-15\`
- **Special Folders**: `UNMAPPED_FILES\`, `DUPLICATES\`
- **Logs Subfolder**: `LOGS\` (with session logs and Excel reports)

### 🚀 **Command to Process Dataset1_ClassicExcelMap:**

```bash
# Navigate to ETL system
cd "C:\Users\kulka\Downloads\ETL\medical_etl_system"

# Run processing command
C:/Users/kulka/Downloads/ETL/.venv/Scripts/python.exe main.py "C:\Users\kulka\Downloads\Dataset1_ClassicExcelMap" "C:\Users\kulka\Downloads\ETL\processed_datasets\Dataset1_Output"

# With mapping file (optional)
C:/Users/kulka/Downloads/ETL/.venv/Scripts/python.exe main.py "C:\Users\kulka\Downloads\Dataset1_ClassicExcelMap" "C:\Users\kulka\Downloads\ETL\processed_datasets\Dataset1_Output" --mapping "data\Patient_Mapping_Template.xlsx"

# Dry run (test mode)
C:/Users/kulka/Downloads/ETL/.venv/Scripts/python.exe main.py "C:\Users\kulka\Downloads\Dataset1_ClassicExcelMap" "C:\Users\kulka\Downloads\ETL\processed_datasets\Dataset1_Output" --dry-run
```

### 📊 **Expected Results After Processing:**

```
C:\Users\kulka\Downloads\ETL\processed_datasets\Dataset1_Output\
├── 📁 Patient_1001\
│   ├── 📄 clinicaldocument_1001.pdf
│   └── 📄 labresult_1001.png
├── 📁 Patient_1002\
│   ├── 📄 clinicaldocument_1002.pdf
│   └── 📄 labresult_1002.png
├── 📁 UNMAPPED_FILES\
├── 📁 DUPLICATES\
└── 📁 LOGS\
    ├── 📄 Dataset1_ClassicExcelMap_100920252146_real_run_part1.log
    ├── 📄 Processing_Summary.xlsx
    └── 📄 Patient_Report.xlsx
```

### 🔧 **How to Customize Locations:**

#### **Change Log Directory:**
Edit `C:\Users\kulka\Downloads\ETL\medical_etl_system\config\config.py`:
```python
LOGS_DIR = Path("C:/CustomLogs")  # Your custom location
```

#### **Change Default Output:**
Update the command line arguments or modify the script to use different destination paths.

All paths are now clearly mapped and ready for Dataset1_ClassicExcelMap processing!