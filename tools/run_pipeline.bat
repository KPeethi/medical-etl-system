@echo off
setlocal

REM Change these paths before running
set SOURCE=C:\Users\kulka\Downloads\Dataset1_ClassicExcelMap\Export
set DEST=C:\Users\kulka\Downloads\Dataset1_ClassicExcelMap\Mapped_Output
set MAPPING=C:\Users\kulka\Downloads\Dataset1_ClassicExcelMap\demographics.xlsx

REM Activate venv if present
if exist "%~dp0..\..\.venv\Scripts\activate.bat" (
  call "%~dp0..\..\.venv\Scripts\activate.bat"
)

python "%~dp0..\main.py" "%SOURCE%" "%DEST%" --mapping "%MAPPING%"

endlocal
