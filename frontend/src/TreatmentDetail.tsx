import {
  Box,
  Button,
  Container,
  ContentLayout,
  Header,
  SpaceBetween,
} from '@cloudscape-design/components';

const TreatmentDetail = () => {
  return (
    <ContentLayout
      header={
        <Header variant="h1">
          Treatment Recommendations
        </Header>
      }
    >
      <Container>
        <SpaceBetween size="l">
          <Box variant="p" fontSize="body-l" color="text-body-secondary">
            AI-powered treatment recommendations coming soon.
          </Box>
          <Box variant="p">
            This page will provide:
          </Box>
          <ul>
            <li>Personalized treatment insights based on your health data</li>
            <li>AI-powered health recommendations</li>
            <li>Treatment plan tracking and progress</li>
            <li>Evidence-based health suggestions</li>
            <li>Integration with your care team's recommendations</li>
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

export default TreatmentDetail;
