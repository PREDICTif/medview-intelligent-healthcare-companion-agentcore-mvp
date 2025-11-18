-- Sample Appointments Data
-- 10 appointments for various patients with different providers and statuses

-- Note: Replace provider_id and facility_id with actual UUIDs from your database
-- These are placeholder UUIDs that should be updated based on your healthcare_providers and medical_facilities tables

INSERT INTO appointments (
    patient_id,
    provider_id,
    facility_id,
    appointment_type,
    appointment_reason,
    scheduled_date,
    scheduled_time,
    duration_minutes,
    appointment_status,
    scheduling_notes,
    created_by
) VALUES
-- Appointment 1: Sarah Johnson - Routine Checkup (Scheduled)
(
    (SELECT patient_id FROM patients WHERE medical_record_number = 'MRN-2024-001001'),
    (SELECT provider_id FROM healthcare_providers LIMIT 1 OFFSET 0),
    (SELECT facility_id FROM medical_facilities LIMIT 1),
    'Office Visit',
    'Annual physical examination and diabetes follow-up',
    '2025-01-15',
    '09:00:00',
    30,
    'Scheduled',
    'Patient prefers morning appointments',
    '12345678-1234-1234-1234-123456789012'
),

-- Appointment 2: Michael Smith - Follow-up (Confirmed)
(
    (SELECT patient_id FROM patients WHERE medical_record_number = 'MRN-2024-001002'),
    (SELECT provider_id FROM healthcare_providers LIMIT 1 OFFSET 1),
    (SELECT facility_id FROM medical_facilities LIMIT 1),
    'Follow-up',
    'Blood pressure check and medication review',
    '2025-01-16',
    '10:30:00',
    20,
    'Confirmed',
    'Reminder sent via email',
    '12345678-1234-1234-1234-123456789012'
),

-- Appointment 3: Jennifer Davis - Consultation (Scheduled)
(
    (SELECT patient_id FROM patients WHERE medical_record_number = 'MRN-2024-001003'),
    (SELECT provider_id FROM healthcare_providers LIMIT 1 OFFSET 0),
    (SELECT facility_id FROM medical_facilities LIMIT 1),
    'Consultation',
    'New patient consultation for diabetes management',
    '2025-01-17',
    '14:00:00',
    45,
    'Scheduled',
    'New patient - bring previous medical records',
    '12345678-1234-1234-1234-123456789012'
),

-- Appointment 4: Robert Wilson - Procedure (Confirmed)
(
    (SELECT patient_id FROM patients WHERE medical_record_number = 'MRN-2024-001004'),
    (SELECT provider_id FROM healthcare_providers LIMIT 1 OFFSET 2),
    (SELECT facility_id FROM medical_facilities LIMIT 1),
    'Procedure',
    'Diabetic retinopathy screening',
    '2025-01-18',
    '11:00:00',
    60,
    'Confirmed',
    'Fasting required - no food or drink after midnight',
    '12345678-1234-1234-1234-123456789012'
),

-- Appointment 5: Lisa Chen - Follow-up (Completed)
(
    (SELECT patient_id FROM patients WHERE medical_record_number = 'MRN-2024-001005'),
    (SELECT provider_id FROM healthcare_providers LIMIT 1 OFFSET 1),
    (SELECT facility_id FROM medical_facilities LIMIT 1),
    'Follow-up',
    'Post-procedure follow-up and wound check',
    '2025-01-10',
    '15:30:00',
    15,
    'Completed',
    'Patient arrived on time, no complications',
    '12345678-1234-1234-1234-123456789012'
),

-- Appointment 6: David Brown - Office Visit (Cancelled)
(
    (SELECT patient_id FROM patients WHERE medical_record_number = 'MRN-2024-001006'),
    (SELECT provider_id FROM healthcare_providers LIMIT 1 OFFSET 0),
    (SELECT facility_id FROM medical_facilities LIMIT 1),
    'Office Visit',
    'Routine diabetes check and A1C test',
    '2025-01-12',
    '13:00:00',
    30,
    'Cancelled',
    'Patient called to reschedule due to work conflict',
    '12345678-1234-1234-1234-123456789012'
),

-- Appointment 7: Amanda Garcia - Urgent Care (Checked In)
(
    (SELECT patient_id FROM patients WHERE medical_record_number = 'MRN-2024-001007'),
    (SELECT provider_id FROM healthcare_providers LIMIT 1 OFFSET 2),
    (SELECT facility_id FROM medical_facilities LIMIT 1),
    'Urgent Care',
    'Suspected hypoglycemia episode',
    CURRENT_DATE,
    '08:00:00',
    30,
    'Checked In',
    'Patient in waiting room',
    '12345678-1234-1234-1234-123456789012'
),

-- Appointment 8: Christopher Martinez - Telehealth (Scheduled)
(
    (SELECT patient_id FROM patients WHERE medical_record_number = 'MRN-2024-001008'),
    (SELECT provider_id FROM healthcare_providers LIMIT 1 OFFSET 1),
    NULL,
    'Telehealth',
    'Virtual consultation for medication adjustment',
    '2025-01-20',
    '16:00:00',
    20,
    'Scheduled',
    'Video call link sent to patient email',
    '12345678-1234-1234-1234-123456789012'
),

-- Appointment 9: Jessica Anderson - Lab Work (Confirmed)
(
    (SELECT patient_id FROM patients WHERE medical_record_number = 'MRN-2024-001009'),
    (SELECT provider_id FROM healthcare_providers LIMIT 1 OFFSET 0),
    (SELECT facility_id FROM medical_facilities LIMIT 1),
    'Lab Work',
    'Fasting blood glucose and lipid panel',
    '2025-01-19',
    '07:30:00',
    15,
    'Confirmed',
    'Fasting required - patient confirmed understanding',
    '12345678-1234-1234-1234-123456789012'
),

-- Appointment 10: Matthew Taylor - Follow-up (No Show)
(
    (SELECT patient_id FROM patients WHERE medical_record_number = 'MRN-2024-001010'),
    (SELECT provider_id FROM healthcare_providers LIMIT 1 OFFSET 1),
    (SELECT facility_id FROM medical_facilities LIMIT 1),
    'Follow-up',
    'Diabetes management follow-up',
    '2025-01-11',
    '10:00:00',
    30,
    'No Show',
    'Patient did not arrive, attempted to contact via phone',
    '12345678-1234-1234-1234-123456789012'
);

-- Verify the appointments were inserted
SELECT 
    a.appointment_id,
    p.first_name || ' ' || p.last_name as patient_name,
    p.medical_record_number,
    a.appointment_type,
    a.scheduled_date,
    a.scheduled_time,
    a.appointment_status
FROM appointments a
JOIN patients p ON a.patient_id = p.patient_id
ORDER BY a.scheduled_date, a.scheduled_time;
