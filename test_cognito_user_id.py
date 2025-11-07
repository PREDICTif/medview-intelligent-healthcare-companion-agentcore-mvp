#!/usr/bin/env python3
"""
Test script to verify Cognito user ID extraction in production

This script helps you verify that the AgentCore runtime is correctly
extracting and using Cognito user IDs from authenticated requests.
"""

import boto3
import json
import time
from datetime import datetime, timedelta

def check_cloudwatch_logs_for_user_id():
    """
    Check CloudWatch logs to see if Cognito user IDs are being extracted
    """
    print("🔍 Checking CloudWatch Logs for Cognito User ID Extraction")
    print("=" * 70)
    
    logs_client = boto3.client('logs', region_name='us-east-1')
    
    # The log group name for AgentCore runtime (note: runtimes plural, with -DEFAULT suffix)
    log_group_name = '/aws/bedrock-agentcore/runtimes/strands_agent-7xbjvREebP-DEFAULT'
    
    try:
        # Query logs from the last 30 minutes
        start_time = int((datetime.now() - timedelta(minutes=30)).timestamp() * 1000)
        end_time = int(datetime.now().timestamp() * 1000)
        
        print(f"📅 Searching logs from last 30 minutes...")
        print(f"   Log Group: {log_group_name}")
        
        # Start a query to find user ID extraction logs
        query = """
        fields @timestamp, @message
        | filter @message like /Extracting user ID from context/
            or @message like /Using Cognito user ID/
            or @message like /actor_id/
        | sort @timestamp desc
        | limit 20
        """
        
        response = logs_client.start_query(
            logGroupName=log_group_name,
            startTime=start_time,
            endTime=end_time,
            queryString=query
        )
        
        query_id = response['queryId']
        print(f"🔄 Query started: {query_id}")
        print("   Waiting for results...")
        
        # Wait for query to complete
        max_attempts = 10
        for attempt in range(max_attempts):
            time.sleep(2)
            result = logs_client.get_query_results(queryId=query_id)
            
            if result['status'] == 'Complete':
                print(f"✅ Query completed!\n")
                
                if not result['results']:
                    print("⚠️  No logs found with user ID extraction")
                    print("\n💡 This could mean:")
                    print("   1. No users have made requests in the last 30 minutes")
                    print("   2. Users haven't logged in yet")
                    print("   3. The agent hasn't been invoked recently")
                    return False
                
                print(f"📋 Found {len(result['results'])} log entries:\n")
                
                found_cognito_id = False
                for i, log_entry in enumerate(result['results'], 1):
                    timestamp = None
                    message = None
                    
                    for field in log_entry:
                        if field['field'] == '@timestamp':
                            timestamp = field['value']
                        elif field['field'] == '@message':
                            message = field['value']
                    
                    print(f"{i}. [{timestamp}]")
                    print(f"   {message}")
                    
                    # Check if this log shows a Cognito user ID
                    if 'Using Cognito user ID' in message:
                        found_cognito_id = True
                        # Extract the user ID from the message
                        if 'sub):' in message:
                            user_id = message.split('sub):')[-1].strip()
                            print(f"   ✅ COGNITO USER ID FOUND: {user_id}")
                    
                    print()
                
                if found_cognito_id:
                    print("🎉 SUCCESS! Cognito user IDs are being extracted correctly!")
                    return True
                else:
                    print("⚠️  Logs found but no Cognito user IDs detected")
                    print("   Users might be using session-based fallback")
                    return False
            
            elif result['status'] == 'Failed':
                print(f"❌ Query failed: {result.get('statistics', {})}")
                return False
            
            print(f"   Still running... (attempt {attempt + 1}/{max_attempts})")
        
        print("⏱️  Query timed out")
        return False
        
    except logs_client.exceptions.ResourceNotFoundException:
        print(f"❌ Log group not found: {log_group_name}")
        print("   The agent might not have been invoked yet")
        return False
    except Exception as e:
        print(f"❌ Error querying logs: {e}")
        return False

def check_memory_usage():
    """
    Check if memory is being used with proper user IDs
    """
    print("\n🧠 Checking Memory Usage with User IDs")
    print("=" * 70)
    
    ssm = boto3.client('ssm', region_name='us-east-1')
    
    try:
        # Get memory ID
        response = ssm.get_parameter(Name="/app/medicalassistant/agentcore/memory_id")
        memory_id = response['Parameter']['Value']
        print(f"✅ Memory ID found: {memory_id}")
        
        # Check if memory is being used
        print("\n💡 To verify memory is working with user IDs:")
        print("   1. Log in to the web interface")
        print("   2. Have a conversation with the agent")
        print("   3. Log out and log back in")
        print("   4. Ask the agent about your previous conversation")
        print("   5. If it remembers, memory is working with your Cognito user ID!")
        
        return True
        
    except ssm.exceptions.ParameterNotFound:
        print("⚠️  Memory ID not configured")
        print("   Memory integration might not be set up")
        return False
    except Exception as e:
        print(f"❌ Error checking memory: {e}")
        return False

