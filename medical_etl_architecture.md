# Medical ETL System — Complete Architecture (All-in-One)

## 1) System Context
```mermaid
flowchart LR
  subgraph External[External Actors]
    U[Clinics And Practices];
    Ops[Ops Engineers];
    Int[Integrations EHR DMS BI];
  end;

  subgraph S[Medical ETL System]
    API[REST API];
    CLI[CLI Orchestrator];
    Logs[Logs And Metrics];
    Out[Organized Patient Repos];
    Rep[Reports];
  end;

  U -->|Upload files or Provide mappings| S;
  Ops -->|Configure And Monitor| S;
  Int -->|Pull outputs And reports| S;
  S -->|Organized files And Reports| U;
  S -->|Webhooks And Downloads| U;
  S -->|Datasets And Logs| Int;
```

---

## 2) Container Architecture
```mermaid
flowchart TB
  CLI[CLI Orchestrator mainpy];
  API[Flask API apiserver py];
  Q[Job Queue Workers];

  subgraph Proc[Processing Containers]
    FE[File Extractor];
    MP[Mapping Processor];
    OCR[OCR Processor];
    PP[Patient Parser];
    SL[Smart Lookup Engine];
    DD[Duplicate Detector];
    FO[File Organizer];
    XL[Excel Manager];
    LG[ETL Logger];
  end;

  subgraph Stores[Data Stores]
    TMP[(Temp Storage)];
    OUT[(Patient Output Repos)];
    LOGS[(Logs And Metrics)];
    CFG[(Config And Secrets env)];
    OPT[(Optional SQL Or Blob Store)];
  end;

  CLI --> Q;
  API --> Q;
  Q --> FE --> TMP;
  FE --> MP;
  FE --> OCR;
  OCR --> PP --> SL;
  MP --> SL;
  SL --> DD --> FO --> OUT;
  FO --> XL --> OUT;
  LG <--> LOGS;
  CFG -.-> Proc;
  Proc --> OPT;
```

---

## 3) End-to-End Architecture Flow
```mermaid
flowchart TD
  subgraph Inputs[Input Sources]
    A1[Raw Files pdf tiff jpg xml json zip];
    A2[Mapping Files excel csv json];
    A3[Practice Metadata];
  end;

  subgraph Extraction[Extraction Layer]
    B1[Archive Extraction zip rar sevenz];
    B2[Recursive Discovery And Validation];
  end;

  subgraph Transform[Transformation Layer]
    C1[Mapping Normalize];
    C2[OCR Processor];
    C3[Patient Parser];
    C4[Duplicate Detector];
    C5[Smart Lookup Five Levels];
  end;

  subgraph Organize[Organization Layer]
    D1[File Organizer lastname firstname dob];
    D2[Folder Buckets medical images reports];
    D3[ETL Logger logs metrics audit];
  end;

  subgraph Outputs[Output Layer]
    E1[Patient Directories];
    E2[Excel And JSON Reports];
    E3[Run And Audit Logs];
  end;

  subgraph Integration[API And Integration]
    F1[Flask REST API];
    F2[Background Job Queue];
    F3[Result Download And Webhooks];
  end;

  subgraph Deploy[Deployment And Observability]
    G1[Docker Gunicorn Nginx];
    G2[Volumes temp out logs];
    G3[Metrics And Alerts];
  end;

  A1 --> B1 --> B2;
  A2 --> C1;
  B2 --> C2;
  C2 --> C3 --> C5;
  C1 --> C5;
  C5 --> C4 --> D1;
  D1 --> D2 --> D3;
  D3 --> E1;
  D3 --> E2;
  D3 --> E3;
  E1 --> F1;
  E2 --> F1;
  F1 --> F2 --> F3;
  F3 --> G1 --> G3;
```

---

## 4) Processing Pipeline (Swimlane)
```mermaid
sequenceDiagram
  participant CLI as CLI Or API;
  participant FE as FileExtractor;
  participant MP as MappingProcessor;
  participant OCR as OCRProcessor;
  participant PP as PatientParser;
  participant SL as SmartLookup;
  participant DD as DuplicateDetector;
  participant FO as FileOrganizer;
  participant LG as ETLLogger;

  CLI->>FE: Discover And extract recursively;
  FE-->>CLI: File list And temp paths;
  CLI->>MP: Load excel csv json mappings;
  CLI->>OCR: OCR text PDF to images to OCR;
  OCR-->>PP: Plain text;
  PP->>SL: Name DOB ID candidates;
  MP-->>SL: Normalized reference rows;
  SL->>DD: Identity And document key;
  DD-->>FO: Unique or keep decision;
  FO->>LG: Copy or skip And naming And category;
  LG-->>CLI: Summary And metrics And reports;
```

---

## 5) Five-Level Patient Identification
```mermaid
flowchart TD
  A[File] --> B[Mapping Hit];
  B -->|Yes| H[Map To Patient];
  B -->|No| C[Filename Pattern];
  C -->|Yes| H;
  C -->|No| D[Folder Cues];
  D -->|Yes| H;
  D -->|No| E[OCR Or Text Match];
  E -->|Yes| H;
  E -->|No| F[Heuristics Low Confidence];
  H --> G[Normalize Name Dob Id] --> I[Cross Check And Threshold];
  F --> I;
  I -->|gte threshold| P[Assign Patient];
  I -->|lt threshold| Q[Unresolved Send To Review];
```

---

## 6) Bronze to Silver to Gold Data Flow
```mermaid
flowchart LR
  BZ[Bronze Raw Intake] --> SV[Silver Normalized Parsed] --> GD[Gold Curated Output];

  subgraph Bronze[Bronze Layer]
    R1[Raw Files pdf tiff jpg json zip];
    R2[Mappings excel csv json];
    R3[Intake Logs];
  end;

  subgraph Silver[Silver Layer]
    S1[Extracted Text];
    S2[Normalized Mapping Table];
    S3[Parsed Entities name dob id];
    S4[Linkage file to patient];
    S5[Dedup Decisions];
  end;

  subgraph Gold[Gold Layer]
    G1[Patient Folders lastname firstname dob];
    G2[Module Buckets];
    G3[Run Reports excel json];
    G4[Audit Trails];
  end;

  R1 --> S1;
  R2 --> S2;
  S1 --> S3 --> S4 --> S5 --> G1;
  S2 --> S4;
  G1 --> G3;
  S5 --> G4;
```

---

## 7) Deployment And Runtime Topology
```mermaid
flowchart TB
  subgraph Client[User And Client]
    C1[CLI];
    C2[Postman Or UI];
  end;

  subgraph AppTier[Application Tier]
    A1[Gunicorn Workers];
    A2[Flask API];
    A3[Background Workers];
  end;

  subgraph Infra[Infrastructure]
    I1[Nginx SSL];
    I2[Load Balancer];
    I3[Volumes temp out logs];
    I4[Tesseract And Poppler];
    I5[Optional SQL Or Blob];
    I6[Metrics And Logging];
  end;

  C1 --> A2;
  C2 --> I1 --> I2 --> A1 --> A2 --> A3;
  A3 --> I3;
  A3 --> I4;
  A3 --> I5;
  A2 --> I6;
```
