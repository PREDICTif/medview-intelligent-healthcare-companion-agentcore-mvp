# Medications Implementation

## Overview

This document describes the implementation of medication management functionality in the MedView Healthcare System.

## Components

### 1. Database Schema

**Table**: `medications` (defined in `database/schema/02_clinical_data.sql`)

Key fields:
- `medication_id` (UUID, primary key)
- `patient_id` (UUID, foreign key to patients)
- `medication_name` (brand name)
- `generic_name` (generic name)
- `ndc_code` (National Drug Code)
- `dosage`, `frequency`, `route`
- `prescription_date`, `start_date`, `end_date`
- `medication_status` (Active, Discontinued, Completed)
- `refills_remaining`
- `instructions`, `notes`

### 2. Sample Data

**File**: `database/data/03_medications_sample_data.sql`

Contains 10 sample medications including:
- Metformin (diabetes)
- Lisinopril (hypertension)
- Atorvastatin (cholesterol)
- Levothyroxine (hypothyroidism)
- Omeprazole (GERD)
- Albuterol (asthma)
- Sertraline (depression/anxiety)
- Gabapentin (neuropathic pain)
- Warfarin (atrial fibrillation)
- Amoxicillin (infection - completed)

### 3. Lambda Handler

**File**: `lambda/database-handler/index.py`

**New Function**: `get_patient_medications(patient_id)`
- Queries medications table for a specific patient
- Joins with healthcare_providers for prescriber information
- Orders by status (Active → Discontinued → Completed) and date
- Returns formatted medication list

**New Action**: `get_patient_medications`
- Endpoint: POST with `{"action": "get_patient_medications", "patient_id": "<uuid>"}`
- Returns: JSON with medications array

### 4. Agent Tool

**File**: `agent/patient_tools.py`

**Updated Tool**: `get_patient_medication_list(patient_identifier)`
- Takes patient ID or MRN as input
- Calls Lambda endpoint to retrieve medications
- Formats response with:
  - Active medications (with full details)
  - Discontinued medications (with reason)
  - Completed courses
- Includes safety warnings about verifying with patient

## Usage

### From Agent

```python
from patient_tools import get_patient_medication_list

# Get medications by MRN
result = get_patient_medication_list("MRN-2024-001001")

# Get medications by patient UUID
result = get_patient_medication_list("123e4567-e89b-12d3-a456-426614174000")
```

### From Lambda Directly

```python
import boto3
import json

lambda_client = boto3.client('lambda')

payload = {
    "action": "get_patient_medications",
    "patient_id": "123e4567-e89b-12d3-a456-426614174000"
}

response = lambda_client.invoke(
    FunctionName='your-lambda-function',
    Payload=json.dumps(payload)
)

result = json.loads(response['Payload'].read())
```

### Via API Gateway

```bash
curl -X POST https://your-api-gateway-url \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_patient_medications",
    "patient_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

## Testing

### Load Sample Data

```bash
# Connect to your database
psql -h your-db-host -U your-db-user -d medical_records

# Load sample medications
\i database/data/03_medications_sample_data.sql
```

### Test Lambda Endpoint

```bash
cd scripts
python test_medications.py --mrn MRN-2024-001001 -v
```

### Test Agent Tool

```bash
cd scripts
python test_medications.py --mrn MRN-2024-001001
```

## Deployment

### 1. Update Lambda Function

```bash
# Package and deploy Lambda
cd lambda/database-handler
zip -r function.zip .
aws lambda update-function-code \
  --function-name your-lambda-function \
  --zip-file fileb://function.zip
```

### 2. Update Agent

```bash
# Rebuild agent container
cd agent
docker build -t your-agent:latest .

# Or if using CDK
cd cdk
npx cdk deploy AgentCoreRuntime
```

### 3. Load Sample Data

```bash
# Run the medications sample data script
psql -h your-db-host -U your-db-user -d medical_records \
  -f database/data/03_medications_sample_data.sql
```

## Response Format

### Success Response

```json
{
  "status": "success",
  "message": "Found 3 medication(s)",
  "medications": [
    {
      "medication_id": "uuid",
      "patient_id": "uuid",
      "medication_name": "Metformin",
      "generic_name": "Metformin Hydrochloride",
      "ndc_code": "00093-7214-01",
      "dosage": "500mg",
      "frequency": "Twice daily with meals",
      "route": "Oral",
      "quantity_prescribed": 60,
      "refills_remaining": 3,
      "prescription_date": "2024-01-15",
      "start_date": "2024-01-15",
      "end_date": null,
      "medication_status": "Active",
      "discontinuation_reason": null,
      "instructions": "Take with food to reduce stomach upset...",
      "notes": "Patient tolerating well...",
      "prescribed_by_name": "Dr. John Smith"
    }
  ],
  "count": 3
}
```

### Error Response

```json
{
  "status": "error",
  "message": "Error retrieving medications: ...",
  "error_type": "Exception"
}
```

## Security Considerations

1. **Patient ID Validation**: Always validate patient_id is a valid UUID
2. **Authorization**: Ensure caller has permission to access patient data
3. **PHI Protection**: Medications are Protected Health Information (PHI)
4. **Audit Logging**: Log all medication access for compliance
5. **Encryption**: Data encrypted at rest and in transit

## Future Enhancements

1. **Medication Interactions**: Check for drug-drug interactions
2. **Allergy Checking**: Cross-reference with patient allergies
3. **Refill Management**: Track refill requests and approvals
4. **Medication Adherence**: Track patient compliance
5. **E-Prescribing**: Integration with pharmacy systems
6. **Medication History**: Track changes over time
7. **Formulary Checking**: Verify insurance coverage

## Troubleshooting

### No medications returned

- Check if sample data was loaded: `SELECT COUNT(*) FROM medications;`
- Verify patient_id exists: `SELECT patient_id FROM patients WHERE medical_record_number = 'MRN-2024-001001';`
- Check Lambda logs: `aws logs tail /aws/lambda/your-function --follow`

### Lambda timeout

- Increase Lambda timeout in CDK/CloudFormation
- Add database indexes on `patient_id`
- Optimize query performance

### Permission errors

- Verify Lambda has RDS Data API permissions
- Check security group allows Lambda → RDS connection
- Verify IAM role has necessary permissions

## Related Files

- Schema: `database/schema/02_clinical_data.sql`
- Sample Data: `database/data/03_medications_sample_data.sql`
- Lambda Handler: `lambda/database-handler/index.py`
- Agent Tool: `agent/patient_tools.py`
- Test Script: `scripts/test_medications.py`