def test_with_web_interface():
    """
    Provide instructions for testing via web interface
    """
    print("\n🌐 Testing via Web Interface")
    print("=" * 70)
    
    print("Follow these steps to verify Cognito user ID extraction:\n")
    
    print("1️⃣  Open the web interface:")
    print("   https://d1kg75xyopexst.cloudfront.net\n")
    
    print("2️⃣  Sign up or log in with Cognito:")
    print("   - Create a new account or use existing credentials")
    print("   - Cognito will generate a unique user ID (sub)\n")
    
    print("3️⃣  Send a test message:")
    print("   Example: 'Hello, what can you help me with?'\n")
    
    print("4️⃣  Check CloudWatch logs:")
    print("   Run this script again to see if your Cognito user ID appears\n")
    
    print("5️⃣  Test memory persistence:")
    print("   - Have a conversation")
    print("   - Log out")
    print("   - Log back in")
    print("   - Ask: 'What did we talk about earlier?'")
    print("   - If it remembers, your Cognito user ID is working!\n")
    
    print("6️⃣  Verify in logs:")
    print("   Look for log entries like:")
    print("   '✅ Using Cognito user ID (sub): 12345678-1234-1234-1234-123456789abc'\n")

def check_cognito_configuration():
    """
    Verify Cognito is properly configured
    """
    print("\n🔐 Checking Cognito Configuration")
    print("=" * 70)
    
    cf_client = boto3.client('cloudformation', region_name='us-east-1')
    
    try:
        # Get AgentCoreAuth stack outputs
        response = cf_client.describe_stacks(StackName='AgentCoreAuth')
        outputs = response['Stacks'][0]['Outputs']
        
        user_pool_id = None
        client_id = None
        
        for output in outputs:
            if output['OutputKey'] == 'UserPoolId':
                user_pool_id = output['OutputValue']
            elif output['OutputKey'] == 'UserPoolClientId':
                client_id = output['OutputValue']
        
        if user_pool_id and client_id:
            print(f"✅ Cognito User Pool: {user_pool_id}")
            print(f"✅ Client ID: {client_id}")
            
            # Check if user pool has users
            cognito = boto3.client('cognito-idp', region_name='us-east-1')
            users_response = cognito.list_users(UserPoolId=user_pool_id, Limit=10)
            
            user_count = len(users_response['Users'])
            print(f"✅ Registered users: {user_count}")
            
            if user_count > 0:
                print("\n📋 Sample users (showing sub/username only):")
                for i, user in enumerate(users_response['Users'][:5], 1):
                    username = user['Username']
                    # Find the sub attribute
                    sub = None
                    for attr in user['Attributes']:
                        if attr['Name'] == 'sub':
                            sub = attr['Value']
                            break
                    
                    print(f"   {i}. Username: {username}")
                    if sub:
                        print(f"      Cognito Sub: {sub}")
                print()
            else:
                print("\n⚠️  No users registered yet")
                print("   Sign up at: https://d1kg75xyopexst.cloudfront.net\n")
            
            return True
        else:
            print("❌ Could not find Cognito configuration")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Cognito: {e}")
        return False

def main():
    """
    Main test function
    """
    print("\n" + "=" * 70)
    print("🧪 COGNITO USER ID EXTRACTION TEST")
    print("=" * 70)
    print()
    
    # Check Cognito configuration
    cognito_ok = check_cognito_configuration()
    
    # Check CloudWatch logs
    logs_ok = check_cloudwatch_logs_for_user_id()
    
    # Check memory configuration
    memory_ok = check_memory_usage()
    
    # Provide web interface testing instructions
    test_with_web_interface()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"Cognito Configuration: {'✅ OK' if cognito_ok else '❌ ISSUE'}")
    print(f"CloudWatch Logs:       {'✅ OK' if logs_ok else '⚠️  NO DATA'}")
    print(f"Memory Configuration:  {'✅ OK' if memory_ok else '⚠️  NOT SET'}")
    print()
    
    if logs_ok:
        print("🎉 SUCCESS! Cognito user IDs are being extracted correctly!")
    elif cognito_ok:
        print("💡 Cognito is configured but no user activity detected yet.")
        print("   Try logging in and sending a message, then run this test again.")
    else:
        print("⚠️  Please check the configuration and try again.")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
