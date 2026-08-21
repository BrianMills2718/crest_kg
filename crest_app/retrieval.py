"""Deterministic chunking and evidence ranking for collection questions."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .answerability import judge_supporting
from .models import EvidenceChunk, EvidenceScore
from .semantic_index import lexical_overlap, rank_texts


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
            paragraph_boundary = body.rfind("\n\n", floor, hard_end)
            sentence_boundary = body.rfind(". ", floor, hard_end)
            word_boundary = body.rfind(" ", floor, hard_end)
            # Preserve the strongest available semantic boundary rather than
            # allowing a later ordinary space to outrank a paragraph or
            # sentence break. Sentence punctuation belongs to the preceding
            # chunk; paragraph separators and word-boundary whitespace do not.
            if paragraph_boundary > start:
                end = paragraph_boundary
            elif sentence_boundary > start:
                end = sentence_boundary + 1
            elif word_boundary > start:
                end = word_boundary + 1
        exact_start, exact_end, text = _trimmed_window(body, start, end)
        if text:
            chunks.append(
                _ChunkCandidate(
                    document=document,
                    start_char=exact_start,
                    end_char=exact_end,
                    text=text,
                )
            )
        if end >= len(body):
            break
        next_start = max(start + 1, end - overlap_chars)
        while next_start < len(body) and next_start > 0 and not body[next_start - 1].isspace():
            next_start += 1
        start = next_start
    return chunks








def rank_evidence(
    question: str,
    documents: list[RetrievalDocument],
    *,
    limit: int = 6,
    max_chars_per_document: int = 50_000,
    max_chunk_chars: int = 900,
    overlap_chars: int = 120,
) -> list[EvidenceChunk]:
    """Rank exact source chunks by semantic similarity to the question.

    Ranking only. This never abstains beyond returning nothing when there is
    nothing to rank -- deciding that a well-ranked passage still fails to answer
    the question is a separate judgment, made in ``select_evidence``.
    """

    if limit <= 0 or not question.strip():
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

    texts = [
        f"{candidate.document.title}. {candidate.text}" for candidate in candidates
    ]
    scores = rank_texts(question, texts)
    scored = sorted(
        zip(scores, range(len(candidates))),
        key=lambda item: (
            -item[0],
            candidates[item[1]].document.document_id,
            candidates[item[1]].start_char,
        ),
    )

    # Give each source one opportunity before a long document can consume the
    # whole evidence budget.
    selected: list[tuple[float, int]] = []
    seen_documents: set[str] = set()
    for score, index in scored:
        document_id = candidates[index].document.document_id
        if document_id in seen_documents:
            continue
        selected.append((score, index))
        seen_documents.add(document_id)
        if len(selected) >= limit:
            break
    if len(selected) < limit:
        chosen = {index for _score, index in selected}
        selected.extend(item for item in scored if item[1] not in chosen)
    selected = selected[:limit]

    query_tokens = {token.casefold() for token in re.findall(r"[A-Za-z0-9]+", question)}
    evidence: list[EvidenceChunk] = []
    for rank, (score, index) in enumerate(selected, 1):
        candidate = candidates[index]
        identity = "\0".join(
            (
                candidate.document.document_id,
                str(candidate.start_char),
                str(candidate.end_char),
                candidate.text,
            )
        )
        matched = sorted(
            query_tokens
            & {token.casefold() for token in re.findall(r"[A-Za-z0-9]+", candidate.text)}
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
                # Fused cosine lives in [-1, 1] but EvidenceChunk.score must be
                # positive. Shift to (0, 1] -- monotonic, so ranking is unchanged.
                score=round((float(score) + 1.0) / 2.0, 8),
                score_components=EvidenceScore(
                    bm25=0.0,
                    coverage=lexical_overlap(question, candidate.text),
                    fuzzy=0.0,
                    phrase=0.0,
                    title=0.0,
                ),
                matched_terms=matched,
            )
        )
    return evidence


def select_evidence(
    question: str,
    documents: list[RetrievalDocument],
    *,
    limit: int = 6,
    allow_calls: bool = True,
    trace_id: str = "crest_kg.answerability",
    **rank_kwargs: object,
) -> list[EvidenceChunk]:
    """Rank, then withhold everything when no passage states the requested fact.

    This is the product-facing entry point. ``rank_evidence`` alone will always
    return its best guesses, which is correct for ranking and wrong for a
    workbench that must be able to say the corpus does not answer a question.
    """

    ranked = rank_evidence(question, documents, limit=limit, **rank_kwargs)  # type: ignore[arg-type]
    if not ranked:
        return []
    verdict = judge_supporting(
        question,
        [(item.id, item.text) for item in ranked],
        trace_id=trace_id,
        allow_calls=allow_calls,
    )
    supporting = set(verdict.supporting_ids)
    kept = [item for item in ranked if item.id in supporting]
    return [item.model_copy(update={"rank": rank}) for rank, item in enumerate(kept, 1)]


def evaluate_retrieval_fixture(
    path: Path, *, allow_calls: bool = True
) -> dict[str, object]:
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
        evidence = select_evidence(
            case["query"],
            documents,
            limit=case["top_k"],
            allow_calls=allow_calls,
            trace_id=f"crest_kg.fixture/{path.stem}/{case['case_id']}",
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
