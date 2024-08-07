import os
import json
import copy
import requests
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
# from tenacity import retry, wait_random_exponential, stop_after_attempt
from dotenv import load_dotenv
import openai
from openai import AzureOpenAI
from langchain.text_splitter import TokenTextSplitter, RecursiveCharacterTextSplitter

# Load environment variables from .env file
load_dotenv()

# Define the target directory (change yours)
target_directory = (
    r"/tmp/ingest_sharepoint"
)

# Check if the directory exists
if os.path.exists(target_directory):
    # Change the current working directory
    os.chdir(target_directory)
    print(f"Directory changed to {os.getcwd()}")
else:
    print(f"Directory {target_directory} does not exist.")

endpoint = os.environ["SEARCH_SERVICE_ENDPOINT"]
search_client = SearchClient(
    endpoint=endpoint,
    index_name=os.environ["SEARCH_INDEX_NAME"],
    credential=AzureKeyCredential(os.environ["SEARCH_ADMIN_API_KEY"]),
)

admin_client = SearchIndexClient(
    endpoint=endpoint,
    index_name=os.environ["SEARCH_INDEX_NAME"],
    credential=AzureKeyCredential(os.environ["SEARCH_ADMIN_API_KEY"]),
)

openai.api_key = os.environ["OPEN_API_KEY"]
openai.api_base = os.environ["OPEN_API_BASE"]
openai.api_type = "azure"
openai.api_version = "2023-05-15"

model = os.environ["OPEN_API_MODEL"]

client = AzureOpenAI(
        api_version=openai.api_version,
        azure_endpoint=openai.api_base,
        api_key=openai.api_key
    )

# This is in characters and there is an avg of 4 chars / token
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1024*4,
    chunk_overlap  = 102*4
)