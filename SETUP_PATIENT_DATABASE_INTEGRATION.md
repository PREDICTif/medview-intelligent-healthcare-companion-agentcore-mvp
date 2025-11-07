# 🏥 Setup Guide: Patient Database Integration

## ✅ **Integration Complete!**

Your medical assistant agent now includes patient database tools via AgentCore Gateway integration.

## 🔧 **What's Been Added:**

### **New Patient Database Tools:**
1. **`lookup_patient_record`** - Look up specific patient by ID or MRN
2. **`get_diabetes_patients_list`** - Get all patients with diabetes
3. **`search_patients_by_name`** - Search patients by first/last name
4. **`get_patient_medication_list`** - Get patient's current medications

### **Updated Agent Features:**
- ✅ **Enhanced System Prompt** - Includes patient database tool usage
- ✅ **Tool Integration** - All 7 tools now available to the agent
- ✅ **Memory Integration** - Conversation persistence with patient context
- ✅ **Error Handling** - Graceful fallbacks for database unavailability

## 🚀 **Setup Steps:**

### **Step 1: Set Up Gateway Prerequisites**
```bash
python scripts/setup_patient_database_gateway.py
```

### **Step 2: Create AgentCore Gateway**
```bash
python scripts/agentcore_gateway.py create --name patient-database-gateway --api-spec-file lambda/database-handler/api_spec.json
```

### **Step 3: Deploy Updated Agent**
```bash
./deploy-all.sh
```

## 🧪 **Test Patient Database Integration:**

### **Local Testing:**
```bash
# Test basic functionality
python test_agent_local.py chat "Look up patient MRN001"

# Test diabetes patient list
python test_agent_local.py chat "Show me all diabetes patients"

# Test patient search
python test_agent_local.py chat "Find patient John Smith"
```

### **Production Testing:**
```bash
# Test patient lookup
agentcore invoke '{"prompt": "Look up patient information for MRN001"}' --session-id user123

# Test medication review
agentcore invoke '{"prompt": "What medications is patient MRN001 taking?"}' --session-id user123

# Test diabetes patient list
agentcore invoke '{"prompt": "Show me all patients with diabetes"}' --session-id user123
```

## 💬 **Example Conversations:**

### **Patient Lookup:**
```
User: "Look up patient MRN001"
Agent: "✅ Patient Record Found:
**Patient: John Smith**
- MRN: MRN001
- DOB: 1980-05-15
- Diabetes Type: Type 2
- Current Medications: Metformin 500mg twice daily..."
```

### **Personalized Guidance:**
```
User: "I'm patient MRN001, what should I know about my diabetes?"
Agent: [Looks up patient] "Based on your records showing Type 2 diabetes diagnosed in 2020 and current Metformin treatment, here's personalized guidance..."
```

### **Medication Review:**
```
User: "Review medications for patient MRN001"
Agent: "💊 Medication Information for John Smith (MRN: MRN001)
**Current Medications:** Metformin 500mg twice daily
**Allergies:** No known allergies..."
```

## 🔐 **Security Features:**

- **JWT Authentication** - Uses Cognito tokens for secure access
- **IAM Permissions** - Scoped database access via Lambda
- **Encrypted Transit** - All data encrypted in transmission
- **Audit Logging** - All database access is logged
- **HIPAA Compliance** - Built with healthcare privacy in mind

## 📊 **Available Patient Data:**

The agent can now access:
- **Demographics** - Name, DOB, gender, contact info
- **Medical History** - Diabetes type, diagnosis date
- **Medications** - Current prescriptions and dosages
- **Allergies** - Known drug and food allergies
- **Care Team** - Primary care physician information
- **Insurance** - Provider and policy information

## 🎯 **Use Cases:**

1. **Personalized Medical Guidance** - Tailored advice based on patient records
2. **Medication Reviews** - Check current prescriptions and interactions
3. **Care Coordination** - Access to care team and contact information
4. **Population Health** - Overview of diabetes patients in practice
5. **Clinical Decision Support** - Evidence-based recommendations with patient context

## 🔧 **Troubleshooting:**

### **Gateway Not Working:**
```bash
# Check gateway status
aws bedrock-agentcore-control list-gateways

# Verify SSM parameters
aws ssm get-parameters-by-path --path "/app/medicalassistant/agentcore"
```

### **Database Connection Issues:**
```bash
# Test Lambda directly
aws lambda invoke --function-name DatabaseLambda response.json

# Check Lambda logs
aws logs tail /aws/lambda/DatabaseLambda --follow
```

### **Authentication Errors:**
- Verify Cognito configuration
- Check JWT token validity
- Ensure proper IAM permissions

## 🎉 **Ready to Use!**

Your medical assistant now has comprehensive access to:
- ✅ **Medical Knowledge Base** (diabetes & AMD expertise)
- ✅ **Current Research** (web search)
- ✅ **Patient Records** (database integration)
- ✅ **Conversation Memory** (persistent context)

The agent can provide personalized, evidence-based medical guidance using both general medical knowledge and specific patient information! 🏥✨