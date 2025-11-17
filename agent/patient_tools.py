#!/usr/bin/env python3
"""
Patient Database Tools for Medical Assistant Agent
Strands tool implementations for patient database access via AgentCore Gateway
"""

import os
import boto3
import requests
import json
from strands import tool
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

def get_ssm_parameter(parameter_name: str) -> Optional[str]:
    """Get parameter from SSM"""
    try:
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception:
        return None

def get_lambda_url() -> Optional[str]:
    """Get the Lambda Function URL from SSM"""
    return get_ssm_parameter("/app/medicalassistant/agentcore/lambda_url")

def format_patient_summary(patient: Dict[str, Any]) -> str:
    """Format patient data for display in agent responses"""
    try:
        summary = f"**Patient: {patient.get('first_name', 'Unknown')} {patient.get('last_name', 'Unknown')}**\n"
        summary += f"- MRN: {patient.get('medical_record_number', 'N/A')}\n"
        summary += f"- DOB: {patient.get('date_of_birth', 'N/A')}\n"
        summary += f"- Gender: {patient.get('gender', 'N/A')}\n"
        
        if patient.get('phone_primary'):
            summary += f"- Phone: {patient.get('phone_primary')}\n"
            
        if patient.get('email'):
            summary += f"- Email: {patient.get('email')}\n"
            
        if patient.get('city') and patient.get('state'):
            summary += f"- Location: {patient.get('city')}, {patient.get('state')}\n"
        
        return summary
        
    except Exception as e:
        return f"Error formatting patient data: {str(e)}"

