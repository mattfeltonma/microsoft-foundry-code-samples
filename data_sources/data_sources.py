import logging
import sys
import os
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from dotenv import load_dotenv

import time
import datetime

# This function sets up logging
#
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

# This function obtains an access token from Entra ID using a service principal with a client id and client secret
#
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
    # LLM_DEPLOYMENT_NAME, OPENAI_API_VERSION, AZURE_OPENAI_ENDPOINT, EMBEDDING_DEPLOYMENT_NAME,
    # AZURE_AI_SEARCH_ENDPOINT, AZURE_AI_SEARCH_INDEX_NAME, and AZURE_AI_SEARCH_SEMANTIC_CONFIG_NAME
    try:
        load_dotenv('.env')
    except Exception as e:
        logging.error(
            'Failed to load environmental variables: ', exc_info=True)
        sys.exit(1)

    # Obtain an access token
    ##
    token_provider = authenticate_with_service_principal(
        scope="https://cognitiveservices.azure.com/.default")

    # Perform a batch ChatCompletion
    ##
    try:
        # Create the Azure OpenAI Service client
        #
        client = AzureOpenAI(
          api_version=os.getenv('OPENAI_API_VERSION'),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            azure_ad_token_provider=token_provider
        )

        response = client.chat.completions.create(
            model=os.getenv('LLM_DEPLOYMENT_NAME'),
            messages=[
                {   "role": "system", 
                    "content": "You are helpful assistant." },
                {
                    "role": "user",
                    "content": "What was Microsoft's income?"
                }
            ],
            max_tokens=100,
            
            # Extra body required for querying Azure Search
            # Thee options will return the top 3 results based on a hybrid semantic search
            # using the embedding model specified in the environment variable EMBEDDING_DEPLOYMENT_NAME
            extra_body = {
                "data_sources": [
                    {
                        "type": "azure_search",
                        "parameters": {
                            "endpoint": os.getenv('AZURE_AI_SEARCH_ENDPOINT'),
                            "index_name": os.getenv('AZURE_AI_SEARCH_INDEX_NAME'),
                            "in_scope": True,
                            "query_type": "vector_semantic_hybrid",
                            "embedding_dependency": {
                                "type": "deployment_name",
                                "deployment_name": os.getenv('EMBEDDING_DEPLOYMENT_NAME'),
                            },
                            "semantic_configuration": os.getenv('AZURE_AI_SEARCH_SEMANTIC_CONFIG_NAME'),
                            "top_n_documents": 3,
                            "max_search_queries": 3,
                            "authentication": {
                                "type": "system_assigned_managed_identity"
                            }                   
                        }
                    }
                ],
            },            
        )
        print(response.choices[0].message.content)
    except:
        logging.error('Failed chat completion: ', exc_info=True)

if __name__ == "__main__":
    main()