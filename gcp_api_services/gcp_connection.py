"""Centralized GCP connection module.

Provides a single entry point for GCP project configuration and
cached clients for Cloud Storage, BigQuery, and Vertex AI (GenAI).
All other GCP service modules should use this instead of creating
their own clients.
"""

import os
import threading
from google.cloud import bigquery, storage
from google import genai


_DEFAULT_PROJECT_ID = "abcds-detector-488021"
_DEFAULT_LOCATION = "us-central1"


def get_project_id() -> str:
    """Return the GCP project ID from env or default."""
    return os.environ.get("GCP_PROJECT_ID", _DEFAULT_PROJECT_ID)


def get_location() -> str:
    """Return the GCP region/location from env or default."""
    return os.environ.get("GCP_LOCATION", _DEFAULT_LOCATION)


class _ClientCache:
    """Thread-safe lazy cache for GCP clients."""

    def __init__(self):
        self._lock = threading.Lock()
        self._storage_client: storage.Client | None = None
        self._bigquery_client: bigquery.Client | None = None
        self._genai_client: genai.Client | None = None

    def get_storage_client(self) -> storage.Client:
        if self._storage_client is None:
            with self._lock:
                if self._storage_client is None:
                    self._storage_client = storage.Client(project=get_project_id())
        return self._storage_client

    def get_bigquery_client(self) -> bigquery.Client:
        if self._bigquery_client is None:
            with self._lock:
                if self._bigquery_client is None:
                    self._bigquery_client = bigquery.Client(project=get_project_id())
        return self._bigquery_client

    def get_genai_client(self) -> genai.Client:
        if self._genai_client is None:
            with self._lock:
                if self._genai_client is None:
                    self._genai_client = genai.Client(
                        vertexai=True,
                        project=get_project_id(),
                        location=get_location(),
                    )
        return self._genai_client


_cache = _ClientCache()

get_storage_client = _cache.get_storage_client
get_bigquery_client = _cache.get_bigquery_client
get_genai_client = _cache.get_genai_client
