"""
BDA Data Extraction Lambda Function
Extracts and processes data from S3 buckets and medical database
"""

import json
import boto3
import logging
import os
from typing import Dict, Any
from botocore.config import Config
from helper import get_blueprint, create_blueprint, create_extraction_project, invoke_bda, ArgsException, ExtractionException, wait_for_bda_job, create_input_s3_uri, create_output_s3_uri, get_results_uri, process_results, write_results_to_s3, TransformException
# from django.utils.timezone import now
from datetime import datetime, timezone

now = datetime.now(timezone.utc)
now_date = now.strftime('%Y%m%d')
# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
rds_data_client = boto3.client('rds-data')
secrets_client = boto3.client('secretsmanager')

# Environment variables

DB_CLUSTER_ARN = os.environ.get('DB_CLUSTER_ARN')
DB_SECRET_ARN = os.environ.get('DB_SECRET_ARN')
DB_NAME = os.environ.get('DB_NAME', 'medical_records')

configuration = Config(
    connect_timeout = 300,
    read_timeout = 300
)

sts_client = boto3.client(service_name='sts')
account_id = sts_client.get_caller_identity()['Account']

bedrock_data_automation_client = boto3.client(service_name='bedrock-data-automation', region_name='us-east-1')
bedrock_data_automation_runtime_client = boto3.client(service_name="bedrock-data-automation-runtime", region_name="us-east-1")
s3_client = boto3.client(service_name="s3", region_name="us-east-1")

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    BDA Data Extraction Lambda Handler
    
    Processes data extraction requests from S3 and database
    """
    try:
        logger.info(f"BDA Data Extraction started")
        logger.info(f"Event: {json.dumps(event)}")
        print(f"Event: {json.dumps(event)}")
        
        # Get patient_id from event (Cognito user ID)
        patient_id = event.get('patient_id', 'ssdudu8y7wkdkdiid')  # Default for testing
        medical_document_type = event.get('medical_document_type', 'Prescription')
        
        current_date = now.strftime("%Y-%m-%d")
        processed_data_bucket = os.getenv("PROCESSED_BUCKET", None)
        bucket_doc_prefix = "medical_documents"
        raw_data_bucket = os.getenv("RAW_BUCKET", None)
        
        # Initial URIs for folder paths
        input_folder_uri = f"s3://{raw_data_bucket}/{bucket_doc_prefix}/{medical_document_type}/{patient_id}/{now_date}/"
        output_s3_uri = f"s3://{processed_data_bucket}/{bucket_doc_prefix}/{medical_document_type}/{patient_id}/{now_date}/"
        print(f"Input folder URI: {input_folder_uri}")
        print(f"Output S3 URI: {output_s3_uri}")

        temp_dir = "/tmp"
        print(f"Rawbucket: {raw_data_bucket}")
        print(f"Processedbucket: {processed_data_bucket}")

        # Verify input S3 path has files and get the first file
        print(f"=== VERIFYING S3 ACCESS ===")
        input_file_key = None
        try:
            # Parse S3 URI
            input_bucket = raw_data_bucket
            input_prefix = f"{bucket_doc_prefix}/{medical_document_type}/{patient_id}/{now_date}/"
            
            # List objects in input path
            list_response = s3_client.list_objects_v2(
                Bucket=input_bucket,
                Prefix=input_prefix
            )
            
            if 'Contents' in list_response:
                # Filter out folder markers (0 byte objects ending with /)
                files = [obj for obj in list_response['Contents'] if obj['Size'] > 0 and not obj['Key'].endswith('/')]
                print(f"Found {len(files)} files in input path:")
                for obj in files:
                    print(f"  - {obj['Key']} (size: {obj['Size']} bytes)")
                
                if files:
                    # Use the first actual file
                    input_file_key = files[0]['Key']
                    print(f"Will process file: {input_file_key}")
                else:
                    raise Exception("No valid files found in input path (only folders or empty files)")
            else:
                raise Exception(f"No files found in input path: s3://{input_bucket}/{input_prefix}")
            
        except Exception as s3_ex:
            print(f"S3 verification error: {str(s3_ex)}")
            raise
        print(f"=== END S3 VERIFICATION ===")

        blueprint = get_blueprint("prescription-label")
        uploaded_blueprint = create_blueprint(bedrock_data_automation_client, blueprint)

        print(f"Blueprint: {uploaded_blueprint}")

        project_arn = create_extraction_project(bedrock_data_automation_client, uploaded_blueprint)
        
        print(f"Project ARN created: {project_arn}")

        # Use the specific file path, not folder path
        input_s3_uri = f"s3://{raw_data_bucket}/{input_file_key}"
        print(f"Processing file: {input_s3_uri}")

        invocation_arn = invoke_bda(bedrock_data_automation_runtime_client, input_s3_uri, output_s3_uri, account_id, project_arn)

        status_response = wait_for_bda_job(bedrock_data_automation_runtime_client, invocation_arn)

        results_s3_uri = get_results_uri(s3_client, status_response["outputConfiguration"]["s3Uri"], temp_dir)

        processed_results = process_results(s3_client, results_s3_uri, temp_dir)

        output_s3_uri = write_results_to_s3(s3_client, processed_data_bucket, bucket_doc_prefix, patient_id, temp_dir, processed_results)

        # Insert prescription data into RDS if patient_id is provided
        if patient_id and processed_results:
            # Log the processed results structure for debugging
            print(f"=== PROCESSED RESULTS FOR DB INSERT ===")
            print(f"Processed results keys: {list(processed_results.keys())}")
            print(f"Full processed results: {json.dumps(processed_results, indent=2, default=str)[:2000]}")
            print(f"=== END PROCESSED RESULTS ===")
            
            # Insert prescription data into RDS
            try:
                insert_medication_to_rds(
                    rds_data_client,
                    DB_CLUSTER_ARN,
                    DB_SECRET_ARN,
                    DB_NAME,
                    patient_id,
                    processed_results
                )
                print(f"Successfully inserted medication data for patient: {patient_id}")
            except Exception as db_ex:
                print(f"Failed to insert to database: {str(db_ex)}")
                # Don't fail the whole request if DB insert fails
        
        return {
            "statusCode": 200,
            "body": json.dumps({ 
                "outputS3Uri": output_s3_uri,
                "patient_id": patient_id,
                "message": "Prescription data extracted and stored successfully"
            })
        }
    except ArgsException as ex:
        print(str(ex))
        return {
            "statusCode": 400,
            "body": json.dumps({ "errorMessage": f"Error during init." })
        }
    except ExtractionException as ex:
        print(str(ex))
        return {
            "statusCode": 500,
            "body": json.dumps({ "errorMessage": f"Extraction error during execution." })
        }
    except TransformException as ex:
        print(str(ex))
        return {
            "statusCode": 500,
            "body": json.dumps({ "errorMessage": f"Error processing results." })
        }
    except Exception as ex:
        print(str(ex))
        return {
            "statusCode": 500,
            "body": json.dumps({ "errorMessage": "Unexpected error occurred during execution." })
        }
        # # Determine the action to perform
        # action = event.get('action', 'extract')
        
        # if action == 'extract_from_s3':
        #     return extract_from_s3(event)
        # elif action == 'extract_from_db':
        #     return extract_from_db(event)
        # elif action == 'process_data':
        #     return process_data(event)
        # elif action == 'health_check':
        #     return health_check()
        # else:
        #     return {
        #         'statusCode': 200,
        #         'body': json.dumps({
        #             'message': 'BDA Data Extraction Lambda is ready',
        #             'available_actions': [
        #                 'extract_from_s3',
        #                 'extract_from_db',
        #                 'process_data',
        #                 'health_check'
        #             ],
        #             'buckets': {
        #                 'raw': RAW_BUCKET,
        #                 'processed': PROCESSED_BUCKET,
        #                 'curated': CURATED_BUCKET
        #             }
        #         })
        #     }
            
    # except Exception as e:
    #     logger.error(f"Error in BDA data extraction: {str(e)}")
    #     return {
    #         'statusCode': 500,
    #         'body': json.dumps({
    #             'error': 'Internal server error',
    #             'message': str(e)
    #         })
    #     }



def insert_medication_to_rds(rds_client, cluster_arn: str, secret_arn: str, database: str, patient_id: str, prescription_data: dict):
    """
    Insert extracted prescription data into the medications table in RDS
    Maps BDA output to the existing medications table schema
    """
    try:
        # Extract from inference_result which contains the actual extracted data
        inference_result = prescription_data.get('inference_result', {})
        
        # Get the nested objects
        prescription_details = inference_result.get('prescrription_details', {})
        prescription_date_obj = inference_result.get('prescription_details', {})
        pharmacy_details = inference_result.get('pharmacy_details', {})
        customer_details = inference_result.get('customer_details', {})
        
        # Helper function to safely get values (handles empty strings)
        def get_value(data, key, default=None):
            if not data:
                return default
            val = data.get(key, default)
            # Treat empty strings as None
            if val == '':
                return default
            return val
        
        # Extract medication values from BDA output
        prescribed_medication = get_value(prescription_details, 'prescribed_medication')
        quantity_str = get_value(prescription_details, 'prescription_quantity')
        frequency = get_value(prescription_details, 'intake_fequency')
        route = get_value(prescription_details, 'intake_method')
        prescription_date = get_value(prescription_date_obj, 'prescription_date')
        
        # Parse medication name and dosage from prescribed_medication
        # Format is typically: "300 MG PILLNAMELOL" or just "PILLNAMELOL"
        medication_name = prescribed_medication
        dosage = None
        
        if prescribed_medication:
            # Try to extract dosage pattern like "300 MG" or "10 ML"
            import re
            dosage_match = re.search(r'(\d+\s*(?:MG|ML|MCG|G|L|UNITS?))', prescribed_medication, re.IGNORECASE)
            if dosage_match:
                dosage = dosage_match.group(1).strip()
                # Remove dosage from medication name to get clean name
                medication_name = prescribed_medication.replace(dosage_match.group(0), '').strip()
        
        # Parse quantity as integer
        try:
            quantity_prescribed = int(quantity_str) if quantity_str else None
        except (ValueError, TypeError):
            quantity_prescribed = None
            print(f"Warning: Could not parse quantity '{quantity_str}' as integer")
        
        # Parse refills info
        allows_refills = prescription_details.get('allows_refills', False)
        # If refills are allowed but we don't know the count, assume 1 refill remaining
        # If no refills, set to 0
        refills_remaining = 1 if allows_refills else 0
        
        # Build notes from extracted data
        notes_parts = []
        
        prescribed_by_text = get_value(prescription_details, 'prescribed_by')
        if prescribed_by_text:
            notes_parts.append(f"Prescribed by: {prescribed_by_text}")
        
        expiration = get_value(prescription_details, 'expiration_date')
        if expiration:
            notes_parts.append(f"Expiration: {expiration}")
            
        needs_auth = prescription_details.get('needs_dr_authorization_for_refills', False)
        if needs_auth:
            notes_parts.append("Requires doctor authorization for refills")
        
        # Add pharmacy info to notes
        pharmacy_name = get_value(pharmacy_details, 'pharmacy_name')
        if pharmacy_name:
            notes_parts.append(f"Pharmacy: {pharmacy_name}")
        
        rx_number = get_value(pharmacy_details, 'Rx_number')
        if rx_number:
            notes_parts.append(f"Rx#: {rx_number}")
        
        # Add customer info to notes
        customer_name = get_value(customer_details, 'customer_name')
        if customer_name:
            notes_parts.append(f"Patient name on label: {customer_name}")
        
        notes = "; ".join(notes_parts) if notes_parts else None
        
        print(f"=== EXTRACTED VALUES FOR DB ===")
        print(f"Medication: {medication_name}")
        print(f"Dosage: {dosage}")
        print(f"Quantity prescribed: {quantity_prescribed}")
        print(f"Frequency: {frequency}")
        print(f"Route: {route}")
        print(f"Prescription date: {prescription_date}")
        print(f"Refills remaining: {refills_remaining}")
        print(f"Notes: {notes}")
        print(f"=== END EXTRACTED VALUES ===")
        
        # Build the SQL INSERT statement matching the actual schema
        sql = """
        INSERT INTO medications (
            patient_id,
            medication_name,
            dosage,
            quantity_prescribed,
            frequency,
            route,
            prescription_date,
            refills_remaining,
            medication_status,
            notes,
            created_by,
            created_at,
            updated_at
        ) VALUES (
            :patient_id::uuid,
            :medication_name,
            :dosage,
            :quantity_prescribed,
            :frequency,
            :route,
            :prescription_date::date,
            :refills_remaining,
            'Active',
            :notes,
            :created_by::uuid,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        """
        
        parameters = [
            {'name': 'patient_id', 'value': {'stringValue': patient_id}},
            {'name': 'medication_name', 'value': {'stringValue': medication_name or 'Unknown'}},
            {'name': 'dosage', 'value': {'stringValue': dosage} if dosage else {'isNull': True}},
            {'name': 'quantity_prescribed', 'value': {'longValue': quantity_prescribed} if quantity_prescribed is not None else {'isNull': True}},
            {'name': 'frequency', 'value': {'stringValue': frequency} if frequency else {'isNull': True}},
            {'name': 'route', 'value': {'stringValue': route} if route else {'isNull': True}},
            {'name': 'prescription_date', 'value': {'stringValue': prescription_date} if prescription_date else {'stringValue': str(now.date())}},
            {'name': 'refills_remaining', 'value': {'longValue': refills_remaining}},
            {'name': 'notes', 'value': {'stringValue': notes} if notes else {'isNull': True}},
            {'name': 'created_by', 'value': {'stringValue': patient_id}}  # Using patient_id as created_by for now
        ]
        
        # Execute the SQL statement
        response = rds_client.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database,
            sql=sql,
            parameters=parameters
        )
        
        print(f"Medication inserted successfully. Response: {response}")
        return response
        
    except Exception as ex:
        print(f"Error inserting medication to RDS: {str(ex)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise
