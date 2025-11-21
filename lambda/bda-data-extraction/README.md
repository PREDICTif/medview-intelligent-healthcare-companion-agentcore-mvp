# BDA Data Extraction Lambda

Lambda function for Big Data Analytics (BDA) data extraction and processing.

## Features

- Extract data from S3 buckets (raw, processed, curated)
- Extract data from medical database using RDS Data API
- Process and transform data between buckets
- Health check endpoint

## Environment Variables

- `RAW_BUCKET` - Raw data S3 bucket name
- `PROCESSED_BUCKET` - Processed data S3 bucket name
- `CURATED_BUCKET` - Curated data S3 bucket name
- `DB_CLUSTER_ARN` - Aurora database cluster ARN
- `DB_SECRET_ARN` - Database credentials secret ARN
- `DB_NAME` - Database name (default: medical_records)

## Actions

### extract_from_s3
Extract data from an S3 bucket.

**Request:**
```json
{
  "action": "extract_from_s3",
  "bucket": "bucket-name",
  "key": "path/to/file.json"
}
```

### extract_from_db
Extract data from the medical database.

**Request:**
```json
{
  "action": "extract_from_db",
  "query": "SELECT * FROM patients LIMIT 10"
}
```

### process_data
Process data from one bucket to another.

**Request:**
```json
{
  "action": "process_data",
  "source_bucket": "raw-bucket",
  "dest_bucket": "processed-bucket",
  "key": "data.json"
}
```

### health_check
Check Lambda function health.

**Request:**
```json
{
  "action": "health_check"
}
```

## Permissions

The Lambda has the following permissions:
- Read/Write access to raw, processed, and curated S3 buckets
- Read access to database secrets
- RDS Data API access for database queries
- KMS decrypt for encrypted data
- VPC access for database connectivity

## Deployment

The Lambda is deployed as part of the MihcStack:

```bash
cd cdk
npx cdk deploy MihcStack
```

## Testing

Invoke the Lambda directly:

```bash
aws lambda invoke \
  --function-name <function-name> \
  --payload '{"action":"health_check"}' \
  response.json
```

## Configuration

- **Runtime:** Python 3.11
- **Timeout:** 15 minutes
- **Memory:** 1024 MB
- **VPC:** Deployed in private subnets with egress
- **Security:** Uses Lambda security group with database access
