# PHI Redaction Notes

## Current Coverage (MVP)

The SecurityManager.redact_path() method redacts the following patterns from file paths:

### Covered Patterns ✓
- `LastName, FirstName MM-DD-YYYY/` (e.g., "Brown, Patricia 03-15-1985/notes")
- `FirstName_LastName/` (e.g., "Johnson_Mary/labs")
- `FirstName_LastName-YYYY/` (e.g., "Williams_Robert-2023/imaging")
- `FirstName_LastName-ER/` (e.g., "Smith_John-ER/records")
- `FirstName_LastName_YYYY/` (e.g., "Davis_Michael_2024/files")
- Date formats: YYYY-MM-DD, MM-DD-YYYY, MM/DD/YYYY
- SSN patterns: XXX-XX-XXXX, XXX.XX.XXXX
- MRN patterns: 2 letters + 6 digits

### Known Limitations (Edge Cases)
- Names with apostrophes in underscore format may not redact: `O'Connor_Patrick/` or `D'Amico_Rose-2024/`
  - Workaround: These names will redact if in comma format: "O'Connor, Patrick" ✓
- All-caps abbreviations in filenames: `LAB_REPORT.PDF` won't be redacted (intentional - not PHI)
- Mixed case generic terms: `Test_Results/` won't be redacted (intentional - not patient names)

## Design Philosophy

The redaction aims for **pragmatic PHI safety** rather than perfect coverage:
1. Redact 95%+ of real-world patient folder patterns
2. Avoid over-redaction of generic medical terms (lab_report, test_results, etc.)
3. Balance security with log utility

## Recommendations for Production

For production deployments handling names with apostrophes/special characters:
1. Consider using hash-based patient folder names instead of readable names
2. Implement additional post-processing redaction layer
3. Use secure log aggregation with field-level encryption
4. Limit log retention and implement strict access controls

## Testing

Test paths in `tests/test_redaction.py` cover common cases. For comprehensive testing, use real de-identified data samples from the target practice.
