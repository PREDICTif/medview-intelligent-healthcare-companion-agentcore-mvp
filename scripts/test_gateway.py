#!/usr/bin/env python3
"""
Test script for the patient-database-gateway.
Tests the AgentCore Gateway by invoking the Lambda function directly.
"""

import sys
import json
import boto3
import click
from pathlib import Path

# Add scripts directory to path for utils
sys.path.insert(0, str(Path(__file__).parent))

from utils import get_ssm_parameter, get_aws_region

REGION = get_aws_region()


class GatewayTester:
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name=REGION)
        self.lambda_arn = None
        
    def setup(self):
        """Get Lambda ARN from SSM"""
        try:
            self.lambda_arn = get_ssm_parameter("/app/medicalassistant/agentcore/lambda_arn")
            if not self.lambda_arn:
                click.echo("❌ Lambda ARN not found in SSM parameter store")
                return False
            click.echo(f"✅ Found Lambda ARN: {self.lambda_arn}")
            return True
        except Exception as e:
            click.echo(f"❌ Error getting Lambda ARN: {e}")
            return False
    
    def invoke_lambda(self, method: str, path: str, body: dict = None):
        """Invoke the Lambda function with API Gateway event format"""
        event = {
            "httpMethod": method,
            "path": path,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(body) if body else None
        }
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.lambda_arn,
                InvocationType='RequestResponse',
                Payload=json.dumps(event)
            )
            
            payload = json.loads(response['Payload'].read())
            
            if 'statusCode' in payload:
                status_code = payload['statusCode']
                body = json.loads(payload.get('body', '{}'))
                return status_code, body
            else:
                return None, payload
                
        except Exception as e:
            click.echo(f"❌ Error invoking Lambda: {e}")
            return None, {"error": str(e)}
    
    def test_lookup_patient(self):
        """Test patient record lookup"""
        click.echo("\n🧪 Testing: Lookup Patient Record")
        
        # Test with patient_id
        status, body = self.invoke_lambda("GET", "/patients/123e4567-e89b-12d3-a456-426614174000")
        
        if status == 200:
            click.echo(f"✅ Success: Found patient {body.get('first_name', '')} {body.get('last_name', '')}")
            return True
        elif status == 404:
            click.echo(f"⚠️  Patient not found (this is OK if no test data exists)")
            return True
        else:
            click.echo(f"❌ Failed with status {status}: {body}")
            return False
    
    def test_search_patients(self):
        """Test patient search by name"""
        click.echo("\n🧪 Testing: Search Patients by Name")
        
        status, body = self.invoke_lambda("GET", "/patients/search?first_name=John")
        
        if status == 200:
            patients = body.get('patients', [])
            click.echo(f"✅ Success: Found {len(patients)} patient(s)")
            return True
        else:
            click.echo(f"❌ Failed with status {status}: {body}")
            return False
    
    def test_diabetes_patients(self):
        """Test diabetes patients list"""
        click.echo("\n🧪 Testing: Get Diabetes Patients List")
        
        status, body = self.invoke_lambda("GET", "/patients/diabetes")
        
        if status == 200:
            patients = body.get('patients', [])
            click.echo(f"✅ Success: Found {len(patients)} diabetes patient(s)")
            return True
        else:
            click.echo(f"❌ Failed with status {status}: {body}")
            return False
    
    def test_patient_medications(self):
        """Test patient medication list"""
        click.echo("\n🧪 Testing: Get Patient Medications")
        
        status, body = self.invoke_lambda("GET", "/patients/123e4567-e89b-12d3-a456-426614174000/medications")
        
        if status == 200:
            medications = body.get('medications', [])
            click.echo(f"✅ Success: Found {len(medications)} medication(s)")
            return True
        elif status == 404:
            click.echo(f"⚠️  Patient not found (this is OK if no test data exists)")
            return True
        else:
            click.echo(f"❌ Failed with status {status}: {body}")
            return False
    
    def test_get_appointments(self):
        """Test get appointments"""
        click.echo("\n🧪 Testing: Get Appointments")
        
        status, body = self.invoke_lambda("GET", "/appointments")
        
        if status == 200:
            appointments = body.get('appointments', [])
            click.echo(f"✅ Success: Found {len(appointments)} appointment(s)")
            return True
        else:
            click.echo(f"❌ Failed with status {status}: {body}")
            return False
    
    def test_create_appointment(self):
        """Test create appointment"""
        click.echo("\n🧪 Testing: Create Appointment")
        
        appointment_data = {
            "patient_id": "123e4567-e89b-12d3-a456-426614174000",
            "provider_id": "456e7890-e89b-12d3-a456-426614174001",
            "appointment_date": "2024-12-20T10:00:00Z",
            "created_by": "789e0123-e89b-12d3-a456-426614174002",
            "duration_minutes": 30,
            "appointment_type": "Test",
            "reason_for_visit": "Gateway test appointment"
        }
        
        status, body = self.invoke_lambda("POST", "/appointments", appointment_data)
        
        if status == 201:
            click.echo(f"✅ Success: Created appointment {body.get('appointment_id', '')}")
            return True
        elif status == 404:
            click.echo(f"⚠️  Patient or provider not found (this is OK if no test data exists)")
            return True
        else:
            click.echo(f"❌ Failed with status {status}: {body}")
            return False
    
    def run_all_tests(self):
        """Run all gateway tests"""
        click.echo("🚀 Starting patient-database-gateway tests...")
        click.echo(f"📍 Region: {REGION}")
        
        if not self.setup():
            return False
        
        results = []
        
        # Run all tests
        results.append(("Lookup Patient", self.test_lookup_patient()))
        results.append(("Search Patients", self.test_search_patients()))
        results.append(("Diabetes Patients", self.test_diabetes_patients()))
        results.append(("Patient Medications", self.test_patient_medications()))
        results.append(("Get Appointments", self.test_get_appointments()))
        results.append(("Create Appointment", self.test_create_appointment()))
        
        # Summary
        click.echo("\n" + "="*60)
        click.echo("📊 Test Results Summary")
        click.echo("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            click.echo(f"{status} - {test_name}")
        
        click.echo("="*60)
        click.echo(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            click.echo("🎉 All tests passed!")
            return True
        else:
            click.echo("⚠️  Some tests failed")
            return False


@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def main(verbose):
    """Test the patient-database-gateway Lambda function."""
    tester = GatewayTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
