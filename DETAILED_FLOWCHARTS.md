# Detailed Algorithm Flowcharts

**Medical Records ETL System - Internal Logic**

Visual diagrams showing how the core algorithms work internally.

---

## 1) Identity Matching Algorithm (Filename → Patient)

This flowchart shows how the system matches a file to a patient using fuzzy matching on the filename.

```mermaid
flowchart TD
    Start([File: Smith_John_1980-05-15_lab.pdf]) --> ParseName[Parse Filename]
    
    ParseName --> Extract[Extract Components:<br/>Last = Smith<br/>First = John<br/>DOB = 1980-05-15]
    
    Extract --> LoadRoster[Load Roster<br/>from roster.xlsx]
    
    LoadRoster --> Autodetect{Autodetect<br/>Columns?}
    
    Autodetect -->|Yes| DetectCols[Detect last/first/dob<br/>columns with confidence]
    Autodetect -->|No| UseDefined[Use defined<br/>column mappings]
    
    DetectCols --> BuildIndex[Build Patient Index<br/>Key = Last|First|DOB]
    UseDefined --> BuildIndex
    
    BuildIndex --> ExactMatch{Exact Match<br/>Found?}
    
    ExactMatch -->|Yes| MatchFound[✓ Patient Matched<br/>Confidence: 1.0]
    
    ExactMatch -->|No| FuzzyLast{Fuzzy Match<br/>Last Name?<br/>threshold: 0.85}
    
    FuzzyLast -->|Match| FuzzyFirst{Fuzzy Match<br/>First Name?<br/>threshold: 0.85}
    
    FuzzyFirst -->|Match| DOBMatch{DOB<br/>Matches?}
    
    DOBMatch -->|Yes| MatchFound2[✓ Patient Matched<br/>Confidence: 0.90]
    DOBMatch -->|No| PartialMatch[⚠ Partial Match<br/>Confidence: 0.60]
    
    FuzzyFirst -->|No Match| NoMatch
    FuzzyLast -->|No Match| NoMatch[✗ No Match<br/>→ UNMAPPED]
    
    MatchFound --> Route[Route to:<br/>Patients/Smith, John 05-15-1980/]
    MatchFound2 --> Route
    PartialMatch --> ManualReview[→ Manual Review Queue]
    NoMatch --> Unmapped[→ Unmapped/]
    
    Route --> End([File Copied])
    ManualReview --> End2([Queued for Review])
    Unmapped --> End3([File in Unmapped/])
    
    style MatchFound fill:#90EE90
    style MatchFound2 fill:#90EE90
    style PartialMatch fill:#FFD700
    style NoMatch fill:#FFB6C1
```

**Matching Logic:**
1. **Parse filename** for patient identifiers (last, first, DOB)
2. **Autodetect** roster columns (or use defined mappings)
3. **Exact match** first (fastest path)
4. **Fuzzy match** if exact fails (handles typos)
5. **Confidence scoring**:
   - Exact: 1.0
   - Fuzzy + DOB: 0.90
   - Fuzzy only: 0.60
   - No match: → Unmapped

---

## 2) Deduplication Decision Tree

This flowchart shows how the system decides whether to copy, skip, or rename files based on deduplication rules.

