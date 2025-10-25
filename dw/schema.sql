-- Medical ETL Data Warehouse Schema
-- Enterprise-Lite MVP Version

-- Dimension: Patient Master
CREATE TABLE IF NOT EXISTS DIM_Patient (
    PatientKey SERIAL PRIMARY KEY,
    PatientID VARCHAR(50) UNIQUE NOT NULL,
    LastName VARCHAR(100),
    FirstName VARCHAR(100),
    MiddleName VARCHAR(100),
    DateOfBirth DATE,
    CreatedUTC TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    UpdatedUTC TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    IsActive BOOLEAN DEFAULT TRUE
);

-- Reference: Mapping Configuration (versioned configs)
CREATE TABLE IF NOT EXISTS REF_MappingConfiguration (
    ConfigKey SERIAL PRIMARY KEY,
    PracticeID VARCHAR(100) NOT NULL,
    ConfigName VARCHAR(200),
    ConfigurationValue TEXT,
    ConfigHash VARCHAR(64),
    CreatedUTC TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    IsActive BOOLEAN DEFAULT TRUE
);

-- Reference: File Manifest (per session integrity)
CREATE TABLE IF NOT EXISTS REF_FileManifest (
    ManifestKey SERIAL PRIMARY KEY,
    SessionKey VARCHAR(64) NOT NULL,
    FilePath TEXT NOT NULL,
    ContentHash VARCHAR(64),
    SizeBytes BIGINT,
    CreatedUTC TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC')
);

-- Fact: File Processing Events (append-only audit trail)
CREATE TABLE IF NOT EXISTS FACT_FileProcessing (
    FileProcessingKey SERIAL PRIMARY KEY,
    RunID VARCHAR(64) NOT NULL,
    SessionKey VARCHAR(64) NOT NULL,
    EventTimeUTC TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    PatientKey INT REFERENCES DIM_Patient(PatientKey),
    SourcePath TEXT,
    DestinationPath TEXT,
    Action VARCHAR(50) NOT NULL,
    Reason TEXT,
    Module VARCHAR(50),
    FileExtension VARCHAR(20),
    FileSizeBytes BIGINT,
    ProvenanceID VARCHAR(64),
    ConfigHash VARCHAR(64),
    ContentHash VARCHAR(64),
    OcrConfidence DECIMAL(5,2),
    RouterDecision VARCHAR(50),
    NameParsingSource VARCHAR(20),
    NestedLevel INT,
    InvokedByUser VARCHAR(100),
    HostPlatform VARCHAR(100),
    PythonVersion VARCHAR(20),
    ScriptVersion VARCHAR(20),
    Mode VARCHAR(20),
    PracticeID VARCHAR(100)
);

-- Audit: HIPAA Compliance Log (tamper-evident with integrity chain)
CREATE TABLE IF NOT EXISTS AUDIT_HIPAALog (
    AuditKey SERIAL PRIMARY KEY,
    EventTimeUTC TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    EventType VARCHAR(50) NOT NULL,
    UserID VARCHAR(100),
    Action VARCHAR(100) NOT NULL,
    ResourceType VARCHAR(50),
    ResourceID VARCHAR(200),
    BeforeValue TEXT,
    AfterValue TEXT,
    IPAddress VARCHAR(45),
    UserAgent TEXT,
    IntegrityChainHash VARCHAR(64)
);

-- Views for SSIS Export
CREATE OR REPLACE VIEW VW_SSISPatientExport AS
SELECT 
    p.PatientKey,
    p.PatientID,
    p.LastName,
    p.FirstName,
    p.MiddleName,
    p.DateOfBirth,
    COUNT(DISTINCT f.FileProcessingKey) as TotalFiles,
    COUNT(DISTINCT CASE WHEN f.Action = 'COPY' THEN f.FileProcessingKey END) as CopiedFiles,
    COUNT(DISTINCT CASE WHEN f.Action LIKE 'SKIP%' THEN f.FileProcessingKey END) as SkippedFiles,
    MAX(f.EventTimeUTC) as LastProcessedUTC
