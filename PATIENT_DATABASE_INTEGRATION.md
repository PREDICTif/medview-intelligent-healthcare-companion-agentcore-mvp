# 🏥 Patient Database Integration with AgentCore Gateway

## Overview

This integration connects your medical assistant agent to the patient database via AgentCore Gateway, allowing the chatbot to access patient records and provide personalized medical guidance.

## 🏗️ Architecture

```
Medical Assistant Agent → AgentCore Gateway → Database Handler Lambda → Aurora Database
```

## 📋 Prerequisites

1. **Deployed Infrastructure:**
   - ✅ MihcStack (Database + Lambda)
   - ✅ AgentCoreAuth (Cognito)
   - ✅ AgentCoreInfra (IAM roles)

2. **Required Components:**
   - ✅ Database Handler Lambda with Function URL
   - ✅ AgentCore Gateway script
   - ✅ API specification for database operations

## 🚀 Setup Instructions

### Step 1: Set Up Gateway Prerequisites

```bash
# Set up required SSM parameters
python scripts/setup_patient_database_gateway.py
```

This script will:
- Extract Lambda ARN from MihcStack
- Configure Cognito authentication
- Set up IAM roles for gateway

### Step 2: Create AgentCore Gateway

```bash
# Create the gateway with patient database API
python scripts/agentcore_gateway.py create --name patient-database-gateway
```

This will:
- Create AgentCore Gateway
- Configure Lambda target
- Set up authentication
- Store gateway URL in SSM

### Step 3: Add Database Tools to Agent

Add the patient database tool to your medical assistant:

```python
# In agent/strands_agent.py, add the import
from patient_database_tool import get_patient_records, get_diabetes_patients, search_patients_by_name

# Add to your tools list
tools=[
    diabetes_specialist_tool, 
    amd_specialist_tool, 
    web_search,
    patient_database_tool  # NEW
]
```

## 🔧 Available Database Functions

### 1. Get All Patients
```python
result = get_patient_records()
# Returns: {"status": "success", "patients": [...], "count": 5}
```

### 2. Get Specific Patient
```python
result = get_patient_records(patient_id="12345")
result = get_patient_records(medical_record_number="MRN001")
# Returns: {"status": "success", "patient": {...}}
```

### 3. Search Patients by Name
```python
result = search_patients_by_name(first_name="John", last_name="Smith")
# Returns: {"status": "success", "patients": [...]}
```

### 4. Get Diabetes Patients
```python
result = get_diabetes_patients()
# Returns: {"status": "success", "patients": [...]}
```

## 🛠️ Integration with Medical Assistant

### Example Agent Tool Implementation

```python
from strands import tool
from patient_database_tool import get_patient_records, format_patient_summary

@tool
def lookup_patient_info(patient_identifier: str) -> str:
    """
    Look up patient information from the medical database
    
    Args:
        patient_identifier: Patient ID or Medical Record Number
        
    Returns:
        Formatted patient information or error message
    """
    result = get_patient_records(patient_id=patient_identifier)
    
    if result["status"] == "success":
        patient = result["patient"]
        return format_patient_summary(patient)
    else:
        return f"Could not find patient: {result['message']}"

@tool  
def get_diabetes_patient_list() -> str:
    """
    Get a list of all patients with diabetes diagnosis
    
    Returns:
        Summary of diabetes patients
    """
    result = get_diabetes_patients()
    
    if result["status"] == "success":
        patients = result["patients"]
        summary = f"Found {result['count']} diabetes patients:\n\n"
        
        for patient in patients[:5]:  # Limit to first 5
            summary += format_patient_summary(patient) + "\n"
            
        if len(patients) > 5:
            summary += f"... and {len(patients) - 5} more patients"
            
        return summary
    else:
        return f"Error retrieving diabetes patients: {result['message']}"
```

## 🔐 Security Considerations

### Authentication Flow
1. **Agent Authentication:** Uses Cognito JWT tokens
2. **Gateway Security:** Custom JWT authorizer validates tokens
3. **Lambda Security:** IAM roles control database access
4. **Database Security:** Aurora with encryption at rest

### Data Privacy
- Patient data is encrypted in transit and at rest
- Access is logged and auditable
- HIPAA compliance considerations built-in

## 🧪 Testing the Integration

### 1. Test Gateway Connection
```bash
# Get the gateway URL
GATEWAY_URL=$(aws ssm get-parameter --name "/app/medicalassistant/agentcore/gateway_url" --query "Parameter.Value" --output text)

# Test patients endpoint
curl "$GATEWAY_URL/patients"
```

### 2. Test Agent Integration
```bash
# Test with local agent
python test_agent_local.py chat "Can you look up patient information for MRN001?"
```

### 3. Test Specific Queries
- "Show me all diabetes patients"
- "Look up patient John Smith"
- "What medications is patient MRN001 taking?"

## 📊 Use Cases

### 1. Personalized Medical Guidance
```
User: "I'm patient MRN001, what should I know about my diabetes?"
Agent: [Looks up patient] "Based on your records showing Type 2 diabetes diagnosed in 2020..."
```

### 2. Medication Review
```
User: "Review my current medications"
Agent: [Accesses patient record] "Your current medications include Metformin 500mg..."
```

### 3. Care Coordination
```
User: "Who is my primary care physician?"
Agent: [Checks database] "Your primary care physician is Dr. Smith..."
```

## 🔧 Troubleshooting

### Common Issues

1. **Gateway Not Found**
   - Run setup script: `python scripts/setup_patient_database_gateway.py`
   - Check SSM parameters exist

2. **Authentication Errors**
   - Verify Cognito configuration
   - Check JWT token validity

3. **Database Connection Issues**
   - Verify Lambda function is running
   - Check VPC/security group configuration

4. **Permission Errors**
   - Ensure IAM roles have proper permissions
   - Check Lambda execution role

### Debug Commands
```bash
# Check gateway status
aws bedrock-agentcore-control list-gateways

# Check SSM parameters
aws ssm get-parameters-by-path --path "/app/medicalassistant/agentcore"

# Test Lambda directly
aws lambda invoke --function-name DatabaseLambda response.json
```

## 🎯 Next Steps

1. **Deploy the integration** using the setup scripts
2. **Test the database connection** with sample queries
3. **Add patient lookup tools** to your medical assistant
4. **Customize the responses** based on patient data
5. **Monitor usage** and optimize performance

The integration provides a secure, scalable way to give your medical assistant access to patient records while maintaining HIPAA compliance and security best practices! 🎉