```mermaid
flowchart TD
    Start([Incoming File:<br/>Smith_lab_2024.pdf]) --> CheckDest{File Already<br/>Exists in Dest?}
    
    CheckDest -->|No| CopyNew[Action: COPY_NEW<br/>✓ Copy file to destination]
    
    CheckDest -->|Yes| GetPolicy[Check dedupe_policy<br/>from config.yml]
    
    GetPolicy --> PolicyType{Dedup<br/>Policy?}
    
    PolicyType -->|hash_only| HashCompare[Compare SHA256 Hash]
    PolicyType -->|same_size_same_module| SizeModuleCompare[Compare File Size<br/>+ Module Type]
    PolicyType -->|name_size_module| NameSizeModuleCompare[Compare Name<br/>+ Size + Module]
    PolicyType -->|always_keep| AlwaysKeep[Never Skip]
    
    HashCompare --> HashMatch{Hashes<br/>Match?}
    
    HashMatch -->|Yes| DupHash[Action: DUP_HASH<br/>✗ Skip - exact duplicate]
    HashMatch -->|No| DifferentContent[Different Content]
    
    SizeModuleCompare --> SizeModMatch{Size + Module<br/>Match?}
    
    SizeModMatch -->|Yes| DupSizeMod[Action: DUP_SIZE_MODULE<br/>✗ Skip - likely duplicate]
    SizeModMatch -->|No| DifferentFile
    
    NameSizeModuleCompare --> AllMatch{Name + Size<br/>+ Module Match?}
    
    AllMatch -->|Yes| DupNameSizeMod[Action: DUP_NAME_SIZE_MODULE<br/>✗ Skip - duplicate]
    AllMatch -->|No| DifferentFile[Different File]
    
    AlwaysKeep --> Rename[Generate Unique Name:<br/>filename_001.pdf]
    DifferentContent --> Rename
    DifferentFile --> Rename
    
    Rename --> CopyRenamed[Action: COPY_RENAMED<br/>✓ Copy with new name]
    
    CopyNew --> LogAction[Log to CSV:<br/>fact_fileprocessing]
    DupHash --> LogAction
    DupSizeMod --> LogAction
    DupNameSizeMod --> LogAction
    CopyRenamed --> LogAction
    
    LogAction --> End([Complete])
    
    style CopyNew fill:#90EE90
    style CopyRenamed fill:#90EE90
    style DupHash fill:#FFB6C1
    style DupSizeMod fill:#FFB6C1
    style DupNameSizeMod fill:#FFB6C1
```

**Dedup Policies:**

| Policy | Checks | Use Case |
|--------|--------|----------|
| `hash_only` | SHA256 hash | Strict - only skip if binary identical |
| `same_size_same_module` | File size + module type | Fast - likely duplicates |
| `name_size_module` | Name + size + module | Balanced - good default |
| `always_keep` | Nothing | Keep all files (rename if needed) |

---

## 3) Module Classification Logic (Labs/Imaging/Notes/Reports)

This flowchart shows how files are categorized into clinical modules.

```mermaid
flowchart TD
    Start([File: patient_xray_chest.pdf]) --> CheckFolder{Parent Folder<br/>Has Keyword?}
    
    CheckFolder -->|Yes| FolderKeyword[Check folder_keywords<br/>from config.yml]
    
    FolderKeyword --> LabsFolder{Folder contains:<br/>lab, labs, laboratory,<br/>pathology?}
    
    LabsFolder -->|Yes| ModuleLabs[Module: Labs]
    LabsFolder -->|No| ImagingFolder{Folder contains:<br/>xray, ct, mri,<br/>imaging, radiology?}
    
    ImagingFolder -->|Yes| ModuleImaging[Module: Imaging]
    ImagingFolder -->|No| NotesFolder{Folder contains:<br/>note, notes, progress,<br/>encounter, clinical?}
    
    NotesFolder -->|Yes| ModuleNotes[Module: Notes]
    NotesFolder -->|No| ReportsFolder{Folder contains:<br/>report, reports,<br/>summary?}
    
    ReportsFolder -->|Yes| ModuleReports[Module: Reports]
    ReportsFolder -->|No| CheckFilename
    
    CheckFolder -->|No| CheckFilename[Check Filename Patterns]
    
    CheckFilename --> LabsPattern{Filename matches:<br/>.*LAB.*<br/>.*PATH.*?}
    
    LabsPattern -->|Yes| ModuleLabs
    LabsPattern -->|No| ImagingPattern{Filename matches:<br/>.*XRAY.*<br/>.*CT.*<br/>.*MRI.*?}
    
    ImagingPattern -->|Yes| ModuleImaging
    ImagingPattern -->|No| NotesPattern{Filename matches:<br/>.*NOTE.*<br/>.*PROGRESS.*?}
    
    NotesPattern -->|Yes| ModuleNotes
    NotesPattern -->|No| ReportsPattern{Filename matches:<br/>.*REPORT.*<br/>.*SUMMARY.*?}
    
    ReportsPattern -->|Yes| ModuleReports
    ReportsPattern -->|No| CheckCustom[Check Custom<br/>module_mappings]
    
    CheckCustom --> CustomMatch{Custom Pattern<br/>Match?}
    
    CustomMatch -->|Yes| ModuleCustom[Module: Custom]
    CustomMatch -->|No| DefaultModule[Module: Reports<br/>default fallback]
    
    ModuleLabs --> Route[Route to:<br/>Patients/Smith, John/Labs/]
    ModuleImaging --> Route2[Route to:<br/>Patients/Smith, John/Imaging/]
    ModuleNotes --> Route3[Route to:<br/>Patients/Smith, John/Notes/]
    ModuleReports --> Route4[Route to:<br/>Patients/Smith, John/Reports/]
    ModuleCustom --> Route5[Route to:<br/>Patients/Smith, John/Custom/]
    DefaultModule --> Route4
    
    Route --> End([File Classified])
    Route2 --> End
    Route3 --> End
    Route4 --> End
    Route5 --> End
    
    style ModuleLabs fill:#ADD8E6
    style ModuleImaging fill:#90EE90
    style ModuleNotes fill:#FFD700
    style ModuleReports fill:#FFB6C1
    style ModuleCustom fill:#DDA0DD
```

