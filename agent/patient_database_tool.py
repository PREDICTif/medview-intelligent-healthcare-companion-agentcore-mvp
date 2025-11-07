#!/usr/bin/env python3
"""
Patient Database Tool for Medical Assistant Agent
Integrates with AgentCore Gateway to access patient records
"""

import os
import boto3
import requests
import json
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

def get_patient_records(patient_id: Optional[str] = None, medical_record_number: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve patient records from the database via AgentCore Gateway
    
    Args:
        patient_id: Optional patient ID to search for specific patient
        medical_record_number: Optional MRN to search for specific patient
        
    Returns:
        Dictionary containing patient data or error information
    """
    try:
        gateway_url = get_gateway_url()
        if not gateway_url:
            return {
                "status": "error",
                "message": "Gateway URL not configured. Please set up AgentCore Gateway first."
            }
        
        # If searching for specific patient
        if patient_id or medical_record_number:
            search_id = patient_id or medical_record_number
            url = f"{gateway_url}/patient/{search_id}"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                patient_data = response.json()
                return {
                    "status": "success",
                    "patient": patient_data,
                    "message": f"Found patient record for {search_id}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Patient not found: {search_id}",
                    "status_code": response.status_code
                }
        
        # Get all patients
        else:
            url = f"{gateway_url}/patients"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                patients_data = response.json()
                return {
                    "status": "success",
                    "patients": patients_data.get("patients", []),
                    "count": len(patients_data.get("patients", [])),
                    "message": "Retrieved patient list successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to retrieve patient list",
                    "status_code": response.status_code
                }
                
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Request timeout - database may be slow to respond"
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error", 
            "message": "Cannot connect to patient database gateway"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error accessing patient database: {str(e)}"
        }

def search_patients_by_name(first_name: Optional[str] = None, last_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for patients by name (client-side filtering)
    
    Args:
        first_name: Patient's first name to search for
        last_name: Patient's last name to search for
        
    Returns:
        Dictionary containing matching patients
    """
    try:
        # Get all patients first
        all_patients_result = get_patient_records()
        
        if all_patients_result["status"] != "success":
            return all_patients_result
        
        patients = all_patients_result.get("patients", [])
        matching_patients = []
        
        # Filter patients by name
        for patient in patients:
            match = True
            
            if first_name:
                patient_first = patient.get("first_name", "").lower()
                if first_name.lower() not in patient_first:
                    match = False
            
            if last_name:
                patient_last = patient.get("last_name", "").lower()
                if last_name.lower() not in patient_last:
                    match = False
            
            if match:
                matching_patients.append(patient)
        
        return {
            "status": "success",
            "patients": matching_patients,
            "count": len(matching_patients),
            "message": f"Found {len(matching_patients)} patients matching search criteria"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching patients: {str(e)}"
        }

def get_diabetes_patients() -> Dict[str, Any]:
    """
    Get all patients with diabetes diagnosis
    
    Returns:
        Dictionary containing diabetes patients
    """
    try:
        # Get all patients first
        all_patients_result = get_patient_records()
        
        if all_patients_result["status"] != "success":
            return all_patients_result
        
        patients = all_patients_result.get("patients", [])
        diabetes_patients = []
        
        # Filter for diabetes patients
        for patient in patients:
            diabetes_type = patient.get("diabetes_type")
            if diabetes_type and diabetes_type.strip():
                diabetes_patients.append(patient)
        
        return {
            "status": "success",
            "patients": diabetes_patients,
            "count": len(diabetes_patients),
            "message": f"Found {len(diabetes_patients)} patients with diabetes diagnosis"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving diabetes patients: {str(e)}"
        }

def format_patient_summary(patient: Dict[str, Any]) -> str:
    """
    Format patient data for display in agent responses
    
    Args:
        patient: Patient data dictionary
        
    Returns:
        Formatted string with patient information
    """
    try:
        summary = f"**Patient: {patient.get('first_name', 'Unknown')} {patient.get('last_name', 'Unknown')}**\n"
        summary += f"- MRN: {patient.get('medical_record_number', 'N/A')}\n"
        summary += f"- DOB: {patient.get('date_of_birth', 'N/A')}\n"
        summary += f"- Gender: {patient.get('gender', 'N/A')}\n"
        
        if patient.get('diabetes_type'):
            summary += f"- Diabetes Type: {patient.get('diabetes_type')}\n"
            
        if patient.get('diagnosis_date'):
            summary += f"- Diagnosis Date: {patient.get('diagnosis_date')}\n"
            
        if patient.get('current_medications'):
            summary += f"- Current Medications: {patient.get('current_medications')}\n"
            
        if patient.get('allergies'):
            summary += f"- Allergies: {patient.get('allergies')}\n"
            
        if patient.get('primary_care_physician'):
            summary += f"- Primary Care Physician: {patient.get('primary_care_physician')}\n"
        
        return summary
        
    except Exception as e:
        return f"Error formatting patient data: {str(e)}"