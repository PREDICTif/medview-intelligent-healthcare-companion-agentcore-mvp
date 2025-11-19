# Medication Display Implementation Plan

**Date:** 2025-11-19 16:30:00
**Project:** Medview Connect - Intelligent Healthcare Companion
**Objective:** Implement Medication Display Functionality for Patient Dashboard and Detail Page

---

## Current State Analysis

### Existing Infrastructure
- **Database:** AWS RDS PostgreSQL with medications table populated
  - Sample data: 10 medications inserted via `database/data/03_medications_sample_data.sql`
  - Key fields: medication_name, generic_name, dosage, frequency, route, medication_status, prescription_date, instructions
  - Patient linking: Uses `patient_id` (Cognito user ID)
  - Status values: 'Active', 'Completed'

- **Backend Tools:** Agent tools exist for patient data
  - File: `agent/patient_database_tool.py`
  - Functions: `get_patient_records()`, `search_patients_by_name()`, `get_diabetes_patients()`
  - Uses AgentCore Gateway: `/app/medicalassistant/agentcore/gateway_url` (SSM parameter)
  - API pattern: Calls `/patient/{id}`, `/patients` endpoints
  - **Gap:** NO medication-specific functions exist yet

- **Frontend Pages:**
  - `frontend/src/HomePage.tsx` - Dashboard with medication card (placeholder)
  - `frontend/src/MedicationsDetail.tsx` - Placeholder page with "coming soon" message
  - Both need implementation to display real data

- **Authentication:** Amazon Cognito
  - User ID (Cognito ID) is used as `patient_id` in database
  - Need to extract current user's Cognito ID from auth context

### What Does NOT Currently Exist
- ❌ Backend API endpoints for medications (`/medications/{patient_id}`, `/medications/{patient_id}/active`)
- ❌ Lambda handler functions to query medications table
- ❌ Frontend state management for medication data
- ❌ Frontend API calls to fetch medications
- ❌ UI components to display medication information
- ❌ Medication-specific utility functions in agent tools (optional)

---

## Requirements

### Functional Requirements

1. **HomePage Medication Card Enhancement**
   - Display current active medications for logged-in patient
   - Show medication count (e.g., "You have 5 active medications")
   - List top 3-5 active medications with basic info (name, dosage)
   - "Learn more →" link navigates to full medication history page

2. **MedicationsDetail Page Implementation**
   - Display ALL medications for logged-in patient (both Active and Completed)
   - **Chronological Order:** Display medications from newest to oldest (prescription_date DESC)
   - Show comprehensive medication information:
     - Medication name (brand and generic)
     - Dosage and frequency
     - Route of administration
     - Status (Active/Completed)
     - Prescription date and date range
     - Prescribing physician
     - Instructions
     - Refills remaining (for active medications)
   - Provide filtering options (Active/Completed/All)
   - Support search/sort functionality
   - "Back to Home" navigation button

### Non-Functional Requirements
- **Performance:** Page load < 2 seconds
- **Security:** Authentication required, patient can only see their own medications
- **Error Handling:** Graceful degradation if API fails
- **Responsive:** Works on mobile and desktop
- **Accessibility:** WCAG 2.1 AA compliant using Cloudscape components

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌────────────────┐              ┌─────────────────────────┐    │
│  │ HomePage.tsx   │              │ MedicationsDetail.tsx   │    │
│  │ - Auth Context │              │ - Auth Context          │    │
│  │ - Get User ID  │              │ - Get User ID           │    │
│  │ - Fetch Active │              │ - Fetch All Meds        │    │
│  │ - Display 3-5  │              │ - Display Table/Cards   │    │
│  └────────┬───────┘              └───────────┬─────────────┘    │
│           │                                   │                  │
└───────────┼───────────────────────────────────┼──────────────────┘
            │ GET /medications/{id}/active      │ GET /medications/{id}
            │                                   │