**Classification Priority:**
1. **Folder keywords** (fastest - checks parent folder name)
2. **Filename patterns** (regex matching on file name)
3. **Custom mappings** (user-defined patterns in config.yml)
4. **Default fallback** (Reports if no match)

---

## 4) Processing Pipeline (End-to-End Execution)

This flowchart shows the complete processing flow from API request to file organization.

```mermaid
flowchart TD
    Start([POST /api/process]) --> Auth{API Key<br/>Valid?}
    
    Auth -->|No| Unauthorized[HTTP 401<br/>Unauthorized]
    Auth -->|Yes| ValidateConfig[Config Validation<br/>JSON Schema]
    
    ValidateConfig --> RosterCheck{roster.path<br/>exists?}
    
    RosterCheck -->|No| Error400[HTTP 400<br/>roster.path required]
    RosterCheck -->|Yes| FileCheck{Source files<br/>exist?}
    
    FileCheck -->|No| Error404[HTTP 400<br/>source not found]
    FileCheck -->|Yes| ExtractZIP{Source is<br/>ZIP file?}
    
    ExtractZIP -->|Yes| SafeExtract[Safe ZIP Extraction<br/>prevent ZIP slip/symlinks]
    ExtractZIP -->|No| UseSource[Use source path directly]
    
    SafeExtract --> LoadConfig[Load Config YAML<br/>or from request body]
    UseSource --> LoadConfig
    
    LoadConfig --> Autodetect[Roster Autodetect<br/>detect last/first/dob]
    
    Autodetect --> BuildRoster[Build Patient Index]
    
    BuildRoster --> ScanFiles[Scan Source Files<br/>max_depth: 12]
    
    ScanFiles --> FileLoop{For Each<br/>File}
    
    FileLoop --> CheckExt{File Extension<br/>Allowed?}
    
    CheckExt -->|No| Skip[Skip - excluded extension]
    CheckExt -->|Yes| IdentityMatch[Identity Matching<br/>filename → patient]
    
    IdentityMatch --> Matched{Patient<br/>Found?}
    
    Matched -->|No| ToUnmapped[→ Unmapped/]
    Matched -->|Yes| ClassifyModule[Module Classification<br/>Labs/Imaging/Notes/Reports]
    
    ClassifyModule --> CheckDedup[Deduplication Check<br/>hash/size/module]
    
    CheckDedup --> IsDup{Is<br/>Duplicate?}
    
    IsDup -->|Yes| SkipDup[Action: DUP_*<br/>Skip file]
    IsDup -->|No| PHIRedact[PHI Redaction<br/>SSN, MRN, Account#]
    
    PHIRedact --> DryRun{Dry Run<br/>Mode?}
    
    DryRun -->|Yes| PlanOnly[Log to Plan<br/>No file copy]
    DryRun -->|No| CopyFile[Copy File to Gold<br/>Patients/Last, First DOB/Module/]
    
    PlanOnly --> LogEvent
    CopyFile --> LogEvent[Log to CSV + Warehouse<br/>fact_fileprocessing]
    ToUnmapped --> LogEvent
    SkipDup --> LogEvent
    Skip --> FileLoop
    
    LogEvent --> FileLoop
    
    FileLoop -->|Done| CalcStats[Calculate Statistics<br/>copied, unmapped, duped]
    
    CalcStats --> HighUnmapped{Unmapped Rate<br/>> 60%?}
    
    HighUnmapped -->|Yes + Dry Run| Warn409[HTTP 409 Conflict<br/>+ warning message]
    HighUnmapped -->|Yes + Real Run| Warn200[HTTP 200 OK<br/>+ warning field]
    HighUnmapped -->|No| Success200[HTTP 200 OK<br/>Success]
    
    Warn409 --> Cleanup
    Warn200 --> Cleanup
    Success200 --> Cleanup[Cleanup Temp Files<br/>extracted ZIPs, temp configs]
    
    Cleanup --> End([Response to Client])
    
    Unauthorized --> End2([Error Response])
    Error400 --> End2
    Error404 --> End2
    
    style Success200 fill:#90EE90
    style Warn200 fill:#FFD700
    style Warn409 fill:#FFB6C1
    style Unauthorized fill:#FFB6C1
    style Error400 fill:#FFB6C1
    style Error404 fill:#FFB6C1
```

