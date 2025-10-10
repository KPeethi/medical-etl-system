# 📊 Excel File Formats for Medical ETL System

## 📋 **Excel Mapping File Format**

### **Main Sheet: "Patient_Mapping"**

| Patient_ID | Last_Name | First_Name | DOB        | File_Name               |
|------------|-----------|------------|------------|-------------------------|
| 12345      | Smith     | John       | 01-15-1980 | john_smith_chart.pdf    |
| 67890      | Johnson   | Mary       | 03-22-1975 | mary_johnson_xray.jpg   |
| 11111      | Brown     | David      | 05-10-1990 | david_brown_lab.pdf     |
| 22222      | Davis     | Sarah      | 12-03-1985 | sarah_davis_report.png  |
| 33333      | Wilson    | Michael    | 08-20-1970 | michael_wilson_scan.tiff|
| 44444      | Garcia    | Lisa       | 02-14-1995 | lisa_garcia_document.pdf|
| 55555      | Martinez  | Robert     | 11-30-1988 | robert_martinez_image.jpg|

### **Flexible Column Names (System Auto-Detects)**

#### **Patient ID Columns** (Any of these names work):
- `Patient_ID`, `ID`, `PatientID`, `PNo`, `P_No`, `Patient_No`
- `Patient_Number`, `ID_Number`, `Medical_ID`, `MRN`
- `Medical_Record_Number`, `Chart_ID`, `Entity_ID`

#### **Name Columns** (Any of these names work):
**Last Name:**
- `Last_Name`, `LastName`, `LName`, `Surname`, `Family_Name`
- `Last`, `Sur_Name`, `FamilyName`

**First Name:**
- `First_Name`, `FirstName`, `FName`, `Given_Name`, `GivenName`
- `First`, `Forename`, `Christian_Name`

#### **File Columns** (Any of these names work):
- `File_Name`, `FileName`, `File`, `Document`, `Doc`
- `Document_Name`, `Doc_Name`, `Name`, `FilePath`

#### **Date of Birth Columns** (Any of these names work):
- `DOB`, `Date_of_Birth`, `DateOfBirth`, `Birth_Date`
- `BirthDate`, `Birth`, `Born`, `Birthday`

### **Date Formats Supported:**
- `01-15-1980`, `01/15/1980`, `01.15.1980`
- `15-01-1980`, `15/01/1980`, `15.01.1980`
- `1980-01-15`, `1980/01/15`, `1980.01.15`
- `January 15, 1980`, `Jan 15, 1980`

---

## 📈 **Excel Log Export Format**

### **Sheet 1: "Session_Summary"**

| Metric                      | Value              |
|-----------------------------|-------------------|
| Session ID                  | 20251009_143015   |
| Run Type                    | real_run          |
| Duration (minutes)          | 15.25             |
| Total Files Processed       | 1250              |
| Successful Operations       | 1200              |
| Failed Operations           | 5                 |
| Duplicate Files Found       | 23                |
| Unmapped Files             | 45                |
| Unique Patients Processed   | 856               |
| Total Errors               | 5                 |
| Total Warnings             | 12                |

### **Sheet 2: "File_Operations" (Complete File Tracking)**

| Operation_ID | Source_File | Destination_File | File_Size_MB | File_Type | Status | Patient_ID | Patient_First_Name | Patient_Last_Name | Patient_DOB | Data_Source | Processing_Duration_Sec | Errors | Warnings |
|-------------|-------------|------------------|--------------|-----------|--------|------------|-------------------|------------------|-------------|-------------|------------------------|--------|----------|
| file_0 | C:\Medical\scan001.pdf | C:\Organized\Smith, John 01-15-1980\2023_scan001.pdf | 2.5 | .pdf | completed | 12345 | John | Smith | 01-15-1980 | mapping_file | 3.2 | | |
| file_1 | C:\Medical\xray.jpg | C:\Organized\Johnson, Mary 03-22-1975\xray.jpg | 1.8 | .jpg | completed | 67890 | Mary | Johnson | 03-22-1975 | filename_parsing | 2.1 | | |
| file_2 | C:\Medical\random_doc.pdf | C:\Organized\Brown, David 05-10-1990\2022_random_doc.pdf | 4.2 | .pdf | completed | | David | Brown | 05-10-1990 | deep_pdf_scan | 15.8 | | |
| file_3 | C:\Medical\unclear.pdf | C:\Organized\unmapped\unclear.pdf | 1.1 | .pdf | completed | | | | | unmapped | 8.5 | | No patient data found |

