"""Bounded LangGraph workflow with unmodified TradingAgents bull/bear roles."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, TypedDict

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from tradingagents.agents.researchers.bear_researcher import create_bear_researcher
from tradingagents.agents.researchers.bull_researcher import create_bull_researcher

from stai.committee.evidence import deterministic_findings
from stai.committee.schemas import Evidence, Finding, FindingsPacket, Recommendation
from stai.committee.storage import save_finding


class ResearchState(TypedDict):
    findings: list[Finding]
    debate: dict[str, Any]
    recommendation: Recommendation | None


def validate_citations(
    findings: list[Finding], evidence: list[Evidence], expected_roles: set[str]
) -> None:
    if {f.role for f in findings} != expected_roles or len(findings) != len(expected_roles):
        raise ValueError("The stage returned missing or duplicate roles")
    allowed = {e.id for e in evidence}
    if any(not set(f.evidence_ids) <= allowed for f in findings):
        raise ValueError("Model cited an unknown evidence ID")


def checked_recommendation(
    rec: Recommendation, evidence: list[Evidence], market_type: str, now: datetime
) -> Recommendation:
    allowed = {e.id for e in evidence}
    if not set(rec.evidence_ids) <= allowed:
        raise ValueError("Recommendation cited unknown evidence")
    reasons: list[str] = []
    market = next(e for e in evidence if e.id == "market")
    if market.status != "fresh" or not 0 <= (now - market.observed_at).total_seconds() <= 60:
        reasons.append("Market observation is stale at recommendation time.")
    if any(e.status != "fresh" for e in evidence):
        reasons.append("Required evidence is stale or unavailable.")
    if market_type == "spot" and (
        rec.action == "research_short" or (rec.terms is not None and rec.terms.leverage != 1)
    ):
        reasons.append("Spot research must be long-only and unleveraged.")
    if rec.terms is not None:
        loss = abs(rec.terms.entry - rec.terms.stop) / rec.terms.entry * rec.terms.notional_usdt
        if loss > 5:
            reasons.append("Indicative planned loss exceeds initial 5 USDT research bound.")
    if reasons and rec.action != "abstain":
        return Recommendation(
            action="abstain",
            thesis="Research withheld: " + " ".join(reasons),
            confidence=0,
            supporting=rec.supporting,
            opposing=rec.opposing,
            uncertainties=list(dict.fromkeys(rec.uncertainties + reasons))[:8],
            evidence_ids=rec.evidence_ids,
            terms=None,
        )
    return rec


def build_workflow(
    database: Any,
    run_id: str,
    provider: Any,
    evidence: list[Evidence],
    symbol: str,
    market_type: str,
    memory: list[str],
    clock: Any,
):
    context = json.dumps(
        {
            "symbol": symbol,
            "marketType": market_type,
            "evidence": [e.model_dump(mode="json", by_alias=True) for e in evidence],
            "memory": memory,
            "limits": "No recurring runs approved; advisory-only; entries closed",
        },
        separators=(",", ":"),
    )

    def store(findings: list[Finding], roles: set[str]) -> None:
        validate_citations(findings, evidence, roles)
        for finding in findings:
            save_finding(database, run_id, finding)

    def calculations(state: ResearchState):
        findings = deterministic_findings(evidence)
        store(findings, {"quantitative", "execution"})
        return {"findings": findings}

    def analysts(state: ResearchState):
        packet = provider.generate(
            "analysts",
            "Produce exactly three role findings: technical, intelligence, derivatives. "
            "Assess 1h/15m alignment, public headline relevance, and swap funding/book conditions; "
            "spot derivatives analysis is contextual only. Mark unavailable news explicitly.\n"
            + context,
            FindingsPacket,
        )
        store(packet.findings, {"technical", "intelligence", "derivatives"})
        return {"findings": state["findings"] + packet.findings}

    def debate_node(role: str, factory: Any):
        def node(state: ResearchState):
            class RoleClient:
                def invoke(self, prompt: str):
                    finding = provider.generate(
                        role, f"Return a Finding with role exactly '{role}'.\n" + prompt, Finding
                    )
                    store([finding], {role})
                    self.finding = finding
                    return AIMessage(content=finding.model_dump_json())

            client = RoleClient()
            inherited = factory(client)
            debate = state.get("debate") or {
                "history": "",
                "bull_history": "",
                "bear_history": "",
                "current_response": "",
                "count": 0,
            }
            research = json.dumps([f.model_dump() for f in state["findings"]])
            updated = inherited(
                {
                    "trade_date": clock().isoformat(),
                    "company_of_interest": symbol,
                    "asset_type": "crypto",
                    "ticker": symbol,
                    "market_report": context + "\n" + research,
                    "sentiment_report": "Unavailable: no verified social sentiment source.",
                    "news_report": next(e for e in evidence if e.id == "news").model_dump_json(),
                    "fundamentals_report": "Not applicable: no equity fundamentals.",
                    "investment_debate_state": debate,
                }
            )
            return {
                "findings": state["findings"] + [client.finding],
                "debate": updated["investment_debate_state"],
            }

        return node

    def portfolio_risk(state: ResearchState):
        result = provider.generate(
            "portfolio_risk",
            "Return exactly portfolio and risk role findings. "
            "This is advisory review, not deterministic risk-engine approval.\n"
            + context
            + "\nPrior findings: "
            + json.dumps([f.model_dump() for f in state["findings"]]),
            FindingsPacket,
        )
        store(result.findings, {"portfolio", "risk"})
        return {"findings": state["findings"] + result.findings}

    def decision(state: ResearchState):
        rec = provider.generate(
            "cio",
            "As Chief Investment Officer produce one structured advisory recommendation. "
            "Prefer abstain if evidence is incomplete or old. Proposed terms are research only, "
            "not a proposal for approval. No account trades or historical success can be claimed.\n"
            + context
            + "\nFindings: "
            + json.dumps([f.model_dump() for f in state["findings"]]),
            Recommendation,
        )
        rec = checked_recommendation(rec, evidence, market_type, clock())
        finding = Finding(
            role="cio",
            summary=rec.thesis,
            confidence=rec.confidence,
            supporting=rec.supporting,
            opposing=rec.opposing,
            uncertainties=rec.uncertainties,
            evidence_ids=rec.evidence_ids,
        )
        store([finding], {"cio"})
        return {"findings": state["findings"] + [finding], "recommendation": rec}

    graph = StateGraph(ResearchState)
    for name, node in [
        ("calculations", calculations),
        ("analysts", analysts),
        ("bull", debate_node("bull", create_bull_researcher)),
        ("bear", debate_node("bear", create_bear_researcher)),
        ("portfolio_risk", portfolio_risk),
        ("cio", decision),
    ]:
        graph.add_node(name, node)
    nodes = [START, "calculations", "analysts", "bull", "bear", "portfolio_risk", "cio", END]
    for a, b in zip(nodes, nodes[1:], strict=False):
        graph.add_edge(a, b)
    return graph.compile()