**Pipeline Stages:**

| Stage | Purpose | On Failure |
|-------|---------|------------|
| **Authentication** | Verify API key (if enabled) | HTTP 401 |
| **Config Validation** | Check roster.path, file formats | HTTP 400 |
| **ZIP Extraction** | Safe extraction (prevent attacks) | HTTP 400 |
| **Autodetect** | Find patient columns automatically | Use defaults |
| **Identity Match** | Link files to patients | → Unmapped |
| **Classification** | Categorize to module | → Reports (default) |
| **Deduplication** | Skip duplicate files | Log as DUP_* |
| **PHI Redaction** | Remove sensitive data from logs | Always enforced |
| **Execution** | Copy files (or plan in dry-run) | Log errors |
| **Statistics** | Calculate unmapped rate | Warn if >60% |

---

## 5) Config Validation Flow (Quick Wins Feature)

This flowchart shows the new validation system that prevents silent failures.

```mermaid
flowchart TD
    Start([Incoming Request]) --> ParseJSON[Parse JSON Body]
    
    ParseJSON --> HasMapping{mapping field<br/>present?}
    
    HasMapping -->|No| ErrorNoConfig[HTTP 400<br/>Configuration is required]
    
    HasMapping -->|Yes| CheckRosterPath{roster.path<br/>defined?}
    
    CheckRosterPath -->|No| ErrorNoRoster[HTTP 400<br/>roster.path is required]
    
    CheckRosterPath -->|Yes| RosterExists{File<br/>exists?}
    
    RosterExists -->|No| ErrorNotFound[HTTP 400<br/>Roster file not found: path]
    
    RosterExists -->|Yes| CheckFormat{Valid format?<br/>.xlsx .csv .json}
    
    CheckFormat -->|No| ErrorBadFormat[HTTP 400<br/>Unsupported roster format]
    
    CheckFormat -->|Yes| TestRead[Try to Read File]
    
    TestRead --> Readable{File<br/>readable?}
    
    Readable -->|No| ErrorPermission[HTTP 400<br/>Cannot read roster file]
    
    Readable -->|Yes| ValidationPass[✓ Validation PASS]
    
    ValidationPass --> ProceedProcessing[Proceed to Processing Pipeline]
    
    ErrorNoConfig --> End([Error Response])
    ErrorNoRoster --> End
    ErrorNotFound --> End
    ErrorBadFormat --> End
    ErrorPermission --> End
    
    ProceedProcessing --> End2([Continue])
    
    style ValidationPass fill:#90EE90
    style ErrorNoConfig fill:#FFB6C1
    style ErrorNoRoster fill:#FFB6C1
    style ErrorNotFound fill:#FFB6C1
    style ErrorBadFormat fill:#FFB6C1
    style ErrorPermission fill:#FFB6C1
```