### **Sheet 3: "Data_Sources"**

| Data_Source        | File_Count | Percentage |
|-------------------|------------|------------|
| mapping_file      | 600        | 48.0       |
| filename_parsing  | 300        | 24.0       |
| basic_ocr         | 200        | 16.0       |
| deep_pdf_scan     | 80         | 6.4        |
| combined_partial  | 20         | 1.6        |
| unmapped          | 50         | 4.0        |

### **Sheet 4: "Deep_Scan_Stats"**

| Metric                    | Value |
|---------------------------|-------|
| Files Requiring Deep Scan | 80    |
| Deep Scan Successful      | 75    |
| Deep Scan Failed          | 5     |
| Average Pages Processed   | 14.2  |
| Total Pages Processed     | 1136  |

### **Sheet 5: "Errors_Warnings"**

| Type    | Operation        | Message                           | Timestamp           | Context                    |
|---------|------------------|-----------------------------------|---------------------|----------------------------|
| ERROR   | File Processing  | Corrupted PDF file               | 2025-10-09T14:32:15 | {"file": "corrupted.pdf"} |
| WARNING | Deep PDF Scan    | No patient data found in 20 pages| 2025-10-09T14:35:22 | {"file": "unclear.pdf"}   |
| ERROR   | OCR Processing   | Tesseract failed                 | 2025-10-09T14:38:10 | {"file": "bad_image.jpg"}  |

---

## 🎯 **Key Features of Excel Logs**

### **✅ Complete Source & Destination Tracking:**
- **Source_File**: Full path to original file
- **Destination_File**: Full path to organized file location
- **Patient folder structure**: `"Smith, John 01-15-1980\2023_chart.pdf"`

### **✅ Processing Method Visibility:**
- **Data_Source** column shows exactly how patient data was found:
  - `mapping_file` - Found in your Excel mapping
  - `filename_parsing` - Extracted from filename patterns
  - `basic_ocr` - Found in first 3 pages via OCR
  - `deep_pdf_scan` - Found via deep 20-page scan
  - `combined_partial` - Best combination of partial data
  - `unmapped` - Safely stored in unmapped folder

### **✅ Performance Metrics:**
- **Processing_Duration_Sec**: How long each file took
- **File_Size_MB**: File sizes for performance analysis
- **Deep scan statistics**: Pages processed, success rates

### **✅ Complete Audit Trail:**
- Every file operation logged with timestamps
- Source and destination paths for compliance
- Error and warning details for troubleshooting
- Patient data extraction confidence scores

### **✅ Excel Benefits:**
- **Filterable**: Sort by data source, file type, errors
- **Pivot tables**: Analyze processing patterns
- **Charts**: Visualize success rates, processing times
- **Integration**: Import into other systems easily
- **Compliance**: Complete audit trail for medical records

## 📁 **File Locations**

### **Mapping Files:**
- `data/Patient_Mapping_Template.xlsx` - Template with examples
- `data/Patient_Mapping_Empty.xlsx` - Empty template
- Your custom mapping files (any Excel/CSV format)

### **Log Files:**
- `logs/session_log_YYYYMMDD_HHMMSS.xlsx` - Complete Excel log
- `logs/session_summary_YYYYMMDD_HHMMSS.json` - JSON summary
- `logs/real_run_YYYYMMDD_HHMMSS.log` - Detailed text log

## 🚀 **Usage Examples**

### **Creating Mapping File:**
1. Open `Patient_Mapping_Template.xlsx`
2. Replace example data with your patient records
3. Save as `your_hospital_mapping.xlsx`
4. Use: `python main.py source dest --mapping your_hospital_mapping.xlsx`

### **Analyzing Results:**
1. Open `session_log_YYYYMMDD_HHMMSS.xlsx`
2. Use Excel filters on "Data_Source" column
3. Create pivot tables for processing statistics
4. Review "Errors_Warnings" sheet for issues

The Excel format provides **complete visibility** into the enhanced processing system with full source/destination tracking and processing method transparency!