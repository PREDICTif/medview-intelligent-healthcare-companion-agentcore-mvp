#!/usr/bin/env python3
"""
Test script for appointments endpoint
"""

import boto3
import json

# Get Lambda URL from SSM
ssm = boto3.client('ssm')
try:
    response = ssm.get_parameter(Name="/app/medicalassistant/agentcore/lambda_url")
    lambda_url = response['Parameter']['Value']
    print(f"✅ Lambda URL: {lambda_url}")
except Exception as e:
    print(f"❌ Error getting Lambda URL: {e}")
    exit(1)

# Test patient ID (Sarah Johnson from sample data)
# This should be the Cognito user ID that matches the patient_id
test_patient_id = "94c894a8-e0c1-7059-39f2-0cbe3c207746"

# Test appointments endpoint
import requests

print(f"\n📅 Testing appointments endpoint...")
print(f"Patient ID: {test_patient_id}")

payload = {
    "action": "get_patient_appointments",
    "patient_id": test_patient_id
}

try:
    response = requests.post(lambda_url, json=payload, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 'success':
            appointments = data.get('appointments', [])
            print(f"\n✅ Found {len(appointments)} appointments")
            for i, appt in enumerate(appointments, 1):
                print(f"\n{i}. {appt.get('appointment_type')} - {appt.get('scheduled_date')} {appt.get('scheduled_time')}")
                print(f"   Status: {appt.get('appointment_status')}")
                print(f"   Provider: {appt.get('provider_name')}")
        else:
            print(f"\n❌ Error: {data.get('message')}")
    else:
        print(f"\n❌ HTTP Error: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