┌───────────▼───────────────────────────────────▼──────────────────┐
│                   API Gateway / AgentCore Gateway                 │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NEW Routes:                                                │  │
│  │ - GET /medications/{patient_id}/active                     │  │
│  │ - GET /medications/{patient_id}                            │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬──────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────┐
│              Lambda Function (database-handler)                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NEW Functions:                                             │  │
│  │ - get_patient_medications(patient_id, active_only=False)   │  │
│  │ - format_medication_response(medication_records)           │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬──────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────┐
│                      AWS RDS PostgreSQL                           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ medications table                                          │  │
│  │ - patient_id (UUID, FK to patients.patient_id)            │  │
│  │ - medication_name, generic_name                            │  │
│  │ - dosage, frequency, route                                 │  │
│  │ - medication_status ('Active', 'Completed')                │  │
│  │ - prescription_date, start_date, end_date                  │  │
│  │ - prescribed_by (UUID, FK to healthcare_providers)         │  │
│  │ - instructions, notes, refills_remaining                   │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Backend API Development

#### Step 1.1: Update Lambda Database Handler
**File:** `lambda/database-handler/index.py`

**Add New Functions:**

```python
def get_patient_medications(patient_id: str, active_only: bool = False) -> Dict[str, Any]:
    """
    Retrieve medications for a specific patient

    Args:
        patient_id: Patient's UUID (Cognito ID)
        active_only: If True, return only active medications

    Returns:
        Dictionary with medications list and metadata
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Base query with JOIN to get prescriber information
        query = """
            SELECT
                m.medication_id,
                m.medication_name,
                m.generic_name,
                m.ndc_code,
                m.dosage,
                m.frequency,
                m.route,
                m.quantity_prescribed,
                m.refills_remaining,
                m.prescription_date,
                m.start_date,
                m.end_date,
                m.medication_status,
                m.instructions,
                m.notes,
                hp.first_name || ' ' || hp.last_name as prescribed_by_name,
                hp.specialty as prescriber_specialty
            FROM medications m
            LEFT JOIN healthcare_providers hp ON m.prescribed_by = hp.provider_id
            WHERE m.patient_id = %s
        """

        params = [patient_id]

        # Add status filter if active_only
        if active_only:
            query += " AND m.medication_status = 'Active'"

        # IMPORTANT: Order by prescription date (newest first) for chronological display
        # This ensures medications appear from newest to oldest on the detail page
        query += " ORDER BY m.prescription_date DESC, m.created_at DESC"

        cursor.execute(query, params)
        medications = cursor.fetchall()

        cursor.close()
        connection.close()

        # Convert to list of dicts
        medication_list = [dict(med) for med in medications]

        return {
            "status": "success",
            "patient_id": patient_id,
            "medications": medication_list,
            "count": len(medication_list),
            "active_only": active_only
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving medications: {str(e)}",
            "patient_id": patient_id
        }
```

**Add Route Handlers:**

```python
def lambda_handler(event, context):
    """Main Lambda handler with medication routes"""

    # ... existing code ...

    # NEW: Get all medications for a patient
    if path == f"/medications/{patient_id}":
        if http_method == 'GET':
            result = get_patient_medications(patient_id, active_only=False)
            return {
                'statusCode': 200 if result['status'] == 'success' else 500,
                'headers': cors_headers,
                'body': json.dumps(result)
            }

    # NEW: Get active medications only
    if path == f"/medications/{patient_id}/active":
        if http_method == 'GET':
            result = get_patient_medications(patient_id, active_only=True)
            return {
                'statusCode': 200 if result['status'] == 'success' else 500,
                'headers': cors_headers,
                'body': json.dumps(result)
            }

    # ... existing code ...
```

**Deployment:**
- Test locally with sample patient_id
- Deploy Lambda function
- Verify endpoints in API Gateway
- Test with Postman/curl

---

#### Step 1.2: (Optional) Add Agent Tool Functions
**File:** `agent/patient_database_tool.py`

**Add Medication Functions:**

