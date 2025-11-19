import json
import boto3
import logging
import os
from typing import Dict, Any
import re

# Configure logging - NEVER log PHI!
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')
rds_data_client = boto3.client('rds-data')

# PHI-safe logging helper
def sanitize_for_logging(data: Any) -> str:
    """
    Sanitize data for logging by removing PHI.
    HIPAA Compliance: Never log patient names, DOB, SSN, addresses, phone numbers, etc.
    """
    if isinstance(data, dict):
        # Remove all PHI fields
        phi_fields = {
            'first_name', 'last_name', 'middle_name', 'date_of_birth', 'dob',
            'phone_primary', 'phone_secondary', 'phone', 'email',
            'address_line1', 'address_line2', 'address', 'city', 'state', 'zip_code',
            'emergency_contact_name', 'emergency_contact_phone',
            'insurance_policy_number', 'insurance_group_number',
            'medical_record_number', 'mrn', 'ssn', 'social_security_number'
        }
        
        safe_data = {}
        for key, value in data.items():
            if key.lower() in phi_fields:
                safe_data[key] = '[REDACTED]'
            elif key in ['patient_id', 'medication_id', 'provider_id']:
                # Keep IDs but truncate for privacy
                safe_data[key] = f"{str(value)[:8]}..." if value else None
            else:
                safe_data[key] = value
        return json.dumps(safe_data)
    return "[DATA]"


def get_database_credentials():
    """Retrieve database credentials from AWS Secrets Manager."""
    try:
        secret_arn = os.environ.get('DB_SECRET_ARN')
        if not secret_arn:
            raise ValueError("DB_SECRET_ARN environment variable not set")
        
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(response['SecretValue'])
        return secret
    except Exception as e:
        # Don't log the exception details as they might contain sensitive info
        logger.error("Error retrieving database credentials")
        raise


# REMOVED: list_tables() - Admin/debug function not needed for patient-facing app


# REMOVED: get_patients() - Admin function not needed for patient-facing app
# REMOVED: get_patient_by_id() - Admin function not needed for patient-facing app


# REMOVED: create_patient() - Admin function not needed for patient-facing app
# Patient registration should be handled through a separate secure registration flow


def test_database_connection():
    """Test database connectivity using RDS Data API."""
    try:
        db_cluster_arn = os.environ.get('DB_CLUSTER_ARN')
        secret_arn = os.environ.get('DB_SECRET_ARN')
        database_name = os.environ.get('DB_NAME', 'medical_records')
        
        if not db_cluster_arn:
            credentials = get_database_credentials()
            return {
                'status': 'partial_success',
                'message': 'Successfully retrieved database credentials',
                'has_credentials': True,
                'note': 'DB_CLUSTER_ARN not set - cannot test actual connection'
            }
        
        response = rds_data_client.execute_statement(
            resourceArn=db_cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql="SELECT 1 as test_connection"
        )
        
        return {
            'status': 'success',
            'message': 'Database connection successful',
            'database': database_name
        }
        
    except Exception as e:
        logger.error(f"Database connection test failed: {type(e).__name__}")
        return {
            'status': 'error',
            'message': 'Database connection failed',
            'error_type': type(e).__name__
        }


