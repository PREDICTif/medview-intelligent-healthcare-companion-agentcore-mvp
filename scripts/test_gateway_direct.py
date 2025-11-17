#!/usr/bin/env python3
"""
Test the patient-database-gateway by calling the Lambda directly.
This bypasses OAuth and tests the Lambda function that the gateway uses.
"""

import sys
import json
import boto3
import click
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_ssm_parameter, get_aws_region

REGION = get_aws_region()


@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Show full responses')
def main(verbose):
    """Test the gateway Lambda function directly (bypasses OAuth).
    
    This tests the Lambda function that the AgentCore Gateway uses,
    without going through the gateway's OAuth layer.
    """
    
    click.echo("🚀 Testing patient-database-gateway Lambda directly")
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
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    # Test cases - MCP protocol format
    test_cases = [
        {
            "name": "List Tools",
            "payload": {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
        },
        {
            "name": "Lookup Patient",
            "payload": {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "lookup_patient_record",
                    "arguments": {
                        "patient_identifier": "123e4567-e89b-12d3-a456-426614174000"
                    }
                }
            }
        },
        {
            "name": "Search Patients",
            "payload": {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "search_patients_by_name",
                    "arguments": {
                        "first_name": "John"
                    }
                }
            }
        },
        {
            "name": "Get Diabetes Patients",
            "payload": {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "get_diabetes_patients_list",
                    "arguments": {}
                }
            }
        }
    ]
    
    results = []
    
    for test in test_cases:
        click.echo(f"🧪 {test['name']}")
        
        try:
            response = lambda_client.invoke(
                FunctionName=lambda_arn,
                InvocationType='RequestResponse',
                Payload=json.dumps(test['payload'])
            )
            
            payload = json.loads(response['Payload'].read())
            
            if 'result' in payload:
                click.echo(f"   ✅ Success")
                if verbose:
                    click.echo(f"   📄 {json.dumps(payload['result'], indent=2)}")
                elif test['name'] == "List Tools" and 'tools' in payload['result']:
                    tools = payload['result']['tools']
                    click.echo(f"   📋 Found {len(tools)} tools:")
                    for tool in tools:
                        click.echo(f"      - {tool.get('name', 'unknown')}")
                results.append(True)
            elif 'error' in payload:
                click.echo(f"   ❌ Error: {payload['error']}")
                results.append(False)
            else:
                click.echo(f"   ⚠️  Unexpected response format")
                if verbose:
                    click.echo(f"   📄 {json.dumps(payload, indent=2)}")
                results.append(False)
                
        except Exception as e:
            click.echo(f"   ❌ Exception: {e}")
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
