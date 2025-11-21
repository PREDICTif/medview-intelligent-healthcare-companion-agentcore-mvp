import json
import logging
import time
import os
from dataclasses import dataclass
from uuid import uuid4
from urllib.parse import urlparse


INITIAL = "INITIAL"
FETCHED_BUT_CHECK = "INTERNAL_FETCHED_BUT_CHECK"
INTERNAL_STATUS_INITIAL = "INTERNAL_INITIAL"


class ArgsException(Exception):

    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)


class ExtractionException(Exception):

    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)


class TransformException(Exception):

    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)


@dataclass
class Blueprint:
    name: str
    schema: str


@dataclass
class UploadedBlueprint:
    name: str
    arn: str


@dataclass
class S3Parts:
    bucket: str
    key: str


def create_input_s3_uri(raw_data_bucket: str | None, raw_data_prefix: str | None, po_id: str | None) -> str:
    if not raw_data_bucket or not raw_data_prefix or not po_id:
        print(f"Missing data for input s3 uri creation: raw bucket: {raw_data_bucket}, raw prefix: {raw_data_prefix}, po_id: {po_id}")
        raise ArgsException("Required data for input s3 uri creation missing")
    return f"s3://{raw_data_bucket}/{raw_data_prefix}/{po_id}"


def create_output_s3_uri(processed_data_bucket: str | None, processed_data_prefix: str | None) -> str:
    if not processed_data_bucket or not processed_data_prefix:
        print(f"Missing data for output s3 uri creation: processed bucket: {processed_data_bucket}, processed prefix: {processed_data_prefix}")
        raise ArgsException("Required data for output s3 uri creation missing")
    return f"s3://{processed_data_bucket}/{processed_data_prefix}"



def read_blueprint(blueprint_name: str) -> str:
    try:
        with open(f"{blueprint_name}.json", encoding="utf-8", mode="r") as b:
            blueprint_content = b.read()
            blueprint_schema = json.dumps(json.loads(blueprint_content))
        
        print(f"=== BLUEPRINT SCHEMA DEBUG ===")
        print(f"Blueprint file: {blueprint_name}.json")
        print(f"Schema preview (first 500 chars): {blueprint_schema[:500]}")
        print(f"=== END BLUEPRINT DEBUG ===")
        
        return blueprint_schema
    except Exception as e:
        print(f"Exception - error reading blueprint {blueprint_name}.json: {str(e)}")
        raise ExtractionException(f"Failed to read blueprint file")


def get_blueprint(blueprint_name: str) -> Blueprint:
    return Blueprint(
        name=blueprint_name,
        schema=read_blueprint(blueprint_name)
    )


def call_list_blueprints(bedrock_data_automation_client, next_token: str) -> dict:
    if next_token != INITIAL:
        return bedrock_data_automation_client.list_blueprints(maxResults=25, nextToken=next_token)
    else:
        return bedrock_data_automation_client.list_blueprints(maxResults=25)


def get_blueprint_arn(bedrock_data_automation_client, blueprint: Blueprint) -> str | None:
    itr = 0
    next_token = INITIAL
    while itr < 10 and next_token:
        srv_blueprints = call_list_blueprints(bedrock_data_automation_client, next_token)

        next_token = srv_blueprints.get("nextToken")
        itr += 1

        for bp in srv_blueprints.get("blueprints"):
            if bp.get("blueprintName") == blueprint.name:
                return bp["blueprintArn"]

    return None