@tool
def lookup_patient_record(patient_identifier: str) -> str:
    """
    Look up a specific patient's medical record from the database
    
    Args:
        patient_identifier: Patient ID or Medical Record Number (MRN) to search for
        
    Returns:
        Formatted patient information including medical history, medications, and care details
    """
    try:
        lambda_url = get_lambda_url()
        if not lambda_url:
            return "❌ Patient database is not available. Lambda function not configured."
        
        # Clean the Lambda URL and make action-based request
        base_url = lambda_url.rstrip('/')
        
        # Use action-based approach for Lambda function
        payload = {
            "action": "get_patient_by_id",
            "medical_record_number": patient_identifier
        }
        
        response = requests.post(base_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            patient_data = response.json()
            
            if patient_data.get('status') == 'success' and patient_data.get('patient'):
                patient = patient_data['patient']
                formatted_info = format_patient_summary(patient)
                return f"✅ **Patient Record Found:**\n\n{formatted_info}"
            elif patient_data.get('status') == 'not_found':
                return f"❌ No patient found with identifier: {patient_identifier}"
            else:
                return f"❌ Error: {patient_data.get('message', 'Unknown error')}"
                
        elif response.status_code == 404:
            return f"❌ No patient found with identifier: {patient_identifier}"
        else:
            return f"❌ Error accessing patient database (Status: {response.status_code})"
            
    except requests.exceptions.Timeout:
        return "❌ Patient database request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to patient database. Please check system status."
    except Exception as e:
        return f"❌ Error looking up patient record: {str(e)}"

@tool
def get_diabetes_patients_list() -> str:
    """
    Retrieve a list of all patients with diabetes diagnosis
    
    Returns:
        Summary of patients with diabetes including their diabetes type and key information
    """
    try:
        lambda_url = get_lambda_url()
        if not lambda_url:
            return "❌ Patient database is not available. Lambda function not configured."
        
        # Get all patients using action-based approach
        base_url = lambda_url.rstrip('/')
        
        payload = {
            "action": "get_patients"
        }
        
        response = requests.post(base_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            patients_data = response.json()
            
            if patients_data.get('status') == 'success' and patients_data.get('patients'):
                all_patients = patients_data['patients']
                
                # For now, return all patients since we don't have diabetes-specific filtering in the database
                # In a real implementation, you'd filter by diabetes diagnosis
                if not all_patients:
                    return "📋 No patients found in the database."
                
                # Format response
                summary = f"📋 **Found {len(all_patients)} patients in the database:**\n\n"
                
                # Show first 5 patients with details
                for i, patient in enumerate(all_patients[:5], 1):
                    summary += f"{i}. {format_patient_summary(patient)}\n"
                
                if len(all_patients) > 5:
                    summary += f"\n... and {len(all_patients) - 5} more patients in the database."
                
                summary += "\n\n*Note: Diabetes-specific filtering will be added when medical history data is available.*"
                
                return summary
            else:
                return f"❌ Error: {patients_data.get('message', 'Unknown error')}"
            
        else:
            return f"❌ Error accessing patient database (Status: {response.status_code})"
            
    except requests.exceptions.Timeout:
        return "❌ Patient database request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to patient database. Please check system status."
    except Exception as e:
        return f"❌ Error retrieving patients: {str(e)}"

@tool
def search_patients_by_name(first_name: str = "", last_name: str = "") -> str:
    """
    Search for patients by their first name and/or last name
    
    Args:
        first_name: Patient's first name to search for (optional)
        last_name: Patient's last name to search for (optional)
        
    Returns:
        List of patients matching the search criteria
    """
    try:
        if not first_name and not last_name:
            return "❌ Please provide at least a first name or last name to search for."
        
        lambda_url = get_lambda_url()
        if not lambda_url:
            return "❌ Patient database is not available. Lambda function not configured."
        
        # Get all patients first, then filter by name
        base_url = lambda_url.rstrip('/')
        
        payload = {
            "action": "get_patients"
        }
        
        response = requests.post(base_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            patients_data = response.json()
            
            if patients_data.get('status') == 'success' and patients_data.get('patients'):
                all_patients = patients_data['patients']
                
                # Filter patients by name
                matching_patients = []
                for patient in all_patients:
                    match = True
                    
                    if first_name:
                        patient_first = patient.get('first_name', '').lower()
                        if first_name.lower() not in patient_first:
                            match = False
                    
                    if last_name:
                        patient_last = patient.get('last_name', '').lower()
                        if last_name.lower() not in patient_last:
                            match = False
                    
                    if match:
                        matching_patients.append(patient)
                
                if not matching_patients:
                    search_terms = []
                    if first_name:
                        search_terms.append(f"first name '{first_name}'")
                    if last_name:
                        search_terms.append(f"last name '{last_name}'")
                    return f"📋 No patients found with {' and '.join(search_terms)}."
                
                # Format response
                search_terms = []
                if first_name:
                    search_terms.append(f"first name '{first_name}'")
                if last_name:
                    search_terms.append(f"last name '{last_name}'")
                    
                summary = f"📋 **Found {len(matching_patients)} patients with {' and '.join(search_terms)}:**\n\n"
                
                # Show all matching patients (limit to 10 for readability)
                for i, patient in enumerate(matching_patients[:10], 1):
                    summary += f"{i}. {format_patient_summary(patient)}\n"
                
                if len(matching_patients) > 10:
                    summary += f"\n... and {len(matching_patients) - 10} more matching patients."
                
                return summary
            else:
                return f"❌ Error: {patients_data.get('message', 'Unknown error')}"
            
        else:
            return f"❌ Error accessing patient database (Status: {response.status_code})"
            
    except requests.exceptions.Timeout:
        return "❌ Patient database request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to patient database. Please check system status."
    except Exception as e:
        return f"❌ Error searching for patients: {str(e)}"

@tool
def get_patient_medication_list(patient_identifier: str) -> str:
    """
    Get the current medication list for a specific patient from the medications table
    
    This tool queries the medications table to retrieve all medications prescribed to a patient,
    including active medications, discontinued medications, and completed courses.
    
    Args:
        patient_identifier: Patient ID (UUID) or Medical Record Number (MRN) like 'MRN-2024-001001'
        
    Returns:
        Formatted list of patient's medications with details including:
        - Medication name (brand and generic)
        - Dosage and frequency
        - Route of administration
        - Prescription dates and refills
        - Status (Active, Discontinued, Completed)
        - Instructions and clinical notes
    """
    try:
        # First, get the patient to verify they exist and get their UUID
        patient_data = lookup_patient_record(patient_identifier)
        
        if "❌" in patient_data or "not found" in patient_data.lower():
            return patient_data  # Return the error message
        
        # Extract patient UUID from the lookup result
        # The lookup_patient_record returns formatted text, so we need to call the API directly
        lambda_url = get_lambda_url()
        if not lambda_url:
            return "❌ Patient database is not available. Lambda function not configured."
        
        # Get patient UUID
        base_url = lambda_url.rstrip('/')
        patient_payload = {
            "action": "get_patient_by_id",
            "medical_record_number": patient_identifier
        }
        
        patient_response = requests.post(base_url, json=patient_payload, timeout=30)
        
        if patient_response.status_code != 200:
            return f"❌ Could not retrieve patient information (Status: {patient_response.status_code})"
        
        patient_info = patient_response.json()
        if patient_info.get('status') != 'success' or not patient_info.get('patient'):
            return f"❌ Patient not found: {patient_identifier}"
        
        patient = patient_info['patient']
        patient_id = patient.get('patient_id')
        patient_name = f"{patient.get('first_name', 'Unknown')} {patient.get('last_name', 'Unknown')}"
        mrn = patient.get('medical_record_number', 'N/A')
        
        # Now query medications for this patient
        medications_payload = {
            "action": "get_patient_medications",
            "patient_id": patient_id
        }
        
        med_response = requests.post(base_url, json=medications_payload, timeout=30)
        
        if med_response.status_code == 200:
            med_data = med_response.json()
            
            if med_data.get('status') == 'success':
                medications = med_data.get('medications', [])
                
                # Build formatted response
                summary = f"💊 **Medication List for {patient_name} (MRN: {mrn})**\n\n"
                
                if not medications:
                    summary += "📋 **No medications found in the system.**\n\n"
                    summary += "This patient currently has no recorded medications in the database.\n"
                    summary += "⚠️ Always verify with the patient if they are taking any medications, including over-the-counter drugs and supplements."
                    return summary
                
                # Group medications by status
                active_meds = [m for m in medications if m.get('medication_status') == 'Active']
                discontinued_meds = [m for m in medications if m.get('medication_status') == 'Discontinued']
                completed_meds = [m for m in medications if m.get('medication_status') == 'Completed']
                
                # Active Medications
                if active_meds:
                    summary += f"✅ **Active Medications ({len(active_meds)}):**\n\n"
                    for i, med in enumerate(active_meds, 1):
                        summary += f"{i}. **{med.get('medication_name', 'Unknown')}**"
                        if med.get('generic_name'):
                            summary += f" ({med.get('generic_name')})"
                        summary += "\n"
                        summary += f"   - Dosage: {med.get('dosage', 'N/A')}\n"
                        summary += f"   - Frequency: {med.get('frequency', 'N/A')}\n"
                        summary += f"   - Route: {med.get('route', 'N/A')}\n"
                        if med.get('prescription_date'):
                            summary += f"   - Prescribed: {med.get('prescription_date')}\n"
                        if med.get('refills_remaining') is not None:
                            summary += f"   - Refills Remaining: {med.get('refills_remaining')}\n"
                        if med.get('instructions'):
                            summary += f"   - Instructions: {med.get('instructions')}\n"
                        if med.get('notes'):
                            summary += f"   - Notes: {med.get('notes')}\n"
                        summary += "\n"
                
                # Discontinued Medications
                if discontinued_meds:
                    summary += f"⏸️ **Discontinued Medications ({len(discontinued_meds)}):**\n\n"
                    for i, med in enumerate(discontinued_meds, 1):
                        summary += f"{i}. **{med.get('medication_name', 'Unknown')}**"
                        if med.get('generic_name'):
                            summary += f" ({med.get('generic_name')})"
                        summary += "\n"
                        summary += f"   - Dosage: {med.get('dosage', 'N/A')}\n"
                        if med.get('discontinuation_reason'):
                            summary += f"   - Reason: {med.get('discontinuation_reason')}\n"
                        if med.get('end_date'):
                            summary += f"   - Discontinued: {med.get('end_date')}\n"
                        summary += "\n"
                
                # Completed Medications
                if completed_meds:
                    summary += f"✔️ **Completed Courses ({len(completed_meds)}):**\n\n"
                    for i, med in enumerate(completed_meds, 1):
                        summary += f"{i}. **{med.get('medication_name', 'Unknown')}** - {med.get('dosage', 'N/A')}\n"
                        if med.get('start_date') and med.get('end_date'):
                            summary += f"   - Duration: {med.get('start_date')} to {med.get('end_date')}\n"
                        if med.get('notes'):
                            summary += f"   - Notes: {med.get('notes')}\n"
                        summary += "\n"
                
                summary += "\n⚠️ **Important:** Always verify current medications with the patient and check for any recent changes before providing medical advice."
                
                return summary
            else:
                return f"❌ Error retrieving medications: {med_data.get('message', 'Unknown error')}"
        else:
            return f"❌ Error accessing medications database (Status: {med_response.status_code})"
            
    except requests.exceptions.Timeout:
        return "❌ Patient database request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to patient database. Please check system status."
    except Exception as e:
        return f"❌ Error retrieving patient medications: {str(e)}"


# =============================================================================
# APPOINTMENT MANAGEMENT TOOLS
# =============================================================================

@tool
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
    try:
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
        
        payload = {
            'action': 'get_appointments',
            **params
        }
        
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        function_name = os.environ.get(
            'APPOINTMENT_LAMBDA_FUNCTION_NAME',
            'MihcStack-GatewayLambda679C3A36-lWEbMl7wejem'
        )
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result.get('body', '{}'))
            return json.dumps(body, indent=2)
        else:
            return json.dumps({
                'error': 'Failed to retrieve appointments',
                'details': result
            }, indent=2)
            
    except Exception as e:
        return json.dumps({'error': str(e)}, indent=2)


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
    try:
        params = {
            'action': 'create_appointment',
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
        
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        function_name = os.environ.get(
            'APPOINTMENT_LAMBDA_FUNCTION_NAME',
            'MihcStack-GatewayLambda679C3A36-lWEbMl7wejem'
        )
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(params)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result.get('body', '{}'))
            return json.dumps(body, indent=2)
        else:
            return json.dumps({
                'error': 'Failed to create appointment',
                'details': result
            }, indent=2)
            
    except Exception as e:
        return json.dumps({'error': str(e)}, indent=2)
