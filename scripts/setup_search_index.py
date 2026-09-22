"""Create or update the bounded Azure AI Search index used by the demo."""

import argparse
import os

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)


def build_index(name: str, dimensions: int) -> SearchIndex:
    return SearchIndex(
        name=name,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
            SimpleField(name="content_hash", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="text", type=SearchFieldDataType.String),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SimpleField(name="source_url", type=SearchFieldDataType.String),
            SimpleField(name="locator", type=SearchFieldDataType.String),
            SimpleField(name="corpus_version", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="approved", type=SearchFieldDataType.Boolean, filterable=True),
            SimpleField(name="reviewed_on", type=SearchFieldDataType.String, filterable=True),
            SearchField(
                name="vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=dimensions,
                vector_search_profile_name="placement-vector-profile",
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="placement-hnsw")],
            profiles=[
                VectorSearchProfile(
                    name="placement-vector-profile",
                    algorithm_configuration_name="placement-hnsw",
                )
            ],
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--dimensions", type=int, default=1536)
    args = parser.parse_args()
    if not args.endpoint.startswith("https://") or args.dimensions <= 0:
        raise ValueError("A secure endpoint and positive vector dimensions are required")
    api_key = os.environ.get("AZURE_SEARCH_API_KEY", "").strip()
    credential = AzureKeyCredential(api_key) if api_key else DefaultAzureCredential()
    client = SearchIndexClient(endpoint=args.endpoint, credential=credential)
    try:
        result = client.create_or_update_index(build_index(args.name, args.dimensions))
        print(f"Search index ready: {result.name} ({args.dimensions} dimensions)")
    finally:
        client.close()


if __name__ == "__main__":
    main()
