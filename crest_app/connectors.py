"""Typed extension seam for searchable source connectors."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from crest_pipeline import RawDocument

from .models import (
    ConnectorProbe,
    ConnectorStatus,
    DocumentDetail,
    SearchResponse,
)


@runtime_checkable
class SourceConnector(Protocol):
    """One searchable source with explicit availability and acquisition failure."""

    search_endpoint: str
    last_status: ConnectorStatus

    def search(self, query: str, *, limit: int) -> SearchResponse: ...

    def detail(self, document_id: str) -> DocumentDetail: ...

    def raw_document(self, document_id: str) -> RawDocument: ...

    def contains(self, document_id: str) -> bool: ...

    def probe(self) -> ConnectorProbe: ...
