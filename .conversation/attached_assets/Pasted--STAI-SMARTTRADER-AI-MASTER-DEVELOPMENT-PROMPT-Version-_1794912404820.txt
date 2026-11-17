# STAI — SMARTTRADER AI
## MASTER DEVELOPMENT PROMPT
### Version 1.0 | Replit MVP | November 2026

## 1. PROJECT OVERVIEW

You are the Lead Software Architect and Senior Full-Stack Engineer responsible for building **STAI (SmartTrader AI)**, pronounced "Stay."

STAI is a personal AI-powered cryptocurrency research, portfolio management, and paper-trading platform.

It operates like a small investment firm where specialized AI agents collaborate to analyze financial markets, debate opportunities, assess risks, and recommend trades.

The owner retains final control over every new trade entry.

Our initial objective is to operate a **1,000 USDT virtual fund for 30 consecutive days**, using real OKX market data, realistic simulated execution, and AI-generated trading recommendations.

The goal is to evaluate trading performance, decision quality, risk management, and the practical usefulness of a multi-agent AI investment committee.

**This release is strictly for paper trading. Real-money trading is prohibited.**

Build a functioning web application, not just a UI prototype.

---

## 2. YOUR ENGINEERING ROLE

Act as a coordinated development team with the following responsibilities:

- Software architecture
- Frontend engineering
- Backend engineering
- AI agent integration
- Quantitative trading integration
- Database engineering
- Security
- Testing and quality assurance
- Deployment and operations
- UI/UX design

Use established software engineering practices, but keep the MVP architecture simple and maintainable.

Do not introduce microservices, Kubernetes, complex event streaming, or unnecessary enterprise infrastructure.

Prefer a modular monolith for STAI's custom application, with separate trading and AI workers only where technically necessary.

Make decisions that allow future scaling without requiring premature complexity.

---

## 3. BRANDING AND DESIGN SYSTEM

### Working identity

Brand name: **STAI**

Pronunciation: Stay

Expanded name: SmartTrader AI

Primary tagline: **Stay Ahead. Stay in Control.**

Supporting tagline: **Intelligence in Every Trade.**

Brand personality:

- Intelligent
- Analytical
- Disciplined
- Trustworthy
- Precise
- Modern
- Technology-forward

STAI is a working name. Do not assume trademark clearance or commercial exclusivity.

### Visual direction

Create a hybrid design combining:

**Institutional trading platform**
- Professional financial dashboards
- Precise data visualization
- Clean portfolio tables
- Advanced market charts
- Readable financial metrics
- Clear trading controls

**Futuristic AI intelligence platform**
- AI agent status panels
- Research workflow visualizations
- Agent collaboration views
- Subtle technology-inspired visual elements
- Restrained teal accents
- Clear presentation of AI findings

Avoid excessive animations, neon effects, and speculative cryptocurrency imagery.

### Brand colors

| Token | Hex |
|---|---|
| Main background | #0B1220 |
| Card background | #151F30 |
| Brand accent | #25C6B0 |
| Primary text | #F4F7FB |
| Secondary text | #94A3B8 |
| Profit | #22C55E |
| Loss | #EF6464 |
| Warning/approval | #E7B65A |

Typography:

- Inter for general UI
- IBM Plex Mono for financial values
- Tabular numerals for changing prices

### Logo

Create a minimal geometric S monogram with a subtle data-signal concept.

Use STAI as the primary wordmark and SmartTrader AI as the expanded descriptor.

Provide a favicon and application icon.

Treat logo assets as provisional until brand clearance.

### UI requirements

Responsive desktop and mobile web application.

Dark theme by default.

Clearly label all trading screens as PAPER mode.

Never display fictional trading results as actual portfolio performance.

---

## 4. MANDATORY OPEN-SOURCE RESEARCH

Before implementation, inspect these GitHub repositories.

### A. Freqtrade — Trading engine

Repository:
https://github.com/freqtrade/freqtrade

