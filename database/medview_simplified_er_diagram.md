# Medview Connect - Simplified ER Diagram

## Core Medical Data Model
This simplified ER diagram shows the essential tables for patient management and clinical data.

```mermaid
erDiagram
    %% Core Tables
    PATIENTS {
        uuid patient_id PK
        varchar medical_record_number UK
        varchar first_name
        varchar last_name
        varchar middle_name
        date date_of_birth
        varchar gender
        varchar phone_primary
        varchar email
        varchar address_line1
        varchar city
        varchar state
        varchar zip_code
        varchar insurance_provider
        boolean active
        timestamp created_at
        timestamp updated_at
    }

    HEALTHCARE_PROVIDERS {
        uuid provider_id PK
        varchar npi_number UK
        varchar first_name
        varchar last_name
        varchar title
        varchar specialty
        varchar license_number
        varchar phone
        varchar email
        boolean active
        timestamp created_at
        timestamp updated_at
    }

    MEDICAL_FACILITIES {
        uuid facility_id PK
        varchar facility_name
        varchar facility_type
        varchar address_line1
        varchar city
        varchar state
        varchar phone
        boolean active
        timestamp created_at
        timestamp updated_at
    }

    MEDICAL_ENCOUNTERS {
        uuid encounter_id PK
        uuid patient_id FK
        uuid provider_id FK
        uuid facility_id FK
        varchar encounter_type
        timestamp encounter_date
        timestamp discharge_date
        text chief_complaint
        text diagnosis_primary
        varchar encounter_status
        timestamp created_at
        timestamp updated_at
    }

    %% Clinical Data Tables
    MEDICAL_CONDITIONS {
        uuid condition_id PK
        uuid patient_id FK
        uuid encounter_id FK
        text condition_name
        varchar icd10_code
        varchar severity
        date onset_date
        date resolution_date
        varchar condition_status
        text notes
        timestamp created_at
        timestamp updated_at
    }

    MEDICATIONS {
        uuid medication_id PK
        uuid patient_id FK
        uuid encounter_id FK
        uuid prescribed_by FK
        text medication_name
        text generic_name
        text dosage
        text frequency
        varchar route
        date prescription_date
        date start_date
        date end_date
        varchar medication_status
        text instructions
        timestamp created_at
        timestamp updated_at
    }

    ALLERGIES {
        uuid allergy_id PK
        uuid patient_id FK
        text allergen
        varchar allergy_type
        text reaction_type
        varchar severity
        date onset_date
        text symptoms
        boolean active
        timestamp created_at
        timestamp updated_at
    }

    VITAL_SIGNS {
        uuid vital_sign_id PK
        uuid patient_id FK
        uuid encounter_id FK
        timestamp measurement_date
        uuid measured_by FK
        integer systolic_bp
        integer diastolic_bp
        integer heart_rate
        integer respiratory_rate
        decimal temperature
        integer oxygen_saturation
        decimal weight
        decimal height
        decimal bmi
        integer pain_scale
        timestamp created_at
        timestamp updated_at
    }

    LAB_RESULTS {
        uuid lab_result_id PK
        uuid patient_id FK
        uuid encounter_id FK
        uuid ordered_by FK
        text test_name
        varchar test_code
        text test_category
        text result_value
        varchar result_unit
        text reference_range
        varchar abnormal_flag
        date order_date
        timestamp collection_date
        timestamp result_date
        varchar result_status
        text notes
        timestamp created_at
        timestamp updated_at
    }

    %% Key Diabetes Tables
    BLOOD_GLUCOSE_READINGS {
        uuid reading_id PK
        uuid patient_id FK
        timestamp reading_date
        integer glucose_value
        varchar reading_type
        varchar meal_relation
        text measurement_method
        boolean insulin_taken
        text insulin_type
        decimal insulin_units
        text notes
        timestamp created_at
        timestamp updated_at
    }

    DIABETES_LAB_RESULTS {
        uuid diabetes_lab_id PK
        uuid patient_id FK
        uuid lab_result_id FK
        date test_date
        text test_type
        decimal hba1c_percentage
        integer estimated_avg_glucose
        integer fasting_glucose
        text result_interpretation
        timestamp created_at
        timestamp updated_at
    }

    %% Relationships
    PATIENTS ||--o{ MEDICAL_ENCOUNTERS : "has"
    HEALTHCARE_PROVIDERS ||--o{ MEDICAL_ENCOUNTERS : "provides"
    MEDICAL_FACILITIES ||--o{ MEDICAL_ENCOUNTERS : "hosts"
    
    PATIENTS ||--o{ MEDICAL_CONDITIONS : "has"
    MEDICAL_ENCOUNTERS ||--o{ MEDICAL_CONDITIONS : "documents"
    
    PATIENTS ||--o{ MEDICATIONS : "prescribed"
    MEDICAL_ENCOUNTERS ||--o{ MEDICATIONS : "prescribed_during"
    HEALTHCARE_PROVIDERS ||--o{ MEDICATIONS : "prescribes"
    
    PATIENTS ||--o{ ALLERGIES : "has"
    
    PATIENTS ||--o{ VITAL_SIGNS : "measured"
    MEDICAL_ENCOUNTERS ||--o{ VITAL_SIGNS : "recorded_during"
    HEALTHCARE_PROVIDERS ||--o{ VITAL_SIGNS : "measures"
    
    PATIENTS ||--o{ LAB_RESULTS : "tested"
    MEDICAL_ENCOUNTERS ||--o{ LAB_RESULTS : "ordered_during"
    HEALTHCARE_PROVIDERS ||--o{ LAB_RESULTS : "orders"
    
    PATIENTS ||--o{ BLOOD_GLUCOSE_READINGS : "monitors"
    
    PATIENTS ||--o{ DIABETES_LAB_RESULTS : "tested"
    LAB_RESULTS ||--o{ DIABETES_LAB_RESULTS : "extends"
```

## Key Tables Overview

### Core Tables (4)
- **PATIENTS**: Patient demographics and contact information
- **HEALTHCARE_PROVIDERS**: Doctors, nurses, and medical staff
- **MEDICAL_FACILITIES**: Hospitals, clinics, and medical centers
- **MEDICAL_ENCOUNTERS**: Patient visits and appointments

### Clinical Data Tables (5)
- **MEDICAL_CONDITIONS**: Diagnoses and medical conditions
- **MEDICATIONS**: Prescriptions and medication history
- **ALLERGIES**: Patient allergies and adverse reactions
- **VITAL_SIGNS**: Blood pressure, heart rate, weight, etc.
- **LAB_RESULTS**: Laboratory test results

### Essential Diabetes Tables (2)
- **BLOOD_GLUCOSE_READINGS**: Blood sugar monitoring
- **DIABETES_LAB_RESULTS**: HbA1c and diabetes-specific lab tests

## Key Relationships
- All clinical data is linked to **PATIENTS**
- **MEDICAL_ENCOUNTERS** connect patients with providers and facilities
- Clinical data can be associated with specific encounters
- Diabetes-specific tables extend the core clinical data model

This simplified model focuses on the essential patient care and clinical data management capabilities.