```python
def get_patient_medications(patient_id: str, active_only: bool = False) -> Dict[str, Any]:
    """
    Retrieve medications for a patient via AgentCore Gateway

    Args:
        patient_id: Patient's UUID (Cognito ID)
        active_only: If True, return only active medications

    Returns:
        Dictionary containing medication data
    """
    try:
        gateway_url = get_gateway_url()
        if not gateway_url:
            return {
                "status": "error",
                "message": "Gateway URL not configured"
            }

        # Choose endpoint based on active_only flag
        endpoint = "/active" if active_only else ""
        url = f"{gateway_url}/medications/{patient_id}{endpoint}"

        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            return response.json()
        else:
            return {
                "status": "error",
                "message": f"Failed to retrieve medications",
                "status_code": response.status_code
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error accessing medications: {str(e)}"
        }

def format_medication_summary(medication: Dict[str, Any]) -> str:
    """
    Format medication data for display

    Args:
        medication: Medication data dictionary

    Returns:
        Formatted string with medication information
    """
    try:
        summary = f"**{medication.get('medication_name', 'Unknown')}**"
        if medication.get('generic_name'):
            summary += f" ({medication['generic_name']})\n"
        else:
            summary += "\n"

        summary += f"- Dosage: {medication.get('dosage', 'N/A')}\n"
        summary += f"- Frequency: {medication.get('frequency', 'N/A')}\n"
        summary += f"- Status: {medication.get('medication_status', 'N/A')}\n"

        if medication.get('prescribed_by_name'):
            summary += f"- Prescribed by: {medication['prescribed_by_name']}\n"

        if medication.get('instructions'):
            summary += f"- Instructions: {medication['instructions']}\n"

        return summary

    except Exception as e:
        return f"Error formatting medication: {str(e)}"
```

---

### Phase 2: Frontend - HomePage Medication Card

**DECISION: SKIP API UTILITY** - For only 2 API calls (HomePage active meds, MedicationsDetail all meds), creating a separate utility file adds unnecessary complexity. We'll define interfaces inline and make fetch calls directly in components.

#### Step 2.1: ~~Create API Client Utility~~ (SKIPPED)
**File:** ~~`frontend/src/utils/api.ts`~~ (NOT NEEDED)

