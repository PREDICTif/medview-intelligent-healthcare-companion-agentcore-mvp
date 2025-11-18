import {
  Box,
  Button,
  Container,
  ContentLayout,
  Header,
  SpaceBetween,
} from '@cloudscape-design/components';

const LifestyleDetail = () => {
  return (
    <ContentLayout
      header={
        <Header variant="h1">
          Lifestyle & Wellness
        </Header>
      }
    >
      <Container>
        <SpaceBetween size="l">
          <Box variant="p" fontSize="body-l" color="text-body-secondary">
            Lifestyle tracking features coming soon.
          </Box>
          <Box variant="p">
            This page will allow you to:
          </Box>
          <ul>
            <li>Track daily activities and exercise</li>
            <li>Monitor nutrition and dietary habits</li>
            <li>Log sleep patterns and quality</li>
            <li>Set and track wellness goals</li>
            <li>View health metrics and trends</li>
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

export default LifestyleDetail;