Documentation:
https://www.freqtrade.io/

Investigate:

- OKX exchange support
- Spot trading
- USDT perpetual futures
- Dry-run trading
- Strategy engine
- Order management
- Stop-loss and take-profit
- Backtesting
- Position accounting
- REST API
- Persistent trading history

Relevant source files:

- `freqtrade/freqtradebot.py`
- `freqtrade/exchange/okx.py`
- `freqtrade/optimize/backtesting.py`
- `freqtrade/rpc/api_server/api_v1.py`
- `freqtrade/strategy/interface.py`

Use existing functionality wherever reliable.

Do not rewrite the trading engine without a justified reason.

### B. TradingAgents — AI investment committee

Repository:
https://github.com/TauricResearch/TradingAgents

Inspect:

- `tradingagents/graph/trading_graph.py`
- `tradingagents/graph/setup.py`
- Analyst agents
- Bull/Bear research debate
- Risk debate
- Portfolio manager
- Trader agent
- LLM configuration
- Agent memory
- Research reporting

Adapt the framework to cryptocurrency markets.

### C. Supporting libraries

LangGraph:
https://github.com/langchain-ai/langgraph

CCXT:
https://github.com/ccxt/ccxt

FreqUI:
https://github.com/freqtrade/frequi

Optional architectural references:

https://github.com/hummingbot/hummingbot

https://github.com/virattt/ai-hedge-fund

Do not install or merge all these projects automatically.

Use only what is needed.

Record the upstream versions, relevant licenses, dependencies, and integration decisions.

Freqtrade is GPL-3.0; document licensing implications for potential future distribution or commercialization.

---

## 5. RECOMMENDED TECHNOLOGY STACK

Frontend:

- React
- TypeScript
- Tailwind CSS
- Next.js or Vite, whichever is more appropriate for the Replit runtime
- Lightweight financial charting

Backend:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic migrations

Database:

- PostgreSQL

AI:

- TradingAgents
- LangGraph
- Configurable LLM provider
- Structured agent outputs

Trading:

- Freqtrade
- OKX public market data
- CCXT where necessary

Operations:

- Replit Secrets
- Persistent database
- Background processing
- Application logging
- Health checks
- Automated tests

Use one custom application backend and a small number of dedicated workers if required.

Verify Replit deployment capabilities before finalizing the architecture.

Do not assume that a development workspace will remain active 24/7.

---

## 6. CORE APPLICATION MODULES

### Module 1 — Fund Command Center

Create the main dashboard showing:

- Virtual fund equity
- Available capital
- Spot allocation
- Futures allocation
- Current exposure
- Realized P&L
- Unrealized P&L
- Daily performance
- Open positions
- Pending approvals
- System health

### Module 2 — AI Investment Committee

Create specialized agents:

1. Chief Investment Officer
2. Technical Analyst
3. Quantitative Researcher
4. Market Intelligence Analyst
5. Derivatives Analyst
6. Bull Researcher
7. Bear Researcher
8. Portfolio Manager
9. Risk Officer
10. Execution Specialist

Reuse TradingAgents' existing roles where possible.

Do not create ten independent LLM calls when existing shared workflows or deterministic calculations are sufficient.

Agents must provide structured findings and evidence.

### Module 3 — Market Scanner

Monitor:

- BTC/USDT
- ETH/USDT
- SOL/USDT

Support spot and eligible USDT-margined perpetual instruments.

Display:

- Prices
- Market trends
- Technical indicators
- Volatility
- Potential opportunities
- Market-data freshness

### Module 4 — Trade Proposal Center

AI-generated proposals must contain:

- Instrument
- Market type
- Trade direction
- Proposed entry
- Quantity
- Position notional
- Leverage if applicable
- Stop-loss
- Take-profit
- Maximum planned loss
- Estimated trading costs
- AI investment thesis
- Risk assessment
- Proposal expiration

The owner can approve or reject proposals.

