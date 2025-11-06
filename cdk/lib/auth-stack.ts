import * as cdk from 'aws-cdk-lib';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import { Construct } from 'constructs';

export class AuthStack extends cdk.Stack {
    public readonly userPool: cognito.UserPool;
    public readonly userPoolClient: cognito.UserPoolClient;

    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        // Cognito User Pool
        this.userPool = new cognito.UserPool(this, 'AgentCoreUserPool', {
            userPoolName: 'agentcore-users',
            selfSignUpEnabled: true,
            signInAliases: {
                email: true,
            },
            autoVerify: {
                email: true,
            },
            standardAttributes: {
                email: {
                    required: true,
                    mutable: false,
                },
            },
            passwordPolicy: {
                minLength: 8,
                requireLowercase: true,
                requireUppercase: true,
                requireDigits: true,
                requireSymbols: false,
            },
            accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
            removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev - change to RETAIN for prod
        });

        // User Pool Client for frontend
        this.userPoolClient = new cognito.UserPoolClient(this, 'AgentCoreUserPoolClient', {
            userPool: this.userPool,
            userPoolClientName: 'agentcore-web-client',
            authFlows: {
                userPassword: true,
                userSrp: true,
            },
            generateSecret: false, // Public client (frontend)
            preventUserExistenceErrors: true,
            // Token validity settings
            accessTokenValidity: cdk.Duration.hours(1), // 1 hour access token
            idTokenValidity: cdk.Duration.hours(1), // 1 hour ID token  
            refreshTokenValidity: cdk.Duration.days(30), // 30 day refresh token
            // Enable token refresh
            authSessionValidity: cdk.Duration.minutes(3), // 3 minutes for auth flow
        });

        // Outputs
        new cdk.CfnOutput(this, 'UserPoolId', {
            value: this.userPool.userPoolId,
            description: 'Cognito User Pool ID',
            exportName: 'AgentCoreUserPoolId',
        });

        new cdk.CfnOutput(this, 'UserPoolArn', {
            value: this.userPool.userPoolArn,
            description: 'Cognito User Pool ARN',
            exportName: 'AgentCoreUserPoolArn',
        });

        new cdk.CfnOutput(this, 'UserPoolClientId', {
            value: this.userPoolClient.userPoolClientId,
            description: 'Cognito User Pool Client ID',
            exportName: 'AgentCoreUserPoolClientId',
        });
    }
}
