import os
import requests
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import (
    RawVectorQuery,
)
from azure.search.documents.indexes.models import (
    CorsOptions,
    ExhaustiveKnnParameters,
    ExhaustiveKnnVectorSearchAlgorithmConfiguration,
    HnswParameters,
    HnswVectorSearchAlgorithmConfiguration,
    SimpleField,
    SearchField,
    ComplexField,
    SearchFieldDataType,
    SearchIndex,
    VectorSearch,
    VectorSearchAlgorithmKind,
    VectorSearchProfile,
)

from dotenv import load_dotenv

load_dotenv()

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

try:
    result = admin_client.delete_index(os.environ["SEARCH_INDEX_NAME"])
    print("Index", os.environ["SEARCH_INDEX_NAME"], "deleted")
except Exception as ex:
    print(ex)

fields = [
    SimpleField(
        name="id",
        type=SearchFieldDataType.String,
        filterable=True,
        sortable=True,
        key=True,
    ),
    SimpleField(
        name="doc_id",
        type=SearchFieldDataType.String,
        filterable=True,
        facetable=True,
        sortable=True,
        key=False,
    ),
    SimpleField(
        name="chunk_id",
        type=SearchFieldDataType.Int32,
        filterable=True,
        sortable=True,
        key=False,
    ),
    SearchField(
        name="name", type=SearchFieldDataType.String, filterable=True, sortable=True, analyzer_name="en.microsoft"
    ),
    SimpleField(
        name="created_datetime",
        type=SearchFieldDataType.DateTimeOffset,
        facetable=True,
        filterable=True,
        sortable=True,
    ),
    SearchField(
        name="created_by",
        type=SearchFieldDataType.String,
        filterable=True,
        sortable=True,
    ),
    SimpleField(
        name="size",
        type=SearchFieldDataType.Int32,
        facetable=True,
        filterable=True,
        sortable=True,
    ),
    SimpleField(
        name="last_modified_datetime",
        type=SearchFieldDataType.DateTimeOffset,
        facetable=True,
        filterable=True,
        sortable=True,
    ),
    SearchField(
        name="last_modified_by",
        type=SearchFieldDataType.String,
        filterable=True,
        sortable=True,
    ),
    SimpleField(name="source", type=SearchFieldDataType.String),
    SearchField(
        name="content", type=SearchFieldDataType.String, analyzer_name="en.microsoft"
    ),
    SearchField(
        name="contentVector",
        hidden=False,
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=1536,
        vector_search_profile="myHnswProfile"
    ),
    ComplexField(
        name="read_access_entity",
        collection=True,
        fields=[SimpleField(name="list_item", type=SearchFieldDataType.String, searchable=True, filterable=True, )],
        searchable=True),

]
cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
scoring_profiles = []
suggester = [{"name": "sg", "source_fields": ["name"]}]

# Configure the vector search configuration
vector_search = VectorSearch(
    algorithms=[
        HnswVectorSearchAlgorithmConfiguration(
            name="myHnsw",
            kind=VectorSearchAlgorithmKind.HNSW,
            parameters=HnswParameters(
                m=4,
                ef_construction=400,
                ef_search=1000,
                metric="cosine",
            ),
        )
    ],
    profiles=[
        VectorSearchProfile(
            name="myHnswProfile",
            algorithm="myHnsw",
        ),
    ],
)

index = SearchIndex(
    name=os.environ["SEARCH_INDEX_NAME"],
    fields=fields,
    scoring_profiles=scoring_profiles,
    suggesters=suggester,
    cors_options=cors_options,
    vector_search=vector_search
)

try:
    result = admin_client.create_index(index)
    print("Index", result.name, "created")
except Exception as ex:
    print(ex)
