/**
 * The ten modules of the STAI specification, and the phase that delivers each one.
 *
 * This file is the single source for module names, routes and phases. Screens read it;
 * nothing here is sample data. Update a module's entry when its phase is delivered.
 */

export interface StaiPhase {
  number: number;
  name: string;
  delivers: string;
}

export const PHASES: readonly StaiPhase[] = [
  {
    number: 1,
    name: 'Foundation',
    delivers:
      'Backend, database, owner sign-in, design system, navigation and the ported analytics.',
  },
  {
    number: 2,
    name: 'Trading engine',
    delivers:
      'Paper-trading bots behind the approval gate, OKX market data, the virtual fund and its ledger.',
  },
  {
    number: 3,
    name: 'AI committee',
    delivers: 'The ten committee roles and structured recommendations.',
  },
  {
    number: 4,
    name: 'Approval and risk',
    delivers: 'Risk engine, proposals and approval, emails and halts.',
  },
  {
    number: 5,
    name: 'Dashboard and analytics',
    delivers:
      'Command Center, Journal, Performance, Strategy Laboratory, Risk and Pilot Monitor.',
  },
  {
    number: 6,
    name: 'Quality assurance',
    delivers: 'Full test run and several days of continuous running.',
  },
  {
    number: 7,
    name: 'Pilot readiness',
    delivers:
      'Acceptance criteria checked and Start Pilot enabled for the owner.',
  },
] as const;

/** The phase that is built and running now. */
export const CURRENT_PHASE = 1;

export interface StaiModule {
  /** Stable key, also used in test IDs. */
  id: string;
  /** Module number in the specification, 1 to 10. */
  number: number;
  /** Short name for navigation. */
  name: string;
  /** Full name from the specification. */
  title: string;
  /** Route inside the app. */
  path: string;
  /** Phase that delivers this screen. */
  phase: number;
  /** One sentence on what the module is for. */
  summary: string;
  /** What the screen will contain, as listed in the specification. */
  willContain: readonly string[];
  /** Extra fact the owner should know, when there is one. */
  note?: string;
}

export const MODULES: readonly StaiModule[] = [
  {
    id: 'command-center',
    number: 1,
    name: 'Command Center',
    title: 'Fund Command Center',
    path: '/command-center',
    phase: 5,
    summary: 'The main dashboard of the virtual fund.',
    willContain: [
      'Virtual fund equity',
      'Available capital',
      'Spot allocation',
      'Futures allocation',
      'Current exposure',
      'Realized P&L',
      'Unrealized P&L',
      'Daily performance',
      'Open positions',
      'Pending approvals',
      'System health',
    ],
  },
  {
    id: 'ai-committee',
    number: 2,
    name: 'AI Committee',
    title: 'AI Investment Committee',
    path: '/ai-committee',
    phase: 3,
    summary:
      'Ten committee roles that turn market data into one structured recommendation with evidence.',
    willContain: [
      'Chief Investment Officer',
      'Technical Analyst',
      'Quantitative Researcher',
      'Market Intelligence Analyst',
      'Derivatives Analyst',
      'Bull Researcher',
      'Bear Researcher',
      'Portfolio Manager',
      'Risk Officer',
      'Execution Specialist',
    ],
  },
  {
    id: 'market-scanner',
    number: 3,
    name: 'Market Scanner',
    title: 'Market Scanner',
    path: '/market-scanner',
    phase: 2,
    summary:
      'Monitors BTC/USDT, ETH/USDT and SOL/USDT on OKX public data, spot and USDT-margined perpetuals.',
    willContain: [
      'Prices',
      'Market trends',
      'Technical indicators',
      'Volatility',
      'Potential opportunities',
      'Market-data freshness',
    ],
  },
  {
    id: 'proposals',
    number: 4,
    name: 'Proposal Center',
    title: 'Trade Proposal Center',
    path: '/proposals',
    phase: 4,
    summary:
      'Every proposed trade with its exact parameters. The owner approves or rejects each one, and approval applies only to those exact parameters.',
    willContain: [
      'Instrument',
      'Market type',
      'Trade direction',
      'Proposed entry',
      'Quantity',
      'Position notional',
      'Leverage if applicable',
      'Stop-loss',
      'Take-profit',
      'Maximum planned loss',
      'Estimated trading costs',
      'AI investment thesis',
      'Risk assessment',
      'Proposal expiration',
    ],
  },
  {
    id: 'portfolio',
    number: 5,
    name: 'Portfolio',
    title: 'Portfolio Management',
    path: '/portfolio',
    phase: 2,
    summary: "The virtual fund's holdings, read from the decimal ledger.",
    willContain: [
      'Cash',
      'Spot holdings',
      'Futures positions',
      'Available margin',
      'Collateral',
      'Exposure',
      'Fees',
      'Funding',
      'Realized and unrealized P&L',
    ],
  },
  {
    id: 'journal',
    number: 6,
    name: 'Journal',
    title: 'Trading Journal',
    path: '/journal',
    phase: 5,
    summary:
      'The record of every recommendation, decision and simulated trade.',
    willContain: [
      'AI recommendations',
      'Approval decisions',
      'Simulated orders',
      'Order fills',
      'Position changes',
      'Fees',
      'Funding',
      'Exits',
      'Trading results',
    ],
  },
  {
    id: 'performance',
    number: 7,
    name: 'Performance',
    title: 'Performance Analytics',
    path: '/performance',
    phase: 5,
    summary:
      'How the virtual fund performs, measured from recorded paper trades only.',
    willContain: [
      'Equity curve',
      'Daily P&L',
      'Cumulative return',
      'Win rate',
      'Profit factor',
      'Maximum drawdown',
      'Trade expectancy',
      'Spot and futures performance',
      'Benchmark comparisons',
      'AI operating costs',
    ],
  },
  {
    id: 'strategy-lab',
    number: 8,
    name: 'Strategy Lab',
    title: 'Strategy Laboratory',
    path: '/strategy-lab',
    phase: 5,
    summary:
      "Historical backtesting and strategy comparisons, using the trading engine's existing capabilities.",
    willContain: ['Historical backtests', 'Strategy comparisons'],
  },
  {
    id: 'risk',
    number: 9,
    name: 'Risk',
    title: 'Risk Management',
    path: '/risk',
    phase: 5,
    summary:
      'The limits that every trade must pass, and the events they produce.',
    willContain: [
      'Position limits',
      'Leverage limits',
      'Daily loss limit',
      'Drawdown limit',
      'Capital allocation',
      'Emergency halt',
      'Risk events',
    ],
    note: 'The risk engine and the halts are built in Phase 4. This screen follows in Phase 5.',
  },
  {
    id: 'pilot-monitor',
    number: 10,
    name: 'Pilot Monitor',
    title: 'Pilot Monitor',
    path: '/pilot-monitor',
    phase: 5,
    summary: 'Tracks the formal 30-day paper-trading experiment.',
    willContain: ['Progress of the 30-day pilot'],
    note: 'The pilot does not start by itself. It starts only when the owner presses Start Pilot, after Phase 7.',
  },
] as const;

/** The one screen with live content in Phase 1. */
export const SYSTEM_STATUS_PATH = '/system-status';

export function getPhase(number: number): StaiPhase {
  const phase = PHASES.find((candidate) => candidate.number === number);
  if (!phase) {
    throw new Error(`Unknown phase ${number}`);
  }
  return phase;
}

export function getModuleByPath(path: string): StaiModule | undefined {
  return MODULES.find((module) => module.path === path);
}