def upload_blueprint(bedrock_data_automation_client, blueprint: Blueprint, force_recreate: bool = True):
    try:
        blueprint_arn = get_blueprint_arn(bedrock_data_automation_client, blueprint)

        if blueprint_arn:
            print(f"Found existing blueprint: {blueprint.name} with ARN: {blueprint_arn}")
            
            if force_recreate:
                # Delete and recreate the blueprint to ensure schema is updated
                print(f"Deleting existing blueprint to recreate with new schema...")
                try:
                    bedrock_data_automation_client.delete_blueprint(
                        blueprintArn=blueprint_arn
                    )
                    print(f"Blueprint deleted successfully, creating new one...")
                    
                    # Create new blueprint with updated schema
                    blueprint_response = bedrock_data_automation_client.create_blueprint(
                        blueprintName=blueprint.name,
                        type="DOCUMENT",
                        blueprintStage="LIVE",
                        schema=blueprint.schema
                    )
                    new_arn = blueprint_response["blueprint"]["blueprintArn"]
                    print(f"New blueprint created with ARN: {new_arn}")
                    return new_arn
                    
                except Exception as delete_ex:
                    print(f"Failed to delete/recreate blueprint: {str(delete_ex)}")
                    print(f"Will use existing blueprint")
                    return blueprint_arn
            
            return blueprint_arn

        print(f"Creating new blueprint: {blueprint.name}")
        blueprint_response = bedrock_data_automation_client.create_blueprint(
            blueprintName=blueprint.name,
            type="DOCUMENT",
            blueprintStage="LIVE",
            schema=blueprint.schema
        )
        new_arn = blueprint_response["blueprint"]["blueprintArn"]
        print(f"Blueprint created with ARN: {new_arn}")
        return new_arn
        
    except Exception as ex:
        print(f"Failed to get or upload blueprint: {blueprint.name}: {str(ex)}")
        raise ExtractionException(f"Failed to get or upload blueprint")


def create_blueprint(bedrock_data_automation_client, blueprint: Blueprint) -> UploadedBlueprint:
    return UploadedBlueprint(
        name=blueprint.name,
        arn=upload_blueprint(bedrock_data_automation_client, blueprint)
    )


def create_blueprint_request(uploaded_blueprint: UploadedBlueprint) -> dict:
    return {
        "blueprints": [{
            "blueprintArn": uploaded_blueprint.arn,
            "blueprintStage": "LIVE"
        }]
    }


def call_list_projects(bedrock_data_automation_client, next_token: str) -> dict:
    if next_token != INITIAL:
        return bedrock_data_automation_client.list_data_automation_projects(maxResults=25, nextToken=next_token)
    else:
        return bedrock_data_automation_client.list_data_automation_projects(maxResults=25)


def get_project(bedrock_data_automation_client, project_name: str) -> str | None:
    itr = 0
    next_token = INITIAL
    while itr < 10 and next_token:
        srv_projects = call_list_projects(bedrock_data_automation_client, next_token)

        next_token = srv_projects.get("nextToken")
        itr += 1

        for pr in srv_projects.get("projects"):
            if pr.get("projectName") == project_name:
                return pr["projectArn"]

    return None


def create_project(bedrock_data_automation_client, project_name: str, project_desc: str, std_out: dict, overrides: dict, blueprint_request: dict) -> str:
    try:
        srv_project_arn = get_project(bedrock_data_automation_client, project_name)

        if srv_project_arn:
            status = FETCHED_BUT_CHECK
            project_arn = srv_project_arn
        else:
            response = bedrock_data_automation_client.create_data_automation_project(
                projectName=project_name,
                projectDescription=project_desc,
                projectStage="LIVE",
                standardOutputConfiguration=std_out,
                customOutputConfiguration=blueprint_request,
                overrideConfiguration=overrides
            )
            status = response["status"]
            project_arn = response["projectArn"]

        itr = 0
        while itr < 5 and status != "COMPLETED" and status != "FAILED":
            if status != FETCHED_BUT_CHECK:
                time.sleep(30)

            project_get_response = bedrock_data_automation_client.get_data_automation_project(
                projectArn=project_arn,
                projectStage="LIVE"
            )
            status = project_get_response["project"]["status"]
            itr += 1

        if status != "COMPLETED":
            print(f"Failed to get COMPLETED status: project ({project_arn}) status ({status})")
            raise ExtractionException(f"Project failed to get COMPLETED status before timeout")

        return project_arn

    except Exception as ex:
        print(f"Exception: {str(ex)}")
        raise ExtractionException(f"Failed to get or create project {project_name}")