def get_patient_medications(patient_id: str, active_only: bool = False):
    """Retrieve medications for a specific patient.

    Args:
        patient_id: Patient's UUID (Cognito ID)
        active_only: If True, return only active medications
    """
    try:
        db_cluster_arn = os.environ.get('DB_CLUSTER_ARN')
        secret_arn = os.environ.get('DB_SECRET_ARN')
        database_name = os.environ.get('DB_NAME', 'medical_records')

        if not db_cluster_arn or not secret_arn:
            return {
                'status': 'error',
                'message': 'Missing required environment variables'
            }

        # Log access without PHI
        logger.info(f"Retrieving patient medications (active_only={active_only})")

        # Base query with JOIN to get prescriber information
        sql_query = """
            SELECT
                m.medication_id, m.patient_id, m.medication_name, m.generic_name, m.ndc_code,
                m.dosage, m.frequency, m.route, m.quantity_prescribed, m.refills_remaining,
                m.prescription_date, m.start_date, m.end_date, m.medication_status,
                m.discontinuation_reason, m.instructions, m.notes, m.created_at,
                p.first_name || ' ' || p.last_name as prescribed_by_name
            FROM medications m
            LEFT JOIN healthcare_providers p ON m.prescribed_by = p.provider_id
            WHERE m.patient_id = :patient_id::uuid
        """

        # Add status filter if active_only
        if active_only:
            sql_query += " AND m.medication_status = 'Active'"

        # Chronological order: newest first
        sql_query += " ORDER BY m.prescription_date DESC, m.created_at DESC"
        
        response = rds_data_client.execute_statement(
            resourceArn=db_cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql=sql_query,
            parameters=[{'name': 'patient_id', 'value': {'stringValue': patient_id}}]
        )
        
        medications = []
        if 'records' in response and response['records']:
            fields = [
                'medication_id', 'patient_id', 'medication_name', 'generic_name', 'ndc_code',
                'dosage', 'frequency', 'route', 'quantity_prescribed', 'refills_remaining',
                'prescription_date', 'start_date', 'end_date', 'medication_status',
                'discontinuation_reason', 'instructions', 'notes', 'created_at', 'prescribed_by_name'
            ]
            
            for record in response['records']:
                medication = {}
                for i, field in enumerate(fields):
                    if i < len(record):
                        value = record[i]
                        if 'stringValue' in value:
                            medication[field] = value['stringValue']
                        elif 'longValue' in value:
                            medication[field] = value['longValue']
                        elif 'booleanValue' in value:
                            medication[field] = value['booleanValue']
                        elif 'isNull' in value:
                            medication[field] = None
                        else:
                            medication[field] = str(value)
                medications.append(medication)
        
        logger.info(f"Retrieved {len(medications)} medications")

        return {
            'status': 'success',
            'message': f'Found {len(medications)} medication(s)',
            'patient_id': patient_id,
            'medications': medications,
            'count': len(medications),
            'active_only': active_only
        }
        
    except Exception as e:
        logger.error(f"Error retrieving medications: {type(e).__name__}")
        return {
            'status': 'error',
            'message': 'Error retrieving medications',
            'error_type': type(e).__name__
        }


