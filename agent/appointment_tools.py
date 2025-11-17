"""
Direct appointment management tools that call the Lambda function directly.
No Gateway, no MCP, no OAuth tokens - just simple Lambda invocations.
"""

import json
import os
import boto3
from strands import tool
from typing import Optional

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name='us-east-1')

# Get Lambda function name from environment
LAMBDA_FUNCTION_NAME = os.environ.get(
    'APPOINTMENT_LAMBDA_FUNCTION_NAME',
    'MihcStack-GatewayLambda679C3A36-lWEbMl7wejem'
)

def invoke_lambda(action: str, parameters: dict) -> dict:
    """Helper function to invoke the appointment Lambda"""
    try:
        payload = {
            'action': action,
            **parameters
        }
        
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        return result
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

@toolits")
def get_appointments(
    patient_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """
    Retrieve patient appointments with optional filters.
    
    Args:
        patient_id: Filter by patient UUID
        provider_id: Filter by provider UUID
        status: Filter by status (Scheduled, Confirmed, Cancelled, Completed, No-Show)
        start_date: Filter from this date (YYYY-MM-DD)
        end_date: Filter until this date (YYYY-MM-DD)
    
    Returns:
        JSON string with appointments list
    """
    params = {}
    if patient_id:
        params['patient_id'] = patient_id
    if provider_id:
        params['provider_id'] = provider_id
    if status:
        params['status'] = status
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    result = invoke_lambda('get_appointments', params)
    
    if result.get('statusCode') == 200:
        body = json.loads(result.get('body', '{}'))
        return json.dumps(body, indent=2)
    else:
        return json.dumps({
            'error': 'Failed to retrieve appointments',
            'details': result
        }, indent=2)

@tool
def create_appointment(
    patient_id: str,
    provider_id: str,
    appointment_date: str,
    created_by: str,
    facility_id: Optional[str] = None,
    duration_minutes: int = 30,
    appointment_type: Optional[str] = None,
    reason_for_visit: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """
    Create a new appointment.
    
    Args:
        patient_id: Patient UUID
        provider_id: Provider UUID
        appointment_date: Date and time (ISO 8601 format)
        created_by: UUID of user creating appointment
        facility_id: Facility UUID (optional)
        duration_minutes: Duration in minutes
        appointment_type: Type (Consultation, Follow-up, etc.)
        reason_for_visit: Reason for visit
        notes: Additional notes
    
    Returns:
        JSON string with created appointment details
    """
    params = {
        'patient_id': patient_id,
        'provider_id': provider_id,
        'appointment_date': appointment_date,
        'created_by': created_by,
        'duration_minutes': duration_minutes
    }
    
    if facility_id:
        params['facility_id'] = facility_id
    if appointment_type:
        params['appointment_type'] = appointment_type
    if reason_for_visit:
        params['reason_for_visit'] = reason_for_visit
    if notes:
        params['notes'] = notes
    
    result = invoke_lambda('create_appointment', params)
    
    if result.get('statusCode') == 200:
        body = json.loads(result.get('body', '{}'))
        return json.dumps(body, indent=2)
    else:
        return json.dumps({
            'error': 'Failed to create appointment',
            'details': result
        }, indent=2)

@tool
def update_appointment(
    appointment_id: str,
    updated_by: str,
    appointment_date: Optional[str] = None,
    appointment_status: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    appointment_type: Optional[str] = None,
    reason_for_visit: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """
    Update an existing appointment.
    
    Args:
        appointment_id: UUID of appointment to update
        updated_by: UUID of user updating
        appointment_date: New date/time
        appointment_status: New status
        duration_minutes: New duration
        appointment_type: New type
        reason_for_visit: Updated reason
        notes: Updated notes
    
    Returns:
        JSON string with updated appointment details
    """
    params = {
        'appointment_id': appointment_id,
        'updated_by': updated_by
    }
    
    if appointment_date:
        params['appointment_date'] = appointment_date
    if appointment_status:
        params['appointment_status'] = appointment_status
    if duration_minutes:
        params['duration_minutes'] = duration_minutes
    if appointment_type:
        params['appointment_type'] = appointment_type
    if reason_for_visit:
        params['reason_for_visit'] = reason_for_visit
    if notes:
        params['notes'] = notes
    
    result = invoke_lambda('update_appointment', params)
    
    if result.get('statusCode') == 200:
        body = json.loads(result.get('body', '{}'))
        return json.dumps(body, indent=2)
    else:
        return json.dumps({
            'error': 'Failed to update appointment',
            'details': result
        }, indent=2)

@tool
def cancel_appointment(
    appointment_id: str,
    cancelled_by: str,
    reason: Optional[str] = None
) -> str:
    """
    Cancel an appointment.
    
    Args:
        appointment_id: UUID of appointment to cancel
        cancelled_by: UUID of user cancelling
        reason: Cancellation reason (optional)
    
    Returns:
        JSON string with cancellation confirmation
    """
    params = {
        'appointment_id': appointment_id,
        'cancelled_by': cancelled_by
    }
    
    if reason:
        params['reason'] = reason
    
    result = invoke_lambda('cancel_appointment', params)
    
    if result.get('statusCode') == 200:
        body = json.loads(result.get('body', '{}'))
        return json.dumps(body, indent=2)
    else:
        return json.dumps({
            'error': 'Failed to cancel appointment',
            'details': result
        }, indent=2)
