#!/usr/bin/env python3
"""
Setup OAuth for AgentCore Gateway.
Creates a machine-to-machine client in Cognito for gateway authentication.
"""

import boto3
import click
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_ssm_parameter, put_ssm_parameter, get_aws_region

REGION = get_aws_region()


def create_machine_client():
    """Create a machine-to-machine OAuth client in Cognito"""
    
    cognito = boto3.client('cognito-idp', region_name=REGION)
    ssm = boto3.client('ssm', region_name=REGION)
    
    # Get user pool ID
    user_pool_id = 'us-east-1_GReO412Ab'  # agentcore-users pool
    
    click.echo(f"🔐 Setting up OAuth for Gateway")
    click.echo(f"User Pool: {user_pool_id}\n")
    
    # Create machine-to-machine client
    client_name = 'gateway-machine-client'
    
    try:
        click.echo(f"Creating OAuth client: {client_name}")
        
        response = cognito.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName=client_name,
            GenerateSecret=True,  # Required for client_credentials flow
            ExplicitAuthFlows=[],  # No user auth flows
            AllowedOAuthFlows=['client_credentials'],
            AllowedOAuthScopes=[],  # No custom scopes for now
            AllowedOAuthFlowsUserPoolClient=True,
            SupportedIdentityProviders=['COGNITO']
        )
        
        client_id = response['UserPoolClient']['ClientId']
        client_secret = response['UserPoolClient']['ClientSecret']
        
        click.echo(f"✅ Created client: {client_id}")
        
    except Exception as e:
        error_msg = str(e)
        if 'already exists' in error_msg.lower() or 'ResourceConflictException' in error_msg:
            click.echo(f"⚠️  Client '{client_name}' already exists, looking it up...")
            
            # List clients to find it
            clients = cognito.list_user_pool_clients(
                UserPoolId=user_pool_id,
                MaxResults=60
            )
            
            found = False
            for client in clients['UserPoolClients']:
                if client['ClientName'] == client_name:
                    client_id = client['ClientId']
                    
                    # Get client details (including secret)
                    client_details = cognito.describe_user_pool_client(
                        UserPoolId=user_pool_id,
                        ClientId=client_id
                    )
                    
                    client_secret = client_details['UserPoolClient'].get('ClientSecret')
                    
                    if client_secret:
                        click.echo(f"✅ Found existing client: {client_id}")
                        found = True
                        break
                    else:
                        click.echo("❌ Existing client doesn't have a secret (public client)")
                        click.echo("Please delete it manually and run this script again")
                        sys.exit(1)
            
            if not found:
                click.echo("❌ Could not find existing client")
                sys.exit(1)
        else:
            click.echo(f"❌ Error creating client: {e}")
            sys.exit(1)
    
    # Store in SSM
    put_ssm_parameter('/app/medicalassistant/agentcore/gateway_client_id', client_id)
    put_ssm_parameter('/app/medicalassistant/agentcore/gateway_client_secret', client_secret, with_encryption=True)
    put_ssm_parameter('/app/medicalassistant/agentcore/userpool_id', user_pool_id)
    
    # Get token endpoint
    discovery_url = f"https://cognito-idp.{REGION}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
    token_endpoint = f"https://agentcore-users.auth.{REGION}.amazoncognito.com/oauth2/token"
    
    put_ssm_parameter('/app/medicalassistant/agentcore/token_endpoint', token_endpoint)
    
    click.echo("\n✅ OAuth configuration complete!")
    click.echo(f"\nClient ID: {client_id}")
    click.echo(f"Client Secret: {client_secret[:10]}...")
    click.echo(f"Token Endpoint: {token_endpoint}")
    click.echo(f"\nConfiguration saved to SSM Parameter Store")
    
    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'token_endpoint': token_endpoint,
        'discovery_url': discovery_url
    }


@click.command()
def main():
    """Setup OAuth for AgentCore Gateway"""
    config = create_machine_client()
    
    click.echo("\n" + "="*60)
    click.echo("🎉 Setup complete!")
    click.echo("\nYou can now test the gateway with:")
    click.echo("  python test_gateway_oauth.py")
    click.echo("="*60)


if __name__ == "__main__":
    main()
