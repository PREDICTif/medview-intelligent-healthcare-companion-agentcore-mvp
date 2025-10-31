param(
    [Parameter(Mandatory=$true)]
    [string]$UserPoolId,
    
    [Parameter(Mandatory=$true)]
    [string]$UserPoolClientId,
    
    [Parameter(Mandatory=$true)]
    [string]$AgentRuntimeArn,
    
    [Parameter(Mandatory=$true)]
    [string]$Region,
    
    [Parameter(Mandatory=$false)]
    [string]$LambdaFunctionUrl = ""
)

Write-Host "Building frontend with:"
Write-Host "  User Pool ID: $UserPoolId"
Write-Host "  User Pool Client ID: $UserPoolClientId"
Write-Host "  Agent Runtime ARN: $AgentRuntimeArn"
Write-Host "  Region: $Region"

# Set environment variables for build
$env:VITE_USER_POOL_ID = $UserPoolId
$env:VITE_USER_POOL_CLIENT_ID = $UserPoolClientId
$env:VITE_AGENT_RUNTIME_ARN = $AgentRuntimeArn
$env:VITE_REGION = $Region

# Set Lambda Function URL if provided
if (-not [string]::IsNullOrEmpty($LambdaFunctionUrl)) {
    Write-Host "  Lambda Function URL: $LambdaFunctionUrl"
    $env:VITE_LAMBDA_FUNCTION_URL = $LambdaFunctionUrl
} else {
    Write-Host "  Lambda Function URL: Not provided (patient registration will not work)" -ForegroundColor Yellow
}

# Build frontend
Set-Location frontend
npm run build

Set-Location ..
Write-Host "Frontend build complete"
