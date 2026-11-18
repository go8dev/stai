"""Bounded public evidence; no tools are exposed to model-generated instructions."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree  # noqa: S405 (DTD/entity input rejected below)

import httpx

from stai.committee.schemas import Evidence, Finding
from stai.core.time import utcnow
from stai.marketdata.schemas import MarketScannerRow

NEWS_URL = "https://cointelegraph.com/rss"


async def public_news(http: httpx.AsyncClient, now: datetime) -> Evidence:
    """Headlines/links only, never full articles. Failure is explicit evidence."""
    items: list[dict[str, str]] = []
    try:
        async with http.stream("GET", NEWS_URL, follow_redirects=False) as response:
            response.raise_for_status()
            content = b""
            async for chunk in response.aiter_bytes():
                content += chunk
                if len(content) > 400_000:
                    raise ValueError("oversized feed")
        if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
            raise ValueError("DTD not accepted")
        root = ElementTree.fromstring(content)  # noqa: S314 (bounded, DTD-free input)
        for item in root.findall(".//item")[:40]:
            title = re.sub(r"<[^>]*>", "", item.findtext("title") or "")[:180]
            link = item.findtext("link") or ""
            published = parsedate_to_datetime(item.findtext("pubDate") or "")
            if published.tzinfo is None:
                continue
            age = (now - published.astimezone(UTC)).total_seconds()
            if 0 <= age <= 86400 and link.startswith("https://cointelegraph.com/"):
                items.append({"title": title, "url": link, "publishedAt": published.isoformat()})
            if len(items) == 5:
                break
    except (httpx.HTTPError, ValueError, TypeError, ElementTree.ParseError, OverflowError):
        items = []
    return Evidence(
        id="news",
        kind="public_headlines",
        source=NEWS_URL,
        observed_at=now,
        status="fresh" if items else "unavailable",
        summary="Attributed crypto headlines from the last 24h; relevance must be assessed."
        if items
        else "Public news unavailable; no sentiment or news claims are supported.",
        data={"headlines": items, "scope": "Broad crypto news, not asset-specific sentiment"},
    )


def market_evidence(row: MarketScannerRow, snapshot_id: str) -> Evidence:
    data = row.model_dump(mode="json", by_alias=True)
    # Only completed candles, bounded to 8 observations per interval for prompt size.
    # Indicators were calculated from the full completed series by the reused analytics.
    data["candles"] = [c.model_dump(mode="json", by_alias=True) for c in row.candles if c.complete][
        -8:
    ]
    data["candles15M"] = [
        c.model_dump(mode="json", by_alias=True) for c in row.candles_15m if c.complete
    ][-8:]
    return Evidence(
        id="market",
        kind="okx_snapshot",
        source="https://www.okx.com",
        observed_at=row.observed_at or utcnow(),
        status=row.status,
        summary=f"{row.symbol} {row.market_type}; persisted snapshot {snapshot_id}",
        data=data,
    )


def deterministic_findings(evidence: list[Evidence]) -> list[Finding]:
    market = next(e for e in evidence if e.id == "market")
    data = market.data
    scores = data.get("setupScores")
    score_summary = (
        {
            side: {"score": result.get("score"), "reasons": result.get("reasons")}
            for side, result in scores.get("scores", {}).items()
        }
        if isinstance(scores, dict)
        else "Unavailable"
    )
    return [
        Finding(
            role="quantitative",
            summary="Completed 1h/15m indicator screen and deterministic setup scoring.",
            supporting=[str(data.get("indicators")), str(score_summary)],
            opposing=["Screening scores are not calibrated probabilities or trade permissions."],
            uncertainties=["Stop/target rules still require pre-pilot OKX backtesting."],
            evidence_ids=["market"],
            confidence=100 if market.status == "fresh" else 0,
        ),
        Finding(
            role="execution",
            summary="Read-only execution feasibility; entry gate remains closed.",
            supporting=[
                f"Visible spread percentage: {data.get('spreadPct')}",
                f"Instrument rules: {data.get('instrument')}",
                "Spot maker/taker defaults 0.10%/0.15%; futures 0.02%/0.05% per notional.",
            ],
            opposing=["No order submission, permit issuance or deterministic risk approval."],
            uncertainties=["Displayed depth is not guaranteed liquidity; fills are simulated."],
            evidence_ids=["market", "portfolio"],
            confidence=100,
        ),
    ]
