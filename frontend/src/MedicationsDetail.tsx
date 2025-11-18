import {
  Box,
  Button,
  Container,
  ContentLayout,
  Header,
  SpaceBetween,
} from '@cloudscape-design/components';

const MedicationsDetail = () => {
  return (
    <ContentLayout
      header={
        <Header variant="h1">
          Medications Management
        </Header>
      }
    >
      <Container>
        <SpaceBetween size="l">
          <Box variant="p" fontSize="body-l" color="text-body-secondary">
            Medication tracking and management features coming soon.
          </Box>
          <Box variant="p">
            This page will allow you to:
          </Box>
          <ul>
            <li>View your current medications and prescriptions</li>
            <li>Track medication schedules and dosages</li>
            <li>Set reminders for medication intake</li>
            <li>View medication history and refill status</li>
            <li>Manage prescription information</li>
          </ul>
          <Box>
            <Button
              onClick={() => {
                window.location.hash = 'home';
              }}
              iconName="arrow-left"
            >
              Back to Home
            </Button>
          </Box>
        </SpaceBetween>
      </Container>
    </ContentLayout>
  );
};

export default MedicationsDetail;
