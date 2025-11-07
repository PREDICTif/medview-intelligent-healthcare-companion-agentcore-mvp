# Testing Guide - Patient Database Integration

## 🎉 Deployment Complete!

Your medical assistant agent with patient database integration is now live!

## 🌐 Access the Application

**Web Interface**: https://d1kg75xyopexst.cloudfront.net

## 🧪 Test Questions

### 1. Test Patient Lookup
```
"Can you look up patient MRN-2024-001001?"
```
**Expected**: Patient details (name, DOB, contact info)

### 2. Test Diabetes Patients List
```
"Show me all diabetes patients in the database"
```
**Expected**: List of patients with their information

### 3. Test Patient Search by Name
```
"Search for patients named John"
```
**Expected**: List of patients with "John" in their name

### 4. Test Multiple Patients
```
"Look up patient MRN-2024-001028"
```
**Expected**: Jonathan Adams from Lakewood, WA

### 5. Test Non-Existent Patient
```
"Find patient MRN999"
```
**Expected**: "No patient found" message

## 📊 Sample Patients to Test

- **MRN-2024-001001** - Jonathan Adams
- **MRN-2024-001002** - Michael Smith
- **MRN-2024-001003** - Jennifer Davis
- **MRN-2024-001028** - Jonathan Adams (Lakewood, WA)
- **MRN-2024-001234** - Sarah Johnson

## ✅ What to Verify

1. **Patient Tools Working**:
   - ✅ Agent can look up patients by MRN
   - ✅ Agent can list all patients
   - ✅ Agent can search by name
   - ✅ No 401 authentication errors
   - ✅ No "database not available" messages

2. **Cognito User ID**:
   - ✅ User ID extracted from Cognito
   - ✅ Memory tied to user ID
   - ✅ Conversations persist across sessions

3. **Streaming Responses**:
   - ✅ Clean text output
   - ✅ No garbage data
   - ✅ Smooth streaming

## 🔍 Verify Deployment

### Check CloudWatch Logs
```bash
python test_cognito_user_id.py
```

### Test Lambda Function
```bash
curl -X POST https://lgivqyjg6ilcs3ndbh2wp2tocu0ducok.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"action": "get_patients"}' | jq
```

### Check Recent Logs
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/strands_agent-7xbjvREebP-DEFAULT \
  --since 5m \
  --region us-east-1 \
  --follow
```

## 🎯 Testing Checklist

- [ ] Log in to web interface
- [ ] Ask: "Show me all diabetes patients"
- [ ] Ask: "Look up patient MRN-2024-001001"
- [ ] Ask: "Search for patients named John"
- [ ] Verify patient data is displayed
- [ ] Check no authentication errors
- [ ] Test memory persistence (log out/in)
- [ ] Verify Cognito user ID in logs

## 🚨 Troubleshooting

### If you see "database not available":
```bash
# Check Lambda URL is in SSM
aws ssm get-parameter \
  --name "/app/medicalassistant/agentcore/lambda_url" \
  --region us-east-1
```

### If patient data doesn't show:
```bash
# Test Lambda directly
curl -X POST https://lgivqyjg6ilcs3ndbh2wp2tocu0ducok.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"action": "get_patient_by_id", "medical_record_number": "MRN-2024-001001"}'
```

### Check agent logs:
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/strands_agent-7xbjvREebP-DEFAULT \
  --since 10m \
  --region us-east-1
```

## 📈 Success Metrics

✅ **Patient Database Integration**: Working
✅ **Cognito Authentication**: Active
✅ **Memory Persistence**: Configured
✅ **Streaming Responses**: Clean
✅ **104 Patients**: Available in database

## 🎊 You're All Set!

Your medical assistant can now:
- Look up patient records
- Search patient database
- Provide personalized medical guidance
- Remember conversations across sessions
- Access 104 patient records

**Start testing at**: https://d1kg75xyopexst.cloudfront.net
