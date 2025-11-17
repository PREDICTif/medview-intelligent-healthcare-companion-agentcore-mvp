#!/usr/bin/env python3
"""
Simple test script for the patient-database-gateway.
Tests available endpoints and provides clear feedback.
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


def invoke_lambda(lambda_arn: str, method: str, path: str, body: dict = None):
    """Invoke the Lambda function with API Gateway event format"""
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    event = {
        "httpMethod": method,
        "path": path,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body) if body else None
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=lambda_arn,
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
        return None, {"error": str(e)}


@click.command()
@click.option('--endpoint', '-e', help='Test specific endpoint (e.g., /patients, /patients/diabetes)')
@click.option('--verbose', '-v', is_flag=True, help='Show full response bodies')
def main(endpoint, verbose):
    """Test the patient-database-gateway Lambda function.
    
    Examples:
        python test_gateway_simple.py
        python test_gateway_simple.py -e /patients
        python test_gateway_simple.py -e /patients/diabetes -v
    """
    
    click.echo("🚀 Testing patient-database-gateway")
    click.echo(f"📍 Region: {REGION}\n")
    
    # Get Lambda ARN
    try:
        lambda_arn = get_ssm_parameter("/app/medicalassistant/agentcore/lambda_arn")
        if not lambda_arn:
            click.echo("❌ Lambda ARN not found in SSM parameter store")
            sys.exit(1)
        click.echo(f"✅ Lambda: {lambda_arn}\n")
    except Exception as e:
        click.echo(f"❌ Error getting Lambda ARN: {e}")
        sys.exit(1)
    
    # Define test endpoints
    endpoints = [
        ("GET", "/health", "Health Check"),
        ("GET", "/patients", "List All Patients"),
        ("GET", "/patients/diabetes", "List Diabetes Patients"),
        ("GET", "/patients/search?first_name=John", "Search Patients by Name"),
    ]
    
    # Filter to specific endpoint if requested
    if endpoint:
        endpoints = [(m, p, d) for m, p, d in endpoints if p.startswith(endpoint)]
        if not endpoints:
            click.echo(f"⚠️  No matching endpoints for: {endpoint}")
            sys.exit(1)
    
    # Run tests
    results = []
    for method, path, description in endpoints:
        click.echo(f"🧪 {description}")
        click.echo(f"   {method} {path}")
        
        status, body = invoke_lambda(lambda_arn, method, path)
        
        if status == 200:
            click.echo(f"   ✅ Success (200)")
            
            # Show summary based on response
            if 'patients' in body:
                count = len(body['patients'])
                click.echo(f"   📊 Found {count} patient(s)")
            elif 'medications' in body:
                count = len(body['medications'])
                click.echo(f"   📊 Found {count} medication(s)")
            elif 'message' in body:
                click.echo(f"   💬 {body['message']}")
            
            if verbose:
                click.echo(f"   📄 Response: {json.dumps(body, indent=2)}")
            
            results.append(True)
        elif status == 404:
            click.echo(f"   ⚠️  Not Found (404)")
            if verbose and body:
                click.echo(f"   📄 Response: {json.dumps(body, indent=2)}")
            results.append(True)  # 404 is expected for missing data
        elif status:
            click.echo(f"   ❌ Failed ({status})")
            if body:
                click.echo(f"   📄 Error: {body.get('message', body)}")
            results.append(False)
        else:
            click.echo(f"   ❌ Lambda invocation failed")
            if body:
                click.echo(f"   📄 Error: {body}")
            results.append(False)
        
        click.echo()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    click.echo("="*60)
    if passed == total:
        click.echo(f"🎉 All {total} tests passed!")
        sys.exit(0)
    else:
        click.echo(f"⚠️  {passed}/{total} tests passed")
        sys.exit(1)


if __name__ == "__main__":
    main()