**What Validation Prevents:**
- ❌ **Silent failures** (roster.path = null)
- ❌ **File not found errors** mid-processing
- ❌ **Wrong file formats** causing crashes
- ❌ **Permission issues** discovered late

**What You Get:**
- ✅ **Immediate feedback** (HTTP 400 with clear message)
- ✅ **Actionable errors** (tells you exactly what's missing)
- ✅ **Early validation** (before any processing starts)

---

## Real-World Example: Complete Flow

**Scenario:** Process 10 patient files from Valley Neurology

```
Input: 10 PDFs in Export folder
Roster: patients.xlsx with 8 patients
```

**Flow:**

1. **API Request** → Validate API key ✓
2. **Config Validation** → roster.path exists ✓
3. **Autodetect** → Finds "Last Name", "First Name", "DOB" ✓
4. **Build Index** → 8 patients loaded into index
5. **Scan Files** → 10 PDFs found

**Per-File Processing:**

| File | Identity Match | Module | Dedup | Action |
|------|----------------|--------|-------|--------|
| Smith_lab.pdf | ✓ Smith, John | Labs | New | COPY_NEW |
| Johnson_xray.pdf | ✓ Johnson, Mary | Imaging | New | COPY_NEW |
| Smith_lab.pdf | ✓ Smith, John | Labs | DUP_HASH | Skip |
| Brown_mri.pdf | ✓ Brown, Patricia | Imaging | New | COPY_NEW |
| Wilson_note.pdf | ✗ No match | Notes | - | UNMAPPED |
| Davis_report.pdf | ✗ No match | Reports | - | UNMAPPED |
| Smith_lab_2.pdf | ✓ Smith, John | Labs | DUP_SIZE | Skip |
| Johnson_ct.pdf | ✓ Johnson, Mary | Imaging | New | COPY_NEW |
| Anderson_lab.pdf | ✓ Anderson, Lisa | Labs | New | COPY_NEW |
| Martinez_xray.pdf | ✗ No match | Imaging | - | UNMAPPED |

**Statistics:**
```
Processed: 10
Copied: 5 (50%)
Duplicates: 2 (20%)
Unmapped: 3 (30%)
```

**Unmapped Rate:** 30% (< 60% threshold) → ✓ No warning

**Result:**
```
Patients/
├── Anderson, Lisa 01-15-1982/
│   └── Labs/
│       └── Anderson_lab.pdf
├── Brown, Patricia 03-10-1985/
│   └── Imaging/
│       └── Brown_mri.pdf
├── Johnson, Mary 03-20-1975/
│   └── Imaging/
│       ├── Johnson_xray.pdf
│       └── Johnson_ct.pdf
└── Smith, John 05-15-1980/
    └── Labs/
        └── Smith_lab.pdf

Unmapped/
├── Wilson_note.pdf
├── Davis_report.pdf
└── Martinez_xray.pdf
```

---

## Summary: Algorithm Decision Points

| Algorithm | Key Decision | Fast Path | Slow Path |
|-----------|--------------|-----------|-----------|
| **Identity Match** | Exact vs Fuzzy | Exact match (hash lookup) | Fuzzy matching (iterative) |
| **Deduplication** | Hash vs Metadata | SHA256 comparison | Name+Size+Module check |
| **Classification** | Folder vs Filename | Folder keyword match | Regex pattern matching |
| **Validation** | File exists? | Direct path check | Try read + format validation |

**Performance Tips:**
- Use **exact matching** when possible (faster than fuzzy)
- Use **folder keywords** for classification (faster than regex)
- Use **metadata dedup** (`same_size_same_module`) instead of hashing for speed
- **Autodetect once** per roster, cache results

---

**Related Documents:**
- `BRONZE_SILVER_GOLD_ARCHITECTURE.md` - High-level architecture
- `QUICK_WINS_IMPLEMENTED.md` - Validation and autodetect features
- `COMPLETE_ARCHITECTURE_GUIDE.md` - Full technical guide