Approval must apply to the exact trade parameters.

### Module 5 — Portfolio Management

Track:

- Cash
- Spot holdings
- Futures positions
- Available margin
- Collateral
- Exposure
- Fees
- Funding
- Realized and unrealized P&L

### Module 6 — Trading Journal

Record:

- AI recommendations
- Approval decisions
- Simulated orders
- Order fills
- Position changes
- Fees
- Funding
- Exits
- Trading results

### Module 7 — Performance Analytics

Show:

- Equity curve
- Daily P&L
- Cumulative return
- Win rate
- Profit factor
- Maximum drawdown
- Trade expectancy
- Spot/futures performance
- Benchmark comparisons
- AI operating costs

### Module 8 — Strategy Laboratory

Provide historical backtesting and strategy comparisons using existing engine capabilities.

### Module 9 — Risk Management

Show and enforce:

- Position limits
- Leverage limits
- Daily loss limit
- Drawdown limit
- Capital allocation
- Emergency halt
- Risk events

### Module 10 — Pilot Monitor

Track the formal 30-day paper-trading experiment.

---

## 7. AI TRADING WORKFLOW

Implement this process:

1. Scan market data.
2. Detect a possible opportunity.
3. Run technical and quantitative analysis.
4. Collect relevant market intelligence.
5. Analyze futures conditions when applicable.
6. Conduct Bull/Bear debate.
7. Review portfolio allocation.
8. Evaluate risk.
9. Generate CIO recommendation.
10. Run deterministic risk validation.
11. Create pending trade proposal.
12. Notify owner.
13. Wait for owner approval.
14. Revalidate the proposal.
15. Execute in paper mode.
16. Record results in the portfolio ledger and journal.

AI agents are advisory.

The deterministic risk engine has veto authority.

**Every new entry requires explicit human approval.**

Protective exits may execute automatically only under the policy approved with the entry.

No agent can directly submit an order.

---

## 8. VIRTUAL FUND CONFIGURATION

Initial capital:

**1,000 USDT**

Initial allocation:

- 600 USDT spot
- 400 USDT futures

These are allocations within one fund, not separate additional balances.

Initial risk configuration:

- Planned risk per trade: 0.5% of equity
- Maximum position notional: 20% of equity
- Maximum concurrent positions: 3
- Maximum futures leverage: 2×
- Futures margin mode: isolated
- Daily loss halt: 2%
- Portfolio drawdown pause: 5%

All limits must be configurable.

Validate all supported OKX instruments, minimum order sizes, contract sizes, and margin requirements.

Do not force trades that cannot satisfy the limits with 1,000 USDT.

---

## 9. REALISTIC PAPER EXECUTION

Use live OKX market data.

Simulate:

- Bid/ask spread
- Slippage
- Trading fees
- Market and limit orders
- Order latency
- Partial fills where feasible
- Stop-loss and take-profit
- Futures funding
- Collateral usage
- Margin requirements
- Liquidation risk

Do not assume every order executes at the last traded price.

Use documented conservative assumptions when reliable data is unavailable.

Preserve raw simulation events and adjusted portfolio accounting.

No live order submission is permitted.

---

## 10. DATABASE REQUIREMENTS

Use PostgreSQL with migrations.

Minimum data models:

- Users
- Funds
- Allocations
- Risk policies
- Instruments
- Market snapshots
- Agents
- Agent runs
- Strategies
- Trade proposals
- Risk evaluations
- Approvals
- Orders
- Fills
- Positions
- Funding payments
- Ledger entries
- Equity snapshots
- Pilot sessions
- Audit events

Use decimal-safe financial values.

Use UTC timestamps.

Record all significant trading events.

Implement idempotency for orders and approval actions.

The portfolio ledger must reconcile cash, positions, fees, funding, and equity.

---

## 11. INDUSTRY-STANDARD DEVELOPMENT GUIDELINES

Follow these practices without introducing unnecessary complexity.

### 11.1 Clean architecture

