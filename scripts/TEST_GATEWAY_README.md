# Patient Database Gateway Test Scripts

Three test scripts are available to test the patient-database-gateway at different levels.

## Test Scripts Overview

### 1. `test_gateway_simple.py` - Direct Lambda Testing
**Recommended for: Quick testing and debugging**

Tests the Lambda function directly without going through the AgentCore Gateway.

```bash
# Run all tests
python test_gateway_simple.py

# Test specific endpoint
python test_gateway_simple.py -e /patients

# Verbose output
python test_gateway_simple.py -v
```

**What it tests:**
- Lambda function is accessible
- Database connection works
- Basic endpoints respond correctly

**Pros:**
- Fast and simple
- No OAuth setup required
- Good for debugging Lambda issues

**Cons:**
- Doesn't test the full gateway flow
- Doesn't test authentication

---

### 2. `test_gateway.py` - Comprehensive Lambda Testing
**Recommended for: Full Lambda endpoint testing**

Tests all available Lambda endpoints with detailed reporting.

```bash
# Run all tests
python test_gateway.py

# Verbose output
python test_gateway.py -v
```

**What it tests:**
- All patient database endpoints
- Appointment endpoints (if implemented)
- Error handling
- Response formats

**Pros:**
- Comprehensive coverage
- Detailed test results
- Tests all endpoints

**Cons:**
- Doesn't test OAuth flow
- Doesn't test AgentCore Gateway

---

### 3. `test_gateway_oauth.py` - Full Gateway Testing
**Recommended for: Production-like testing**

Tests the complete flow through AgentCore Gateway with OAuth authentication.

```bash
# Run all tests
python test_gateway_oauth.py

# Test specific tool
python test_gateway_oauth.py -t lookup_patient_record

# Verbose output
python test_gateway_oauth.py -v
```

**What it tests:**
- Cognito OAuth token generation
- AgentCore Gateway authentication
- MCP protocol communication
- End-to-end flow

**Pros:**
- Tests production flow
- Validates OAuth setup
- Tests gateway configuration

**Cons:**
- Requires gateway to be created
- Requires Cognito configuration
- More complex setup

---

## Prerequisites

### For All Scripts
- AWS credentials configured
- Python 3.8+
- boto3 installed
- Access to SSM parameters

### For OAuth Script Only
- AgentCore Gateway created: `python agentcore_gateway.py create --name patient-database-gateway`
- Cognito machine client configured
- requests library: `pip install requests`

---

## SSM Parameters Required

All scripts read configuration from SSM Parameter Store:

| Parameter | Used By | Description |
|-----------|---------|-------------|
| `/app/medicalassistant/agentcore/lambda_arn` | All | Lambda function ARN |
| `/app/medicalassistant/agentcore/gateway_url` | OAuth script | Gateway endpoint URL |
| `/app/medicalassistant/agentcore/machine_client_id` | OAuth script | Cognito client ID |
| `/app/medicalassistant/agentcore/cognito_secret` | OAuth script | Cognito client secret |
| `/app/medicalassistant/agentcore/cognito_discovery_url` | OAuth script | Cognito discovery URL |

---

## Troubleshooting

### "Lambda ARN not found"
```bash
# Check if Lambda is deployed
aws lambda list-functions --query 'Functions[?contains(FunctionName, `Database`)].FunctionName'

# Manually set SSM parameter
aws ssm put-parameter --name /app/medicalassistant/agentcore/lambda_arn \
  --value "arn:aws:lambda:REGION:ACCOUNT:function/FUNCTION_NAME" \
  --type String
```

### "Gateway URL not found"
```bash
# Create the gateway first
cd scripts
python agentcore_gateway.py create --name patient-database-gateway
```

### "Failed to get OAuth token"
```bash
# Check Cognito configuration
aws ssm get-parameter --name /app/medicalassistant/agentcore/machine_client_id
aws ssm get-parameter --name /app/medicalassistant/agentcore/cognito_discovery_url

# Verify client secret exists
aws ssm get-parameter --name /app/medicalassistant/agentcore/cognito_secret --with-decryption
```

### "Database handler ready" but no data
This is normal if:
- No test data has been loaded into the database
- The Lambda is working but the database is empty

To load test data:
```bash
# Load sample data (if available)
cd database
psql -h YOUR_DB_HOST -U YOUR_DB_USER -d medical_records -f data/01_core_sample_data.sql
```

---

## Expected Results

### Successful Test Run
```
🚀 Testing patient-database-gateway
📍 Region: us-east-1

✅ Lambda: arn:aws:lambda:...

🧪 Health Check
   GET /health
   ✅ Success (200)
   💬 Database handler ready

============================================================
🎉 All 4 tests passed!
```

### With Test Data
```
🧪 List All Patients
   GET /patients
   ✅ Success (200)
   📊 Found 5 patient(s)

🧪 List Diabetes Patients
   GET /patients/diabetes
   ✅ Success (200)
   📊 Found 2 patient(s)
```

---

## Integration with CI/CD

These scripts can be integrated into CI/CD pipelines:

```bash
# In your deployment script
cd scripts

# Test Lambda directly
python test_gateway_simple.py || exit 1

# Test full gateway flow
python test_gateway_oauth.py || exit 1

echo "✅ All gateway tests passed"
```

---

## Next Steps

1. **Start with simple test**: `python test_gateway_simple.py`
2. **If that works, try comprehensive**: `python test_gateway.py`
3. **Finally test OAuth flow**: `python test_gateway_oauth.py`

If any test fails, check the CloudWatch logs:
```bash
# Lambda logs
aws logs tail /aws/lambda/YOUR_FUNCTION_NAME --follow

# Gateway logs
aws logs tail /aws/vendedlogs/bedrock-agentcore/gateway/APPLICATION_LOGS/patient-database-gateway-* --follow
```
