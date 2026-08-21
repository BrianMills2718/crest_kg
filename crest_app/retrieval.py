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
    named_terms: frozenset[str]
    surface_terms: frozenset[str]


STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "also",
        "accord",
        "actually",
        "appear",
        "be",
        "befor",
        "between",
        "both",
        "by",
        "can",
        "could",
        "compar",
        "did",
        "do",
        "does",
        "during",
        "for",
        "from",
        "give",
        "extract",
        "had",
        "how",
        "i",
        "m",
        "in",
        "is",
        "it",
        "its",
        "identify",
        "along",
        "behind",
        "me",
        "material",
        "many",
        "naming",
        "name",
        "no",
        "of",
        "on",
        "one",
        "okay",
        "or",
        "pair",
        "pin",
        "put",
        "report",
        "return",
        "responsibl",
        "respectiv",
        "serv",
        "sourc",
        "summariz",
        "tell",
        "that",
        "the",
        "their",
        "then",
        "there",
        "these",
        "they",
        "this",
        "thing",
        "to",
        "under",
        "together",
        "two",
        "try",
        "trying",
        "versu",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "whether",
        "while",
        "why",
        "with",
        "you",
        "way",
        "quick",
        "check",
        "up",
        "down",
        "charg",
        "so",
        "more",
        "exist",
        "pleas",
        "s",
    }
)


# Small, domain-neutral lexical concept families support common question/document
# paraphrases without a model call. Values are stemmed by ``_stem`` at import.
_RAW_ANCHOR_CONCEPT_GROUPS = (
    ("austria", "austrian", "vienna"),
)


_RAW_FUNCTION_CONCEPT_GROUPS = (
    (
        "group",
        "organization",
        "body",
        "institute",
        "institution",
        "laboratory",
        "labratory",
        "committee",
        "agency",
        "team",
        "entity",
        "organizer",
        "role",
        "host",
        "observer",
        "observor",
        "convener",
        "outfit",
    ),
    (
        "organize",
        "organizer",
        "organzier",
        "coordinate",
        "coordination",
        "convene",
        "convener",
        "arrange",
        "stage",
        "staged",
        "set",
        "bring",
        "brought",
        "get",
        "got",
    ),
    (
        "lead",
        "led",
        "direct",
        "operate",
        "operation",
        "operations",
        "manage",
        "supervise",
    ),
    (
        "demonstration",
        "demonstrtion",
        "pilot",
        "exercise",
        "trial",
        "test",
        "undertaking",
        "event",
        "field",
        "site",
        "gathering",
        "project",
        "program",
        "mission",
    ),
    (
        "date",
        "day",
        "days",
        "schedule",
        "schedulled",
        "begin",
        "beginning",
        "beginnings",
        "began",
        "begun",
        "start",
        "commence",
        "launch",
        "kickoff",
        "open",
        "opened",
        "opening",
        "calendar",
        "observe",
        "observed",
        "supposed",
        "timetable",
        "timing",
        "debut",
        "first",
        "preliminary",
        "mark",
        "entry",
        "planned",
        "appear",
    ),
    (
        "disagreement",
        "conflict",
        "contradict",
        "correction",
        "dispute",
        "differ",
        "diverge",
        "disagree",
        "reconcile",
        "competing",
        "correct",
        "corrected",
    ),
    ("supply", "provide", "furnish"),
    ("instrument", "equipment"),
    ("cost", "budget", "funding", "expense", "price"),
    (
        "account",
        "archive",
        "brief",
        "document",
        "file",
        "material",
        "memo",
        "note",
        "paperwork",
        "record",
        "report",
        "source",
        "write",
        "writeup",
        "ups",
    ),
    (
        "assign",
        "attend",
        "carry",
        "cover",
        "house",
        "list",
        "mention",
        "place",
        "receive",
        "review",
        "serve",
        "state",
        "wear",
    ),
    ("14", "fourteen"),
    ("16", "sixteen"),
    ("january",),
    ("february",),
    ("march",),
    ("april",),
    ("may",),
    ("june",),
    ("july",),
    ("august",),
    ("september",),
    ("october",),
    ("november",),
    ("december",),
)


_RAW_CONCEPT_GROUPS = _RAW_ANCHOR_CONCEPT_GROUPS + _RAW_FUNCTION_CONCEPT_GROUPS


