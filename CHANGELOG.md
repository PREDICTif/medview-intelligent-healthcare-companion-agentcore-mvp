# Medview Intelligent Healthcare Companion - Changelog

## 2025-11-10 - Height & Weight Fields Added to Patient Registration

### Fixed
- **Aurora PostgreSQL Version**: Updated from VER_15_4 to VER_15_5 (version 15.4 no longer available in AWS)
  - File: `cdk/lib/mihc-stack.ts`
  - Previous deployment failed with "Cannot find version 15.4 for aurora-postgresql"
  
- **CDK Stack Outputs**: Added missing `DatabaseClusterArn` and `DatabaseSecretArn` outputs to MihcStack for migration script support
  - File: `cdk/lib/mihc-stack.ts`
  - Required for database migration scripts to retrieve connection information

### Added
- **Height and Weight Fields**: Patient registration form now collects required height (feet & inches) and weight (lbs) during registration
  - Files: `frontend/src/PatientRegistration.tsx`, `frontend/src/database.ts`, `lambda/database-handler/index.py`, `database/schema/01_core_tables.sql`
  - Height input: Two fields (feet: 3-8 range, inches: 0-11 range)
  - Weight input: Single decimal field (positive values required)
  - Validation: All three fields are required with range constraints
  - Database: Added height_feet (INTEGER), height_inches (INTEGER), weight_lbs (DECIMAL(5,2)) columns with CHECK constraints
  
- **Database Migration System**: Created Python-based migration script for database schema changes
  - Files: `database/migrations/add_height_weight_to_patients.sql`, `scripts/migrate_add_height_weight.py`
  - Automatically retrieves database credentials from CloudFormation stack
  - Executes SQL migrations via RDS Data API
  - Verifies successful migration completion
  - Usage: `cd scripts && python migrate_add_height_weight.py`

### Modified
- `frontend/src/PatientRegistration.tsx`: Added height/weight state variables, validation logic, UI inputs in Personal Information section
- `frontend/src/database.ts`: Updated PatientData interface with height_feet, height_inches, weight_lbs fields
- `lambda/database-handler/index.py`: Updated create_patient function to handle new numeric fields with proper type casting (longValue for integers, doubleValue for decimals)
- `database/schema/01_core_tables.sql`: Added Physical Measurements section with height and weight columns including CHECK constraints

### Why It Matters
- Enables comprehensive patient health data collection at registration
- Provides foundation for BMI calculation and health monitoring features
- Ensures data integrity through database-level constraints
- Simplifies future schema updates with reusable migration script pattern

## 2025-10-30 - Patient Registration Feature + Lambda Function URL Fix (Updated)

### Fixed - Deployed App Error
- **"Lambda function URL not configured" in deployed AWS app**: Fixed environment variable build process
  - Files: `scripts/build-frontend.sh`, `scripts/build-frontend.ps1`, `deploy-all.sh`, `deploy-all.ps1`
  - Build scripts now accept Lambda Function URL as parameter
  - Deployment scripts automatically retrieve Lambda URL from MihcStack
  - Lambda URL is baked into frontend build at build-time (Vite requirement)
  - Created quick fix script: `scripts/redeploy-with-lambda-url.sh`
  - Created comprehensive guide: `FIX_DEPLOYED_APP_LAMBDA_URL.md`

### How to Fix Deployed App
**Quick Fix:** Run `./scripts/redeploy-with-lambda-url.sh`

This will:
1. Deploy MihcStack (creates Lambda Function URL)
2. Rebuild frontend with Lambda URL baked in
3. Redeploy frontend to S3+CloudFront
4. Patient registration will work in deployed app after CloudFront propagates (5-10 min)

### Fixed - Local Development
- **Lambda Function URL Configuration**: Added Lambda Function URL to CDK stack for HTTP access
  - Files: `cdk/lib/mihc-stack.ts`
  - Added Function URL with CORS support (development mode with authType: NONE)
  - Added CloudFormation output for easy URL retrieval
  - Created setup documentation: `frontend/README_SETUP.md` and `frontend/ENVIRONMENT_SETUP.txt`

