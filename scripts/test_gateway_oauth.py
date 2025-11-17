#!/usr/bin/env python3
"""
Test script for the patient-database-gateway via AgentCore Gateway with OAuth.
This tests the full gateway flow including Cognito authentication.
"""

import sys
import json
import requests
import click
from pathlib import Path

# Add scripts directory to path for utils
sys.path.insert(0, str(Path(__file__).parent))

from utils import get_ssm_parameter, get_aws_region

REGION = get_aws_region()


def get_oauth_token():
    """Get OAuth token from Cognito for machine-to-machine authentication"""
    try:
        # Get Cognito configuration for gateway machine client
        client_id = get_ssm_parameter("/app/medicalassistant/agentcore/gateway_client_id")
        client_secret = get_ssm_parameter("/app/medicalassistant/agentcore/gateway_client_secret")
        token_endpoint = get_ssm_parameter("/app/medicalassistant/agentcore/token_endpoint")
        
        if not all([client_id, client_secret, token_endpoint]):
            click.echo("❌ Missing Cognito configuration in SSM")
            click.echo("   Run: python setup_gateway_oauth.py")
            return None
        
        # Request token using client credentials flow
        response = requests.post(
            token_endpoint,
            data={
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': 'patient-database/read patient-database/write'
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access_token')
        else:
            click.echo(f"❌ Failed to get OAuth token: {response.status_code}")
            click.echo(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        click.echo(f"❌ Error getting OAuth token: {e}")
        return None


def call_gateway(gateway_url: str, token: str, tool_name: str, arguments: dict = None):
    """Call the AgentCore Gateway with OAuth token"""
    try:
        # MCP protocol format
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            gateway_url,
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {
                'status_code': response.status_code,
                'error': response.text
            }
            
    except Exception as e:
        return False, {'error': str(e)}


@click.command()
@click.option('--tool', '-t', help='Test specific tool (e.g., lookup_patient_record)')
@click.option('--verbose', '-v', is_flag=True, help='Show full response bodies')
def main(tool, verbose):
    """Test the patient-database-gateway via AgentCore Gateway with OAuth.
    
    This tests the complete flow:
    1. Get OAuth token from Cognito
    2. Call AgentCore Gateway with token
    3. Gateway invokes Lambda function
    4. Return results
    
    Examples:
        python test_gateway_oauth.py
        python test_gateway_oauth.py -t lookup_patient_record -v
    """
    
    click.echo("🚀 Testing patient-database-gateway via AgentCore Gateway")
    click.echo(f"📍 Region: {REGION}\n")
    
    # Get gateway URL
    try:
        gateway_url = get_ssm_parameter("/app/medicalassistant/agentcore/gateway_url")
        if not gateway_url:
            click.echo("❌ Gateway URL not found in SSM")
            click.echo("   Run: python agentcore_gateway.py create --name patient-database-gateway")
            sys.exit(1)
        click.echo(f"✅ Gateway URL: {gateway_url}")
    except Exception as e:
        click.echo(f"❌ Error getting gateway URL: {e}")
        sys.exit(1)
    
    # Get OAuth token
    click.echo("\n🔐 Getting OAuth token from Cognito...")
    token = get_oauth_token()
    if not token:
        click.echo("❌ Failed to get OAuth token")
        sys.exit(1)
    click.echo(f"✅ Got OAuth token: {token[:20]}...")
    
    # Define test tools
    tools = [
        ("lookup_patient_record", {"patient_identifier": "123e4567-e89b-12d3-a456-426614174000"}, "Lookup Patient Record"),
        ("search_patients_by_name", {"first_name": "John"}, "Search Patients by Name"),
        ("get_diabetes_patients_list", {}, "Get Diabetes Patients"),
        ("get_patient_medication_list", {"patient_identifier": "123e4567-e89b-12d3-a456-426614174000"}, "Get Patient Medications"),
    ]
    
    # Filter to specific tool if requested
    if tool:
        tools = [(n, a, d) for n, a, d in tools if n == tool]
        if not tools:
            click.echo(f"\n⚠️  Unknown tool: {tool}")
            click.echo("Available tools: lookup_patient_record, search_patients_by_name, get_diabetes_patients_list, get_patient_medication_list")
            sys.exit(1)
    
    # Run tests
    click.echo("\n" + "="*60)
    results = []
    
    for tool_name, arguments, description in tools:
        click.echo(f"\n🧪 {description}")
        click.echo(f"   Tool: {tool_name}")
        click.echo(f"   Args: {arguments}")
        
        success, response = call_gateway(gateway_url, token, tool_name, arguments)
        
        if success:
            click.echo(f"   ✅ Success")
            
            if verbose:
                click.echo(f"   📄 Response: {json.dumps(response, indent=2)}")
            elif 'result' in response:
                result = response['result']
                if isinstance(result, dict):
                    if 'patients' in result:
                        click.echo(f"   📊 Found {len(result['patients'])} patient(s)")
                    elif 'medications' in result:
                        click.echo(f"   📊 Found {len(result['medications'])} medication(s)")
                    else:
                        click.echo(f"   📄 Result: {str(result)[:100]}...")
                else:
                    click.echo(f"   📄 Result: {str(result)[:100]}...")
            
            results.append(True)
        else:
            click.echo(f"   ❌ Failed")
            click.echo(f"   📄 Error: {response}")
            results.append(False)
    
    # Summary
    click.echo("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        click.echo(f"🎉 All {total} tests passed!")
        sys.exit(0)
    else:
        click.echo(f"⚠️  {passed}/{total} tests passed")
        sys.exit(1)


if __name__ == "__main__":
    main()
