#!/usr/bin/env python3
"""
Test PDF Creator - Creates sample PDFs with patient information
This helps test the content reading functionality
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pathlib import Path
import shutil

def create_test_pdfs():
    """Create sample PDFs with patient information for testing"""
    
    test_folder = Path(r"C:\Users\kulka\Downloads\test_pdfs")
    if test_folder.exists():
        shutil.rmtree(test_folder)
    test_folder.mkdir(parents=True, exist_ok=True)
    
    # Test PDF 1: Standard medical report format
    pdf1_path = test_folder / "mystery_patient_1.pdf"
    c = canvas.Canvas(str(pdf1_path), pagesize=letter)
    c.drawString(100, 750, "MEDICAL REPORT")
    c.drawString(100, 700, "Patient Last Name: Smith")
    c.drawString(100, 680, "Patient First Name: John")
    c.drawString(100, 660, "Date of Birth: 02/14/1985")
    c.drawString(100, 620, "Medical Record Number: MRN001")
    c.drawString(100, 580, "Visit Date: 10/15/2024")
    c.drawString(100, 540, "Diagnosis: Annual Physical Exam")
    c.save()
    
    # Test PDF 2: Different format with synonyms
    pdf2_path = test_folder / "mystery_patient_2.pdf"
    c = canvas.Canvas(str(pdf2_path), pagesize=letter)
    c.drawString(100, 750, "LABORATORY RESULTS")
    c.drawString(100, 700, "Surname: Kumar")
    c.drawString(100, 680, "Given Name: Anita")
    c.drawString(100, 660, "DOB: 1969-12-12")
    c.drawString(100, 620, "Patient ID: PAT456")
    c.drawString(100, 580, "Test Date: 10/20/2024")
    c.drawString(100, 540, "Test Results: Normal Range")
    c.save()
    
    # Test PDF 3: Different date format
    pdf3_path = test_folder / "mystery_patient_3.pdf"
    c = canvas.Canvas(str(pdf3_path), pagesize=letter)
    c.drawString(100, 750, "VISIT NOTES")
    c.drawString(100, 700, "Family Name: Nguyen")
    c.drawString(100, 680, "Forename: Linh")
    c.drawString(100, 660, "Birth Date: 07-23-1990")
    c.drawString(100, 620, "Chart Number: CHT789")
    c.drawString(100, 580, "Visit Type: Follow-up")
    c.drawString(100, 540, "Notes: Patient doing well")
    c.save()
    
    # Test PDF 4: Multiple patients (should match first one found)
    pdf4_path = test_folder / "multi_patient_doc.pdf"
    c = canvas.Canvas(str(pdf4_path), pagesize=letter)
    c.drawString(100, 750, "GROUP APPOINTMENT SUMMARY")
    c.drawString(100, 700, "Patient 1 - Last Name: Smith, First Name: John")
    c.drawString(100, 680, "DOB: 02/14/1985")
    c.drawString(100, 640, "Patient 2 - Last Name: Kumar, First Name: Anita") 
    c.drawString(100, 620, "DOB: 12/12/1969")
    c.drawString(100, 580, "Group Session Notes...")
    c.save()
    
    print(f"✅ Created 4 test PDFs in: {test_folder}")
    print("📋 Test files created:")
    for pdf_file in test_folder.glob("*.pdf"):
        print(f"   📄 {pdf_file.name}")
    
    return test_folder

if __name__ == "__main__":
    create_test_pdfs()