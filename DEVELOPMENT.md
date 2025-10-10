# Development Setup Instructions

## Quick Development Setup

1. **Clone and setup virtual environment:**
```bash
git clone https://github.com/yourusername/medical-etl-system.git
cd medical-etl-system
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy  # Dev dependencies
```

3. **Install Tesseract:**
- **Ubuntu/Debian:** `sudo apt-get install tesseract-ocr`
- **macOS:** `brew install tesseract`
- **Windows:** Download from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

4. **Configure environment:**
```bash
cp config/environment_example.env config/.env
# Edit config/.env if needed (optional - auto-detection works)
```

5. **Verify setup:**
```bash
python -c "from config.config import load_environment_config; print('✅ Setup successful')"
python process_dataset1.py --demo
```

## Repository Structure

```
medical_etl_system/
├── .github/                 # GitHub-specific files
│   ├── workflows/          # GitHub Actions CI/CD
│   └── ISSUE_TEMPLATE/     # Issue templates
├── config/                 # Configuration management
│   ├── config.py          # Main configuration
│   ├── .env               # Environment variables (create from example)
│   └── environment_example.env
├── modules/               # Core processing modules
│   ├── file_extractor.py
│   ├── ocr_processor.py
│   ├── patient_parser.py
│   └── ...
├── docs/                  # Documentation (optional)
├── tests/                 # Test files (create as needed)
├── main.py               # Main ETL processor
├── process_dataset1.py   # Dataset-specific processor
└── requirements.txt      # Python dependencies
```

## Development Workflow

1. **Create feature branch:** `git checkout -b feature/your-feature`
2. **Make changes and test:** `pytest`, `black .`, `flake8 .`
3. **Commit:** `git commit -m "feat: description"`
4. **Push and create PR:** `git push origin feature/your-feature`

## Testing

- **Unit tests:** `pytest`
- **Coverage:** `pytest --cov=modules --cov=config`
- **Demo mode:** `python process_dataset1.py --demo`
- **Linting:** `black . && flake8 .`