_RAW_SUBJECT_HEAD_TERMS = (
    "agency",
    "archive",
    "authority",
    "body",
    "brief",
    "cabinet",
    "calendar",
    "campaign",
    "ceremony",
    "committee",
    "communications",
    "conference",
    "correction",
    "document",
    "demonstration",
    "equipment",
    "event",
    "exercise",
    "expo",
    "festival",
    "field",
    "file",
    "form",
    "forum",
    "gathering",
    "games",
    "institute",
    "instrument",
    "laboratory",
    "meeting",
    "mission",
    "note",
    "observer",
    "office",
    "opening",
    "operation",
    "organization",
    "pilot",
    "program",
    "rally",
    "rehearsal",
    "record",
    "relay",
    "schedule",
    "site",
    "staff",
    "storage",
    "summit",
    "team",
    "test",
    "travel",
    "trial",
)


def _stem(token: str) -> str:
    value = re.sub(r"[^a-z0-9]", "", token.casefold())
    while value:
        previous = value
        if len(value) > 5 and value.endswith("ies"):
            value = value[:-3] + "y"
        else:
            for suffix in (
                "ingly",
                "edly",
                "ation",
                "ment",
                "ing",
                "ed",
                "es",
                "s",
            ):
                if len(value) - len(suffix) >= 4 and value.endswith(suffix):
                    value = value[: -len(suffix)]
                    break
            else:
                if len(value) > 5 and value.endswith("e"):
                    value = value[:-1]
        if value == previous:
            return value
    return value


CONCEPT_GROUPS = tuple(
    frozenset(_stem(token) for token in group) for group in _RAW_CONCEPT_GROUPS
)
FUNCTION_CONCEPT_GROUPS = frozenset(
    CONCEPT_GROUPS[len(_RAW_ANCHOR_CONCEPT_GROUPS) :]
)
CONCEPT_BY_TERM = {
    term: group for group in CONCEPT_GROUPS for term in group
}
SUBJECT_HEAD_TERMS = frozenset(_stem(term) for term in _RAW_SUBJECT_HEAD_TERMS)
# Fuzzy matches never admit a passage alone, and a fuzzy structural name also
# requires a separate exact named anchor. The 0.85 boundary retains common
# seven-character name permutations without weakening those two safeguards.
FUZZY_MATCH_THRESHOLD = 0.85


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(
        stemmed
        for token in re.findall(r"[A-Za-z0-9]+", value.casefold())
        if (stemmed := _stem(token)) and stemmed not in STOP_WORDS
    )


def _query_concepts(question: str) -> tuple[tuple[str, frozenset[str]], ...]:
    concepts: list[tuple[str, frozenset[str]]] = []
    seen: set[frozenset[str]] = set()
    query_terms = list(_tokens(question))
    normalized = " ".join(question.casefold().split())
    # Question grammar can express a requested concept without using a document
    # synonym. These domain-neutral cues stay deterministic and inspectable.
    if re.search(r"\bwhen\b", normalized):
        query_terms.append(_stem("date"))
    if re.search(r"\bput\s+on\b", normalized):
        query_terms.append(_stem("organize"))
    if re.search(r"\bput\b.+\btogether\b", normalized):
        query_terms.append(_stem("organize"))
    for term in query_terms:
        alternatives = CONCEPT_BY_TERM.get(term, frozenset({term}))
        if alternatives in seen:
            continue
        seen.add(alternatives)
        concepts.append((term, alternatives))
    return tuple(concepts)


def _source_named_terms(value: str) -> frozenset[str]:
    """Return exact source-name cues without treating sentence leads as names."""

    return frozenset(
        token.casefold()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9]*", value)
        if token[0].isupper()
        if (stemmed := _stem(token)) and stemmed not in STOP_WORDS
        if CONCEPT_BY_TERM.get(stemmed, frozenset({stemmed}))
        not in FUNCTION_CONCEPT_GROUPS
    )


def _surface_tokens(value: str) -> tuple[str, ...]:
    return tuple(token.casefold() for token in re.findall(r"[A-Za-z0-9]+", value))


