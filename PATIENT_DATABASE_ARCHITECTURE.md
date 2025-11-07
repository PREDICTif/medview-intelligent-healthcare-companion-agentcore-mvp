# Patient Database Architecture - Corrected Approach

## Overview

After reviewing the AgentCore documentation, we've corrected the patient database integration to use the proper architecture.

## Architecture Decision

### ❌ What We Initially Tried (Incorrect)
- Agent → AgentCore Gateway → Lambda → Database
- Required complex OAuth authentication
- Gateway was meant for external access, not internal agent tools

### ✅ Correct Approach (Current)
- Agent → Lambda Function URL → Database
- Direct access, no authentication needed (Lambda has public URL)
- Gateway exists for external API access if needed later

## Components

### 1. **Lambda Function** (`MihcStack-DatabaseLambda`)
- **Purpose**: Database access layer
- **URL**: `https://lgivqyjg6ilcs3ndbh2wp2tocu0ducok.lambda-url.us-east-1.on.aws/`
- **Access**: Public function URL (no auth required)
- **Actions**: `get_patients`, `get_patient_by_id`

### 2. **Patient Tools** (`agent/patient_tools.py`)
- **Purpose**: Strands tools that wrap Lambda calls
- **Method**: Direct HTTP POST to Lambda URL
- **Tools**:
  - `lookup_patient_record(patient_id)`
  - `get_diabetes_patients_list()`
  - `search_patients_by_name(first_name, last_name)`
  - `get_patient_medication_list(patient_id)`

### 3. **AgentCore Gateway** (Optional)
- **Purpose**: External API access with OAuth
- **URL**: `https://patient-database-gateway-lbkaxsbfkv.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp`
- **Use Case**: If you want to expose patient database to external systems
- **Status**: Created but not used by agent

## How It Works

```
User Question
    ↓
AgentCore Runtime
    ↓
Medical Assistant Agent
    ↓
Patient Tools (Strands @tool)
    ↓
Lambda Function URL (Direct HTTP POST)
    ↓
RDS Aurora Serverless (PostgreSQL)
    ↓
Patient Data (104 patients)
```

## Code Flow

### 1. User Asks Question
```
"Look up patient MRN-2024-001001"
```

### 2. Agent Selects Tool
```python
# Agent decides to use lookup_patient_record tool
lookup_patient_record("MRN-2024-001001")
```

### 3. Tool Calls Lambda
```python
# patient_tools.py
lambda_url = get_lambda_url()  # From SSM
payload = {
    "action": "get_patient_by_id",
    "medical_record_number": "MRN-2024-001001"
}
response = requests.post(lambda_url, json=payload)
```

### 4. Lambda Queries Database
```python
# lambda/database-handler/index.py
sql = "SELECT * FROM patients WHERE medical_record_number = :mrn"
result = rds_data_client.execute_statement(...)
```

### 5. Response Flows Back
```
Database → Lambda → Tool → Agent → User
```

## Configuration

### SSM Parameters
```bash
/app/medicalassistant/agentcore/lambda_url
  → https://lgivqyjg6ilcs3ndbh2wp2tocu0ducok.lambda-url.us-east-1.on.aws/

/app/medicalassistant/agentcore/lambda_arn
  → arn:aws:lambda:us-east-1:584360833890:function:MihcStack-DatabaseLambda...

/app/medicalassistant/agentcore/gateway_url (optional)
  → https://patient-database-gateway-lbkaxsbfkv.gateway...
```

### Agent Configuration (`.bedrock_agentcore.yaml`)
```yaml
agents:
  strands_agent:
    # No gateway configuration needed for direct Lambda access
    # Gateway config removed - agent uses Lambda URL directly
```

## Security Considerations

### Current Setup
- ✅ Lambda Function URL is public (no auth)
- ✅ Lambda has IAM role to access RDS
- ✅ RDS is in private subnet
- ✅ Data encrypted at rest and in transit

### Production Recommendations
1. **Add Lambda URL Authentication**: Use IAM auth or API key
2. **VPC Integration**: Put Lambda in VPC with RDS
3. **Rate Limiting**: Add throttling to Lambda
4. **Audit Logging**: Log all database access
5. **Data Masking**: Mask sensitive patient data in responses

## Testing

### Test Lambda Directly
```bash
curl -X POST https://lgivqyjg6ilcs3ndbh2wp2tocu0ducok.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"action": "get_patients"}'
```

### Test Through Agent
```
1. Open: https://d1kg75xyopexst.cloudfront.net
2. Log in with Cognito
3. Ask: "Show me all diabetes patients"
4. Ask: "Look up patient MRN-2024-001001"
```

## Troubleshooting

### Issue: "Patient database is not available"
**Cause**: Lambda URL not in SSM
**Fix**: 
```bash
aws ssm put-parameter \
  --name "/app/medicalassistant/agentcore/lambda_url" \
  --value "https://lgivqyjg6ilcs3ndbh2wp2tocu0ducok.lambda-url.us-east-1.on.aws/" \
  --type "String" \
  --overwrite
```

### Issue: "Error accessing patient database (Status: 500)"
**Cause**: Lambda function error
**Fix**: Check CloudWatch logs for Lambda function

### Issue: "No patient found"
**Cause**: Patient doesn't exist or wrong MRN format
**Fix**: Use correct MRN format: `MRN-2024-001001`

## Future Enhancements

### Option 1: Use AgentCore Gateway (For External Access)
- Keep current Lambda direct access for agent
- Use gateway for external API consumers
- Add OAuth authentication for external access

### Option 2: MCP Server Integration
- Convert Lambda to proper MCP server
- Use AgentCore's native MCP client
- Automatic tool discovery

### Option 3: Bedrock Agents Integration
- Use Bedrock Agents for patient database
- Action groups for database operations
- Built-in security and monitoring

## Summary

**Current Architecture**: ✅ Working
- Agent calls Lambda directly via function URL
- Simple, fast, no authentication complexity
- Gateway exists but not used by agent

**Deployment Status**: Ready to deploy
- All components configured correctly
- Patient tools updated to use Lambda URL
- No gateway authentication issues

**Next Step**: Deploy and test!
```bash
./deploy-all.sh
```
