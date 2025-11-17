# Testing Medications with the Agent

## Quick Start

### Option 1: Single Query Test

```bash
cd scripts
python test_agent_medications.py --query "Show me medications for patient MRN-2024-001001"
```

### Option 2: Interactive Mode

```bash
cd scripts
python test_agent_medications.py --interactive
```

Then try queries like:
- "Show me the medication list for patient MRN-2024-001001"
- "What medications is Sarah Johnson taking?"
- "Is patient MRN-2024-001001 on Metformin?"

### Option 3: Run Test Scenarios

```bash
cd scripts
python test_agent_medications.py
```

This runs 3 pre-defined test scenarios automatically.

## What the Agent Does

When you ask about medications, the agent:

1. **Understands the request** - Recognizes you're asking about medications
2. **Calls the tool** - Uses `get_patient_medication_list(patient_identifier)`
3. **Retrieves data** - Queries the medications table via Lambda
4. **Formats response** - Presents the information in a clear, medical context

## Example Interaction

```
👤 User: Show me the medication list for patient MRN-2024-001001

🤖 Agent: [Calls get_patient_medication_list tool]

**Current Medication List for Patient MRN-2024-001001 (Sarah Johnson):**

**Active Medications:**
- **Metformin 500mg** - Prescribed for diabetes management
  - Take twice daily with meals
  - Oral administration
  - 3 refills remaining
  - Prescribed on January 15, 2024
  - Patient is tolerating well with no reported side effects
  - Important to take with food to minimize stomach upset
  - Regular blood sugar monitoring recommended

The patient is currently on a standard diabetes management regimen with Metformin...
```

## Testing in the Frontend

Once the agent is deployed to AgentCore, you can test it in the web frontend:

1. **Open the frontend** - Navigate to your CloudFront URL
2. **Sign in** - Use your Cognito credentials
3. **Start a conversation** - Type in the chat:
   - "Show me medications for patient MRN-2024-001001"
   - "What medications is Sarah Johnson taking?"
   - "Is this patient on any diabetes medications?"

## Available Test Patients

The sample data includes medications for:
- **MRN-2024-001001** - Sarah Johnson (Metformin for diabetes)
- **MRN-2024-001002** - Michael Smith (Lisinopril for hypertension)
- **MRN-2024-001003** - Jennifer Davis (Atorvastatin for cholesterol)
- **MRN-2024-001004** - Robert Wilson (Levothyroxine for hypothyroidism)
- **MRN-2024-001005** - Lisa Chen (Omeprazole for GERD)
- **MRN-2024-001006** - David Brown (Albuterol for asthma)
- **MRN-2024-001007** - Amanda Garcia (Sertraline for depression/anxiety)
- **MRN-2024-001008** - Christopher Martinez (Gabapentin for neuropathic pain)
- **MRN-2024-001009** - Jessica Anderson (Warfarin for atrial fibrillation)
- **MRN-2024-001010** - Matthew Taylor (Amoxicillin - completed course)

## Troubleshooting

### "No medications found"

Check if sample data was loaded:
```bash
psql -h your-db-host -U your-db-user -d medical_records \
  -c "SELECT COUNT(*) FROM medications;"
```

If zero, load the sample data:
```bash
psql -h your-db-host -U your-db-user -d medical_records \
  -f database/data/03_medications_sample_data.sql
```

### "Lambda function not configured"

Make sure the Lambda URL is set in SSM:
```bash
aws ssm get-parameter --name /app/medicalassistant/agentcore/lambda_url
```

### "Patient not found"

Verify the patient exists:
```bash
psql -h your-db-host -U your-db-user -d medical_records \
  -c "SELECT medical_record_number, first_name, last_name FROM patients WHERE medical_record_number = 'MRN-2024-001001';"
```

## Advanced Testing

### Test with Different Queries

```python
# Direct medication query
"Show me all medications for MRN-2024-001001"

# Patient lookup + medications
"What medications is Sarah Johnson taking?"

# Specific medication check
"Is patient MRN-2024-001001 on Metformin?"

# Multiple patients
"Show me medications for patients with diabetes"
```

### Test Tool Chaining

The agent can chain multiple tools:

```
User: "Find patients with diabetes and show their medications"

Agent:
1. Calls get_diabetes_patients_list()
2. For each patient, calls get_patient_medication_list()
3. Summarizes the results
```

## Integration with Other Tools

The medications tool works alongside:
- `lookup_patient_record` - Get patient demographics
- `search_patients_by_name` - Find patients by name
- `get_diabetes_patients_list` - Find diabetes patients
- `get_appointments` - View appointments (if implemented)

## Next Steps

1. **Deploy to AgentCore** - Update the runtime with the new tools
2. **Test in production** - Use the web frontend
3. **Add more medications** - Load additional sample data
4. **Extend functionality** - Add medication interaction checking, allergy cross-reference, etc.

## Related Files

- Test Script: `scripts/test_agent_medications.py`
- Agent Tool: `agent/patient_tools.py`
- Lambda Handler: `lambda/database-handler/index.py`
- Sample Data: `database/data/03_medications_sample_data.sql`
- Implementation Guide: `MEDICATIONS_IMPLEMENTATION.md`
