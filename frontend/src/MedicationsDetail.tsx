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

interface Medication {
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
}

interface MedicationsDetailProps {
  userId?: string;
}

const MedicationsDetail = ({ userId }: MedicationsDetailProps) => {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('all');
  const [expandedItems, setExpandedItems] = useState<Medication[]>([]);

  // Fetch all medications on mount
  useEffect(() => {
    const fetchMedications = async () => {
      if (!userId) {
        setError('User not authenticated');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await fetch(`/api/medications?action=get_patient_medications&patient_id=${userId}&active_only=false`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.status === 'success') {
          setMedications(data.medications || []);
          setError(null);
        } else {
          setError(data.message || 'Failed to load medications');
        }
      } catch (err) {
        setError('Unable to load medications. Please try again later.');
        console.error('Error fetching medications:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMedications();
  }, [userId]);

  // Filter medications based on active tab (preserves chronological order)
  const filteredMedications = medications.filter(med => {
    if (activeTab === 'active') return med.medication_status === 'Active';
    if (activeTab === 'completed') return med.medication_status === 'Completed';
    return true;
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
                cell: (item) => {
                  // Check if this is a detail row
                  if ((item as any)._isDetailRow) {
                    return (
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
                    );
                  }
                  return (
                    <div>
                      <strong>{item.medication_name}</strong>
                      {item.generic_name && (
                        <div style={{ fontSize: '0.9em', color: '#666' }}>
                          ({item.generic_name})
                        </div>
                      )}
                    </div>
                  );
                },
                width: 200,
              },
              {
                id: 'dosage',
                header: 'Dosage',
                cell: (item) => (item as any)._isDetailRow ? '' : item.dosage,
                width: 120,
              },
              {
                id: 'frequency',
                header: 'Frequency',
                cell: (item) => (item as any)._isDetailRow ? '' : item.frequency,
                width: 180,
              },
              {
                id: 'status',
                header: 'Status',
                cell: (item) => (item as any)._isDetailRow ? '' : (
                  <Badge color={item.medication_status === 'Active' ? 'green' : 'grey'}>
                    {item.medication_status}
                  </Badge>
                ),
                width: 100,
              },
              {
                id: 'prescription_date',
                header: 'Prescribed',
                cell: (item) => (item as any)._isDetailRow ? '' : new Date(item.prescription_date).toLocaleDateString(),
                width: 120,
              },
              {
                id: 'prescribed_by',
                header: 'Prescriber',
                cell: (item) => (item as any)._isDetailRow ? '' : (item.prescribed_by_name || 'N/A'),
                width: 150,
              },
              {
                id: 'refills',
                header: 'Refills',
                cell: (item) => (item as any)._isDetailRow ? '' : (
                  item.medication_status === 'Active'
                    ? item.refills_remaining?.toString() || '0'
                    : '-'
                ),
                width: 80,
              },
            ]}
            items={filteredMedications}
            expandableRows={{
              getItemChildren: (item) => {
                // Return a detail object when item is expanded
                const isExpanded = expandedItems.some(
                  expanded => expanded.medication_id === item.medication_id
                );
                return isExpanded ? [{ ...item, _isDetailRow: true }] : [];
              },
              isItemExpandable: () => true,
              expandedItems,
              onExpandableItemToggle: ({ detail }) => {
                const item = detail.item as Medication;
                setExpandedItems(prevItems =>
                  detail.expanded
                    ? [...prevItems, item]
                    : prevItems.filter(i => i.medication_id !== item.medication_id)
                );
              },
            }}
          />
        </Container>
      </SpaceBetween>
    </ContentLayout>
  );
};

export default MedicationsDetail;