```typescript
// API client for backend endpoints
const API_BASE_URL = import.meta.env.VITE_API_GATEWAY_URL || '/api';

export interface Medication {
  medication_id: string;
  medication_name: string;
  generic_name?: string;
  dosage: string;
  frequency: string;
  route: string;
  medication_status: 'Active' | 'Completed';
  prescription_date: string;
  start_date: string;
  end_date?: string;
  instructions?: string;
  notes?: string;
  refills_remaining?: number;
  prescribed_by_name?: string;
  prescriber_specialty?: string;
}

export interface MedicationsResponse {
  status: 'success' | 'error';
  patient_id: string;
  medications: Medication[];
  count: number;
  active_only: boolean;
  message?: string;
}

export async function getPatientMedications(
  patientId: string,
  activeOnly: boolean = false
): Promise<MedicationsResponse> {
  const endpoint = activeOnly ? 'active' : '';
  const url = `${API_BASE_URL}/medications/${patientId}${endpoint ? '/' + endpoint : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch medications: ${response.statusText}`);
  }

  return response.json();
}
```

---

#### Step 2.2: Update HomePage Component
**File:** `frontend/src/HomePage.tsx`

**Add Imports:**
```typescript
import { useEffect, useState } from 'react';
import { Alert } from '@cloudscape-design/components';
import { getPatientMedications, Medication } from './utils/api';
```

**Add State Management:**
```typescript
const HomePage = () => {
  const [activeMedications, setActiveMedications] = useState<Medication[]>([]);
  const [medicationsLoading, setMedicationsLoading] = useState(true);
  const [medicationsError, setMedicationsError] = useState<string | null>(null);

  // Get current user's Cognito ID (TODO: implement based on auth setup)
  const getCurrentUserId = (): string | null => {
    // Option 1: From Cognito context/hook
    // const { user } = useAuth();
    // return user?.username;

    // Option 2: From session storage
    // return sessionStorage.getItem('cognitoUserId');

    // Option 3: From auth state in App.tsx (pass as prop)
    // return props.userId;

    // Placeholder - replace with actual implementation
    return 'USER_ID_PLACEHOLDER';
  };

  // Fetch active medications on component mount
  useEffect(() => {
    const fetchMedications = async () => {
      const userId = getCurrentUserId();
      if (!userId) {
        setMedicationsError('User not authenticated');
        setMedicationsLoading(false);
        return;
      }

      try {
        setMedicationsLoading(true);
        const response = await getPatientMedications(userId, true);

        if (response.status === 'success') {
          setActiveMedications(response.medications);
          setMedicationsError(null);
        } else {
          setMedicationsError(response.message || 'Failed to load medications');
        }
      } catch (error) {
        setMedicationsError('Unable to load medications. Please try again later.');
        console.error('Error fetching medications:', error);
      } finally {
        setMedicationsLoading(false);
      }
    };

    fetchMedications();
  }, []);

  // ... existing dashboardCards state ...
```

**Update Medications Card Description:**
```typescript
const dashboardCards: DashboardCard[] = [
  {
    id: 'medications',
    title: 'Medications',
    description: medicationsLoading
      ? 'Loading your medications...'
      : medicationsError
      ? 'Unable to load medications'
      : activeMedications.length === 0
      ? 'No active medications'
      : `You have ${activeMedications.length} active medication${activeMedications.length !== 1 ? 's' : ''}`,
    icon: '💊',
    route: '#medications',
  },
  // ... other cards ...
];
```

**Add Medication Preview (Optional):**
Insert before Cards component:
```typescript
{/* Medication Preview Section */}
{!medicationsLoading && !medicationsError && activeMedications.length > 0 && (
  <Container>
    <SpaceBetween size="s">
      <Box variant="h3">Your Active Medications</Box>
      <Box variant="p" color="text-body-secondary">
        {activeMedications.slice(0, 3).map((med, index) => (
          <div key={med.medication_id}>
            <strong>{med.medication_name}</strong> - {med.dosage}, {med.frequency}
          </div>
        ))}
        {activeMedications.length > 3 && (
          <div style={{ marginTop: '8px', color: '#0972d3' }}>
            +{activeMedications.length - 3} more medication{activeMedications.length - 3 !== 1 ? 's' : ''}
          </div>
        )}
      </Box>
    </SpaceBetween>
  </Container>
)}

{/* Error Alert */}
{medicationsError && (
  <Alert type="error" header="Medication Error">
    {medicationsError}
  </Alert>
)}
```

---

### Phase 3: Frontend - MedicationsDetail Page

#### Step 3.1: Complete MedicationsDetail Implementation
**File:** `frontend/src/MedicationsDetail.tsx`

**Full Implementation:**
```typescript
import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Container,
  ContentLayout,
  Header,
  SpaceBetween,
  Table,
  Tabs,
  Badge,
} from '@cloudscape-design/components';
import { getPatientMedications, Medication } from './utils/api';

const MedicationsDetail = () => {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('all');

  // Get current user ID (same as HomePage)
  const getCurrentUserId = (): string | null => {
    return 'USER_ID_PLACEHOLDER'; // Replace with actual implementation
  };

  // Fetch all medications on mount
  useEffect(() => {
    const fetchMedications = async () => {
      const userId = getCurrentUserId();
      if (!userId) {
        setError('User not authenticated');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await getPatientMedications(userId, false); // Get all medications

        if (response.status === 'success') {
          setMedications(response.medications);
          setError(null);
        } else {
          setError(response.message || 'Failed to load medications');
        }
      } catch (err) {
        setError('Unable to load medications. Please try again later.');
        console.error('Error fetching medications:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMedications();
  }, []);

  // Filter medications based on active tab
  // Note: Medications are already sorted by prescription_date DESC from backend
  // Filtering preserves the chronological order (newest to oldest)
  const filteredMedications = medications.filter(med => {
    if (activeTab === 'active') return med.medication_status === 'Active';
    if (activeTab === 'completed') return med.medication_status === 'Completed';
    return true; // 'all' tab
  });

  const activeMedCount = medications.filter(m => m.medication_status === 'Active').length;
  const completedMedCount = medications.filter(m => m.medication_status === 'Completed').length;

  return (
    <ContentLayout
      header={
        <Header
          variant="h1"
          description="View and manage your medication history"
          actions={
            <Button
              onClick={() => { window.location.hash = 'home'; }}
              iconName="arrow-left"
            >
              Back to Home
            </Button>
          }
        >
          Medications Management
        </Header>
      }
    >
      <SpaceBetween size="l">
        {error && (
          <Alert type="error" header="Error Loading Medications">
            {error}
          </Alert>
        )}

        <Container>
          <Tabs
            activeTabId={activeTab}
            onChange={({ detail }) => setActiveTab(detail.activeTabId)}
            tabs={[
              {
                id: 'all',
                label: `All (${medications.length})`,
                content: null,
              },
              {
                id: 'active',
                label: `Active (${activeMedCount})`,
                content: null,
              },
              {
                id: 'completed',
                label: `Completed (${completedMedCount})`,
                content: null,
              },
            ]}
          />

          <Table
            loading={loading}
            empty={
              <Box textAlign="center" color="text-body-secondary">
                No medications found
              </Box>
            }
            columnDefinitions={[
              {
                id: 'medication_name',
                header: 'Medication',
                cell: (item) => (
                  <div>
                    <strong>{item.medication_name}</strong>
                    {item.generic_name && (
                      <div style={{ fontSize: '0.9em', color: '#666' }}>
                        ({item.generic_name})
                      </div>
                    )}
                  </div>
                ),
                width: 200,
              },
              {
                id: 'dosage',
                header: 'Dosage',
                cell: (item) => item.dosage,
                width: 120,
              },
              {
                id: 'frequency',
                header: 'Frequency',
                cell: (item) => item.frequency,
                width: 180,
              },
              {
                id: 'status',
                header: 'Status',
                cell: (item) => (
                  <Badge color={item.medication_status === 'Active' ? 'green' : 'grey'}>
                    {item.medication_status}
                  </Badge>
                ),
                width: 100,
              },
              {
                id: 'prescription_date',
                header: 'Prescribed',
                cell: (item) => new Date(item.prescription_date).toLocaleDateString(),
                width: 120,
              },
              {
                id: 'prescribed_by',
                header: 'Prescriber',
                cell: (item) => item.prescribed_by_name || 'N/A',
                width: 150,
              },
              {
                id: 'refills',
                header: 'Refills',
                cell: (item) =>
                  item.medication_status === 'Active'
                    ? item.refills_remaining?.toString() || '0'
                    : '-',
                width: 80,
              },
            ]}
            items={filteredMedications}
            expandableRows={{
              getItemChildren: (item) => [],
              expandedItems: [],
              onExpandableItemToggle: () => {},
              expandableContentHeader: () => null,
              expandableContent: (item) => (
                <Container>
                  <SpaceBetween size="m">
                    <div>
                      <Box variant="h4">Administration</Box>
                      <Box variant="p">
                        <strong>Route:</strong> {item.route}
                        <br />
                        <strong>Start Date:</strong> {new Date(item.start_date).toLocaleDateString()}
                        {item.end_date && (
                          <>
                            <br />
                            <strong>End Date:</strong> {new Date(item.end_date).toLocaleDateString()}
                          </>
                        )}
                      </Box>
                    </div>

                    {item.instructions && (
                      <div>
                        <Box variant="h4">Instructions</Box>
                        <Box variant="p">{item.instructions}</Box>
                      </div>
                    )}

                    {item.notes && (
                      <div>
                        <Box variant="h4">Notes</Box>
                        <Box variant="p" color="text-body-secondary">
                          {item.notes}
                        </Box>
                      </div>
                    )}
                  </SpaceBetween>
                </Container>
              ),
            }}
          />
        </Container>
      </SpaceBetween>
    </ContentLayout>
  );
};

export default MedicationsDetail;
```

---

### Phase 4: Authentication Integration

#### Step 4.1: Extract Cognito User ID

**Options for getting current user ID:**

**Option A: From App.tsx User State (Recommended)**
- Pass user ID as prop from App.tsx to HomePage and MedicationsDetail
- App.tsx already has `user` state from Cognito authentication

**Modify App.tsx:**
```typescript
// In renderContent() function
if (activePage === 'home') {
  return <HomePage userId={user?.username} />;
}

if (activePage === 'medications') {
  return <MedicationsDetail userId={user?.username} />;
}
```

**Update HomePage and MedicationsDetail:**
```typescript
interface Props {
  userId?: string;
}

const HomePage = ({ userId }: Props) => {
  const getCurrentUserId = (): string | null => {
    return userId || null;
  };
  // ... rest of component
};
```

**Option B: Create Auth Context (Alternative)**
- Create `frontend/src/contexts/AuthContext.tsx`
- Provide user data throughout app
- Access via `useAuth()` hook

**Option C: Session Storage (Quick Fix)**
- Store Cognito ID in sessionStorage on login
- Retrieve in components as needed
- Less recommended due to potential staleness

---

### Phase 5: Configuration and Deployment

#### Step 5.1: Environment Configuration
**File:** `frontend/.env` (or `.env.local`)

```bash
# API Gateway URL for medications endpoint
VITE_API_GATEWAY_URL=https://your-api-gateway-url.amazonaws.com/prod
```

#### Step 5.2: Update CDK Stack (if needed)
**File:** `cdk/lib/runtime-stack.ts`

Ensure Lambda has necessary permissions:
```typescript
// Add RDS access permissions to Lambda role
lambdaRole.addToPolicy(new iam.PolicyStatement({
  actions: [
    'rds-data:ExecuteStatement',
    'rds-data:BatchExecuteStatement',
  ],
  resources: [rdsClusterArn],
}));

// Add SSM parameter access for gateway URL
lambdaRole.addToPolicy(new iam.PolicyStatement({
  actions: ['ssm:GetParameter'],
  resources: [`arn:aws:ssm:${region}:${account}:parameter/app/medicalassistant/*`],
}));
```

#### Step 5.3: API Gateway Routes
Add new routes in API Gateway:
- `GET /medications/{patient_id}` → Lambda integration
- `GET /medications/{patient_id}/active` → Lambda integration
- Enable CORS for both routes
- Configure authentication (Cognito authorizer)

---

## Testing Plan

### Unit Tests
- Lambda functions with mock database connections
- Frontend components with mock API responses
- Error handling scenarios

### Integration Tests
1. **Database Query Tests:**
   - Query medications for valid patient_id
   - Query with active_only=true
   - Query with non-existent patient_id
   - Query with patient who has no medications

2. **API Endpoint Tests:**
   - GET /medications/{id} returns all medications
   - GET /medications/{id}/active returns only active
   - Authentication required (401 without auth)
   - Authorization (users can only access their own data)

3. **Frontend Tests:**
   - HomePage displays medication count correctly
   - MedicationsDetail displays all medications
   - Tab filtering works (All/Active/Completed)
   - Error states display appropriately
   - Loading states work correctly

### Manual Testing Checklist
- [ ] HomePage loads and displays active medication count
- [ ] Clicking "Learn more" navigates to MedicationsDetail
- [ ] MedicationsDetail displays all medications in table
- [ ] **Medications are sorted chronologically (newest prescription_date at top)**
- [ ] Table columns show correct data
- [ ] Expandable rows show additional details
- [ ] Tabs filter medications correctly (Active/Completed/All)
- [ ] Tab filtering maintains chronological order within each filter
- [ ] "Back to Home" button works
- [ ] Error handling works (network error, no data)
- [ ] Loading states display correctly
- [ ] Mobile responsive layout works
- [ ] Unauthenticated users cannot access medications

---

## Security Considerations

### Data Access Control
- **Authentication:** Require valid Cognito token for all medication endpoints
- **Authorization:** Verify `patient_id` matches authenticated user's Cognito ID
- **SQL Injection Prevention:** Use parameterized queries (already implemented)
- **Data Encryption:** Ensure HTTPS for all API calls
- **Sensitive Data:** Mask or redact sensitive medication info if needed

### HIPAA Compliance Notes
- Medications are Protected Health Information (PHI)
- Ensure audit logging for all medication data access
- Implement data retention policies
- Secure data at rest (RDS encryption)
- Secure data in transit (TLS/HTTPS)

---

## Implementation Order

### Week 1: Backend Foundation
1. ✅ **Day 1-2:** Lambda handler functions
   - Implement `get_patient_medications()`
   - Add route handlers
   - Test with sample data

2. ✅ **Day 3:** API Gateway configuration
   - Add medication endpoints
   - Configure CORS
   - Set up Cognito authorizer

3. ✅ **Day 4-5:** Testing & deployment
   - Unit tests for Lambda functions
   - Integration tests for API
   - Deploy to dev environment

### Week 2: Frontend Implementation
4. ✅ **Day 1-2:** HomePage medication card
   - Create API client utility
   - Add state management
   - Implement medication fetching
   - Update card display

5. ✅ **Day 3-4:** MedicationsDetail page
   - Complete page implementation
   - Add table with all columns
   - Implement tab filtering
   - Add expandable row details

6. ✅ **Day 5:** Authentication integration
   - Extract Cognito user ID
   - Pass to API calls
   - Test with real user accounts

### Week 3: Polish & Deploy
7. ✅ **Day 1-2:** Testing
   - Frontend component tests
   - End-to-end testing
   - Error scenario testing

8. ✅ **Day 3-4:** UI/UX refinement
   - Mobile responsiveness
   - Loading state polish
   - Error message clarity

9. ✅ **Day 5:** Production deployment
   - Deploy backend to prod
   - Deploy frontend to prod
   - Monitor for errors

---

## File Changes Summary

### New Files (2)
1. ✅ `frontend/src/utils/api.ts` - API client with medication functions
2. ✅ `frontend/.env.local` - Environment configuration (if not exists)

### Modified Files (3)
1. ✅ `lambda/database-handler/index.py` - Add medication endpoints and functions
2. ✅ `frontend/src/HomePage.tsx` - Add medication state and display
3. ✅ `frontend/src/MedicationsDetail.tsx` - Complete implementation from placeholder

### Optional Files (2)
1. ⚪ `agent/patient_database_tool.py` - Add medication utility functions
2. ⚪ `cdk/lib/runtime-stack.ts` - Update permissions if needed

---

## Success Metrics

### Functional Metrics
- ✅ Active medications display on HomePage within 2 seconds
- ✅ MedicationsDetail loads full history within 2 seconds
- ✅ **Medications display in chronological order (newest first)**
- ✅ Zero unauthorized access to other patients' data
- ✅ 100% of test cases pass

### User Experience Metrics
- ✅ Medication data is easy to read and understand
- ✅ Navigation is intuitive
- ✅ Error messages are clear and actionable
- ✅ Mobile experience is smooth

---

## Risks and Mitigation

### Risk 1: Performance Issues with Large Medication Lists
**Mitigation:**
- Implement pagination on backend (return max 50 records)
- Add frontend pagination controls
- Consider virtualized table for large datasets

### Risk 2: Database Connection Timeouts
**Mitigation:**
- Implement connection pooling in Lambda
- Add retry logic for transient failures
- Set appropriate timeout values (30s)

### Risk 3: User ID Mismatch (Cognito ID vs Patient ID)
**Mitigation:**
- Verify patient_id mapping during patient registration
- Add data migration script if needed
- Document mapping clearly

### Risk 4: HIPAA Compliance Gaps
**Mitigation:**
- Conduct security review before production
- Implement comprehensive audit logging
- Ensure encryption at rest and in transit
- Add data retention policies

---

## Future Enhancements

### Phase 2 Features (Post-MVP)
- **Medication Reminders:** Set notifications for medication times
- **Refill Tracking:** Alert when refills are low
- **Drug Interactions:** Check for potential interactions
- **Medication Search:** Search by name, status, or date range
- **Export Functionality:** Download medication history as PDF
- **Barcode Scanning:** Add medications via barcode scan
- **Medication Images:** Display pill images for identification
- **Adherence Tracking:** Track whether medications were taken

### Advanced Features
- **Integration with Pharmacy:** Direct refill requests
- **Side Effect Tracking:** Log and track side effects
- **Dosage Calculator:** Based on weight/condition
- **Medication Calendar:** Visual calendar view
- **Multi-language Support:** Translate medication info
- **Voice Commands:** Add/search medications via voice

---

## Dependencies

### Backend
- Python 3.x
- psycopg2 (PostgreSQL adapter)
- boto3 (AWS SDK)
- AWS Lambda
- AWS RDS PostgreSQL
- AWS API Gateway
- AWS Systems Manager (SSM)

### Frontend
- React 18.3.1
- TypeScript
- AWS Cloudscape Design System
- Amazon Cognito (authentication)

---

## Rollback Plan

If issues arise in production:

1. **Immediate Rollback:**
   - Revert Lambda deployment to previous version
   - Disable new API Gateway routes
   - Revert frontend deployment

2. **Data Integrity:**
   - No database schema changes in this phase
   - Read-only operations (no data modification)
   - Safe to rollback without data loss

3. **Communication:**
   - Notify users of temporary unavailability
   - Provide estimated restoration time
   - Update status page

---

## Next Steps

1. **Review this plan** with team and stakeholders
2. **Get approval** for implementation approach
3. **Set up development environment** with test data
4. **Begin Phase 1** (Backend API Development)
5. **Schedule weekly check-ins** to track progress
6. **Document any deviations** from this plan
7. **Update this document** as implementation evolves

---

*End of Planning Document*