Separate responsibilities into:

- Frontend
- API
- Business services
- Trading integration
- AI integration
- Database
- Background jobs

Keep business rules outside UI components.

Avoid duplicated logic.

### 11.2 Coding standards

Use:

- TypeScript strict mode
- Python type hints
- Pydantic validation
- Clear naming conventions
- Small, focused functions
- Consistent error handling
- Dependency version pinning

Use established formatters and linters such as ESLint, Prettier, and Ruff.

### 11.3 Git workflow

Use Git from the beginning.

Maintain a readable commit history.

Use feature branches for significant changes.

Keep the main branch in a working state.

Do not commit API keys, passwords, database credentials, or generated secrets.

### 11.4 Configuration

Use environment variables and Replit Secrets.

Provide an example environment configuration without real credentials.

Separate development, testing, and pilot configurations.

Keep paper mode as the default and only available execution mode in the MVP.

### 11.5 Security

Implement:

- Secure owner authentication
- Server-side authorization
- Input validation
- Secret management
- Safe logging
- Rate limits for sensitive endpoints
- CSRF protection where applicable
- Approval audit history
- Independent execution authorization

Do not expose internal trading APIs publicly without protection.

Do not give AI agents direct order execution privileges.

### 11.6 Testing

Create automated tests for critical functionality.

Prioritize:

- Fund initialization
- Risk calculations
- Approval enforcement
- Order idempotency
- Fee calculations
- Funding accounting
- Position updates
- Portfolio reconciliation
- Emergency halt
- Restart recovery

Use unit tests for calculations and integration tests for service boundaries.

Add a small number of end-to-end tests for essential owner workflows.

### 11.7 Documentation

Maintain:

- README
- Architecture overview
- Environment setup
- Database schema
- Trading integration notes
- AI workflow notes
- Risk rules
- Testing instructions
- Deployment instructions
- Known limitations

Keep documentation concise and updated.

### 11.8 Error handling and observability

Use structured logs.

Include timestamps and correlation IDs for trading workflows.

Expose basic service health status.

Report market-data outages, failed agent runs, order failures, and ledger mismatches.

Do not expose secrets in logs.

### 11.9 Database management

Use migrations.

Do not modify production-like schemas manually.

Use transactions for financial updates.

Never use floating-point arithmetic for authoritative balances.

Maintain an append-only financial audit trail.

### 11.10 Definition of Done

A feature is complete only when:

- The backend function works.
- The UI is connected to actual application data.
- Relevant validation is implemented.
- Critical tests pass.
- Errors are handled.
- Documentation is updated.

A visually complete screen is not automatically a completed feature.

---

## 12. SECURITY AND SAFETY RULES

This MVP is paper-trading only.

Do not implement a live-trading toggle.

Do not store or request real-money exchange trading credentials.

Use public market-data endpoints where possible.

All trade entries must pass through:

1. Valid proposal
2. Deterministic risk validation
3. Owner approval
4. Final risk validation
5. Paper execution adapter

Block Freqtrade's autonomous entry and force-entry paths unless they are routed through this authorization process.

Test this restriction at the backend boundary.

An expired or changed proposal requires new approval.

Emergency halt must block new entries.

---

## 13. THIRTY-DAY PILOT

Implement these states:

SETUP → VALIDATION → READY → RUNNING → COMPLETED → REVIEWED

Do not automatically begin the pilot.

The owner must explicitly select Start Pilot after acceptance testing.

During the pilot:

- Run scheduled market scans.
- Generate AI proposals.
- Require manual approval.
- Execute approved virtual trades.
- Track portfolio performance.
- Monitor risks.
- Preserve trading history.
- Generate daily summaries.
- Detect service interruptions.

At the end:

- Stop new entries.
- Preserve and value open positions.
- Report realized and unrealized P&L separately.
- Calculate net performance.
- Compare against BTC buy-and-hold and cash benchmarks.
- Record AI model costs.
- Generate the final report.

