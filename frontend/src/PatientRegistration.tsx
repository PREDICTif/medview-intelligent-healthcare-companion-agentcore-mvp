import { useState } from 'react';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Form from '@cloudscape-design/components/form';
import FormField from '@cloudscape-design/components/form-field';
import Input from '@cloudscape-design/components/input';
import DatePicker from '@cloudscape-design/components/date-picker';
import Select from '@cloudscape-design/components/select';
import Button from '@cloudscape-design/components/button';
import Alert from '@cloudscape-design/components/alert';
import Grid from '@cloudscape-design/components/grid';
import Box from '@cloudscape-design/components/box';
import { createPatient, PatientData } from './database';
import { getCurrentUser } from './auth';

interface FormErrors {
  [key: string]: string;
}

const genderOptions = [
  { label: 'Male', value: 'Male' },
  { label: 'Female', value: 'Female' },
  { label: 'Other', value: 'Other' },
  { label: 'Prefer not to say', value: 'Prefer not to say' },
];

const stateOptions = [
  { label: 'Alabama', value: 'AL' },
  { label: 'Alaska', value: 'AK' },
  { label: 'Arizona', value: 'AZ' },
  { label: 'Arkansas', value: 'AR' },
  { label: 'California', value: 'CA' },
  { label: 'Colorado', value: 'CO' },
  { label: 'Connecticut', value: 'CT' },
  { label: 'Delaware', value: 'DE' },
  { label: 'Florida', value: 'FL' },
  { label: 'Georgia', value: 'GA' },
  { label: 'Hawaii', value: 'HI' },
  { label: 'Idaho', value: 'ID' },
  { label: 'Illinois', value: 'IL' },
  { label: 'Indiana', value: 'IN' },
  { label: 'Iowa', value: 'IA' },
  { label: 'Kansas', value: 'KS' },
  { label: 'Kentucky', value: 'KY' },
  { label: 'Louisiana', value: 'LA' },
  { label: 'Maine', value: 'ME' },
  { label: 'Maryland', value: 'MD' },
  { label: 'Massachusetts', value: 'MA' },
  { label: 'Michigan', value: 'MI' },
  { label: 'Minnesota', value: 'MN' },
  { label: 'Mississippi', value: 'MS' },
  { label: 'Missouri', value: 'MO' },
  { label: 'Montana', value: 'MT' },
  { label: 'Nebraska', value: 'NE' },
  { label: 'Nevada', value: 'NV' },
  { label: 'New Hampshire', value: 'NH' },
  { label: 'New Jersey', value: 'NJ' },
  { label: 'New Mexico', value: 'NM' },
  { label: 'New York', value: 'NY' },
  { label: 'North Carolina', value: 'NC' },
  { label: 'North Dakota', value: 'ND' },
  { label: 'Ohio', value: 'OH' },
  { label: 'Oklahoma', value: 'OK' },
  { label: 'Oregon', value: 'OR' },
  { label: 'Pennsylvania', value: 'PA' },
  { label: 'Rhode Island', value: 'RI' },
  { label: 'South Carolina', value: 'SC' },
  { label: 'South Dakota', value: 'SD' },
  { label: 'Tennessee', value: 'TN' },
  { label: 'Texas', value: 'TX' },
  { label: 'Utah', value: 'UT' },
  { label: 'Vermont', value: 'VT' },
  { label: 'Virginia', value: 'VA' },
  { label: 'Washington', value: 'WA' },
  { label: 'West Virginia', value: 'WV' },
  { label: 'Wisconsin', value: 'WI' },
  { label: 'Wyoming', value: 'WY' },
];

