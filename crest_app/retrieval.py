"""Deterministic chunking and evidence ranking for collection questions."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Literal

from .models import EvidenceChunk, EvidenceScore


ConnectorId = Literal[
    "bundled-crest", "user-uploads", "cia-reading-room-live"
]


@dataclass(frozen=True)
class RetrievalDocument:
    """Source text and identity supplied by the canonical corpus catalog."""

    document_id: str
    connector_id: ConnectorId
    title: str
    body_text: str


@dataclass(frozen=True)
class _ChunkCandidate:
    document: RetrievalDocument
    start_char: int
    end_char: int
    text: str
    terms: tuple[str, ...]
    title_terms: tuple[str, ...]


STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "did",
        "do",
        "does",
        "for",
        "from",
        "how",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "there",
        "this",
        "to",
        "was",
        "were",
        "what",
        "when",
        "which",
        "who",
        "why",
        "with",
    }
)


# Small, domain-neutral lexical concept families support common question/document
# paraphrases without a model call. Values are stemmed by ``_stem`` at import.
_RAW_CONCEPT_GROUPS = (
    ("group", "organization", "body", "institute", "committee", "agency", "team"),
    ("organize", "coordinate", "convene", "arrange"),
    ("lead", "led", "direct", "operate", "manage", "supervise"),
    ("demonstration", "pilot", "exercise", "trial", "test"),
    ("date", "day", "schedule", "begin", "began", "begun", "start", "launch"),
    ("disagreement", "conflict", "contradict", "correction", "dispute"),
    ("cost", "budget", "funding", "expense", "price"),
)


def _stem(token: str) -> str:
    value = re.sub(r"[^a-z0-9]", "", token.casefold())
    if len(value) > 5 and value.endswith("ies"):
        return value[:-3] + "y"
    for suffix in ("ingly", "edly", "ation", "ment", "ing", "ed", "es", "s"):
        if len(value) - len(suffix) >= 4 and value.endswith(suffix):
            return value[: -len(suffix)]
    if len(value) > 5 and value.endswith("e"):
        return value[:-1]
    return value


CONCEPT_GROUPS = tuple(
    frozenset(_stem(token) for token in group) for group in _RAW_CONCEPT_GROUPS
)
CONCEPT_BY_TERM = {
    term: group for group in CONCEPT_GROUPS for term in group
}


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(
        stemmed
        for token in re.findall(r"[A-Za-z0-9]+", value.casefold())
        if (stemmed := _stem(token)) and stemmed not in STOP_WORDS
    )


def _query_concepts(question: str) -> tuple[tuple[str, frozenset[str]], ...]:
    concepts: list[tuple[str, frozenset[str]]] = []
    seen: set[frozenset[str]] = set()
    for term in _tokens(question):
        alternatives = CONCEPT_BY_TERM.get(term, frozenset({term}))
        if alternatives in seen:
            continue
        seen.add(alternatives)
        concepts.append((term, alternatives))
    return tuple(concepts)


def _trimmed_window(body: str, start: int, end: int) -> tuple[int, int, str]:
    while start < end and body[start].isspace():
        start += 1
    while end > start and body[end - 1].isspace():
        end -= 1
    return start, end, body[start:end]


def chunk_document(
    document: RetrievalDocument,
    *,
    max_chunk_chars: int = 900,
    overlap_chars: int = 120,
) -> list[_ChunkCandidate]:
    """Split text into stable exact-offset windows without normalizing source text."""

    if max_chunk_chars < 200:
        raise ValueError("max_chunk_chars must be at least 200")
    if overlap_chars < 0 or overlap_chars >= max_chunk_chars:
        raise ValueError("overlap_chars must be nonnegative and smaller than a chunk")
    body = document.body_text
    if not body.strip():
        return []
    chunks: list[_ChunkCandidate] = []
    start = 0
    while start < len(body):
        hard_end = min(len(body), start + max_chunk_chars)
        end = hard_end
        if hard_end < len(body):
            floor = start + max_chunk_chars // 2
            candidates = [
                body.rfind("\n\n", floor, hard_end),
                body.rfind(". ", floor, hard_end),
                body.rfind(" ", floor, hard_end),
            ]
            boundary = max(candidates)
            if boundary > start:
                end = boundary + (1 if body[boundary] == " " else 0)
        exact_start, exact_end, text = _trimmed_window(body, start, end)
        if text:
            chunks.append(
                _ChunkCandidate(
                    document=document,
                    start_char=exact_start,
                    end_char=exact_end,
                    text=text,
                    terms=_tokens(text),
                    title_terms=_tokens(document.title),
                )
            )
        if end >= len(body):
            break
        next_start = max(start + 1, end - overlap_chars)
        while next_start < len(body) and next_start > 0 and not body[next_start - 1].isspace():
            next_start += 1
        start = next_start
    return chunks


def _concept_frequency(terms: tuple[str, ...], alternatives: frozenset[str]) -> int:
    return sum(1 for term in terms if term in alternatives)


def _best_fuzzy(term: str, candidate_terms: tuple[str, ...]) -> float:
    if len(term) < 5:
        return 0.0
    return max(
        (SequenceMatcher(None, term, candidate).ratio() for candidate in candidate_terms if len(candidate) >= 5),
        default=0.0,
    )


def rank_evidence(
    question: str,
    documents: list[RetrievalDocument],
    *,
    limit: int = 6,
    max_chars_per_document: int = 50_000,
    max_chunk_chars: int = 900,
    overlap_chars: int = 120,
) -> list[EvidenceChunk]:
    """Rank exact source chunks using BM25, concept coverage, and fuzzy evidence."""

    normalized_question = " ".join(question.casefold().split())
    concepts = _query_concepts(question)
    if not concepts or limit <= 0:
        return []
    candidates = [
        chunk
        for document in documents
        for chunk in chunk_document(
            RetrievalDocument(
                document_id=document.document_id,
                connector_id=document.connector_id,
                title=document.title,
                body_text=document.body_text[:max_chars_per_document],
            ),
            max_chunk_chars=max_chunk_chars,
            overlap_chars=overlap_chars,
        )
    ]
    if not candidates:
        return []

    document_frequencies = [
        sum(
            1
            for candidate in candidates
            if _concept_frequency(candidate.terms, alternatives) > 0
        )
        for _, alternatives in concepts
    ]
    average_length = sum(len(candidate.terms) for candidate in candidates) / len(candidates)
    scored: list[tuple[float, _ChunkCandidate, EvidenceScore, list[str]]] = []
    for candidate in candidates:
        bm25 = 0.0
        exact_matches = 0
        fuzzy_values: list[float] = []
        matched_terms: list[str] = []
        for index, (query_term, alternatives) in enumerate(concepts):
            frequency = _concept_frequency(candidate.terms, alternatives)
            if frequency:
                exact_matches += 1
                matched_terms.append(query_term)
                idf = math.log(
                    1 + (len(candidates) - document_frequencies[index] + 0.5)
                    / (document_frequencies[index] + 0.5)
                )
                denominator = frequency + 1.2 * (
                    0.25 + 0.75 * len(candidate.terms) / max(average_length, 1)
                )
                bm25 += idf * frequency * 2.2 / denominator
                fuzzy_values.append(1.0)
                continue
            fuzzy = _best_fuzzy(query_term, candidate.terms)
            fuzzy_values.append(fuzzy)
            if fuzzy >= 0.86:
                matched_terms.append(query_term)
        fuzzy_match_count = sum(1 for value in fuzzy_values if 0.86 <= value < 1.0)
        match_count = exact_matches + fuzzy_match_count
        minimum_matches = 1 if len(concepts) <= 2 else 2
        coverage = match_count / len(concepts)
        if match_count < minimum_matches:
            continue
        phrase = 3.0 if normalized_question in " ".join(candidate.text.casefold().split()) else 0.0
        title_matches = sum(
            1
            for _, alternatives in concepts
            if _concept_frequency(candidate.title_terms, alternatives)
        )
        title_score = min(2.0, title_matches * 0.5)
        fuzzy_score = sum(value for value in fuzzy_values if 0.86 <= value < 1.0) / len(concepts)
        components = EvidenceScore(
            bm25=bm25,
            coverage=coverage,
            fuzzy=fuzzy_score,
            phrase=phrase,
            title=title_score,
        )
        total = bm25 + coverage * 4.0 + fuzzy_score * 2.0 + phrase + title_score
        scored.append((total, candidate, components, matched_terms))

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1].document.document_id,
            item[1].start_char,
        )
    )
    # Give each relevant source one opportunity before a long document can
    # consume the complete evidence budget.
    selected: list[tuple[float, _ChunkCandidate, EvidenceScore, list[str]]] = []
    seen_documents: set[str] = set()
    for item in scored:
        document_id = item[1].document.document_id
        if document_id in seen_documents:
            continue
        selected.append(item)
        seen_documents.add(document_id)
        if len(selected) >= limit:
            break
    if len(selected) < limit:
        selected_keys = {
            (item[1].document.document_id, item[1].start_char) for item in selected
        }
        selected.extend(
            item
            for item in scored
            if (item[1].document.document_id, item[1].start_char) not in selected_keys
        )
    selected = selected[:limit]

    evidence: list[EvidenceChunk] = []
    for rank, (score, candidate, components, matched_terms) in enumerate(selected, 1):
        identity = "\0".join(
            (
                candidate.document.document_id,
                str(candidate.start_char),
                str(candidate.end_char),
                candidate.text,
            )
        )
        evidence.append(
            EvidenceChunk(
                id=f"evidence-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:20]}",
                document_id=candidate.document.document_id,
                connector_id=candidate.document.connector_id,
                title=candidate.document.title,
                start_char=candidate.start_char,
                end_char=candidate.end_char,
                text=candidate.text,
                rank=rank,
                score=round(score, 8),
                score_components=components,
                matched_terms=matched_terms,
            )
        )
    return evidence


def evaluate_retrieval_fixture(path: Path) -> dict[str, object]:
    """Execute the frozen retrieval regression fixture with per-case evidence."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    documents = [
        RetrievalDocument(
            document_id=item["document_id"],
            connector_id="bundled-crest",
            title=item["title"],
            body_text=item["body_text"],
        )
        for item in payload["documents"]
    ]
    source_by_id = {item.document_id: item for item in documents}
    case_results: list[dict[str, object]] = []
    for case in payload["cases"]:
        evidence = rank_evidence(
            case["query"],
            documents,
            limit=case["top_k"],
        )
        ranked_ids = [item.document_id for item in evidence]
        missing = sorted(set(case["expected_document_ids"]) - set(ranked_ids))
        excluded_in_top_two = sorted(
            set(case["exclude_from_top_two"]) & set(ranked_ids[:2])
        )
        offsets_valid = all(
            source_by_id[item.document_id].body_text[item.start_char : item.end_char]
            == item.text
            for item in evidence
        )
        expected_empty = not case["expected_document_ids"]
        passed = (
            not missing
            and not excluded_in_top_two
            and offsets_valid
            and (not expected_empty or not evidence)
        )
        case_results.append(
            {
                "case_id": case["case_id"],
                "split": case["split"],
                "passed": passed,
                "ranked_document_ids": ranked_ids,
                "missing_expected": missing,
                "excluded_in_top_two": excluded_in_top_two,
                "offsets_valid": offsets_valid,
            }
        )
    return {
        "schema_version": payload["schema_version"],
        "passed": all(item["passed"] for item in case_results),
        "cases": case_results,
    }
