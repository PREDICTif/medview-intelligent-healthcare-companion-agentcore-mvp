#!/usr/bin/env python3
"""
Test script for the medications functionality.
Tests both the Lambda endpoint and the patient tools.
"""

import sys
import json
import boto3
import click
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_ssm_parameter, get_aws_region

REGION = get_aws_region()


def test_lambda_medications(lambda_arn: str, patient_id: str):
    """Test the Lambda medications endpoint directly"""
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    payload = {
        "action": "get_patient_medications",
        "patient_id": patient_id
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=lambda_arn,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result.get('body', '{}'))
            return True, body
        else:
            return False, result
            
    except Exception as e:
        return False, {'error': str(e)}


def test_patient_tools_medications(mrn: str):
    """Test the patient_tools medication function"""
    sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))
    
    try:
        from patient_tools import get_patient_medication_list
        
        result = get_patient_medication_list(mrn)
        return True, result
        
    except Exception as e:
        return False, str(e)


@click.command()
@click.option('--patient-id', default=None, help='Patient UUID to test')
@click.option('--mrn', default='MRN-2024-001001', help='Medical Record Number to test')
@click.option('--verbose', '-v', is_flag=True, help='Show full responses')
def main(patient_id, mrn, verbose):
    """Test medications functionality.
    
    This tests:
    1. Lambda endpoint for getting medications
    2. Patient tools medication function
    """
    
    click.echo("🧪 Testing Medications Functionality")
    click.echo(f"📍 Region: {REGION}\n")
    
    # Get Lambda ARN
    try:
        lambda_arn = get_ssm_parameter("/app/medicalassistant/agentcore/lambda_arn")
        if not lambda_arn:
            click.echo("❌ Lambda ARN not found in SSM")
            sys.exit(1)
        click.echo(f"✅ Lambda: {lambda_arn}\n")
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)
    
    # If no patient_id provided, get it from the first patient
    if not patient_id:
        click.echo("📋 Getting patient ID from database...")
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        get_patient_payload = {
            "action": "get_patient_by_id",
            "medical_record_number": mrn
        }
        
        try:
            response = lambda_client.invoke(
                FunctionName=lambda_arn,
                InvocationType='RequestResponse',
                Payload=json.dumps(get_patient_payload)
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                body = json.loads(result.get('body', '{}'))
                if body.get('status') == 'success' and body.get('patient'):
                    patient_id = body['patient']['patient_id']
                    click.echo(f"✅ Found patient: {patient_id}\n")
                else:
                    click.echo(f"❌ Patient not found: {mrn}")
                    sys.exit(1)
            else:
                click.echo(f"❌ Error getting patient: {result}")
                sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Error: {e}")
            sys.exit(1)
    
    # Test 1: Lambda endpoint
    click.echo("=" * 60)
    click.echo("Test 1: Lambda Medications Endpoint")
    click.echo("=" * 60)
    
    success, result = test_lambda_medications(lambda_arn, patient_id)
    
    if success:
        click.echo("✅ Lambda endpoint working")
        medications = result.get('medications', [])
        click.echo(f"📊 Found {len(medications)} medication(s)")
        
        if verbose and medications:
            click.echo("\n📄 Medications:")
            for i, med in enumerate(medications, 1):
                click.echo(f"\n{i}. {med.get('medication_name', 'Unknown')}")
                click.echo(f"   Dosage: {med.get('dosage', 'N/A')}")
                click.echo(f"   Frequency: {med.get('frequency', 'N/A')}")
                click.echo(f"   Status: {med.get('medication_status', 'N/A')}")
    else:
        click.echo(f"❌ Lambda endpoint failed: {result}")
    
    # Test 2: Patient tools function
    click.echo("\n" + "=" * 60)
    click.echo("Test 2: Patient Tools Medication Function")
    click.echo("=" * 60)
    
    success, result = test_patient_tools_medications(mrn)
    
    if success:
        click.echo("✅ Patient tools function working")
        if verbose:
            click.echo(f"\n📄 Result:\n{result}")
        else:
            # Show first 300 characters
            preview = result[:300] + "..." if len(result) > 300 else result
            click.echo(f"\n📄 Preview:\n{preview}")
    else:
        click.echo(f"❌ Patient tools function failed: {result}")
    
    click.echo("\n" + "=" * 60)
    click.echo("✅ Testing complete!")
    click.echo("=" * 60)


if __name__ == "__main__":
    main()