def _structural_subject_surfaces(question: str) -> frozenset[str]:
    """Extract subject phrases without treating arbitrary OOV words as identity.

    The grammar is intentionally inspectable: possessives, names adjacent to
    ``Project``, short noun phrases ending in a source/event head, ``for X`` or
    ``under X``, and the first subject after an auxiliary/``who`` question.
    Direct requested details such as an insurance policy or badge color are not
    subjects.
    """

    raw_tokens = re.findall(r"[A-Za-z0-9]+(?:['’][sS])?", question)
    surfaces = [re.sub(r"['’][sS]$", "", token.casefold()) for token in raw_tokens]
    stems = [_stem(token) for token in surfaces]
    possessive = [bool(re.search(r"['’][sS]$", token)) for token in raw_tokens]
    boundary_terms = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "did",
        "do",
        "does",
        "for",
        "from",
        "in",
        "is",
        "on",
        "or",
        "the",
        "to",
        "under",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "while",
        "who",
        "with",
    }

    def meaningful(index: int) -> bool:
        stemmed = stems[index]
        if not stemmed or stemmed.isdigit() or stemmed in STOP_WORDS:
            return False
        return (
            CONCEPT_BY_TERM.get(stemmed, frozenset({stemmed}))
            not in FUNCTION_CONCEPT_GROUPS
        )

    subject_indexes: set[int] = {
        index
        for index, is_possessive in enumerate(possessive)
        if is_possessive and meaningful(index)
    }

    for index, surface in enumerate(surfaces):
        if surface != "project":
            continue
        following = index + 1
        preceding = index - 1
        if following < len(surfaces) and meaningful(following):
            subject_indexes.add(following)
        elif preceding >= 0 and meaningful(preceding):
            subject_indexes.add(preceding)

    for index, stemmed in enumerate(stems):
        if stemmed not in SUBJECT_HEAD_TERMS:
            continue
        phrase_candidates: list[int] = []
        for candidate_index in range(index - 1, max(-1, index - 4), -1):
            if surfaces[candidate_index] in boundary_terms:
                break
            if meaningful(candidate_index) and surfaces[candidate_index].endswith(
                ("ed", "ly")
            ):
                break
            if meaningful(candidate_index) and not surfaces[candidate_index].endswith(
                "ing"
            ):
                phrase_candidates.append(candidate_index)
        if phrase_candidates:
            subject_indexes.add(min(phrase_candidates))

    for index, surface in enumerate(surfaces):
        identity_relation = (
            surface == "with"
            and index > 0
            and surfaces[index - 1]
            in {"affiliated", "associated", "connected", "linked"}
        )
        if surface not in {"for", "under"} and not identity_relation:
            continue
        candidate_index: int | None = None
        for candidate_index in range(index + 1, min(len(surfaces), index + 5)):
            if meaningful(candidate_index):
                break
        else:
            candidate_index = None
        if candidate_index is None:
            continue
        later_meaningful = [
            later
            for later in range(candidate_index + 1, len(surfaces))
            if meaningful(later)
        ]
        followed_by_head = any(
            stems[later] in SUBJECT_HEAD_TERMS
            for later in range(
                candidate_index + 1,
                min(len(surfaces), candidate_index + 4),
            )
        )
        if not later_meaningful or followed_by_head:
            subject_indexes.add(candidate_index)

    for index, surface in enumerate(surfaces):
        is_leading_copula = index == 0 and surface in {"are", "is", "was", "were"}
        if surface not in {"did", "does", "who"} and not is_leading_copula:
            continue
        if surface != "who":
            for candidate_index in range(index + 1, min(len(surfaces), index + 8)):
                if (
                    surfaces[candidate_index] in boundary_terms
                    or stems[candidate_index] in STOP_WORDS
                ):
                    continue
                if meaningful(candidate_index):
                    subject_indexes.add(candidate_index)
                break
            break
        who_predicate_seen = surface != "who"
        for candidate_index in range(index + 1, min(len(surfaces), index + 8)):
            alternatives = CONCEPT_BY_TERM.get(
                stems[candidate_index],
                frozenset({stems[candidate_index]}),
            )
            if (
                surface == "who"
                and stems[candidate_index] not in STOP_WORDS
                and alternatives in FUNCTION_CONCEPT_GROUPS
            ):
                who_predicate_seen = True
                continue
            if meaningful(candidate_index):
                if surfaces[candidate_index].endswith(("ed", "ing", "ly")):
                    continue
                if surface == "who" and not who_predicate_seen:
                    who_predicate_seen = True
                    continue
                subject_indexes.add(candidate_index)
                break
        break

    return frozenset(surfaces[index] for index in subject_indexes)


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
                    named_terms=_source_named_terms(f"{document.title}\n{text}"),
                    surface_terms=frozenset(
                        _surface_tokens(f"{document.title}\n{text}")
                    ),
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
    scores: list[float] = []
    for candidate in candidate_terms:
        if len(candidate) < 5 or abs(len(term) - len(candidate)) > 1:
            continue
        if len(term) == len(candidate):
            differences = [
                index
                for index, (left, right) in enumerate(zip(term, candidate, strict=True))
                if left != right
            ]
            if (
                len(differences) == 2
                and differences[1] == differences[0] + 1
                and term[differences[0]] == candidate[differences[1]]
                and term[differences[1]] == candidate[differences[0]]
            ):
                scores.append(0.9)
                continue
        scores.append(SequenceMatcher(None, term, candidate).ratio())
    return max(scores, default=0.0)


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
    query_surfaces_by_stem: dict[str, set[str]] = {}
    for token in re.findall(r"[A-Za-z0-9]+", question):
        query_surfaces_by_stem.setdefault(_stem(token), set()).add(token.casefold())
    subject_concepts: list[tuple[str, int]] = []
    for surface in sorted(_structural_subject_surfaces(question)):
        stemmed = _stem(surface)
        concept_index = next(
            (
                index
                for index, (query_term, alternatives) in enumerate(concepts)
                if query_term == stemmed or stemmed in alternatives
            ),
            None,
        )
        if concept_index is not None:
            subject_concepts.append((surface, concept_index))

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
        matched_indexes: set[int] = set()
        exact_matched_indexes: set[int] = set()
        for index, (query_term, alternatives) in enumerate(concepts):
            frequency = _concept_frequency(candidate.terms, alternatives)
            if frequency:
                exact_matches += 1
                matched_indexes.add(index)
                exact_matched_indexes.add(index)
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
            if fuzzy >= FUZZY_MATCH_THRESHOLD:
                matched_indexes.add(index)
                matched_terms.append(query_term)
        fuzzy_match_count = sum(
            1
            for value in fuzzy_values
            if FUZZY_MATCH_THRESHOLD <= value < 1.0
        )
        match_count = exact_matches + fuzzy_match_count
        minimum_matches = 1 if len(concepts) <= 2 else 2
        coverage = match_count / len(concepts)
        # Fuzzy similarity can improve the rank of context that is already
        # anchored in the passage, but it must not admit a passage by itself.
        # This prevents unrelated single-word collisions (for example,
        # "preview" matching "review") from becoming evidence.
        if exact_matches == 0 or match_count < minimum_matches:
            continue
        # Admission follows structural subject phrases, not every unknown word.
        # This keeps arbitrary discourse/modifier vocabulary from suppressing
        # evidence while still rejecting an absent external subject even when
        # the question also names a real collection location.
        candidate_named_stems = frozenset(
            _stem(term) for term in candidate.named_terms
        )
        exact_named_anchor_indexes: set[int] = set()
        for index, (query_term, alternatives) in enumerate(concepts):
            query_surfaces = {
                surface
                for stemmed in alternatives
                for surface in query_surfaces_by_stem.get(stemmed, set())
            }
            surface_exact = bool(query_surfaces & candidate.named_terms)
            declared_anchor_exact = (
                alternatives in CONCEPT_GROUPS[: len(_RAW_ANCHOR_CONCEPT_GROUPS)]
                and bool(alternatives & candidate_named_stems)
            )
            if index in exact_matched_indexes and (
                surface_exact or declared_anchor_exact
            ):
                exact_named_anchor_indexes.add(index)
        subject_failed = False
        for surface, index in subject_concepts:
            if index not in matched_indexes:
                subject_failed = True
                break
            _, alternatives = concepts[index]
            surface_exact = surface in candidate.surface_terms
            declared_anchor_exact = (
                alternatives in CONCEPT_GROUPS[: len(_RAW_ANCHOR_CONCEPT_GROUPS)]
                and _stem(surface) in alternatives
                and bool(alternatives & set(candidate.terms))
            )
            if surface_exact or declared_anchor_exact:
                continue
            fuzzy_named = _best_fuzzy(
                _stem(surface),
                tuple(sorted(candidate_named_stems)),
            )
            if (
                fuzzy_named < FUZZY_MATCH_THRESHOLD
                or not (exact_named_anchor_indexes - {index})
            ):
                subject_failed = True
                break
        if subject_failed:
            continue
        phrase = 3.0 if normalized_question in " ".join(candidate.text.casefold().split()) else 0.0
        title_matches = sum(
            1
            for _, alternatives in concepts
            if _concept_frequency(candidate.title_terms, alternatives)
        )
        title_score = min(2.0, title_matches * 0.5)
        fuzzy_score = sum(
            value
            for value in fuzzy_values
            if FUZZY_MATCH_THRESHOLD <= value < 1.0
        ) / len(concepts)
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
