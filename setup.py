#!/usr/bin/env python3
"""
Setup script for Medical ETL System
"""

from pathlib import Path
from setuptools import setup, find_packages

# Read README for long description
README = (Path(__file__).parent / "README_GITHUB.md").read_text(encoding="utf-8")

# Read requirements
requirements = []
req_file = Path(__file__).parent / "requirements.txt"
if req_file.exists():
    with open(req_file, encoding="utf-8") as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#") and ";" not in line
        ]

setup(
    name="medical-etl-system",
    version="1.0.0",
    author="Medical ETL System Contributors",
    author_email="contact@medical-etl.example.com",
    description="A comprehensive ETL system for processing medical records with intelligent patient identification",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/medical-etl-system",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/medical-etl-system/issues",
        "Source": "https://github.com/yourusername/medical-etl-system",
        "Documentation": "https://github.com/yourusername/medical-etl-system/wiki",
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: System :: Archiving",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "medical-etl=main:main",
            "medical-etl-dataset1=process_dataset1:main",
        ],
    },
    include_package_data=True,
    package_data={
        "config": ["environment_example.env"],
    },
    keywords=[
        "medical", "etl", "healthcare", "data-processing", "ocr", 
        "patient-records", "file-organization", "archive-extraction"
    ],
    zip_safe=False,
)