### Local Development Configuration
For local development only:
1. Deploy CDK stack: `cd cdk && cdk deploy MihcStack`
2. Copy the `DatabaseLambdaFunctionUrl` from outputs
3. Create `frontend/.env.local` file with:
   ```
   VITE_USER_POOL_ID=your-pool-id
   VITE_USER_POOL_CLIENT_ID=your-client-id
   VITE_LAMBDA_FUNCTION_URL=your-function-url
   ```
4. Restart frontend dev server: `cd frontend && npm run dev`

## 2025-10-30 - Patient Registration Feature (Original)

### Added
- **Patient Registration Form Page**: Created comprehensive patient registration form with all fields matching the database schema
  - Files: `frontend/src/PatientRegistration.tsx`
  - Features:
    - Personal information section (MRN, name, DOB, gender)
    - Contact information (primary/secondary phone, email)
    - Address details with US state dropdown
    - Emergency contact information
    - Insurance details (provider, policy number, group number)
    - Real-time form validation with error messages
    - Success/error alerts for submission feedback
    - Clear form functionality

- **Database API Integration**: Created database utility module for Lambda communication
  - Files: `frontend/src/database.ts`
  - Functions:
    - `createPatient()`: Creates new patient records with authentication
    - `getPatients()`: Retrieves patient list
  - Uses Cognito ID tokens for authentication

- **Lambda Database Handler Enhancements**: Added patient creation functionality
  - Files: `lambda/database-handler/index.py`
  - New function: `create_patient(patient_data)` 
    - Validates required fields (MRN, first_name, last_name, date_of_birth, created_by)
    - Uses RDS Data API for secure database operations
    - Returns created patient data with auto-generated UUID
  - Updated lambda_handler to process 'create_patient' action
  - Added CORS support for cross-origin requests

- **Navigation System**: Implemented side navigation for multi-page support
  - Files: `frontend/src/App.tsx`
  - Features:
    - Side navigation panel with collapsible menu
    - "AI Assistant" page (existing chat interface)
    - "Patient Management" section with "Register Patient" link
    - Navigation state management
    - Responsive layout with Cloudscape Design System

### Form Validation Rules
- **Required fields**: Medical Record Number, First Name, Last Name, Date of Birth
- **Email validation**: Standard email format check
- **Phone validation**: Accepts US phone formats with optional country code
- **ZIP code validation**: 5-digit or 5+4 digit format (12345 or 12345-6789)
- **Date validation**: Date of Birth cannot be in the future

### Database Schema Alignment
All form fields map directly to the `patients` table schema:
- Core identifiers: patient_id (auto-generated UUID), medical_record_number
- Demographics: first_name, last_name, middle_name, date_of_birth, gender
- Contact: phone_primary, phone_secondary, email
- Address: address_line1, address_line2, city, state, zip_code, country
- Emergency: emergency_contact_name, emergency_contact_phone, emergency_contact_relationship
- Insurance: insurance_provider, insurance_policy_number, insurance_group_number
- System fields: active, created_at, updated_at, created_by, updated_by

### Security Features
- All database operations require Cognito authentication
- Lambda uses IAM roles with least-privilege access
- RDS Data API for secure database connections (no direct credentials in code)
- Secrets Manager integration for database credentials
- Patient data encrypted at rest (KMS) and in transit (SSL/TLS)

### Technical Stack
- **Frontend**: React 18 + TypeScript + Vite
- **UI Library**: AWS Cloudscape Design System
- **Authentication**: Amazon Cognito
- **Backend**: AWS Lambda (Python 3.11)
- **Database**: Aurora PostgreSQL Serverless v2
- **API**: RDS Data API

### Files Modified
1. `lambda/database-handler/index.py` - Added create_patient function and handler
2. `frontend/src/App.tsx` - Added navigation system and routing
3. `frontend/src/PatientRegistration.tsx` - New patient registration form component
4. `frontend/src/database.ts` - New database API utility module

### Next Steps
- Deploy Lambda function with updated code
- Test patient creation with various data scenarios
- Consider adding patient search/list view page
- Add patient profile edit functionality
- Implement patient record viewing

