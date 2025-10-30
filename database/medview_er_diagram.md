# Medview Connect - Entity Relationship Diagram

## Database Schema Overview
This ER diagram represents the HIPAA-compliant medical data model for the Medview Connect diabetes management system.

```mermaid
erDiagram
    %% Core Entities
    PATIENTS {
        uuid patient_id PK
        varchar medical_record_number UK
        varchar first_name
        varchar last_name
        varchar middle_name
        date date_of_birth
        varchar gender
        text ssn_encrypted
        varchar phone_primary
        varchar phone_secondary
        varchar email
        varchar address_line1
        varchar address_line2
        varchar city
        varchar state
        varchar zip_code
        varchar country
        varchar emergency_contact_name
        varchar emergency_contact_phone
        varchar emergency_contact_relationship
        varchar insurance_provider
        varchar insurance_policy_number
        varchar insurance_group_number
        boolean active
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    HEALTHCARE_PROVIDERS {
        uuid provider_id PK
        varchar npi_number UK
        varchar first_name
        varchar last_name
        varchar title
        varchar specialty
        varchar license_number
        varchar license_state
        varchar phone
        varchar email
        boolean active
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    MEDICAL_FACILITIES {
        uuid facility_id PK
        varchar facility_name
        varchar facility_type
        varchar address_line1
        varchar address_line2
        varchar city
        varchar state
        varchar zip_code
        varchar phone
        varchar fax
        boolean active
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
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
        text[] diagnosis_secondary
        varchar encounter_status
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    %% Clinical Data
    MEDICAL_CONDITIONS {
        uuid condition_id PK
        uuid patient_id FK
        uuid encounter_id FK
        text condition_name
        varchar icd10_code
        text condition_category
        varchar severity
        date onset_date
        date resolution_date
        varchar condition_status
        text notes
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    MEDICATIONS {
        uuid medication_id PK
        uuid patient_id FK
        uuid encounter_id FK
        uuid prescribed_by FK
        text medication_name
        text generic_name
        varchar ndc_code
        text dosage
        text frequency
        varchar route
        integer quantity_prescribed
        integer refills_remaining
        date prescription_date
        date start_date
        date end_date
        varchar medication_status
        text discontinuation_reason
        text instructions
        text notes
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
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
        text treatment_given
        text notes
        boolean verified
        boolean active
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
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
        text notes
        timestamp created_at
        timestamp updated_at
        uuid created_by
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
        text clinical_significance
        text notes
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    %% Procedures and Imaging
    MEDICAL_PROCEDURES {
        uuid procedure_id PK
        uuid patient_id FK
        uuid encounter_id FK
        uuid performed_by FK
        uuid facility_id FK
        text procedure_name
        varchar cpt_code
        varchar icd10_procedure_code
        text procedure_category
        timestamp scheduled_date
        timestamp start_time
        timestamp end_time
        integer duration_minutes
        text indication
        text technique_used
        text findings
        text complications
        text anesthesia_type
        uuid anesthesia_provider FK
        varchar procedure_status
        text outcome
        text recovery_notes
        text discharge_instructions
        boolean follow_up_required
        date follow_up_date
        boolean billable
        boolean insurance_authorized
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    IMAGING_STUDIES {
        uuid study_id PK
        uuid patient_id FK
        uuid encounter_id FK
        uuid ordered_by FK
        uuid performed_by FK
        uuid facility_id FK
        text study_type
        text body_part
        text study_description
        varchar study_instance_uid UK
        varchar accession_number
        varchar modality
        date order_date
        timestamp scheduled_date
        timestamp study_date
        text clinical_indication
        boolean contrast_used
        text contrast_type
        varchar contrast_amount
        text technique
        integer image_count
        text radiation_dose
        text preliminary_report
        text final_report
        text impression
        text recommendations
        uuid interpreting_radiologist FK
        timestamp report_date
        varchar study_status
        varchar report_status
        boolean critical_result
        boolean critical_result_notified
        timestamp critical_result_notification_time
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    CLINICAL_DOCUMENTS {
        uuid document_id PK
        uuid patient_id FK
        uuid encounter_id FK
        uuid created_by_provider FK
        text document_type
        text document_title
        text document_category
        text document_content
        text template_used
        boolean signed
        uuid signed_by FK
        timestamp signature_timestamp
        text electronic_signature
        varchar document_status
        integer version_number
        uuid parent_document_id FK
        varchar confidentiality_level
        text access_restrictions
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    APPOINTMENTS {
        uuid appointment_id PK
        uuid patient_id FK
        uuid provider_id FK
        uuid facility_id FK
        text appointment_type
        text appointment_reason
        date scheduled_date
        time scheduled_time
        integer duration_minutes
        varchar appointment_status
        timestamp check_in_time
        timestamp check_out_time
        text scheduling_notes
        text provider_notes
        boolean reminder_sent
        timestamp reminder_sent_date
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    %% Diabetes-Specific Tables
    BLOOD_GLUCOSE_READINGS {
        uuid reading_id PK
        uuid patient_id FK
        timestamp reading_date
        integer glucose_value
        decimal glucose_value_mmol
        varchar reading_type
        varchar meal_relation
        integer minutes_after_meal
        text measurement_method
        varchar device_serial_number
        varchar test_strip_lot
        decimal fasting_hours
        boolean exercise_within_2hrs
        varchar stress_level
        boolean illness_present
        boolean insulin_taken
        text insulin_type
        decimal insulin_units
        integer insulin_time_before_reading
        text notes
        text symptoms
        boolean control_solution_used
        boolean reading_flagged
        text flag_reason
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    CGM_READINGS {
        uuid cgm_reading_id PK
        uuid patient_id FK
        text device_type
        varchar device_serial
        varchar sensor_serial
        timestamp reading_timestamp
        integer glucose_value
        varchar glucose_trend
        varchar trend_arrow
        integer signal_strength
        boolean calibration_required
        boolean sensor_error
        boolean low_glucose_alert
        boolean high_glucose_alert
        boolean predicted_low_alert
        timestamp created_at
    }

    INSULIN_ADMINISTRATIONS {
        uuid administration_id PK
        uuid patient_id FK
        timestamp administration_date
        text insulin_type
        text insulin_brand
        decimal units_administered
        varchar injection_site
        text delivery_method
        varchar pump_serial
        boolean meal_bolus
        boolean correction_bolus
        boolean basal_insulin
        integer blood_glucose_before
        integer carbs_to_cover
        decimal correction_factor
        text notes
        boolean missed_dose
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    CARB_INTAKE {
        uuid intake_id PK
        uuid patient_id FK
        timestamp meal_date
        varchar meal_type
        integer total_carbs
        integer fiber_grams
        integer sugar_grams
        integer net_carbs
        text[] food_items
        text[] portion_sizes
        decimal carb_ratio
        decimal insulin_units_calculated
        decimal insulin_units_taken
        text carb_counting_method
        text notes
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    DIABETES_LAB_RESULTS {
        uuid diabetes_lab_id PK
        uuid patient_id FK
        uuid lab_result_id FK
        date test_date
        text test_type
        decimal hba1c_percentage
        integer hba1c_mmol_mol
        integer estimated_avg_glucose
        integer fasting_glucose
        integer random_glucose
        integer ogtt_baseline
        integer ogtt_2hour
        text urine_ketones
        decimal blood_ketones
        decimal microalbumin_mg
        decimal creatinine_mg
        decimal acr_ratio
        integer total_cholesterol
        integer ldl_cholesterol
        integer hdl_cholesterol
        integer triglycerides
        decimal hba1c_target
        text glucose_target_range
        text result_interpretation
        text action_required
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    DIABETES_COMPLICATIONS {
        uuid complication_id PK
        uuid patient_id FK
        text complication_type
        text complication_category
        varchar severity
        varchar stage
        date first_diagnosed_date
        date last_assessment_date
        varchar progression_status
        varchar eye_affected
        varchar visual_acuity_left
        varchar visual_acuity_right
        decimal egfr_value
        varchar ckd_stage
        text neuropathy_type
        text[] affected_areas
        text current_treatment
        text[] medications
        text monitoring_frequency
        date next_assessment_due
        text clinical_notes
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    DIABETES_EDUCATION {
        uuid education_id PK
        uuid patient_id FK
        uuid educator_id FK
        date session_date
        text session_type
        integer duration_minutes
        text[] topics_covered
        text[] materials_provided
        boolean carb_counting_taught
        boolean insulin_administration_taught
        boolean glucose_monitoring_taught
        boolean hypoglycemia_management_taught
        boolean sick_day_management_taught
        boolean exercise_guidelines_taught
        integer pre_session_knowledge_score
        integer post_session_knowledge_score
        boolean competency_demonstrated
        boolean follow_up_required
        date follow_up_date
        text educator_notes
        text patient_questions
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    %% Security and Audit Tables
    USERS {
        uuid user_id PK
        varchar username UK
        varchar email UK
        varchar first_name
        varchar last_name
        varchar employee_id
        varchar department
        varchar job_title
        text password_hash
        text password_salt
        timestamp last_password_change
        date password_expiry_date
        boolean active
        boolean locked
        integer failed_login_attempts
        timestamp last_login
        boolean hipaa_training_completed
        date hipaa_training_date
        date hipaa_training_expiry
        timestamp created_at
        timestamp updated_at
        uuid created_by
        uuid updated_by
    }

    ROLES {
        uuid role_id PK
        varchar role_name UK
        text role_description
        boolean can_read_patient_data
        boolean can_write_patient_data
        boolean can_delete_patient_data
        boolean can_access_sensitive_data
        boolean can_manage_users
        boolean can_view_audit_logs
        boolean active
        timestamp created_at
        timestamp updated_at
    }

    USER_ROLES {
        uuid user_role_id PK
        uuid user_id FK
        uuid role_id FK
        date assigned_date
        uuid assigned_by FK
        date expiry_date
        boolean active
        timestamp created_at
    }

    AUDIT_LOG {
        uuid audit_id PK
        uuid user_id FK
        varchar session_id
        inet ip_address
        text user_agent
        varchar action_type
        varchar table_name
        uuid record_id
        uuid patient_id
        jsonb old_values
        jsonb new_values
        varchar endpoint
        varchar http_method
        text request_body
        boolean success
        text error_message
        timestamp action_timestamp
        integer duration_ms
        text business_justification
        timestamp created_at
    }

    PATIENT_ACCESS_LOG {
        uuid access_id PK
        uuid patient_id FK
        uuid user_id FK
        varchar access_type
        text[] data_accessed
        text access_reason
        varchar session_id
        inet ip_address
        timestamp access_start
        timestamp access_end
        integer duration_seconds
        timestamp created_at
    }

    SECURITY_INCIDENTS {
        uuid incident_id PK
        text incident_type
        varchar severity
        text description
        integer patients_affected
        text[] data_types_affected
        timestamp incident_date
        timestamp discovered_date
        timestamp resolved_date
        boolean reported_to_authorities
        boolean patients_notified
        text mitigation_actions
        uuid investigated_by FK
        text root_cause
        varchar status
        timestamp created_at
        timestamp updated_at
        uuid created_by FK
        uuid updated_by FK
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
    
    PATIENTS ||--o{ MEDICAL_PROCEDURES : "undergoes"
    MEDICAL_ENCOUNTERS ||--o{ MEDICAL_PROCEDURES : "performed_during"
    HEALTHCARE_PROVIDERS ||--o{ MEDICAL_PROCEDURES : "performs"
    MEDICAL_FACILITIES ||--o{ MEDICAL_PROCEDURES : "hosts"
    HEALTHCARE_PROVIDERS ||--o{ MEDICAL_PROCEDURES : "anesthesia_provider"
    
    PATIENTS ||--o{ IMAGING_STUDIES : "undergoes"
    MEDICAL_ENCOUNTERS ||--o{ IMAGING_STUDIES : "ordered_during"
    HEALTHCARE_PROVIDERS ||--o{ IMAGING_STUDIES : "orders"
    HEALTHCARE_PROVIDERS ||--o{ IMAGING_STUDIES : "performs"
    HEALTHCARE_PROVIDERS ||--o{ IMAGING_STUDIES : "interprets"
    MEDICAL_FACILITIES ||--o{ IMAGING_STUDIES : "hosts"
    
    PATIENTS ||--o{ CLINICAL_DOCUMENTS : "documented"
    MEDICAL_ENCOUNTERS ||--o{ CLINICAL_DOCUMENTS : "documented_during"
    HEALTHCARE_PROVIDERS ||--o{ CLINICAL_DOCUMENTS : "creates"
    HEALTHCARE_PROVIDERS ||--o{ CLINICAL_DOCUMENTS : "signs"
    CLINICAL_DOCUMENTS ||--o{ CLINICAL_DOCUMENTS : "amends"
    
    PATIENTS ||--o{ APPOINTMENTS : "schedules"
    HEALTHCARE_PROVIDERS ||--o{ APPOINTMENTS : "sees"
    MEDICAL_FACILITIES ||--o{ APPOINTMENTS : "hosts"
    
    %% Diabetes-specific relationships
    PATIENTS ||--o{ BLOOD_GLUCOSE_READINGS : "monitors"
    PATIENTS ||--o{ CGM_READINGS : "monitors"
    PATIENTS ||--o{ INSULIN_ADMINISTRATIONS : "administers"
    PATIENTS ||--o{ CARB_INTAKE : "tracks"
    PATIENTS ||--o{ DIABETES_LAB_RESULTS : "tested"
    LAB_RESULTS ||--o{ DIABETES_LAB_RESULTS : "extends"
    PATIENTS ||--o{ DIABETES_COMPLICATIONS : "develops"
    PATIENTS ||--o{ DIABETES_EDUCATION : "receives"
    HEALTHCARE_PROVIDERS ||--o{ DIABETES_EDUCATION : "provides"
    
    %% Security relationships
    USERS ||--o{ USER_ROLES : "assigned"
    ROLES ||--o{ USER_ROLES : "grants"
    USERS ||--o{ USER_ROLES : "assigns"
    USERS ||--o{ AUDIT_LOG : "performs"
    PATIENTS ||--o{ AUDIT_LOG : "subject_of"
    PATIENTS ||--o{ PATIENT_ACCESS_LOG : "accessed"
    USERS ||--o{ PATIENT_ACCESS_LOG : "accesses"
    USERS ||--o{ SECURITY_INCIDENTS : "investigates"
    USERS ||--o{ SECURITY_INCIDENTS : "creates"
    USERS ||--o{ SECURITY_INCIDENTS : "updates"
```

