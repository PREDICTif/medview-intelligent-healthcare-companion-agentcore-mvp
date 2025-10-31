import { getIdToken } from './auth';

const LAMBDA_FUNCTION_URL = import.meta.env.VITE_LAMBDA_FUNCTION_URL;

if (!LAMBDA_FUNCTION_URL) {
  console.warn('VITE_LAMBDA_FUNCTION_URL not configured');
}

export interface PatientData {
  patient_id: string;
  medical_record_number: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  date_of_birth: string;
  gender?: string;
  phone_primary?: string;
  phone_secondary?: string;
  email?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relationship?: string;
  insurance_provider?: string;
  insurance_policy_number?: string;
  insurance_group_number?: string;
  created_by: string;
}

export interface Patient extends PatientData {
  patient_id: string;
  active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CreatePatientResponse {
  status: 'success' | 'error';
  message: string;
  patient?: Patient;
}

export const createPatient = async (patientData: PatientData): Promise<CreatePatientResponse> => {
  try {
    if (!LAMBDA_FUNCTION_URL) {
      throw new Error('Lambda function URL not configured');
    }

    const idToken = await getIdToken();
    if (!idToken) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(LAMBDA_FUNCTION_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${idToken}`,
      },
      body: JSON.stringify({
        action: 'create_patient',
        patient_data: patientData,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result;
  } catch (error: any) {
    console.error('Error creating patient:', error);
    return {
      status: 'error',
      message: error.message || 'Failed to create patient',
    };
  }
};

export const getPatients = async (): Promise<any> => {
  try {
    if (!LAMBDA_FUNCTION_URL) {
      throw new Error('Lambda function URL not configured');
    }

    const idToken = await getIdToken();
    if (!idToken) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(LAMBDA_FUNCTION_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${idToken}`,
      },
      body: JSON.stringify({
        action: 'get_patients',
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error: any) {
    console.error('Error fetching patients:', error);
    return {
      status: 'error',
      message: error.message || 'Failed to fetch patients',
      patients: [],
    };
  }
};

