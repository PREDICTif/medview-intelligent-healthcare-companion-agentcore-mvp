#!/usr/bin/env python3
"""
Complete the AgentCore Gateway setup by creating the target
"""

import boto3
import json
from utils import get_ssm_parameter, put_ssm_parameter, load_api_spec

def complete_gateway_setup():
    """Complete the gateway setup by creating the target"""
    
    # Initialize clients
    gateway_client = boto3.client("bedrock-agentcore-control", region_name="us-east-1")
    
    # List gateways to find our gateway
    response = gateway_client.list_gateways()
    
    patient_gateway = None
    for gateway in response['items']:
        if 'patient-database-gateway' in gateway['name']:
            patient_gateway = gateway
            break
    
    if not patient_gateway:
        print("❌ Patient database gateway not found")
        return False
    
    gateway_id = patient_gateway['gatewayId']
    print(f"✅ Found gateway: {gateway_id}")
    print(f"   Status: {patient_gateway['status']}")
    
    if patient_gateway['status'] not in ['ACTIVE', 'READY']:
        print(f"⚠️ Gateway is not ready yet (status: {patient_gateway['status']})")
        print("Please wait for the gateway to become ready and try again")
        return False
    
    # Check if target already exists
    try:
        targets_response = gateway_client.list_gateway_targets(gatewayIdentifier=gateway_id)
        if targets_response['items']:
            print("✅ Gateway target already exists")
            # Save gateway details to SSM
            save_gateway_config(patient_gateway)
            return True
    except Exception as e:
        print(f"Error checking targets: {e}")
    
    # Create the gateway target
    try:
        lambda_target_config = {
            "mcp": {
                "lambda": {
                    "lambdaArn": get_ssm_parameter("/app/medicalassistant/agentcore/lambda_arn"),
                    "toolSchema": {"inlinePayload": load_api_spec("lambda/database-handler/api_spec.json")},
                }
            }
        }
        
        credential_config = [{"credentialProviderType": "GATEWAY_IAM_ROLE"}]
        
        create_target_response = gateway_client.create_gateway_target(
            gatewayIdentifier=gateway_id,
            name="PatientDatabaseTarget",
            description="Patient Database Lambda Target",
            targetConfiguration=lambda_target_config,
            credentialProviderConfigurations=credential_config,
        )
        
        print(f"✅ Gateway target created: {create_target_response['targetId']}")
        
        # Save gateway configuration
        save_gateway_config(patient_gateway)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating gateway target: {e}")
        return False

def save_gateway_config(gateway_info):
    """Save gateway configuration to SSM parameters"""
    try:
        put_ssm_parameter("/app/medicalassistant/agentcore/gateway_id", gateway_info['gatewayId'])
        put_ssm_parameter("/app/medicalassistant/agentcore/gateway_name", gateway_info['name'])
        put_ssm_parameter("/app/medicalassistant/agentcore/gateway_arn", gateway_info['gatewayArn'])
        put_ssm_parameter("/app/medicalassistant/agentcore/gateway_url", gateway_info['gatewayUrl'])
        
        print("✅ Gateway configuration saved to SSM parameters")
        print(f"   Gateway ID: {gateway_info['gatewayId']}")
        print(f"   Gateway URL: {gateway_info['gatewayUrl']}")
        
    except Exception as e:
        print(f"❌ Error saving gateway configuration: {e}")

if __name__ == "__main__":
    print("🔧 Completing AgentCore Gateway setup...")
    
    if complete_gateway_setup():
        print("\n✅ Gateway setup completed successfully!")
        print("\nNext steps:")
        print("1. Deploy the updated agent: ./deploy-all.sh")
        print("2. Test the integration with patient database tools")
    else:
        print("\n❌ Gateway setup failed!")