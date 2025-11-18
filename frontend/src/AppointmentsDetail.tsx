import {
  Box,
  Button,
  Container,
  ContentLayout,
  Header,
  SpaceBetween,
} from '@cloudscape-design/components';

const AppointmentsDetail = () => {
  return (
    <ContentLayout
      header={
        <Header variant="h1">
          Appointments
        </Header>
      }
    >
      <Container>
        <SpaceBetween size="l">
          <Box variant="p" fontSize="body-l" color="text-body-secondary">
            Appointment scheduling features coming soon.
          </Box>
          <Box variant="p">
            This page will allow you to:
          </Box>
          <ul>
            <li>Schedule new medical appointments</li>
            <li>View upcoming and past appointments</li>
            <li>Receive appointment reminders</li>
            <li>Manage appointment details and notes</li>
            <li>Connect with healthcare providers</li>
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

export default AppointmentsDetail;
