# Contributing to Medical ETL System

Thank you for your interest in contributing to the Medical ETL System! We welcome contributions from developers, healthcare professionals, data engineers, and anyone passionate about improving medical data processing.

## 🌟 Ways to Contribute

- 🐛 **Bug Reports**: Help us identify and fix issues
- 🚀 **Feature Requests**: Suggest new functionality
- 💻 **Code Contributions**: Submit pull requests
- 📝 **Documentation**: Improve guides and examples
- 🧪 **Testing**: Help test new features and edge cases
- 💬 **Community Support**: Help others in discussions and issues

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/medical-etl-system.git
cd medical-etl-system

# Add the original repository as upstream
git remote add upstream https://github.com/original-repo/medical-etl-system.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy pre-commit

# Set up pre-commit hooks
pre-commit install
```

### 3. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng libmagic1
```

**macOS:**
```bash
brew install tesseract libmagic
```

**Windows:**
- Download Tesseract from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
- Install Microsoft Visual C++ Redistributable

## 🔄 Development Workflow

### 1. Create a Feature Branch

```bash
# Make sure you're on main and up to date
git checkout main
git pull upstream main

# Create a new branch for your feature
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clear, commented code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run linting
black .
flake8 .
mypy modules/ config/ --ignore-missing-imports

# Run tests
pytest --cov=modules --cov=config

# Test demo functionality
python process_dataset1.py --demo

# Test configuration loading
python -c "from config.config import load_environment_config; print('✅ Config OK')"
```

### 4. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a clear message
git commit -m "feat: add support for DICOM file processing

- Add DICOM file detection and parsing
- Implement metadata extraction
- Add tests for DICOM functionality
- Update documentation

Closes #123"
```

### 5. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create a pull request on GitHub
```

## 📝 Code Style Guidelines

### Python Code Style

We use [Black](https://black.readthedocs.io/) for code formatting and [flake8](https://flake8.pycqa.org/) for linting.

```bash
# Format code
black .

# Check linting
flake8 .

# Type checking
mypy modules/ config/ --ignore-missing-imports
```

### Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system changes
- `ci`: CI/CD changes

**Examples:**
```
feat: add DICOM file support
fix(ocr): handle corrupted PDF files gracefully
docs: update installation guide for macOS
test: add integration tests for file extraction
```

### Code Organization

```
medical_etl_system/
├── config/           # Configuration management
├── modules/          # Core processing modules
├── tests/           # Test files
├── docs/            # Documentation
├── .github/         # GitHub templates and workflows
└── examples/        # Usage examples
```

## 🧪 Testing Guidelines

### Writing Tests

- Write tests for all new functionality
- Include both positive and negative test cases
- Test edge cases and error conditions
- Use meaningful test names and docstrings

```python
def test_patient_parser_extracts_name_from_filename():
    """Test that patient parser correctly extracts names from filenames."""
    parser = PatientParser()
    result = parser.parse_filename("Smith_John_01-15-1990_xray.pdf")
    
    assert result['firstname'] == 'John'
    assert result['lastname'] == 'Smith'
    assert result['dob'] == '01-15-1990'
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules --cov=config --cov-report=html

# Run specific test file
pytest tests/test_patient_parser.py

# Run tests matching a pattern
pytest -k "test_patient"
```

## 📚 Documentation Guidelines

### Code Documentation

- Use clear, descriptive docstrings
- Include parameter and return type information
- Provide usage examples for complex functions

```python
def extract_patient_info(filepath: Path) -> Dict[str, Any]:
    """
    Extract patient information from medical file.
    
    Args:
        filepath: Path to the medical file to process
        
    Returns:
        Dictionary containing patient information:
        - 'firstname': str
        - 'lastname': str  
        - 'dob': str (MM-DD-YYYY format)
        - 'confidence': float (0.0-1.0)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        OCRError: If text extraction fails
        
    Example:
        >>> info = extract_patient_info(Path("smith_john.pdf"))
        >>> print(info['firstname'])
        'John'
    """
```

### Markdown Documentation

- Use clear headings and structure
- Include code examples with syntax highlighting
- Add screenshots for UI-related features
- Keep language clear and concise

## 🔒 Security Guidelines

### Medical Data Handling

⚠️ **IMPORTANT**: Never commit actual medical data or patient information!

- Use synthetic/mock data for testing
- Sanitize all examples and documentation
- Be aware of HIPAA and privacy regulations
- Use environment variables for sensitive configuration

### Code Security

- Validate all inputs
- Handle errors gracefully
- Avoid hardcoded credentials or paths
- Use secure file handling practices

```python
# Good: Validate file paths
def process_file(filepath: str) -> None:
    path = Path(filepath).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

# Bad: No validation
def process_file(filepath: str) -> None:
    with open(filepath) as f:  # Could fail unexpectedly
        # process file
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Clear description** of the issue
2. **Steps to reproduce** the problem
3. **Expected vs actual behavior**
4. **Environment information** (OS, Python version, etc.)
5. **Log output** (sanitized)
6. **Minimal example** if possible

Use our [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).

## 🚀 Feature Requests

When requesting features, please include:

1. **Clear description** of the feature
2. **Use case** and motivation
3. **Proposed solution** or implementation ideas
4. **Acceptance criteria**
5. **Impact assessment**

Use our [feature request template](.github/ISSUE_TEMPLATE/feature_request.md).

## 📋 Pull Request Guidelines

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass and new tests are added
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] No sensitive data is included
- [ ] PR description is clear and complete

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Other: ___

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No sensitive data included
```

## 🏷️ Release Process

1. **Version Bump**: Update version in relevant files
2. **Changelog**: Update CHANGELOG.md with new features and fixes
3. **Tag Release**: Create Git tag with version number
4. **GitHub Release**: Create release with changelog
5. **Package**: Build and publish packages if applicable

## 🤝 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect diverse perspectives and experiences

### Communication

- Use clear, professional language
- Be patient with questions and learning
- Provide helpful, actionable feedback
- Acknowledge contributions from others

## 📞 Getting Help

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/medical-etl-system/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/medical-etl-system/discussions)
- 📖 **Documentation**: [Project Wiki](https://github.com/yourusername/medical-etl-system/wiki)
- 🔧 **Configuration Help**: Use our [configuration template](.github/ISSUE_TEMPLATE/configuration_help.md)

## 🙏 Recognition

Contributors will be:
- Listed in the project README
- Mentioned in release notes
- Credited in documentation
- Invited to join the contributor team

Thank you for helping make medical data processing better for everyone! 🎉

---

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.