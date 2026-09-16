"""One-call evidence brief generation and deterministic citation validation."""

from __future__ import annotations

import json
from pathlib import Path

from .models import EvidenceBrief, EvidenceChunk, ProviderEvidenceBrief


ROOT = Path(__file__).parents[1]
PROMPT_PATH = ROOT / "prompts" / "crest_evidence_brief.yaml"
PROMPT_REF = "crest_kg.crest_evidence_brief@1"


def validate_provider_brief(
    brief: ProviderEvidenceBrief,
    evidence: list[EvidenceChunk],
) -> ProviderEvidenceBrief:
    """Reject invented citations and internally inconsistent answer states."""

    allowed = {item.id for item in evidence}
    cited = set(brief.synthesis_citation_ids)
    cited.update(
        citation_id
        for finding in brief.findings
        for citation_id in finding.citation_ids
    )
    unknown = sorted(cited - allowed)
    if unknown:
        raise ValueError(f"Evidence brief cited unknown chunks: {', '.join(unknown)}")
    if brief.answer_status in {"answered", "partial"}:
        if not brief.synthesis_citation_ids:
            raise ValueError("Answered or partial synthesis requires at least one citation")
        if not brief.findings:
            raise ValueError("Answered or partial brief requires at least one finding")
    if brief.answer_status == "insufficient" and brief.findings:
        if any(item.classification != "uncertainty" for item in brief.findings):
            raise ValueError(
                "An insufficient brief may contain only uncertainty findings"
            )
    return brief


def generate_evidence_brief(
    *,
    question: str,
    collection_title: str,
    evidence: list[EvidenceChunk],
    trace_id: str,
    max_budget_usd: float,
    max_output_tokens: int,
    structured_retries: int = 1,
) -> EvidenceBrief:
    """Generate one traced structured brief, or a deterministic empty result."""

    if not evidence:
        return EvidenceBrief(
            answer_status="insufficient",
            synthesis="No retained collection passage matched the question strongly enough to support an answer.",
            synthesis_citation_ids=[],
            findings=[],
            unresolved_questions=[
                "Which additional source could directly address this question?"
            ],
            model="deterministic-no-evidence",
            trace_id=trace_id,
            observed_cost_usd=0.0,
        )

    from llm_client import call_llm_structured, get_model, render_prompt

    model = get_model("synthesis", use_performance=False)
    evidence_payload = [
        {
            "evidence_id": item.id,
            "document_id": item.document_id,
            "title": item.title,
            "rank": item.rank,
            "exact_text": item.text,
        }
        for item in evidence
    ]
    messages = render_prompt(
        PROMPT_PATH,
        question=question,
        collection_title=collection_title,
        evidence_json=json.dumps(evidence_payload, ensure_ascii=False, indent=2),
    )
    provider_brief, result = call_llm_structured(
        model,
        messages,
        response_model=ProviderEvidenceBrief,
        task="crest_kg.evidence_brief",
        trace_id=f"{trace_id}/brief",
        budget_scope_trace_id=trace_id,
        max_budget=max_budget_usd,
        max_tokens=max_output_tokens,
        num_retries=structured_retries,
        reasoning_effort="medium",
        model_policy="enforce_allowlist",
        model_justification=(
            "Resolved through llm_client get_model('synthesis', "
            "use_performance=False) for one structured CREST evidence brief."
        ),
        prompt_ref=PROMPT_REF,
    )
    validated = validate_provider_brief(provider_brief, evidence)
    return EvidenceBrief(
        **validated.model_dump(),
        model=model,
        trace_id=trace_id,
        observed_cost_usd=float(result.cost or 0.0),
    )