FROM DIM_Patient p
LEFT JOIN FACT_FileProcessing f ON p.PatientKey = f.PatientKey
WHERE p.IsActive = TRUE
GROUP BY p.PatientKey, p.PatientID, p.LastName, p.FirstName, p.MiddleName, p.DateOfBirth;

CREATE OR REPLACE VIEW VW_SSISAuditExport AS
SELECT 
    f.RunID,
    f.SessionKey,
    f.EventTimeUTC,
    p.PatientID,
    p.LastName,
    p.FirstName,
    f.Action,
    f.Reason,
    f.Module,
    f.SourcePath,
    f.DestinationPath,
    f.FileSizeBytes,
    f.ContentHash,
    f.ProvenanceID,
    f.ConfigHash,
    f.InvokedByUser,
    f.PracticeID
FROM FACT_FileProcessing f
LEFT JOIN DIM_Patient p ON f.PatientKey = p.PatientKey
ORDER BY f.EventTimeUTC DESC;

-- Stored Procedure: Start Session
CREATE OR REPLACE FUNCTION SP_StartSession(
    p_run_id VARCHAR(64),
    p_practice_id VARCHAR(100),
    p_invoked_by VARCHAR(100)
) RETURNS VARCHAR(64) AS $$
DECLARE
    v_session_key VARCHAR(64);
BEGIN
    v_session_key := MD5(p_run_id || NOW()::TEXT);
    
    INSERT INTO AUDIT_HIPAALog (EventType, UserID, Action, ResourceType, ResourceID)
    VALUES ('SESSION_START', p_invoked_by, 'START_ETL_RUN', 'SESSION', v_session_key);
    
    RETURN v_session_key;
END;
$$ LANGUAGE plpgsql;

-- Stored Procedure: Upsert Patient
CREATE OR REPLACE FUNCTION SP_UpsertPatient(
    p_patient_id VARCHAR(50),
    p_last_name VARCHAR(100),
    p_first_name VARCHAR(100),
    p_middle_name VARCHAR(100),
    p_dob DATE
) RETURNS INT AS $$
DECLARE
    v_patient_key INT;
BEGIN
    INSERT INTO DIM_Patient (PatientID, LastName, FirstName, MiddleName, DateOfBirth)
    VALUES (p_patient_id, p_last_name, p_first_name, p_middle_name, p_dob)
    ON CONFLICT (PatientID) 
    DO UPDATE SET 
        LastName = EXCLUDED.LastName,
        FirstName = EXCLUDED.FirstName,
        MiddleName = EXCLUDED.MiddleName,
        DateOfBirth = EXCLUDED.DateOfBirth,
        UpdatedUTC = NOW() AT TIME ZONE 'UTC'
    RETURNING PatientKey INTO v_patient_key;
    
    RETURN v_patient_key;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for REF_FileManifest
CREATE INDEX IF NOT EXISTS idx_manifest_session ON REF_FileManifest(SessionKey);
CREATE INDEX IF NOT EXISTS idx_manifest_hash ON REF_FileManifest(ContentHash);

-- Create indexes for FACT_FileProcessing  
CREATE INDEX IF NOT EXISTS idx_fp_run ON FACT_FileProcessing(RunID);
CREATE INDEX IF NOT EXISTS idx_fp_session ON FACT_FileProcessing(SessionKey);
CREATE INDEX IF NOT EXISTS idx_fp_patient ON FACT_FileProcessing(PatientKey);
CREATE INDEX IF NOT EXISTS idx_fp_action ON FACT_FileProcessing(Action);
CREATE INDEX IF NOT EXISTS idx_fp_event_time ON FACT_FileProcessing(EventTimeUTC);

-- Create indexes for AUDIT_HIPAALog
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON AUDIT_HIPAALog(EventType);
CREATE INDEX IF NOT EXISTS idx_audit_user ON AUDIT_HIPAALog(UserID);
CREATE INDEX IF NOT EXISTS idx_audit_event_time ON AUDIT_HIPAALog(EventTimeUTC);
