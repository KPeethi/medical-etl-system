---
name: Bug Report
about: Create a report to help us improve the Medical ETL System
title: '[BUG] '
labels: ['bug', 'needs-triage']
assignees: ''
---

## 🐛 Bug Description
A clear and concise description of what the bug is.

## 🔄 Steps to Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## ✅ Expected Behavior
A clear and concise description of what you expected to happen.

## ❌ Actual Behavior
A clear and concise description of what actually happened.

## 📸 Screenshots
If applicable, add screenshots to help explain your problem.

## 🖥️ Environment Information
**Please complete the following information:**
- OS: [e.g. Windows 10, Ubuntu 20.04, macOS 12.0]
- Python Version: [e.g. 3.9.7]
- Medical ETL Version: [e.g. 1.0.0]
- Tesseract Version: [run `tesseract --version`]

**Python Package Versions:**
```bash
# Run this command and paste the output:
pip list | grep -E "(pandas|pytesseract|pillow|pdf2image|py7zr|rarfile|openpyxl)"
```

## 📁 Dataset Information
**Please provide (without sensitive data):**
- Dataset size: [e.g. 1000 files, 2GB]
- File types: [e.g. PDF, JPG, ZIP]
- Processing mode: [e.g. mapping, no-mapping, both]
- Archive types: [e.g. ZIP, RAR, 7Z]

## 📋 Configuration
**Environment Configuration (remove sensitive paths):**
```env
# Your .env file content (sanitized)
LOG_LEVEL=INFO
WORKER_THREADS=4
# etc.
```

## 📄 Log Output
**Please provide relevant log output:**
```
# Paste log output here (remove any sensitive information)
```

## 🔧 Additional Context
Add any other context about the problem here.

## ✔️ Checklist
- [ ] I have searched existing issues to ensure this is not a duplicate
- [ ] I have removed all sensitive information from this report
- [ ] I have included the environment information
- [ ] I have included relevant log output
- [ ] I can reproduce this issue consistently