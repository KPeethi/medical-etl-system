# Enhanced Medical File Organizer

🚀 **Advanced medical file organization system with PDF content reading capabilities**

## ✨ Features

### 🔍 **PDF Content Reading**
- Extracts patient names and DOB directly from PDF content
- Handles multiple synonyms: lastname, surname, family name, given name, forename
- Supports various date formats: MM/DD/YYYY, YYYY-MM-DD, MM-DD-YYYY
- Multiple PDF libraries for robustness: PyPDF2, pdfplumber, PyMuPDF

### 📁 **Smart File Organization**  
- Creates flat folder structure with module-prefixed filenames
- Patient folders: "Smith, John 02-14-1985/"
- Files: "Laboratory_lab_1.pdf", "Reports_medsummary.pdf"
- Eliminates redundant patient names in filenames

### 🎯 **Intelligent Matching**
1. **Filename parsing** (fastest) - parses structured filenames
2. **PDF content reading** - reads PDF text when filename parsing fails
3. **Fuzzy matching** - handles accent mismatches and variations

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Required packages: pandas, PyPDF2, reportlab

### Installation
```bash
pip install -r requirements.txt
```

### Usage

#### 1. Direct File Processing
```bash
python ultimate_organizer.py
# Choose option 1 for real files, option 2 for testing
```

#### 2. API Server (for Postman integration)
```bash
python flat_api_server.py
# Server runs on localhost:8080
# POST to /api/process with ZIP file
```

#### 3. Test PDF Content Reading
```bash
python create_test_pdfs.py  # Create test files
python ultimate_organizer.py  # Choose option 2
```

## 📊 Test Results

**PDF Content Reading Success Rate: 100%**

✅ `mystery_patient_1.pdf` → Found "Smith, John 02/14/1985" → Matched!  
✅ `mystery_patient_2.pdf` → Found "Kumar, Anita 1969-12-12" → Matched!  
✅ `mystery_patient_3.pdf` → Found "Nguyen, Linh 07-23-1990" → Matched!  
✅ `multi_patient_doc.pdf` → Found first patient → Matched!

## 📁 File Structure

```
enhanced-medical-organizer/
├── ultimate_organizer.py      # Main enhanced organizer
├── flat_organizer.py          # Basic flat structure version
├── enhanced_organizer.py      # PDF content reading version  
├── flat_api_server.py         # Flask API for Postman
├── create_test_pdfs.py        # Test PDF generator
├── main.py                    # Entry point
└── requirements.txt           # Dependencies
```

## 🔧 API Endpoints

### Flask API Server (`flat_api_server.py`)

**Health Check**
```http
GET /health
```

**Process Files**
```http
POST /api/process
Content-Type: multipart/form-data
Body: file=medical_dataset.zip
```

## 🎯 Advanced Features

### PDF Content Recognition Patterns

**Name Detection:**
- "Last Name: Smith" / "Surname: Smith"
- "First Name: John" / "Given Name: John"  
- "Patient: Smith, John" / "Patient - Last Name: Smith"

**Date Detection:**
- "DOB: 02/14/1985" / "Date of Birth: 02-14-1985"
- "Birth Date: 1985-02-14" / "Born: 02/14/1985"

### Module Classification
- **Laboratory** - lab reports, test results
- **Reports** - medical summaries, reports  
- **Clinical_Notes** - visit notes, progress notes
- **Imaging** - photos, medical images
- **Billing** - invoices, billing documents
- **Medical_Records** - patient records

## 🔍 Troubleshooting

**PDF Not Reading?**
- File may be corrupted or image-based
- Try different PDF libraries in ultimate_organizer.py

**Files Not Matching?**  
- Check roster.csv format: last_name, first_name, dob
- Verify date formats in source files

**Accent Issues?**
- System handles basic accent variations
- Check encoding of roster.csv file

## 🚀 Next Steps

**Potential Enhancements:**
- OCR for image files (.tif, .jpg)
- Enhanced accent-insensitive matching
- DICOM medical image processing
- HL7/FHIR format support

---

**Created with ❤️ for efficient medical file organization**