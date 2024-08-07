import os
from dotenv import load_dotenv
from msgraph import GraphServiceClient
from azure.identity.aio import ClientSecretCredential
import asyncio
import base64

load_dotenv()

def getGraphServiceClient():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    tenant_id = os.getenv("TENANT_ID")
    scope = "https://graph.microsoft.com/.default"

    """Fetches the Azure access token."""
    credentials = ClientSecretCredential(
        tenant_id,
        client_id,
        client_secret,
    )

    client = GraphServiceClient(credentials=credentials, scopes=[scope])

    return client


def get_deltas_from_sharepoint():
    graph_client = getGraphServiceClient()

    response = graph_client.sites.by_site_id(
        'mngenvmcap859253.sharepoint.com,3865443c-e21e-4694-bb85-cb4f31322614,40e5ddf0-f1df-4823-a486-8ce31feff0b7').lists.by_list_id(
        '6fb4ee38-e1de-4f4d-856e-d67df199ec4b').items.delta.get()  ## delta_with_token

    token = response.odata_delta_link.split("?token=")[1]  # Extract token from deltaLink for next request
    delta_file_names = []

    for value in response.value:
        if value.content_type.name == 'Document':
            delta_file_names.append(value.web_url)
            base64encoded = base64.b64encode(value.web_url.encode('utf-8'))
            encoded_url = "u!" + base64encoded.decode('utf-8').rstrip('=').replace('/', '_').replace('+', '-')
            print(encoded_url)

    return token, delta_file_names

async def main():
    result = get_deltas_from_sharepoint()
    print(result)


asyncio.run(main())
