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

def get_gateway_url() -> Optional[str]:
    """Get the AgentCore Gateway URL from SSM"""
    return get_ssm_parameter("/app/medicalassistant/agentcore/gateway_url")

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
        gateway_url = get_gateway_url()
        if not gateway_url:
            return "❌ Patient database is not available. Gateway not configured."
        
        # Clean the gateway URL and make action-based request
        base_url = gateway_url.rstrip('/')
        
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
        gateway_url = get_gateway_url()
        if not gateway_url:
            return "❌ Patient database is not available. Gateway not configured."
        
        # Get all patients using action-based approach
        base_url = gateway_url.rstrip('/')
        
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
        
        gateway_url = get_gateway_url()
        if not gateway_url:
            return "❌ Patient database is not available. Gateway not configured."
        
        # Get all patients first, then filter by name
        base_url = gateway_url.rstrip('/')
        
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
    Get the current medication list for a specific patient
    
    Args:
        patient_identifier: Patient ID or Medical Record Number (MRN)
        
    Returns:
        Patient's current medications and allergy information
    """
    try:
        gateway_url = get_gateway_url()
        if not gateway_url:
            return "❌ Patient database is not available. Gateway not configured."
        
        # Clean the gateway URL and make action-based request
        base_url = gateway_url.rstrip('/')
        
        payload = {
            "action": "get_patient_by_id",
            "medical_record_number": patient_identifier
        }
        
        response = requests.post(base_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            patient_data = response.json()
            
            if patient_data.get('status') == 'success' and patient_data.get('patient'):
                patient = patient_data['patient']
                
                # Extract basic information
                patient_name = f"{patient.get('first_name', 'Unknown')} {patient.get('last_name', 'Unknown')}"
                mrn = patient.get('medical_record_number', 'N/A')
                
                summary = f"💊 **Patient Information for {patient_name} (MRN: {mrn})**\n\n"
                summary += f"**Basic Information:**\n"
                summary += f"- Name: {patient_name}\n"
                summary += f"- DOB: {patient.get('date_of_birth', 'N/A')}\n"
                summary += f"- Gender: {patient.get('gender', 'N/A')}\n"
                
                if patient.get('phone_primary'):
                    summary += f"- Phone: {patient.get('phone_primary')}\n"
                
                summary += f"\n**Medical Information:**\n"
                summary += f"*Note: Detailed medication and allergy information will be available when medical history tables are implemented.*\n"
                summary += f"*Current patient record contains basic demographic information only.*\n\n"
                
                summary += "⚠️ **Important:** Always verify current medications with the patient and check for any recent changes before providing medical advice."
                
                return summary
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
        return f"❌ Error retrieving patient medications: {str(e)}"