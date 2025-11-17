-- Sample Medication Data
-- 10 sample medication records for testing
-- Created: 2024

-- Note: This script assumes patients and providers exist from 01_core_sample_data.sql
-- Patient IDs will be retrieved from existing patients table
-- Provider IDs will be retrieved from existing healthcare_providers table

-- Insert 10 sample medications for various patients
-- First, get a provider ID to use for all prescriptions
DO $$
DECLARE
    v_provider_id UUID;
BEGIN
    -- Get the first provider ID
    SELECT provider_id INTO v_provider_id FROM healthcare_providers LIMIT 1;
    
    -- If no provider exists, create a default one
    IF v_provider_id IS NULL THEN
        INSERT INTO healthcare_providers (
            first_name, last_name, specialty, npi_number, 
            phone, email, created_by
        ) VALUES (
            'John', 'Smith', 'Internal Medicine', '1234567890',
            '(206) 555-0001', 'dr.smith@hospital.com',
            '12345678-1234-1234-1234-123456789012'
        ) RETURNING provider_id INTO v_provider_id;
    END IF;
    
    -- Now insert medications
    INSERT INTO medications (
        patient_id,
        prescribed_by,
        medication_name,
        generic_name,
        ndc_code,
        dosage,
        frequency,
        route,
        quantity_prescribed,
        refills_remaining,
        prescription_date,
        start_date,
        end_date,
        medication_status,
        instructions,
        notes,
        created_by
    )
    SELECT 
        p.patient_id,
        v_provider_id,
        med.medication_name,
        med.generic_name,
        med.ndc_code,
        med.dosage,
        med.frequency,
        med.route,
        med.quantity_prescribed,
        med.refills_remaining,
        med.prescription_date,
        med.start_date,
        med.end_date,
        med.medication_status,
        med.instructions,
        med.notes,
        '12345678-1234-1234-1234-123456789012'::UUID
    FROM (
        -- Medication 1: Metformin for diabetes
    SELECT 
        'MRN-2024-001001' as mrn,
        'Metformin' as medication_name,
        'Metformin Hydrochloride' as generic_name,
        '00093-7214-01' as ndc_code,
        '500mg' as dosage,
        'Twice daily with meals' as frequency,
        'Oral' as route,
        60 as quantity_prescribed,
        3 as refills_remaining,
        '2024-01-15'::DATE as prescription_date,
        '2024-01-15'::DATE as start_date,
        NULL::DATE as end_date,
        'Active' as medication_status,
        'Take with food to reduce stomach upset. Monitor blood sugar levels regularly.' as instructions,
        'Patient tolerating well, no adverse effects reported' as notes
    
    UNION ALL
    
    -- Medication 2: Lisinopril for hypertension
    SELECT 
        'MRN-2024-001002',
        'Lisinopril',
        'Lisinopril',
        '68180-0513-01',
        '10mg',
        'Once daily in the morning',
        'Oral',
        30,
        5,
        '2024-02-01'::DATE,
        '2024-02-01'::DATE,
        NULL::DATE,
        'Active',
        'Take at the same time each day. May cause dizziness when standing up quickly.',
        'Blood pressure well controlled on current dose'
    
    UNION ALL
    
    -- Medication 3: Atorvastatin for high cholesterol
    SELECT 
        'MRN-2024-001003',
        'Lipitor',
        'Atorvastatin Calcium',
        '00071-0155-23',
        '20mg',
        'Once daily at bedtime',
        'Oral',
        30,
        6,
        '2024-01-20'::DATE,
        '2024-01-20'::DATE,
        NULL::DATE,
        'Active',
        'Take in the evening. Avoid grapefruit juice. Report any muscle pain immediately.',
        'LDL cholesterol decreased by 30% since starting medication'
    
    UNION ALL
    
    -- Medication 4: Levothyroxine for hypothyroidism
    SELECT 
        'MRN-2024-001004',
        'Synthroid',
        'Levothyroxine Sodium',
        '00074-4341-13',
        '75mcg',
        'Once daily on empty stomach',
        'Oral',
        30,
        11,
        '2023-12-01'::DATE,
        '2023-12-01'::DATE,
        NULL::DATE,
        'Active',
        'Take 30-60 minutes before breakfast. Do not take with calcium or iron supplements.',
        'TSH levels normalized, patient reports improved energy'
    
    UNION ALL
    
    -- Medication 5: Omeprazole for GERD
    SELECT 
        'MRN-2024-001005',
        'Prilosec',
        'Omeprazole',
        '00093-5301-56',
        '20mg',
        'Once daily before breakfast',
        'Oral',
        30,
        2,
        '2024-03-01'::DATE,
        '2024-03-01'::DATE,
        '2024-06-01'::DATE,
        'Active',
        'Take 30 minutes before first meal of the day. Swallow capsule whole.',
        'Symptoms significantly improved, plan to reassess after 3 months'
    
    UNION ALL
    
    -- Medication 6: Albuterol inhaler for asthma
    SELECT 
        'MRN-2024-001006',
        'ProAir HFA',
        'Albuterol Sulfate',
        '59310-0579-18',
        '90mcg/actuation',
        'Two puffs every 4-6 hours as needed',
        'Inhalation',
        1,
        3,
        '2024-02-15'::DATE,
        '2024-02-15'::DATE,
        NULL::DATE,
        'Active',
        'Shake well before use. Rinse mouth after use. Use spacer if available.',
        'Patient using 2-3 times per week, asthma well controlled'
    
    UNION ALL
    
    -- Medication 7: Sertraline for depression/anxiety
    SELECT 
        'MRN-2024-001007',
        'Zoloft',
        'Sertraline Hydrochloride',
        '00049-4960-30',
        '50mg',
        'Once daily in the morning',
        'Oral',
        30,
        5,
        '2024-01-10'::DATE,
        '2024-01-10'::DATE,
        NULL::DATE,
        'Active',
        'May take with or without food. May cause drowsiness initially. Do not stop abruptly.',
        'Patient reports improved mood and reduced anxiety after 6 weeks'
    
    UNION ALL
    
    -- Medication 8: Gabapentin for neuropathic pain
    SELECT 
        'MRN-2024-001008',
        'Neurontin',
        'Gabapentin',
        '00071-0805-24',
        '300mg',
        'Three times daily',
        'Oral',
        90,
        2,
        '2024-02-20'::DATE,
        '2024-02-20'::DATE,
        NULL::DATE,
        'Active',
        'Take with food. May cause dizziness. Do not drive until you know how this affects you.',
        'Pain reduced from 8/10 to 4/10, tolerating medication well'
    
    UNION ALL
    
    -- Medication 9: Warfarin for atrial fibrillation
    SELECT 
        'MRN-2024-001009',
        'Coumadin',
        'Warfarin Sodium',
        '00056-0169-70',
        '5mg',
        'Once daily at the same time',
        'Oral',
        30,
        3,
        '2024-01-05'::DATE,
        '2024-01-05'::DATE,
        NULL::DATE,
        'Active',
        'Take at the same time each day. Avoid foods high in vitamin K. Regular INR monitoring required.',
        'INR therapeutic at 2.5, patient compliant with monitoring schedule'
    
    UNION ALL
    
    -- Medication 10: Amoxicillin for infection (completed course)
    SELECT 
        'MRN-2024-001010',
        'Amoxicillin',
        'Amoxicillin',
        '00093-4155-73',
        '500mg',
        'Three times daily',
        'Oral',
        21,
        0,
        '2024-03-10'::DATE,
        '2024-03-10'::DATE,
        '2024-03-17'::DATE,
        'Completed',
        'Take with or without food. Complete entire course even if feeling better.',
        '7-day course for bacterial sinusitis, symptoms resolved'
    ) med
    JOIN patients p ON p.medical_record_number = med.mrn;
    
    RAISE NOTICE 'Inserted % medication records', (SELECT COUNT(*) FROM medications WHERE created_by = '12345678-1234-1234-1234-123456789012');
END $$;

-- Verify the insert
SELECT 
    m.medication_name,
    m.dosage,
    m.frequency,
    m.medication_status,
    p.first_name || ' ' || p.last_name as patient_name,
    p.medical_record_number as mrn
FROM medications m
JOIN patients p ON m.patient_id = p.patient_id
ORDER BY m.created_at DESC
LIMIT 10;
