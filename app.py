import os
import base64

import requests
import uvicorn
import logging
import json
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from msgraph import GraphServiceClient
from azure.identity.aio import ClientSecretCredential

# Set up logging
logger = logging.getLogger('uvicorn.info')
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

# Create FastAPI instance
app = FastAPI()

# Define scope
scope = "https://graph.microsoft.com/.default"

# Initialize delta token
delta_token = ""


def getAzureAuthToken():
    """Fetches the Azure access token."""
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    tenant_id = os.getenv("TENANT_ID")
    credentials = ClientSecretCredential(
        tenant_id,
        client_id,
        client_secret,
    )
    return credentials


def getGraphServiceClient():
    """Creates a GraphServiceClient instance."""
    credentials = getAzureAuthToken()
    client = GraphServiceClient(credentials=credentials, scopes=[scope])
    return client


async def download_file(url, filename, dest_dir='/tmp/ingest_sharepoint/'):
    """Downloads a file from a given URL."""
    # Normalize the filename to prevent path injection
    filename = os.path.normpath(filename)

    # Join the destination directory with the filename
    dest_path = os.path.join(dest_dir, filename)

    # Get the absolute path to prevent directory traversal
    dest_path = os.path.abspath(dest_path)

    # Ensure the destination is within the intended directory
    if not dest_path.startswith(os.path.abspath(dest_dir)):
        raise ValueError("Invalid filename")

    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, 'wb') as fp:
        for chunk in response.iter_content(chunk_size=8192):
            fp.write(chunk)


async def get_deltas_from_sharepoint(self):
    """Fetches deltas from SharePoint and downloads the files."""
    graph_client = getGraphServiceClient()
    response = await graph_client.sites.by_site_id(
        'mngenvmcap859253.sharepoint.com,3865443c-e21e-4694-bb85-cb4f31322614,40e5ddf0-f1df-4823-a486-8ce31feff0b7').lists.by_list_id(
        '6fb4ee38-e1de-4f4d-856e-d67df199ec4b').items.delta_with_token(self.delta_token).get()

    delta_file_names = []

    for value in response.value:
        if value.content_type.name == 'Document':
            base64encoded = base64.b64encode(value.web_url.encode('utf-8'))
            encoded_url = "u!" + base64encoded.decode('utf-8').rstrip('=').replace('/', '_').replace('+', '-')
            drive_item = await graph_client.shares.by_shared_drive_item_id(encoded_url).drive_item.get()
            delta_file_names.append((drive_item.name, drive_item.additional_data.get("@microsoft.graph.downloadUrl")))

    for filename, url in delta_file_names:
        await download_file(url, filename)

    self.delta_token = response.odata_delta_link.split("?token=")[1]

    return delta_token, delta_file_names


@app.post('/webhook')
async def webhook(request: Request):
    """Endpoint to receive the webhook notifications."""
    if 'validationToken' in request.headers:
        validation_token = request.headers.get('validationToken')
        return validation_token, 200

    request_json = await request.json()
    logger.info('Received notification ' + json.dumps(request_json))

    result = await get_deltas_from_sharepoint()

    return {'status': 'success'}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)