def create_extraction_project(bedrock_data_automation_client, uploaded_blueprint: UploadedBlueprint) -> str:
    std_out = {
        "document": {
            "extraction": {
                "granularity": {
                    "types": ["PAGE"]
                },
                "boundingBox": {
                    "state": "ENABLED"
                }
            },
            "generativeField": {
                "state": "ENABLED"
            },
            "outputFormat": {
                "textFormat": {
                    "types": ["MARKDOWN"]
                },
                "additionalFileFormat": {
                    "state": "DISABLED"
                }
            }
        }
    }

    overrides = {
        "document": {
            "splitter": {
                "state": "DISABLED"
            }
        }
    }

    blueprint_request = create_blueprint_request(uploaded_blueprint)
    
    print(f"=== PROJECT CONFIGURATION DEBUG ===")
    print(f"Blueprint request: {json.dumps(blueprint_request, indent=2)}")
    print(f"Standard output config: {json.dumps(std_out, indent=2)}")
    print(f"=== END PROJECT CONFIG DEBUG ===")

    return create_project(
        bedrock_data_automation_client,
        "prescription-label-project",
        "Prescription Label Extraction Project",
        std_out,
        overrides,
        blueprint_request
    )


def invoke_bda(bedrock_data_automation_runtime_client, input_s3_uri: str, output_s3_uri: str, account_id: str, project_arn: str):
    try:
        invoke_params = {
            "inputConfiguration": {
                "s3Uri": input_s3_uri
            },
            "outputConfiguration": {
                "s3Uri": output_s3_uri
            },
            "dataAutomationConfiguration": {
                "dataAutomationProjectArn": project_arn,
                "stage": "LIVE"
            },
            "dataAutomationProfileArn": f'arn:aws:bedrock:us-east-1:{account_id}:data-automation-profile/us.data-automation-v1'
        }
        
        print(f"=== INVOKE BDA DEBUG ===")
        print(f"Input S3 URI: {input_s3_uri}")
        print(f"Output S3 URI: {output_s3_uri}")
        print(f"Project ARN: {project_arn}")
        print(f"Profile ARN: {invoke_params['dataAutomationProfileArn']}")
        print(f"Full invoke params: {json.dumps(invoke_params, indent=2)}")
        print(f"=== END DEBUG ===")
        
        response = bedrock_data_automation_runtime_client.invoke_data_automation_async(**invoke_params)

        return response["invocationArn"]
    except Exception as ex:
        print(f"Exception invoking BDA: {str(ex)}")
        print(f"Exception type: {type(ex).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise ExtractionException("Failed to run bda project")


def wait_for_bda_job(bedrock_data_automation_runtime_client, invocation_arn: str):
    status_response = { "status": INTERNAL_STATUS_INITIAL }

    itr = 0
    while status_response["status"] != "Success" and status_response["status"] != "ServiceError" and status_response["status"] != "ClientError":
        if itr > 5:
            print(f"BDA job final status: {status_response['status']}")
            raise ExtractionException(f"BDA job timed out")

        if status_response["status"] != INTERNAL_STATUS_INITIAL:
                time.sleep(30)

        status_response = bedrock_data_automation_runtime_client.get_data_automation_status(invocationArn=invocation_arn)
        itr += 1

    if status_response["status"] != "Success":
        print(f"BDA job final status: {status_response['status']}")
        raise ExtractionException(f"BDA job failed to complete")

    return status_response


def uri_to_bucket_and_key(s3_uri: str) -> S3Parts:
    result = urlparse(s3_uri)

    if not result.netloc or not result.path or not result.scheme == "s3":
        print(f"Invalid S3 URI when parsing metadata location: uri - {s3_uri}")
        raise TransformException("Invalid S3 URI")

    usable_key = result.path[1:]
    return S3Parts(bucket=result.netloc, key=usable_key)


def get_json_from_s3(s3_client, s3_uri: str, download_location: str) -> dict:
    s3_parts = uri_to_bucket_and_key(s3_uri)

    s3_client.download_file(s3_parts.bucket, s3_parts.key, download_location)

    with open(download_location, encoding="utf-8", mode="r") as j:
        file_json = json.loads(j.read())

    os.unlink(download_location)

    return file_json


def get_results_uri(s3_client, metadata_s3_uri: str, temp_dir: str) -> str:
    try:
        download_location = f"{temp_dir}/metadata-{uuid4()}.json"
        metadata_json = get_json_from_s3(s3_client, metadata_s3_uri, download_location)
        
        print(f"=== METADATA JSON DEBUG ===")
        print(f"Full metadata JSON: {json.dumps(metadata_json, indent=2)}")
        print(f"=== END METADATA DEBUG ===")
        
        output_metadata = metadata_json.get("output_metadata")

        if not output_metadata or len(output_metadata) != 1:
            print(f"Nullish output metadata or unexpected length at {metadata_s3_uri}")
            raise TransformException("Unexpected output metadata length")

        segment_metadata = output_metadata[0].get("segment_metadata")

        if not segment_metadata or len(segment_metadata) != 1:
            print(f"Nullish segment metadata or unexpected length at {metadata_s3_uri}")
            raise TransformException("Unexpected segment metadata length")

        # Try different possible keys for the results path
        segment = segment_metadata[0]
        result_json_s3_uri = segment.get("custom_output_path") or segment.get("standard_output_path") or segment.get("output_path")

        if not result_json_s3_uri:
            print(f"No output s3 uri found in metadata json for {metadata_s3_uri}")
            print(f"Available keys in segment: {list(segment.keys())}")
            raise TransformException("No output s3 uri found in metadata json")

        print(f"Found result URI: {result_json_s3_uri}")
        return result_json_s3_uri
    except Exception as ex:
        print(f"Exception in get_results_uri: {str(ex)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise TransformException("Failed to process job metadata from S3")


def process_results(s3_client, results_s3_uri: str, temp_dir: str) -> dict:
    try:
        download_location = f"{temp_dir}/results-{uuid4()}.json"
        results_json = get_json_from_s3(s3_client, results_s3_uri, download_location)
        
        print(f"=== RESULTS JSON DEBUG ===")
        print(f"Full results JSON keys: {list(results_json.keys())}")
        print(f"Full results JSON: {json.dumps(results_json, indent=2)[:2000]}...")  # First 2000 chars
        print(f"=== END RESULTS DEBUG ===")
        
        # The structure might be different - just return the raw results for now
        # We can process it later once we see the structure
        return results_json
        
    except Exception as ex:
        print(f"Exception in process_results: {str(ex)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise TransformException("Failed to transform results")


def write_results_to_s3(s3_client, processed_data_bucket: str, processed_data_prefix: str, patient_id: str, temp_dir: str, results: dict):
    try:
        result_str = json.dumps(results)
        file_location = f"{temp_dir}/formatted-results-{uuid4()}.json"
        with open(file_location, encoding="utf-8", mode="w") as f:
            f.write(result_str)

        # having multiple file extensions can mess with HTTPS, so removing file extension

        s3_key = f"{processed_data_prefix}/{uuid4()}/{patient_id}-{uuid4()}-results.json"
        s3_client.upload_file(file_location, processed_data_bucket, s3_key)

        os.unlink(file_location)

        return f"s3://{processed_data_bucket}/{s3_key}"
    except Exception as ex:
        print(f"Exception: {str(ex)}")
        raise TransformException("Failed to write results to S3")