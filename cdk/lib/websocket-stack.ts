import * as cdk from 'aws-cdk-lib';
import * as apigatewayv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { NodejsFunction } from 'aws-cdk-lib/aws-lambda-nodejs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import { WebSocketLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { Construct } from 'constructs';
import * as path from 'path';

export interface WebSocketStackProps extends cdk.StackProps {
  userPool: cognito.IUserPool;
  agentRuntimeArn: string;
  region: string;
}

export class WebSocketStack extends cdk.Stack {
  public readonly webSocketUrl: string;

  constructor(scope: Construct, id: string, props: WebSocketStackProps) {
    super(scope, id, props);

    // Lambda execution role with necessary permissions
    const lambdaRole = new iam.Role(this, 'WebSocketLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    // Grant Bedrock permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeAgent',
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream',
      ],
      resources: ['*'],
    }));

    // Grant API Gateway Management permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'execute-api:ManageConnections',
        'execute-api:Invoke',
      ],
      resources: ['*'],
    }));

    // Connect Lambda - using NodejsFunction to auto-compile TypeScript
    const connectFunction = new NodejsFunction(this, 'ConnectFunction', {
      entry: path.join(__dirname, '../../lambda/websocket-handlers/index.ts'),
      handler: 'connectHandler',
      runtime: lambda.Runtime.NODEJS_22_X,
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      bundling: {
        minify: false,
        sourceMap: true,
        externalModules: ['@aws-sdk/*'], // Use Lambda's built-in AWS SDK
      },
      environment: {
        AGENT_RUNTIME_ARN: props.agentRuntimeArn,
        REGION: props.region,
      },
    });

    // Disconnect Lambda
    const disconnectFunction = new NodejsFunction(this, 'DisconnectFunction', {
      entry: path.join(__dirname, '../../lambda/websocket-handlers/index.ts'),
      handler: 'disconnectHandler',
      runtime: lambda.Runtime.NODEJS_22_X,
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      bundling: {
        minify: false,
        sourceMap: true,
        externalModules: ['@aws-sdk/*'], // Use Lambda's built-in AWS SDK
      },
    });

    // Message Lambda
    const messageFunction = new NodejsFunction(this, 'MessageFunction', {
      entry: path.join(__dirname, '../../lambda/websocket-handlers/index.ts'),
      handler: 'messageHandler',
      runtime: lambda.Runtime.NODEJS_22_X,
      role: lambdaRole,
      timeout: cdk.Duration.minutes(5),
      bundling: {
        minify: false,
        sourceMap: true,
        externalModules: ['@aws-sdk/*'], // Only exclude AWS SDK; bundle @aws-crypto for SigV4
      },
      environment: {
        AGENT_RUNTIME_ARN: props.agentRuntimeArn,
        REGION: props.region,
      },
    });

    // WebSocket API
    const webSocketApi = new apigatewayv2.WebSocketApi(this, 'StreamingWebSocketApi', {
      apiName: 'medview-streaming-websocket',
      description: 'WebSocket API for streaming responses',
      connectRouteOptions: {
        integration: new WebSocketLambdaIntegration('ConnectIntegration', connectFunction),
      },
      disconnectRouteOptions: {
        integration: new WebSocketLambdaIntegration('DisconnectIntegration', disconnectFunction),
      },
      defaultRouteOptions: {
        integration: new WebSocketLambdaIntegration('MessageIntegration', messageFunction),
      },
    });

    // WebSocket Stage
    const stage = new apigatewayv2.WebSocketStage(this, 'ProductionStage', {
      webSocketApi,
      stageName: 'production',
      autoDeploy: true,
    });

    this.webSocketUrl = stage.url;

    // Outputs
    new cdk.CfnOutput(this, 'WebSocketURL', {
      value: this.webSocketUrl,
      description: 'WebSocket API URL',
      exportName: 'WebSocketApiUrl',
    });

    new cdk.CfnOutput(this, 'WebSocketApiId', {
      value: webSocketApi.apiId,
      description: 'WebSocket API ID',
    });
  }
}

