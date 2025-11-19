import { useEffect, useState } from 'react';
import {
  Box,
  Cards,
  Container,
  ContentLayout,
  Grid,
  Header,
  SpaceBetween,
} from '@cloudscape-design/components';

interface DashboardCard {
  id: string;
  title: string;
  description: string;
  icon: string;
  route: string;
}

interface Medication {
  medication_id: string;
  medication_name: string;
  generic_name?: string;
  dosage: string;
  frequency: string;
  medication_status: 'Active' | 'Completed';
  prescription_date: string;
}

interface HomePageProps {
  userId?: string;
}

const HomePage = ({ userId }: HomePageProps) => {
  const [activeMedications, setActiveMedications] = useState<Medication[]>([]);
  const [medicationsLoading, setMedicationsLoading] = useState(true);
  const [medicationsError, setMedicationsError] = useState<string | null>(null);

  // Fetch active medications on mount
  useEffect(() => {
    const fetchMedications = async () => {
      if (!userId) {
        setMedicationsError('User not authenticated');
        setMedicationsLoading(false);
        return;
      }

      try {
        setMedicationsLoading(true);
        const response = await fetch(`/api/medications?action=get_patient_medications&patient_id=${userId}&active_only=true`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.status === 'success') {
          setActiveMedications(data.medications || []);
          setMedicationsError(null);
        } else {
          setMedicationsError(data.message || 'Failed to load medications');
        }
      } catch (error) {
        setMedicationsError('Unable to load medications');
        console.error('Error fetching medications:', error);
      } finally {
        setMedicationsLoading(false);
      }
    };

    fetchMedications();
  }, [userId]);

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
    {
      id: 'appointments',
      title: 'Appointments',
      description: 'Schedule and view your healthcare appointments and medical consultations.',
      icon: '📅',
      route: '#appointments',
    },
    {
      id: 'lifestyle',
      title: 'Lifestyle & Wellness',
      description: 'Track your lifestyle habits, wellness goals, and health metrics.',
      icon: '🏃',
      route: '#lifestyle',
    },
    {
      id: 'treatment',
      title: 'Treatment Recommendations',
      description: 'Get AI-powered personalized treatment insights and health recommendations.',
      icon: '🩺',
      route: '#treatment',
    },
  ];

  const handleCardClick = (route: string) => {
    window.location.hash = route;
  };

  return (
    <ContentLayout
    //   header={
    //     <div style={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
    //       <Header variant="h1">
    //         Welcome to Medview Connect
    //       </Header>
    //     </div>
    //   }
    >
      <Grid
        gridDefinition={[
          { colspan: { default: 12, xs: 1, s: 1, m: 1 } },
          { colspan: { default: 12, xs: 10, s: 10, m: 10 } },
          { colspan: { default: 12, xs: 1, s: 1, m: 1 } }
        ]}
      >
        <div />
        <SpaceBetween size="m">
          <div style={{ textAlign: 'center' }}>
            <h1 style={{ 
              fontSize: 'var(--awsui-font-heading-xl-size, 2rem)',
              fontWeight: 'bold',
              margin: 0,
              padding: '20px 0'
            }}>
              Welcome to Medview Connect
            </h1>
          </div>
          <Container>
            <SpaceBetween size="m">
              <Box variant="h2" fontSize="heading-l">
                Your Intelligent Healthcare Companion
              </Box>
              <Box variant="p" color="text-body-secondary">
                Medview Connect is your comprehensive healthcare management platform,
                powered by AI to help you manage your health journey. Access your medical
                information, track medications, schedule appointments, and receive personalized
                health insights all in one place.
              </Box>
            </SpaceBetween>
          </Container>

          <Cards
            cardDefinition={{
              header: (item) => (
                <Box fontSize="heading-m" fontWeight="bold">
                  <span style={{ marginRight: '8px' }}>{item.icon}</span>
                  {item.title}
                </Box>
              ),
              sections: [
                {
                  id: 'description',
                  content: (item) => (
                    <Box variant="p" color="text-body-secondary">
                      {item.description}
                    </Box>
                  ),
                },
                {
                  id: 'action',
                  content: (item) => (
                    <Box textAlign="right">
                      <span 
                        onClick={() => handleCardClick(item.route)}
                        style={{ 
                          color: '#0972d3', 
                          cursor: 'pointer',
                          textDecoration: 'underline'
                        }}
                      >
                        Learn more →
                      </span>
                    </Box>
                  ),
                }
              ],
            }}
            items={dashboardCards}
            cardsPerRow={[
              { cards: 1 },
              { minWidth: 500, cards: 2 },
            ]}
            // onSelectionChange={({ detail }) => {
            //   if (detail.selectedItems.length > 0) {
            //     handleCardClick(detail.selectedItems[0].route);
            //   }
            // }}
          />
        </SpaceBetween>
        <div />
      </Grid>
    </ContentLayout>
  );
};

export default HomePage;