export default function PatientRegistration() {
  // Personal Information
  const [medicalRecordNumber, setMedicalRecordNumber] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [middleName, setMiddleName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [gender, setGender] = useState<any>(null);

  // Contact Information
  const [phonePrimary, setPhonePrimary] = useState('');
  const [phoneSecondary, setPhoneSecondary] = useState('');
  const [email, setEmail] = useState('');

  // Address
  const [addressLine1, setAddressLine1] = useState('');
  const [addressLine2, setAddressLine2] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState<any>(null);
  const [zipCode, setZipCode] = useState('');
  const [country, setCountry] = useState('USA');

  // Emergency Contact
  const [emergencyContactName, setEmergencyContactName] = useState('');
  const [emergencyContactPhone, setEmergencyContactPhone] = useState('');
  const [emergencyContactRelationship, setEmergencyContactRelationship] = useState('');

  // Insurance Information
  const [insuranceProvider, setInsuranceProvider] = useState('');
  const [insurancePolicyNumber, setInsurancePolicyNumber] = useState('');
  const [insuranceGroupNumber, setInsuranceGroupNumber] = useState('');

  // Form state
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Required fields
    if (!medicalRecordNumber.trim()) {
      newErrors.medicalRecordNumber = 'Medical Record Number is required';
    }
    if (!firstName.trim()) {
      newErrors.firstName = 'First Name is required';
    }
    if (!lastName.trim()) {
      newErrors.lastName = 'Last Name is required';
    }
    if (!dateOfBirth) {
      newErrors.dateOfBirth = 'Date of Birth is required';
    } else {
      // Validate date format and that it's not in the future
      const dob = new Date(dateOfBirth);
      if (isNaN(dob.getTime())) {
        newErrors.dateOfBirth = 'Invalid date format';
      } else if (dob > new Date()) {
        newErrors.dateOfBirth = 'Date of Birth cannot be in the future';
      }
    }

    // Email validation if provided
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Invalid email format';
    }

    // Phone validation if provided (basic US phone format)
    if (phonePrimary && !/^\+?[\d\s\-\(\)]+$/.test(phonePrimary)) {
      newErrors.phonePrimary = 'Invalid phone format';
    }
    if (phoneSecondary && !/^\+?[\d\s\-\(\)]+$/.test(phoneSecondary)) {
      newErrors.phoneSecondary = 'Invalid phone format';
    }
    if (emergencyContactPhone && !/^\+?[\d\s\-\(\)]+$/.test(emergencyContactPhone)) {
      newErrors.emergencyContactPhone = 'Invalid phone format';
    }

    // Zip code validation if provided (5 or 9 digits)
    if (zipCode && !/^\d{5}(-\d{4})?$/.test(zipCode)) {
      newErrors.zipCode = 'Invalid ZIP code format (use 12345 or 12345-6789)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setSuccessMessage('');
    setErrorMessage('');

    if (!validateForm()) {
      setErrorMessage('Please fix the validation errors before submitting');
      return;
    }

    setLoading(true);

    try {
      // Get current user to set created_by
      const currentUser = await getCurrentUser();
      if (!currentUser) {
        setErrorMessage('You must be logged in to register a patient');
        setLoading(false);
        return;
      }

      const patientData: PatientData = {
        patient_id: currentUser.sub,
        medical_record_number: medicalRecordNumber.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        middle_name: middleName.trim() || undefined,
        date_of_birth: dateOfBirth,
        gender: gender?.value || undefined,
        phone_primary: phonePrimary.trim() || undefined,
        phone_secondary: phoneSecondary.trim() || undefined,
        email: email.trim() || undefined,
        address_line1: addressLine1.trim() || undefined,
        address_line2: addressLine2.trim() || undefined,
        city: city.trim() || undefined,
        state: state?.value || undefined,
        zip_code: zipCode.trim() || undefined,
        country: country.trim() || 'USA',
        emergency_contact_name: emergencyContactName.trim() || undefined,
        emergency_contact_phone: emergencyContactPhone.trim() || undefined,
        emergency_contact_relationship: emergencyContactRelationship.trim() || undefined,
        insurance_provider: insuranceProvider.trim() || undefined,
        insurance_policy_number: insurancePolicyNumber.trim() || undefined,
        insurance_group_number: insuranceGroupNumber.trim() || undefined,
        created_by: currentUser.sub,
      };

      const result = await createPatient(patientData);

      if (result.status === 'success') {
        setSuccessMessage(`Patient registered successfully! Patient ID: ${result.patient?.patient_id}`);
        // Clear form
        resetForm();
      } else {
        setErrorMessage(result.message || 'Failed to register patient');
      }
    } catch (error: any) {
      setErrorMessage(error.message || 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setMedicalRecordNumber('');
    setFirstName('');
    setLastName('');
    setMiddleName('');
    setDateOfBirth('');
    setGender(null);
    setPhonePrimary('');
    setPhoneSecondary('');
    setEmail('');
    setAddressLine1('');
    setAddressLine2('');
    setCity('');
    setState(null);
    setZipCode('');
    setCountry('USA');
    setEmergencyContactName('');
    setEmergencyContactPhone('');
    setEmergencyContactRelationship('');
    setInsuranceProvider('');
    setInsurancePolicyNumber('');
    setInsuranceGroupNumber('');
    setErrors({});
  };

  return (
    <Container
      header={
        <Header
          variant="h1"
          description="Register a new patient in the medical records system"
        >
          Patient Registration
        </Header>
      }
    >
      <form onSubmit={handleSubmit}>
        <Form
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Button formAction="none" variant="link" onClick={resetForm}>
                Clear Form
              </Button>
              <Button variant="primary" loading={loading}>
                Register Patient
              </Button>
            </SpaceBetween>
          }
        >
          <SpaceBetween size="l">
            {successMessage && (
              <Alert type="success" dismissible onDismiss={() => setSuccessMessage('')}>
                {successMessage}
              </Alert>
            )}
            {errorMessage && (
              <Alert type="error" dismissible onDismiss={() => setErrorMessage('')}>
                {errorMessage}
              </Alert>
            )}

            {/* Personal Information Section */}
            <Container header={<Header variant="h2">Personal Information</Header>}>
              <SpaceBetween size="l">
                <Grid gridDefinition={[{ colspan: 6 }, { colspan: 6 }]}>
                  <FormField
                    label="Medical Record Number"
                    constraintText="Required. Unique identifier for the patient"
                    errorText={errors.medicalRecordNumber}
                  >
                    <Input
                      value={medicalRecordNumber}
                      onChange={({ detail }) => setMedicalRecordNumber(detail.value)}
                      placeholder="MRN-12345"
                      invalid={!!errors.medicalRecordNumber}
                    />
                  </FormField>
                  <FormField
                    label="Date of Birth"
                    constraintText="Required"
                    errorText={errors.dateOfBirth}
                  >
                    <DatePicker
                      value={dateOfBirth}
                      onChange={({ detail }) => setDateOfBirth(detail.value)}
                      placeholder="YYYY/MM/DD"
                      invalid={!!errors.dateOfBirth}
                    />
                  </FormField>
                </Grid>

                <Grid gridDefinition={[{ colspan: 4 }, { colspan: 4 }, { colspan: 4 }]}>
                  <FormField
                    label="First Name"
                    constraintText="Required"
                    errorText={errors.firstName}
                  >
                    <Input
                      value={firstName}
                      onChange={({ detail }) => setFirstName(detail.value)}
                      placeholder="John"
                      invalid={!!errors.firstName}
                    />
                  </FormField>
                  <FormField label="Middle Name">
                    <Input
                      value={middleName}
                      onChange={({ detail }) => setMiddleName(detail.value)}
                      placeholder="Michael"
                    />
                  </FormField>
                  <FormField
                    label="Last Name"
                    constraintText="Required"
                    errorText={errors.lastName}
                  >
                    <Input
                      value={lastName}
                      onChange={({ detail }) => setLastName(detail.value)}
                      placeholder="Doe"
                      invalid={!!errors.lastName}
                    />
                  </FormField>
                </Grid>

                <FormField label="Gender">
                  <Select
                    selectedOption={gender}
                    onChange={({ detail }) => setGender(detail.selectedOption)}
                    options={genderOptions}
                    placeholder="Select gender"
                  />
                </FormField>
              </SpaceBetween>
            </Container>

            {/* Contact Information Section */}
            <Container header={<Header variant="h2">Contact Information</Header>}>
              <SpaceBetween size="l">
                <Grid gridDefinition={[{ colspan: 4 }, { colspan: 4 }, { colspan: 4 }]}>
                  <FormField
                    label="Primary Phone"
                    errorText={errors.phonePrimary}
                  >
                    <Input
                      value={phonePrimary}
                      onChange={({ detail }) => setPhonePrimary(detail.value)}
                      placeholder="(555) 123-4567"
                      type="tel"
                      invalid={!!errors.phonePrimary}
                    />
                  </FormField>
                  <FormField
                    label="Secondary Phone"
                    errorText={errors.phoneSecondary}
                  >
                    <Input
                      value={phoneSecondary}
                      onChange={({ detail }) => setPhoneSecondary(detail.value)}
                      placeholder="(555) 987-6543"
                      type="tel"
                      invalid={!!errors.phoneSecondary}
                    />
                  </FormField>
                  <FormField
                    label="Email"
                    errorText={errors.email}
                  >
                    <Input
                      value={email}
                      onChange={({ detail }) => setEmail(detail.value)}
                      placeholder="john.doe@example.com"
                      type="email"
                      invalid={!!errors.email}
                    />
                  </FormField>
                </Grid>
              </SpaceBetween>
            </Container>

            {/* Address Section */}
            <Container header={<Header variant="h2">Address</Header>}>
              <SpaceBetween size="l">
                <FormField label="Address Line 1">
                  <Input
                    value={addressLine1}
                    onChange={({ detail }) => setAddressLine1(detail.value)}
                    placeholder="123 Main Street"
                  />
                </FormField>
                <FormField label="Address Line 2">
                  <Input
                    value={addressLine2}
                    onChange={({ detail }) => setAddressLine2(detail.value)}
                    placeholder="Apt 4B"
                  />
                </FormField>
                <Grid gridDefinition={[{ colspan: 5 }, { colspan: 3 }, { colspan: 4 }]}>
                  <FormField label="City">
                    <Input
                      value={city}
                      onChange={({ detail }) => setCity(detail.value)}
                      placeholder="New York"
                    />
                  </FormField>
                  <FormField label="State">
                    <Select
                      selectedOption={state}
                      onChange={({ detail }) => setState(detail.selectedOption)}
                      options={stateOptions}
                      placeholder="Select state"
                      filteringType="auto"
                    />
                  </FormField>
                  <FormField
                    label="ZIP Code"
                    errorText={errors.zipCode}
                  >
                    <Input
                      value={zipCode}
                      onChange={({ detail }) => setZipCode(detail.value)}
                      placeholder="12345"
                      invalid={!!errors.zipCode}
                    />
                  </FormField>
                </Grid>
                <FormField label="Country">
                  <Input
                    value={country}
                    onChange={({ detail }) => setCountry(detail.value)}
                    placeholder="USA"
                  />
                </FormField>
              </SpaceBetween>
            </Container>

            {/* Emergency Contact Section */}
            <Container header={<Header variant="h2">Emergency Contact</Header>}>
              <SpaceBetween size="l">
                <Grid gridDefinition={[{ colspan: 6 }, { colspan: 6 }]}>
                  <FormField label="Emergency Contact Name">
                    <Input
                      value={emergencyContactName}
                      onChange={({ detail }) => setEmergencyContactName(detail.value)}
                      placeholder="Jane Doe"
                    />
                  </FormField>
                  <FormField
                    label="Emergency Contact Phone"
                    errorText={errors.emergencyContactPhone}
                  >
                    <Input
                      value={emergencyContactPhone}
                      onChange={({ detail }) => setEmergencyContactPhone(detail.value)}
                      placeholder="(555) 111-2222"
                      type="tel"
                      invalid={!!errors.emergencyContactPhone}
                    />
                  </FormField>
                </Grid>
                <FormField label="Relationship">
                  <Input
                    value={emergencyContactRelationship}
                    onChange={({ detail }) => setEmergencyContactRelationship(detail.value)}
                    placeholder="Spouse"
                  />
                </FormField>
              </SpaceBetween>
            </Container>

            {/* Insurance Information Section */}
            <Container header={<Header variant="h2">Insurance Information</Header>}>
              <SpaceBetween size="l">
                <FormField label="Insurance Provider">
                  <Input
                    value={insuranceProvider}
                    onChange={({ detail }) => setInsuranceProvider(detail.value)}
                    placeholder="Blue Cross Blue Shield"
                  />
                </FormField>
                <Grid gridDefinition={[{ colspan: 6 }, { colspan: 6 }]}>
                  <FormField label="Policy Number">
                    <Input
                      value={insurancePolicyNumber}
                      onChange={({ detail }) => setInsurancePolicyNumber(detail.value)}
                      placeholder="ABC123456789"
                    />
                  </FormField>
                  <FormField label="Group Number">
                    <Input
                      value={insuranceGroupNumber}
                      onChange={({ detail }) => setInsuranceGroupNumber(detail.value)}
                      placeholder="GRP12345"
                    />
                  </FormField>
                </Grid>
              </SpaceBetween>
            </Container>

            <Box textAlign="center" color="text-body-secondary">
              <small>All fields marked as "Required" must be filled out. Other fields are optional.</small>
            </Box>
          </SpaceBetween>
        </Form>
      </form>
    </Container>
  );
}