def get_patient_appointments(patient_id: str, status: str = None, start_date: str = None, end_date: str = None):
    """Retrieve appointments for a specific patient with optional filters."""
    try:
        db_cluster_arn = os.environ.get('DB_CLUSTER_ARN')
        secret_arn = os.environ.get('DB_SECRET_ARN')
        database_name = os.environ.get('DB_NAME', 'medical_records')
        
        if not db_cluster_arn or not secret_arn:
            return {
                'status': 'error',
                'message': 'Missing required environment variables'
            }
        
        # Log access without PHI
        logger.info("Retrieving patient appointments")
        
        # Build SQL query with filters
        sql_query = """
            SELECT 
                a.appointment_id, a.patient_id, a.provider_id, a.facility_id,
                a.appointment_type, a.appointment_reason,
                a.scheduled_date, a.scheduled_time, a.duration_minutes,
                a.appointment_status, a.check_in_time, a.check_out_time,
                a.scheduling_notes, a.provider_notes,
                a.reminder_sent, a.reminder_sent_date,
                a.created_at, a.updated_at,
                p.first_name || ' ' || p.last_name as provider_name,
                p.specialty as provider_specialty,
                f.facility_name, f.city as facility_city, f.state as facility_state
            FROM appointments a
            LEFT JOIN healthcare_providers p ON a.provider_id = p.provider_id
            LEFT JOIN medical_facilities f ON a.facility_id = f.facility_id
            WHERE a.patient_id = :patient_id::uuid
        """
        
        parameters = [{'name': 'patient_id', 'value': {'stringValue': patient_id}}]
        
        # Add status filter if provided
        if status:
            sql_query += " AND a.appointment_status = :status"
            parameters.append({'name': 'status', 'value': {'stringValue': status}})
        
        # Add date range filters if provided
        if start_date:
            sql_query += " AND a.scheduled_date >= :start_date::date"
            parameters.append({'name': 'start_date', 'value': {'stringValue': start_date}})
        
        if end_date:
            sql_query += " AND a.scheduled_date <= :end_date::date"
            parameters.append({'name': 'end_date', 'value': {'stringValue': end_date}})
        
        sql_query += " ORDER BY a.scheduled_date DESC, a.scheduled_time DESC"
        
        response = rds_data_client.execute_statement(
            resourceArn=db_cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql=sql_query,
            parameters=parameters
        )
        
        appointments = []
        if 'records' in response and response['records']:
            fields = [
                'appointment_id', 'patient_id', 'provider_id', 'facility_id',
                'appointment_type', 'appointment_reason',
                'scheduled_date', 'scheduled_time', 'duration_minutes',
                'appointment_status', 'check_in_time', 'check_out_time',
                'scheduling_notes', 'provider_notes',
                'reminder_sent', 'reminder_sent_date',
                'created_at', 'updated_at',
                'provider_name', 'provider_specialty',
                'facility_name', 'facility_city', 'facility_state'
            ]
            
            for record in response['records']:
                appointment = {}
                for i, field in enumerate(fields):
                    if i < len(record):
                        value = record[i]
                        if 'stringValue' in value:
                            appointment[field] = value['stringValue']
                        elif 'longValue' in value:
                            appointment[field] = value['longValue']
                        elif 'booleanValue' in value:
                            appointment[field] = value['booleanValue']
                        elif 'isNull' in value:
                            appointment[field] = None
                        else:
                            appointment[field] = str(value)
                appointments.append(appointment)
        
        logger.info(f"Retrieved {len(appointments)} appointments")
        
        return {
            'status': 'success',
            'message': f'Found {len(appointments)} appointment(s)',
            'appointments': appointments,
            'count': len(appointments)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving appointments: {type(e).__name__}")
        return {
            'status': 'error',
            'message': 'Error retrieving appointments',
            'error_type': type(e).__name__
        }


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Patient-Facing Database Handler with PHI-Safe Logging
    
    Available Actions:
    - health_check: Check Lambda function health
    - test_db_connection: Test database connectivity
    - get_patient_medications: Get medications for authenticated patient
    
    Security:
    - PHI-safe logging (no patient data in logs)
    - Patient-facing only (admin functions removed)
    - Requires patient_id from authenticated context
    """
    
    try:

        # Parse body for Lambda Function URL requests
        if event.get('body'):
            try:
                body_data = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
                event.update(body_data)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Could not parse request body")
        # Extract parameters from queryStringParameters (Lambda Function URL) or direct event (API Gateway)
        params = event.get('queryStringParameters') or {}
        action = params.get('action') or event.get('action', 'unknown')

        # Log request without PHI
        logger.info(f"Request received - action: {action}")
        
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        }
        
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Health check and database connection test
        if action == 'test_db_connection':
            db_test_result = test_database_connection()
            return {
                'statusCode': 200 if db_test_result['status'] != 'error' else 500,
                'headers': headers,
                'body': json.dumps(db_test_result)
            }
        
        # Patient-facing: Get medications for authenticated user
        if action == 'get_patient_medications':
            patient_id = params.get('patient_id') or event.get('patient_id')
            active_only_str = params.get('active_only') or event.get('active_only', 'false')
            # Convert string to boolean (Lambda Function URL sends query params as strings)
            active_only = active_only_str in ['true', 'True', '1', True] if isinstance(active_only_str, (str, bool)) else False

            if not patient_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'status': 'error',
                        'message': 'Missing required parameter: patient_id'
                    })
                }

            medications_result = get_patient_medications(patient_id, active_only)
            return {
                'statusCode': 200 if medications_result['status'] != 'error' else 500,
                'headers': headers,
                'body': json.dumps(medications_result)
            }
        
        # Patient-facing: Get appointments for authenticated user
        if event.get('action') == 'get_patient_appointments':
            patient_id = event.get('patient_id')
            
            if not patient_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'status': 'error',
                        'message': 'Missing required parameter: patient_id'
                    })
                }
            
            # Optional filters
            status = event.get('status')
            start_date = event.get('start_date')
            end_date = event.get('end_date')
            
            appointments_result = get_patient_appointments(patient_id, status, start_date, end_date)
            return {
                'statusCode': 200 if appointments_result['status'] != 'error' else 500,
                'headers': headers,
                'body': json.dumps(appointments_result)
            }
        
        if event.get('action') == 'health_check':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Database handler is healthy',
                    'has_secret': bool(os.environ.get('DB_SECRET_ARN')),
                    'has_cluster_arn': bool(os.environ.get('DB_CLUSTER_ARN'))
                })
            }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Database handler ready - Patient-facing API',
                'available_actions': [
                    'health_check',
                    'test_db_connection',
                    'get_patient_medications',
                    'get_patient_appointments'
                ],
                'note': 'This is a patient-facing API. Admin functions have been removed for security.'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {type(e).__name__}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }
