#!/usr/bin/env python3
"""
Setup script for AgentCore Gateway integration with patient database
"""

import boto3
import click
from utils import get_aws_region, put_ssm_parameter

def setup_gateway_prerequisites():
    """Set up the required SSM parameters for gateway creation"""
    
    region = get_aws_region()
    
    # Get Lambda function ARN from CloudFormation stack
    cf_client = boto3.client('cloudformation', region_name=region)
    
    try:
        # Get MihcStack outputs
        response = cf_client.describe_stacks(StackName='MihcStack')
        outputs = response['Stacks'][0]['Outputs']
        
        lambda_arn = None
        lambda_url = None
        
        for output in outputs:
            if output['OutputKey'] == 'DatabaseLambdaFunctionArn':
                lambda_arn = output['OutputValue']
            elif output['OutputKey'] == 'DatabaseLambdaFunctionUrl':
                lambda_url = output['OutputValue']
        
        if not lambda_arn:
            click.echo("❌ Could not find DatabaseLambdaFunctionArn in MihcStack outputs")
            return False
            
        # Store Lambda ARN in SSM for gateway creation
        put_ssm_parameter("/app/medicalassistant/agentcore/lambda_arn", lambda_arn)
        click.echo(f"✅ Stored Lambda ARN: {lambda_arn}")
        
        if lambda_url:
            put_ssm_parameter("/app/medicalassistant/agentcore/lambda_url", lambda_url)
            click.echo(f"✅ Stored Lambda URL: {lambda_url}")
        
        # Get Cognito configuration from AgentCoreAuth stack
        try:
            auth_response = cf_client.describe_stacks(StackName='AgentCoreAuth')
            auth_outputs = auth_response['Stacks'][0]['Outputs']
            
            user_pool_id = None
            user_pool_client_id = None
            
            for output in auth_outputs:
                if output['OutputKey'] == 'UserPoolId':
                    user_pool_id = output['OutputValue']
                elif output['OutputKey'] == 'UserPoolClientId':
                    user_pool_client_id = output['OutputValue']
            
            if user_pool_id and user_pool_client_id:
                # Create Cognito discovery URL
                discovery_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
                
                put_ssm_parameter("/app/medicalassistant/agentcore/cognito_discovery_url", discovery_url)
                put_ssm_parameter("/app/medicalassistant/agentcore/machine_client_id", user_pool_client_id)
                
                click.echo(f"✅ Stored Cognito discovery URL: {discovery_url}")
                click.echo(f"✅ Stored Cognito client ID: {user_pool_client_id}")
            
        except Exception as e:
            click.echo(f"⚠️ Could not get Cognito configuration: {e}")
        
        # Create a basic IAM role ARN (this would need to be created separately)
        # For now, we'll use the AgentCore runtime role
        try:
            infra_response = cf_client.describe_stacks(StackName='AgentCoreInfra')
            infra_outputs = infra_response['Stacks'][0]['Outputs']
            
            for output in infra_outputs:
                if output['OutputKey'] == 'RoleArn':
                    role_arn = output['OutputValue']
                    put_ssm_parameter("/app/medicalassistant/agentcore/gateway_iam_role", role_arn)
                    click.echo(f"✅ Stored Gateway IAM role: {role_arn}")
                    break
        except Exception as e:
            click.echo(f"⚠️ Could not get IAM role: {e}")
        
        return True
        
    except Exception as e:
        click.echo(f"❌ Error setting up prerequisites: {e}")
        return False

@click.command()
def main():
    """Set up prerequisites for AgentCore Gateway integration"""
    click.echo("🔧 Setting up AgentCore Gateway prerequisites for patient database...")
    
    if setup_gateway_prerequisites():
        click.echo("\n✅ Prerequisites setup complete!")
        click.echo("\nNext steps:")
        click.echo("1. Run: python scripts/agentcore_gateway.py create --name patient-database-gateway")
        click.echo("2. Add the gateway tools to your medical assistant agent")
    else:
        click.echo("\n❌ Prerequisites setup failed!")

if __name__ == "__main__":
    main()