## Key Features

### Core Medical Data
- **Patient Management**: Complete patient demographics, insurance, and contact information
- **Provider Network**: Healthcare providers with specialties and credentials
- **Encounters**: Medical visits with diagnoses and clinical information
- **Clinical Data**: Conditions, medications, allergies, vital signs, and lab results

### Diabetes-Specific Features
- **Glucose Monitoring**: Blood glucose readings and CGM data
- **Insulin Management**: Detailed insulin administration tracking
- **Carbohydrate Tracking**: Meal and carb intake monitoring
- **Specialized Labs**: HbA1c, ketones, and diabetes-specific test results
- **Complications**: Tracking of diabetic complications (retinopathy, nephropathy, etc.)
- **Education**: Patient education sessions and competency tracking

### HIPAA Compliance
- **User Management**: Role-based access control with detailed permissions
- **Audit Logging**: Comprehensive audit trail for all data access
- **Security Incidents**: Breach tracking and incident management
- **Patient Access Logs**: Detailed tracking of who accessed patient data

### Advanced Features
- **Procedures & Imaging**: Medical procedures and imaging studies with DICOM support
- **Clinical Documentation**: Electronic health records with digital signatures
- **Appointment Scheduling**: Complete appointment management system

This schema supports a comprehensive diabetes management platform with full HIPAA compliance and extensive clinical capabilities.