A profitable 30-day result does not automatically justify real-money deployment.

---

## 14. DEVELOPMENT PHASES

Build incrementally.

### Phase 1 — Research and Foundation

- Audit GitHub repositories.
- Verify Replit compatibility.
- Review licensing.
- Define integration boundaries.
- Create the STAI design system.
- Set up frontend and backend.
- Configure PostgreSQL.
- Implement authentication.

### Phase 2 — Trading Engine

- Integrate Freqtrade.
- Connect OKX market data.
- Initialize the virtual fund.
- Implement paper execution.
- Implement portfolio accounting.
- Verify persistence and restart recovery.

### Phase 3 — AI Investment Committee

- Integrate TradingAgents.
- Adapt crypto analysis.
- Implement structured recommendations.
- Create agent activity and research screens.

### Phase 4 — Approval and Risk

- Implement deterministic risk engine.
- Create proposal workflows.
- Enforce owner approval.
- Connect approved proposals to paper execution.
- Implement emergency halt.

### Phase 5 — Dashboard and Analytics

- Complete portfolio views.
- Complete trading journal.
- Complete performance reporting.
- Complete pilot monitoring.

### Phase 6 — Quality Assurance

- Run automated tests.
- Test order authorization.
- Test financial reconciliation.
- Test service restarts.
- Validate fees and funding.
- Test operational reliability.
- Fix critical defects.

### Phase 7 — Pilot Readiness

- Verify deployment persistence.
- Verify system monitoring.
- Verify 1,000 USDT initialization.
- Freeze pilot configuration.
- Enable Start Pilot.

Do not skip critical phases simply to finish the UI faster.

---

## 15. MVP ACCEPTANCE CRITERIA

The MVP is ready for the 30-day pilot only when:

1. Owner authentication works.
2. The virtual fund starts at exactly 1,000 USDT.
3. OKX market data is available and monitored for freshness.
4. Freqtrade paper execution is operational.
5. TradingAgents generates structured recommendations.
6. The deterministic risk engine enforces all limits.
7. New entries cannot execute without approval.
8. Approved paper trades produce recorded order events.
9. Positions and balances reconcile.
10. Fees and funding are recorded.
11. Portfolio data survives service restarts.
12. The dashboard uses persisted data.
13. The trading journal is complete.
14. Emergency halt works.
15. Background services can operate without an open browser.
16. No live-money execution path is accessible.

If any requirement fails, do not declare the pilot ready.

---

## 16. REPLIT AGENT OPERATING INSTRUCTIONS

Start in Plan mode.

First inspect the open-source repositories and evaluate the actual Replit runtime.

Then present:

- Proposed architecture
- Repository reuse plan
- Technology stack
- Development phases
- Key technical risks
- Deployment limitations
- Estimated implementation effort

Do not begin a large-scale implementation before completing this initial technical review.

Once approved, implement one phase at a time.

After each phase, provide a short report:

- Completed
- Tested
- Pending
- Blocked
- Next recommended action

Prefer functioning integrations over mock implementations.

Use the simplest reliable solution that meets the requirements.

Avoid unnecessary abstractions, premature optimization, and excessive dependencies.

---

## 17. FINAL PRODUCT OBJECTIVE

Deliver STAI, a professional, AI-powered personal trading research and paper-execution platform.

The product must combine:

- Freqtrade's established trading infrastructure
- TradingAgents' collaborative AI investment research
- SmartTrader's custom risk and approval controls
- A unified virtual portfolio
- A professional institutional-futuristic dashboard
- Complete trading history and performance reporting

The first major milestone is a verified, functioning end-to-end flow:

**OKX market data → AI recommendation → Risk validation → Owner approval → Freqtrade paper execution → Reconciled portfolio ledger.**

After that milestone passes, complete the remaining modules and prepare the platform for its 30-day virtual-fund pilot.

**Begin with the technical audit and architecture plan. Do not start live trading.**
