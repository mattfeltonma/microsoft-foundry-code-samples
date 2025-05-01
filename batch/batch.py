import logging
import sys
import os
import json
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from dotenv import load_dotenv

import time
import datetime

## This function sets up logging
##
def configure_logging(level="ERROR"):
    try:
        # Convert the level string to uppercase so it matches what the logging library expects
        logging_level = getattr(logging, level.upper(), None)

        # Setup a logging format
        logging.basicConfig(
            level=logging_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
    except Exception as e:
        print(f"Failed to set up logging: {e}", file=sys.stderr)
        sys.exit(1)

## This function obtains an access token from Entra ID using a service principal with a client id and client secret
##
def authenticate_with_service_principal(scope):
    try:
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            scope
        )
        return token_provider
    except:
        logging.error('Failed to obtain access token: ', exc_info=True)
        sys.exit(1)


def main():
    # Setup logging
    #
    configure_logging("ERROR")

    # Use dotenv library to load environmental variables from .env file.
    # The variables loaded include AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
    # LLM_DEPLOYMENT_NAME, OPENAI_API_VERSION, and AZURE_OPENAI_ENDPOINT
    try:
        load_dotenv('.env')
    except Exception as e:
        logging.error(
            'Failed to load environmental variables: ', exc_info=True)
        sys.exit(1)

    # Obtain an access token
    #
    token_provider = authenticate_with_service_principal(
        scope="https://cognitiveservices.azure.com/.default")

    # Perform a batch ChatCompletion
    #
    try:
        # Create the Azure OpenAI Service client
        # The client must have a batch endpoint configured and it must match the column in the sample.jsonl file
        client = AzureOpenAI(
          api_version=os.getenv('OPENAI_API_VERSION'),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            azure_ad_token_provider=token_provider
        )

        # Upload the batch file to the Azure OpenAI Service
        #
        file = client.files.create(
            file=open("sample.jsonl", 'rb'),
            purpose="batch"
        )

        print(file.model_dump_json(indent=2))
        file_id = file.id

        # Loop while the file is processed and then submit a batch job
        #
        status = "pending"
        while status not in ("processed"):
            print(f"{datetime.datetime.now()} - File Id: {file_id}, Status: {status}")
            time.sleep(30)
            file = client.files.retrieve(file_id)
            status = file.status
            print(f"{datetime.datetime.now()} - File Id: {file_id}, Status: {status}")
            batch_response = client.batches.create(
                input_file_id=file.id,
                endpoint="/chat/completions",
                completion_window="24h"
            )

            batch_id = batch_response.id
            print(batch_response.model_dump_json(indent=2))
    
        # Loop while the batch job is processed and then retrieve and print it out once completed
        #
        status = "validating"
        while status not in ("completed", "failed", "cancelled"):
            print(f"{datetime.datetime.now()
                     } - Batch Id: {batch_id}, Status: {status}")
            time.sleep(5)
            batch_response = client.batches.retrieve(batch_id)
            status = batch_response.status
            print(f"{datetime.datetime.now()
                     } - Batch Id: {batch_id}, Status: {status}")
            
            if batch_response.status == "failed":
                for error in batch_response.errors.data:
                    print(f"Error code: {error.code} Message {error.message}")
                
        output_file_id = batch_response.output_file_id
        if not output_file_id:
            output_file_id = batch_response.error_file_id
        if output_file_id:
            file_response = client.files.content(output_file_id)
            raw_responses = file_response.text.strip().split('\n')  

            for raw_response in raw_responses:  
                json_response = json.loads(raw_response)  
                formatted_json = json.dumps(json_response, indent=2)  
                print(formatted_json)

    except:
        logging.error('Failed batch chat completion: ', exc_info=True)

if __name__ == "__main__":
    main()