Source: https://www.okx.com/docs-v5/en/
Title: Connect – OKX API guide | OKX technical support | OKX
Fetched: 2026-11-18T09:28:39.808Z
Truncated: continue from startIndex 250000

[NAV\\
 ![](https://www.okx.com/docs-v5/en/images/navbar-cad8cdcb.png)](https://www.okx.com/docs-v5/en/#)

- [Overview](https://www.okx.com/docs-v5/en/#overview)  - [API Resources and Support](https://www.okx.com/docs-v5/en/#overview-api-resources-and-support)    - [Tutorials](https://www.okx.com/docs-v5/en/#overview-api-resources-and-support-tutorials)
    - [Python libraries](https://www.okx.com/docs-v5/en/#overview-api-resources-and-support-python-libraries)
    - [Customer service](https://www.okx.com/docs-v5/en/#overview-api-resources-and-support-customer-service)
  - [API key Creation](https://www.okx.com/docs-v5/en/#overview-api-key-creation)    - [Generating an API key](https://www.okx.com/docs-v5/en/#overview-api-key-creation-generating-an-api-key)
    - [API key permissions](https://www.okx.com/docs-v5/en/#overview-api-key-creation-api-key-permissions)
    - [API key security](https://www.okx.com/docs-v5/en/#overview-api-key-creation-api-key-security)
  - [REST Authentication](https://www.okx.com/docs-v5/en/#overview-rest-authentication)    - [Making Requests](https://www.okx.com/docs-v5/en/#overview-rest-authentication-making-requests)
    - [Signature](https://www.okx.com/docs-v5/en/#overview-rest-authentication-signature)
  - [WebSocket](https://www.okx.com/docs-v5/en/#overview-websocket)    - [Overview](https://www.okx.com/docs-v5/en/#overview-websocket-overview)
    - [Connect](https://www.okx.com/docs-v5/en/#overview-websocket-connect)
    - [Connection count limit](https://www.okx.com/docs-v5/en/#overview-websocket-connection-count-limit)
    - [Login](https://www.okx.com/docs-v5/en/#overview-websocket-login)
    - [Subscribe](https://www.okx.com/docs-v5/en/#overview-websocket-subscribe)
    - [Unsubscribe](https://www.okx.com/docs-v5/en/#overview-websocket-unsubscribe)
    - [Notification](https://www.okx.com/docs-v5/en/#overview-websocket-notification)
  - [Account mode](https://www.okx.com/docs-v5/en/#overview-account-mode)
  - [Production Trading Services](https://www.okx.com/docs-v5/en/#overview-production-trading-services)
  - [Demo Trading Services](https://www.okx.com/docs-v5/en/#overview-demo-trading-services)
  - [General Info](https://www.okx.com/docs-v5/en/#overview-general-info)
  - [Transaction Timeouts](https://www.okx.com/docs-v5/en/#overview-transaction-timeouts)    - [REST API](https://www.okx.com/docs-v5/en/#overview-transaction-timeouts-rest-api)
    - [WebSocket](https://www.okx.com/docs-v5/en/#overview-transaction-timeouts-websocket)
  - [Rate Limits](https://www.okx.com/docs-v5/en/#overview-rate-limits)    - [Trading-related APIs](https://www.okx.com/docs-v5/en/#overview-rate-limits-trading-related-apis)
    - [Sub-account rate limit](https://www.okx.com/docs-v5/en/#overview-rate-limits-sub-account-rate-limit)
    - [Fill ratio based sub-account rate limit](https://www.okx.com/docs-v5/en/#overview-rate-limits-fill-ratio-based-sub-account-rate-limit)
    - [Best practices](https://www.okx.com/docs-v5/en/#overview-rate-limits-best-practices)
  - [Market Maker Program](https://www.okx.com/docs-v5/en/#overview-market-maker-program)
  - [Broker Program](https://www.okx.com/docs-v5/en/#overview-broker-program)
- [Trading Account](https://www.okx.com/docs-v5/en/#trading-account)  - [REST API](https://www.okx.com/docs-v5/en/#trading-account-rest-api)    - [Get instruments](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-instruments)
    - [Get balance](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-balance)
    - [Get positions](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-positions)
    - [Get positions history](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-positions-history)
    - [Get account and position risk](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-account-and-position-risk)
    - [Get bills details (last 7 days)](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-bills-details-last-7-days)
    - [Get bills details (last 3 months)](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-bills-details-last-3-months)
    - [Apply bills details (since 2021)](https://www.okx.com/docs-v5/en/#trading-account-rest-api-apply-bills-details-since-2021)
    - [Get bills details (since 2021)](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-bills-details-since-2021)
    - [Get bill types](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-bill-types)
    - [Get account configuration](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-account-configuration)
    - [Set position mode](https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-position-mode)
    - [Set leverage](https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-leverage)
    - [Get maximum order quantity](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-maximum-order-quantity)
    - [Get maximum available balance/equity](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-maximum-available-balance-equity)
    - [Increase/decrease margin](https://www.okx.com/docs-v5/en/#trading-account-rest-api-increase-decrease-margin)
    - [Get leverage](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-leverage)
    - [Get leverage estimated info](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-leverage-estimated-info)
    - [Get the maximum loan of instrument](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-the-maximum-loan-of-instrument)
    - [Get fee rates](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-fee-rates)
    - [Get interest accrued data](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-interest-accrued-data)
    - [Get interest rate](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-interest-rate)
    - [Set fee type](https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-fee-type)
    - [Set greeks (PA/BS)](https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-greeks-pa-bs)
    - [Isolated margin trading settings](https://www.okx.com/docs-v5/en/#trading-account-rest-api-isolated-margin-trading-settings)
    - [Get maximum withdrawals](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-maximum-withdrawals)
    - [Get account risk state](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-account-risk-state)
    - [Get borrow interest and limit](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-borrow-interest-and-limit)
    - [Manual borrow / repay](https://www.okx.com/docs-v5/en/#trading-account-rest-api-manual-borrow-repay)
    - [Set auto repay](https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-auto-repay)
    - [Get borrow/repay history](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-borrow-repay-history)
    - [Position builder (new)](https://www.okx.com/docs-v5/en/#trading-account-rest-api-position-builder-new)
    - [Position builder trend graph](https://www.okx.com/docs-v5/en/#trading-account-rest-api-position-builder-trend-graph)
    - [Set risk offset amount](https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-risk-offset-amount)
    - [Get Greeks](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-greeks)
    - [Get PM position limitation](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-pm-position-limitation)
    - [Activate option](https://www.okx.com/docs-v5/en/#trading-account-rest-api-activate-option)
    - [Activate feature](https://www.okx.com/docs-v5/en/#trading-account-rest-api-activate-feature)
    - [Set auto loan](https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-auto-loan)
    - [Preset account mode switch](https://www.okx.com/docs-v5/en/#trading-account-rest-api-preset-account-mode-switch)
    - [Precheck account mode switch](https://www.okx.com/docs-v5/en/#trading-account-rest-api-precheck-account-mode-switch)
    - [Set account mode](https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-account-mode)
    - [Set collateral assets](https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-collateral-assets)
    - [Get collateral assets](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-collateral-assets)
    - [Reset MMP Status](https://www.okx.com/docs-v5/en/#trading-account-rest-api-reset-mmp-status)
    - [Set MMP](https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-mmp)
    - [GET MMP Config](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-mmp-config)
    - [Move positions](https://www.okx.com/docs-v5/en/#trading-account-rest-api-move-positions)
    - [Get move positions history](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-move-positions-history)
    - [Set auto earn](https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-auto-earn)
    - [Set settle currency](https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-settle-currency)
    - [Set trading config](https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-trading-config)
    - [Precheck set delta neutral](https://www.okx.com/docs-v5/en/#trading-account-rest-api-precheck-set-delta-neutral)
    - [Adjust demo account balance](https://www.okx.com/docs-v5/en/#trading-account-rest-api-adjust-demo-account-balance)
    - [GET / Get GLP today performance](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-get-glp-today-performance)
    - [GET / Get GLP historical performance](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-get-glp-historical-performance)
    - [GET / Get GLP v2 overview](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-get-glp-v2-overview)
    - [GET / Get GLP v2 assessment details](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-get-glp-v2-assessment-details)
    - [GET / Get GLP v2 performance history](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-get-glp-v2-performance-history)
  - [WebSocket](https://www.okx.com/docs-v5/en/#trading-account-websocket)    - [Account channel](https://www.okx.com/docs-v5/en/#trading-account-websocket-account-channel)
    - [Positions channel](https://www.okx.com/docs-v5/en/#trading-account-websocket-positions-channel)
    - [Balance and position channel](https://www.okx.com/docs-v5/en/#trading-account-websocket-balance-and-position-channel)
    - [Position risk warning](https://www.okx.com/docs-v5/en/#trading-account-websocket-position-risk-warning)
    - [Account greeks channel](https://www.okx.com/docs-v5/en/#trading-account-websocket-account-greeks-channel)
- [Order Book Trading](https://www.okx.com/docs-v5/en/#order-book-trading)  - [Trade](https://www.okx.com/docs-v5/en/#order-book-trading-trade)    - [POST / Place order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-place-order)
    - [POST / Place multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-place-multiple-orders)
    - [POST / Cancel order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-cancel-order)
    - [POST / Cancel multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-cancel-multiple-orders)
    - [POST / Amend order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-amend-order)
    - [POST / Amend multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-amend-multiple-orders)
    - [POST / Close positions](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-close-positions)
    - [GET / Order details](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-order-details)
    - [GET / Order List](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-order-list)
    - [GET / Order history (last 7 days)](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-order-history-last-7-days)
    - [GET / Order history (last 3 months)](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-order-history-last-3-months)
    - [GET / Transaction details (last 3 days)](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-transaction-details-last-3-days)
    - [GET / Transaction details (last 3 months)](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-transaction-details-last-3-months)
    - [GET / Easy convert currency list](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-easy-convert-currency-list)
    - [POST / Place easy convert](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-place-easy-convert)
    - [GET / Easy convert history](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-easy-convert-history)
    - [GET / One-click repay currency list](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-one-click-repay-currency-list)
    - [POST / Trade one-click repay](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-trade-one-click-repay)
    - [GET / One-click repay history](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-one-click-repay-history)
    - [GET / One-click repay currency list (New)](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-one-click-repay-currency-list-new)
    - [POST / Trade one-click repay (New)](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-trade-one-click-repay-new)
    - [GET / One-click repay history (New)](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-one-click-repay-history-new)
    - [POST / Mass cancel order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-mass-cancel-order)
    - [POST / Cancel All After](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-cancel-all-after)
    - [GET / Account rate limit](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-account-rate-limit)
    - [POST / Order precheck](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-order-precheck)
    - [WS / Order channel](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-order-channel)
    - [WS / Fills channel](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-fills-channel)
    - [WS / Place order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-place-order)
    - [WS / Place multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-place-multiple-orders)
    - [WS / Cancel order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-cancel-order)
    - [WS / Cancel multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-cancel-multiple-orders)
    - [WS / Amend order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-amend-order)
    - [WS / Amend multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-amend-multiple-orders)
    - [WS / Mass cancel order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-mass-cancel-order)
  - [Algo Trading](https://www.okx.com/docs-v5/en/#order-book-trading-algo-trading)    - [POST / Place algo order](https://www.okx.com/docs-v5/en/#order-book-trading-algo-trading-post-place-algo-order)
    - [POST / Cancel algo order](https://www.okx.com/docs-v5/en/#order-book-trading-algo-trading-post-cancel-algo-order)
    - [POST / Amend algo order](https://www.okx.com/docs-v5/en/#order-book-trading-algo-trading-post-amend-algo-order)
    - [GET / Algo order details](https://www.okx.com/docs-v5/en/#order-book-trading-algo-trading-get-algo-order-details)
    - [GET / Algo order list](https://www.okx.com/docs-v5/en/#order-book-trading-algo-trading-get-algo-order-list)
    - [GET / Algo order history](https://www.okx.com/docs-v5/en/#order-book-trading-algo-trading-get-algo-order-history)
    - [WS / Algo orders channel](https://www.okx.com/docs-v5/en/#order-book-trading-algo-trading-ws-algo-orders-channel)
    - [WS / Advance algo orders channel](https://www.okx.com/docs-v5/en/#order-book-trading-algo-trading-ws-advance-algo-orders-channel)
  - [Grid Trading](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading)    - [POST / Place grid algo order](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-post-place-grid-algo-order)
    - [POST / Amend grid algo order basic param](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-post-amend-grid-algo-order-basic-param)
    - [POST / Amend grid algo order](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-post-amend-grid-algo-order)
    - [POST / Stop grid algo order](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-post-stop-grid-algo-order)
    - [POST / Close position for contract grid](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-post-close-position-for-contract-grid)
    - [POST / Cancel close position order for contract grid](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-post-cancel-close-position-order-for-contract-grid)
    - [POST / Instant trigger grid algo order](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-post-instant-trigger-grid-algo-order)
    - [GET / Grid algo order list](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-get-grid-algo-order-list)
    - [GET / Grid algo order history](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-get-grid-algo-order-history)
    - [GET / Grid algo order details](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-get-grid-algo-order-details)
    - [GET / Grid algo sub orders](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-get-grid-algo-sub-orders)
    - [GET / Grid algo order positions](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-get-grid-algo-order-positions)
    - [POST / Spot grid withdraw income](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-post-spot-grid-withdraw-income)
    - [POST / Compute margin balance](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-post-compute-margin-balance)
    - [POST / Adjust margin balance](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-post-adjust-margin-balance)
    - [POST / Add investment](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-post-add-investment)
    - [GET / Grid AI parameter (public)](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-get-grid-ai-parameter-public)
    - [POST / Compute min investment (public)](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-post-compute-min-investment-public)
    - [GET / RSI back testing (public)](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-get-rsi-back-testing-public)
    - [GET / Max grid quantity (public)](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-get-max-grid-quantity-public)
    - [POST / Copy grid algo order](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-post-copy-grid-algo-order)
    - [WS / Spot grid algo orders channel](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-ws-spot-grid-algo-orders-channel)
    - [WS / Contract grid algo orders channel](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-ws-contract-grid-algo-orders-channel)
    - [WS / Grid positions channel](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-ws-grid-positions-channel)
    - [WS / Grid sub orders channel](https://www.okx.com/docs-v5/en/#order-book-trading-grid-trading-ws-grid-sub-orders-channel)
  - [DCA Trading](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading)    - [POST / Place dca algo order](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading-post-place-dca-algo-order)
    - [POST / Amend spot dca basic param](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading-post-amend-spot-dca-basic-param)
    - [POST / Stop dca algo order](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading-post-stop-dca-algo-order)
    - [GET / DCA algo order details](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading-get-dca-algo-order-details)
    - [GET / DCA algo order history](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading-get-dca-algo-order-history)
    - [GET / DCA sub orders](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading-get-dca-sub-orders)
    - [POST / Add investment](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading-post-add-investment)
    - [POST / Amend dca reinvestment](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading-post-amend-dca-reinvestment)
    - [POST / Amend dca take profit settings](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading-post-amend-dca-take-profit-settings)
    - [Get / DCA algo order position details](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading-get-dca-algo-order-position-details)
    - [GET / DCA cycle list](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading-get-dca-cycle-list)
    - [POST / Add dca margin](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading-post-add-dca-margin)
    - [POST / Reduce dca margin](https://www.okx.com/docs-v5/en/#order-book-trading-dca-trading-post-reduce-dca-margin)
  - [Signal bot trading](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading)    - [POST / Create signal](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-post-create-signal)
    - [GET / Signals](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-get-signals)
    - [POST / Create signal bot](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-post-create-signal-bot)
    - [POST / Cancel signal bots](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-post-cancel-signal-bots)
    - [POST / Adjust margin balance](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-post-adjust-margin-balance)
    - [POST / Amend TPSL](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-post-amend-tpsl)
    - [POST / Set instruments](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-post-set-instruments)
    - [GET / Signal bot order details](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-get-signal-bot-order-details)
    - [GET / Active signal bot](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-get-active-signal-bot)
    - [GET / Signal bot history](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-get-signal-bot-history)
    - [GET / Signal bot order positions](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-get-signal-bot-order-positions)
    - [GET / Position history](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-get-position-history)
    - [POST / Close position](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-post-close-position)
    - [POST / Place sub order](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-post-place-sub-order)
    - [POST / Cancel sub order](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-post-cancel-sub-order)
    - [GET / Signal bot sub orders](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-get-signal-bot-sub-orders)
    - [GET / Signal bot event history](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-get-signal-bot-event-history)
  - [Recurring Buy](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy)    - [POST / Place recurring buy order](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-post-place-recurring-buy-order)
    - [POST / Amend recurring buy order](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-post-amend-recurring-buy-order)
    - [POST / Stop recurring buy order](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-post-stop-recurring-buy-order)
    - [GET / Recurring buy order list](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-get-recurring-buy-order-list)
    - [GET / Recurring buy order history](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-get-recurring-buy-order-history)
    - [GET / Recurring buy order details](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-get-recurring-buy-order-details)
    - [GET / Recurring buy sub orders](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-get-recurring-buy-sub-orders)
    - [WS / Recurring buy orders channel](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-ws-recurring-buy-orders-channel)
    - [POST / Amend recurring buy time](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-post-amend-recurring-buy-time)
    - [POST / Amend recurring buy amount](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-post-amend-recurring-buy-amount)
    - [POST / Add investment](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-post-add-investment)
    - [POST / Pause recurring buy](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-post-pause-recurring-buy)
    - [POST / Restart recurring buy](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-post-restart-recurring-buy)
    - [POST / Amend price range](https://www.okx.com/docs-v5/en/#order-book-trading-recurring-buy-post-amend-price-range)
  - [Copy Trading](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading)    - [GET / Existing lead positions](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-existing-lead-positions)
    - [GET / Lead position history](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-lead-position-history)
    - [POST / Place lead stop order](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-post-place-lead-stop-order)
    - [POST / Close lead position](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-post-close-lead-position)
    - [GET / Leading instruments](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-leading-instruments)
    - [POST / Amend leading instruments](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-post-amend-leading-instruments)
    - [GET / Profit sharing details](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-profit-sharing-details)
    - [GET / Total profit sharing](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-total-profit-sharing)
    - [GET / Unrealized profit sharing details](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-unrealized-profit-sharing-details)
    - [GET / Total unrealized profit sharing](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-total-unrealized-profit-sharing)
    - [POST / Amend profit sharing ratio](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-post-amend-profit-sharing-ratio)
    - [GET / Account configuration](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-account-configuration)
    - [POST / First copy settings](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-post-first-copy-settings)
    - [POST / Amend copy settings](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-post-amend-copy-settings)
    - [POST / Stop copying](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-post-stop-copying)
    - [GET / Copy settings](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-copy-settings)
    - [GET / My lead traders](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-my-lead-traders)
    - [GET / Copy trading configuration](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-copy-trading-configuration)
    - [GET / Lead trader ranks](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-lead-trader-ranks)
    - [GET / Lead trader weekly pnl](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-lead-trader-weekly-pnl)
    - [GET / Lead trader daily pnl](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-lead-trader-daily-pnl)
    - [GET / Lead trader stats](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-lead-trader-stats)
    - [GET / Lead trader currency preferences](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-lead-trader-currency-preferences)
    - [GET / Lead trader current lead positions](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-lead-trader-current-lead-positions)
    - [GET / Lead trader lead position history](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-lead-trader-lead-position-history)
    - [GET / Copy traders](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-get-copy-traders)
    - [WS / Lead trading notification channel](https://www.okx.com/docs-v5/en/#order-book-trading-copy-trading-ws-lead-trading-notification-channel)
  - [Market Data](https://www.okx.com/docs-v5/en/#order-book-trading-market-data)    - [GET / Tickers](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-tickers)
    - [GET / Ticker](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-ticker)
    - [GET / Order book](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-order-book)
    - [GET / RPI order book](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-rpi-order-book)
    - [GET / Full order book](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-full-order-book)
    - [GET / Candlesticks](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-candlesticks)
    - [GET / Candlesticks history](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-candlesticks-history)
    - [GET / Trades](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-trades)
    - [GET / Trades history](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-trades-history)
    - [GET / Option trades by instrument family](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-option-trades-by-instrument-family)
    - [GET / Option trades](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-option-trades)
    - [GET / 24H total volume](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-24h-total-volume)
    - [GET / Call auction details](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-call-auction-details)
    - [WS / Tickers channel](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-ws-tickers-channel)
    - [WS / Candlesticks channel](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-ws-candlesticks-channel)
    - [WS / Trades channel](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-ws-trades-channel)
    - [WS / All trades channel](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-ws-all-trades-channel)
    - [WS / Order book channel](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-ws-order-book-channel)
    - [WS / Option trades channel](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-ws-option-trades-channel)
    - [WS / Call auction details channel](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-ws-call-auction-details-channel)
  - [SBE Market Data](https://www.okx.com/docs-v5/en/#order-book-trading-sbe-market-data)    - [Overview](https://www.okx.com/docs-v5/en/#order-book-trading-sbe-market-data-overview)
    - [XML Schema](https://www.okx.com/docs-v5/en/#order-book-trading-sbe-market-data-xml-schema)
    - [General Information](https://www.okx.com/docs-v5/en/#order-book-trading-sbe-market-data-general-information)
    - [Integration Information](https://www.okx.com/docs-v5/en/#order-book-trading-sbe-market-data-integration-information)
    - [SBE Order book](https://www.okx.com/docs-v5/en/#order-book-trading-sbe-market-data-sbe-order-book)
    - [New error code](https://www.okx.com/docs-v5/en/#order-book-trading-sbe-market-data-new-error-code)
    - [Upgrade](https://www.okx.com/docs-v5/en/#order-book-trading-sbe-market-data-upgrade)
- [Block Trading](https://www.okx.com/docs-v5/en/#block-trading)  - [Block Trading Workflow](https://www.okx.com/docs-v5/en/#block-trading-block-trading-workflow)
  - [REST API](https://www.okx.com/docs-v5/en/#block-trading-rest-api)    - [Get Counterparties](https://www.okx.com/docs-v5/en/#block-trading-rest-api-get-counterparties)
    - [Create RFQ](https://www.okx.com/docs-v5/en/#block-trading-rest-api-create-rfq)
    - [Cancel RFQ](https://www.okx.com/docs-v5/en/#block-trading-rest-api-cancel-rfq)
    - [Cancel multiple RFQs](https://www.okx.com/docs-v5/en/#block-trading-rest-api-cancel-multiple-rfqs)
    - [Cancel all RFQs](https://www.okx.com/docs-v5/en/#block-trading-rest-api-cancel-all-rfqs)
    - [Execute Quote](https://www.okx.com/docs-v5/en/#block-trading-rest-api-execute-quote)
    - [Get Quote products](https://www.okx.com/docs-v5/en/#block-trading-rest-api-get-quote-products)
    - [Set Quote products](https://www.okx.com/docs-v5/en/#block-trading-rest-api-set-quote-products)
    - [Reset MMP status](https://www.okx.com/docs-v5/en/#block-trading-rest-api-reset-mmp-status)
    - [Set MMP](https://www.okx.com/docs-v5/en/#block-trading-rest-api-set-mmp)
    - [Get MMP Config](https://www.okx.com/docs-v5/en/#block-trading-rest-api-get-mmp-config)
    - [Create Quote](https://www.okx.com/docs-v5/en/#block-trading-rest-api-create-quote)
    - [Cancel Quote](https://www.okx.com/docs-v5/en/#block-trading-rest-api-cancel-quote)
    - [Cancel multiple Quotes](https://www.okx.com/docs-v5/en/#block-trading-rest-api-cancel-multiple-quotes)
    - [Cancel all Quotes](https://www.okx.com/docs-v5/en/#block-trading-rest-api-cancel-all-quotes)
    - [Cancel All After](https://www.okx.com/docs-v5/en/#block-trading-rest-api-cancel-all-after)
    - [Get rfqs](https://www.okx.com/docs-v5/en/#block-trading-rest-api-get-rfqs)
    - [Get quotes](https://www.okx.com/docs-v5/en/#block-trading-rest-api-get-quotes)
    - [Get trades](https://www.okx.com/docs-v5/en/#block-trading-rest-api-get-trades)
    - [Get block tickers](https://www.okx.com/docs-v5/en/#block-trading-rest-api-get-block-tickers)
    - [Get block ticker](https://www.okx.com/docs-v5/en/#block-trading-rest-api-get-block-ticker)
    - [Get public multi-leg transactions of block trades](https://www.okx.com/docs-v5/en/#block-trading-rest-api-get-public-multi-leg-transactions-of-block-trades)
    - [Get public single-leg transactions of block trades](https://www.okx.com/docs-v5/en/#block-trading-rest-api-get-public-single-leg-transactions-of-block-trades)
  - [WebSocket Private Channel](https://www.okx.com/docs-v5/en/#block-trading-websocket-private-channel)    - [Rfqs channel](https://www.okx.com/docs-v5/en/#block-trading-websocket-private-channel-rfqs-channel)
    - [Quotes channel](https://www.okx.com/docs-v5/en/#block-trading-websocket-private-channel-quotes-channel)
    - [Structure block trades channel](https://www.okx.com/docs-v5/en/#block-trading-websocket-private-channel-structure-block-trades-channel)
  - [WebSocket Public Channel](https://www.okx.com/docs-v5/en/#block-trading-websocket-public-channel)    - [Public structure block trades channel](https://www.okx.com/docs-v5/en/#block-trading-websocket-public-channel-public-structure-block-trades-channel)
    - [Public block trades channel](https://www.okx.com/docs-v5/en/#block-trading-websocket-public-channel-public-block-trades-channel)
    - [Block tickers channel](https://www.okx.com/docs-v5/en/#block-trading-websocket-public-channel-block-tickers-channel)
- [Spread Trading](https://www.okx.com/docs-v5/en/#spread-trading)  - [Introduction](https://www.okx.com/docs-v5/en/#spread-trading-introduction)    - [Basic Concepts](https://www.okx.com/docs-v5/en/#spread-trading-introduction-basic-concepts)
    - [High Level Workflow](https://www.okx.com/docs-v5/en/#spread-trading-introduction-high-level-workflow)
  - [Comprehensive API Workflow](https://www.okx.com/docs-v5/en/#spread-trading-comprehensive-api-workflow)    - [Obtaining Available Spreads](https://www.okx.com/docs-v5/en/#spread-trading-comprehensive-api-workflow-obtaining-available-spreads)
    - [Retrieving Your Orders](https://www.okx.com/docs-v5/en/#spread-trading-comprehensive-api-workflow-retrieving-your-orders)
    - [Retrieving Your Trades](https://www.okx.com/docs-v5/en/#spread-trading-comprehensive-api-workflow-retrieving-your-trades)
    - [Submitting an Order](https://www.okx.com/docs-v5/en/#spread-trading-comprehensive-api-workflow-submitting-an-order)
    - [Spread States](https://www.okx.com/docs-v5/en/#spread-trading-comprehensive-api-workflow-spread-states)
    - [Trade Lifecycle](https://www.okx.com/docs-v5/en/#spread-trading-comprehensive-api-workflow-trade-lifecycle)
    - [Order State](https://www.okx.com/docs-v5/en/#spread-trading-comprehensive-api-workflow-order-state)
    - [Trade State](https://www.okx.com/docs-v5/en/#spread-trading-comprehensive-api-workflow-trade-state)
    - [All Trades](https://www.okx.com/docs-v5/en/#spread-trading-comprehensive-api-workflow-all-trades)
  - [REST API](https://www.okx.com/docs-v5/en/#spread-trading-rest-api)    - [Place order](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-place-order)
    - [Cancel order](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-cancel-order)
    - [Cancel All orders](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-cancel-all-orders)
    - [Amend order](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-amend-order)
    - [Get order details](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-get-order-details)
    - [Get active orders](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-get-active-orders)
    - [Get orders (last 21 days)](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-get-orders-last-21-days)
    - [Get orders history (last 3 months)](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-get-orders-history-last-3-months)
    - [Get trades (last 7 days)](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-get-trades-last-7-days)
    - [Get Spreads (Public)](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-get-spreads-public)
    - [Get order book (Public)](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-get-order-book-public)
    - [Get ticker (Public)](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-get-ticker-public)
    - [Get public trades (Public)](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-get-public-trades-public)
    - [Get candlesticks](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-get-candlesticks)
    - [Get candlesticks history](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-get-candlesticks-history)
    - [Cancel All After](https://www.okx.com/docs-v5/en/#spread-trading-rest-api-cancel-all-after)
  - [Websocket Trade API](https://www.okx.com/docs-v5/en/#spread-trading-websocket-trade-api)    - [WS / Place order](https://www.okx.com/docs-v5/en/#spread-trading-websocket-trade-api-ws-place-order)
    - [WS / Amend order](https://www.okx.com/docs-v5/en/#spread-trading-websocket-trade-api-ws-amend-order)
    - [WS / Cancel order](https://www.okx.com/docs-v5/en/#spread-trading-websocket-trade-api-ws-cancel-order)
    - [WS / Cancel all orders](https://www.okx.com/docs-v5/en/#spread-trading-websocket-trade-api-ws-cancel-all-orders)
  - [WebSocket Private Channel](https://www.okx.com/docs-v5/en/#spread-trading-websocket-private-channel)    - [Order channel](https://www.okx.com/docs-v5/en/#spread-trading-websocket-private-channel-order-channel)
    - [Trades channel](https://www.okx.com/docs-v5/en/#spread-trading-websocket-private-channel-trades-channel)
  - [WebSocket Public Channel](https://www.okx.com/docs-v5/en/#spread-trading-websocket-public-channel)    - [Order book channel](https://www.okx.com/docs-v5/en/#spread-trading-websocket-public-channel-order-book-channel)
    - [Public Trades channel](https://www.okx.com/docs-v5/en/#spread-trading-websocket-public-channel-public-trades-channel)
    - [Tickers channel](https://www.okx.com/docs-v5/en/#spread-trading-websocket-public-channel-tickers-channel)
    - [Candlesticks channel](https://www.okx.com/docs-v5/en/#spread-trading-websocket-public-channel-candlesticks-channel)
- [Public Data](https://www.okx.com/docs-v5/en/#public-data)  - [REST API](https://www.okx.com/docs-v5/en/#public-data-rest-api)    - [Get instruments](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-instruments)
    - [Get series](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-series)
    - [Get events](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-events)
    - [Get corporate actions](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-corporate-actions)
    - [Get markets](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-markets)
    - [Get estimated delivery/exercise price](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-estimated-delivery-exercise-price)
    - [Get delivery/exercise history](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-delivery-exercise-history)
    - [Get estimated future settlement price](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-estimated-future-settlement-price)
    - [Get futures settlement history](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-futures-settlement-history)
    - [Get funding rate](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-funding-rate)
    - [Get funding rate history](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-funding-rate-history)
    - [Get open interest](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-open-interest)
    - [Get limit price](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-limit-price)
    - [Get option market data](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-option-market-data)
    - [Get discount rate and interest-free quota](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-discount-rate-and-interest-free-quota)
    - [Get system time](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-system-time)
    - [Get mark price](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-mark-price)
    - [Get position tiers](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-position-tiers)
    - [Get interest rate and loan quota](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-interest-rate-and-loan-quota)
    - [Get underlying](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-underlying)
    - [Get security fund](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-security-fund)
    - [Unit convert](https://www.okx.com/docs-v5/en/#public-data-rest-api-unit-convert)
    - [Get instrument tick bands](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-instrument-tick-bands)
    - [Get premium history](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-premium-history)
    - [Get index tickers](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-index-tickers)
    - [Get index candlesticks](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-index-candlesticks)
    - [Get index candlesticks history](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-index-candlesticks-history)
    - [Get mark price candlesticks](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-mark-price-candlesticks)
    - [Get mark price candlesticks history](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-mark-price-candlesticks-history)
    - [Get exchange rate](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-exchange-rate)
    - [Get index components](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-index-components)
    - [Get economic calendar data](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-economic-calendar-data)
    - [Get historical market data](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-historical-market-data)
    - [Get MM instrument types](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-mm-instrument-types)
    - [Get Delta hedge currencies](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-delta-hedge-currencies)
  - [WebSocket](https://www.okx.com/docs-v5/en/#public-data-websocket)    - [Instruments channel](https://www.okx.com/docs-v5/en/#public-data-websocket-instruments-channel)
    - [Event contract markets channel](https://www.okx.com/docs-v5/en/#public-data-websocket-event-contract-markets-channel)
    - [Open interest channel](https://www.okx.com/docs-v5/en/#public-data-websocket-open-interest-channel)
    - [Funding rate channel](https://www.okx.com/docs-v5/en/#public-data-websocket-funding-rate-channel)
    - [Price limit channel](https://www.okx.com/docs-v5/en/#public-data-websocket-price-limit-channel)
    - [Option summary channel](https://www.okx.com/docs-v5/en/#public-data-websocket-option-summary-channel)
    - [Estimated delivery/exercise/settlement price channel](https://www.okx.com/docs-v5/en/#public-data-websocket-estimated-delivery-exercise-settlement-price-channel)
    - [Mark price channel](https://www.okx.com/docs-v5/en/#public-data-websocket-mark-price-channel)
    - [Index tickers channel](https://www.okx.com/docs-v5/en/#public-data-websocket-index-tickers-channel)
    - [Mark price candlesticks channel](https://www.okx.com/docs-v5/en/#public-data-websocket-mark-price-candlesticks-channel)
    - [Index candlesticks channel](https://www.okx.com/docs-v5/en/#public-data-websocket-index-candlesticks-channel)
    - [Liquidation orders channel](https://www.okx.com/docs-v5/en/#public-data-websocket-liquidation-orders-channel)
    - [ADL warning channel](https://www.okx.com/docs-v5/en/#public-data-websocket-adl-warning-channel)
    - [Economic calendar channel](https://www.okx.com/docs-v5/en/#public-data-websocket-economic-calendar-channel)
- [Trading Statistics](https://www.okx.com/docs-v5/en/#trading-statistics)  - [REST API](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api)    - [Get support coin](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-support-coin)
    - [Get contract open interest history](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-contract-open-interest-history)
    - [Get taker volume](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-taker-volume)
    - [Get contract taker volume](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-contract-taker-volume)
    - [Get margin long/short ratio](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-margin-long-short-ratio)
    - [Get top traders contract long/short ratio](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-top-traders-contract-long-short-ratio)
    - [Get top traders contract long/short ratio (by position)](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-top-traders-contract-long-short-ratio-by-position)
    - [Get contract long/short ratio](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-contract-long-short-ratio)
    - [Get long/short ratio](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-long-short-ratio)
    - [Get contracts open interest and volume](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-contracts-open-interest-and-volume)
    - [Get options open interest and volume](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-options-open-interest-and-volume)
    - [Get put/call ratio](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-put-call-ratio)
    - [Get open interest and volume (expiry)](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-open-interest-and-volume-expiry)
    - [Get open interest and volume (strike)](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-open-interest-and-volume-strike)
    - [Get taker flow](https://www.okx.com/docs-v5/en/#trading-statistics-rest-api-get-taker-flow)
- [Funding Account](https://www.okx.com/docs-v5/en/#funding-account)  - [REST API](https://www.okx.com/docs-v5/en/#funding-account-rest-api)    - [Get currencies](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-currencies)
    - [Get balance](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-balance)
    - [Get non-tradable assets](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-non-tradable-assets)
    - [Get account asset valuation](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-account-asset-valuation)
    - [Funds transfer](https://www.okx.com/docs-v5/en/#funding-account-rest-api-funds-transfer)
    - [Get funds transfer state](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-funds-transfer-state)
    - [Asset bills details](https://www.okx.com/docs-v5/en/#funding-account-rest-api-asset-bills-details)
    - [Asset bills history](https://www.okx.com/docs-v5/en/#funding-account-rest-api-asset-bills-history)
    - [Get deposit address](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-deposit-address)
    - [Get deposit history](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-deposit-history)
    - [Withdrawal](https://www.okx.com/docs-v5/en/#funding-account-rest-api-withdrawal)
    - [Cancel withdrawal](https://www.okx.com/docs-v5/en/#funding-account-rest-api-cancel-withdrawal)
    - [Get withdrawal history](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-withdrawal-history)
    - [Get deposit withdraw status](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-deposit-withdraw-status)
    - [Get exchange list (public)](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-exchange-list-public)
    - [Apply for monthly statement (last year)](https://www.okx.com/docs-v5/en/#funding-account-rest-api-apply-for-monthly-statement-last-year)
    - [Get monthly statement (last year)](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-monthly-statement-last-year)
    - [Get convert currencies](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-convert-currencies)
    - [Get convert currency pair](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-convert-currency-pair)
    - [Estimate quote](https://www.okx.com/docs-v5/en/#funding-account-rest-api-estimate-quote)
    - [Convert trade](https://www.okx.com/docs-v5/en/#funding-account-rest-api-convert-trade)
    - [Get convert history](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-convert-history)
    - [Get deposit payment methods](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-deposit-payment-methods)
    - [Get withdrawal payment methods](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-withdrawal-payment-methods)
    - [Create withdrawal order](https://www.okx.com/docs-v5/en/#funding-account-rest-api-create-withdrawal-order)
    - [Cancel withdrawal order](https://www.okx.com/docs-v5/en/#funding-account-rest-api-cancel-withdrawal-order)
    - [Get withdrawal order history](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-withdrawal-order-history)
    - [Get withdrawal order detail](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-withdrawal-order-detail)
    - [Get deposit order history](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-deposit-order-history)
    - [Get deposit order detail](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-deposit-order-detail)
    - [Get buy/sell currencies](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-buy-sell-currencies)
    - [Get buy/sell currency pair](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-buy-sell-currency-pair)
    - [Get buy/sell quote](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-buy-sell-quote)
    - [Buy/sell trade](https://www.okx.com/docs-v5/en/#funding-account-rest-api-buy-sell-trade)
    - [Get buy/sell trade history](https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-buy-sell-trade-history)
  - [WebSocket](https://www.okx.com/docs-v5/en/#funding-account-websocket)    - [Deposit info channel](https://www.okx.com/docs-v5/en/#funding-account-websocket-deposit-info-channel)
    - [Withdrawal info channel](https://www.okx.com/docs-v5/en/#funding-account-websocket-withdrawal-info-channel)
- [Sub-account](https://www.okx.com/docs-v5/en/#sub-account)  - [REST API](https://www.okx.com/docs-v5/en/#sub-account-rest-api)    - [Get sub-account list](https://www.okx.com/docs-v5/en/#sub-account-rest-api-get-sub-account-list)
    - [Create sub-account](https://www.okx.com/docs-v5/en/#sub-account-rest-api-create-sub-account)
    - [Create an API Key for a sub-account](https://www.okx.com/docs-v5/en/#sub-account-rest-api-create-an-api-key-for-a-sub-account)
    - [Query the API Key of a sub-account](https://www.okx.com/docs-v5/en/#sub-account-rest-api-query-the-api-key-of-a-sub-account)
    - [Reset the API Key of a sub-account](https://www.okx.com/docs-v5/en/#sub-account-rest-api-reset-the-api-key-of-a-sub-account)
    - [Delete the API Key of sub-accounts](https://www.okx.com/docs-v5/en/#sub-account-rest-api-delete-the-api-key-of-sub-accounts)
    - [Get sub-account trading balance](https://www.okx.com/docs-v5/en/#sub-account-rest-api-get-sub-account-trading-balance)
    - [Get sub-account funding balance](https://www.okx.com/docs-v5/en/#sub-account-rest-api-get-sub-account-funding-balance)
    - [Get sub-account maximum withdrawals](https://www.okx.com/docs-v5/en/#sub-account-rest-api-get-sub-account-maximum-withdrawals)
    - [Get history of sub-account transfer](https://www.okx.com/docs-v5/en/#sub-account-rest-api-get-history-of-sub-account-transfer)
    - [Get history of managed sub-account transfer](https://www.okx.com/docs-v5/en/#sub-account-rest-api-get-history-of-managed-sub-account-transfer)
    - [Master accounts manage the transfers between sub-accounts](https://www.okx.com/docs-v5/en/#sub-account-rest-api-master-accounts-manage-the-transfers-between-sub-accounts)
    - [Set permission of transfer out](https://www.okx.com/docs-v5/en/#sub-account-rest-api-set-permission-of-transfer-out)
    - [Get custody trading sub-account list](https://www.okx.com/docs-v5/en/#sub-account-rest-api-get-custody-trading-sub-account-list)
- [Financial Product](https://www.okx.com/docs-v5/en/#financial-product)  - [On-chain earn](https://www.okx.com/docs-v5/en/#financial-product-on-chain-earn)    - [GET / Offers](https://www.okx.com/docs-v5/en/#financial-product-on-chain-earn-get-offers)
    - [POST / Purchase](https://www.okx.com/docs-v5/en/#financial-product-on-chain-earn-post-purchase)
    - [POST / Redeem](https://www.okx.com/docs-v5/en/#financial-product-on-chain-earn-post-redeem)
    - [POST / Cancel purchases/redemptions](https://www.okx.com/docs-v5/en/#financial-product-on-chain-earn-post-cancel-purchases-redemptions)
    - [GET / Active orders](https://www.okx.com/docs-v5/en/#financial-product-on-chain-earn-get-active-orders)
    - [GET / Order history](https://www.okx.com/docs-v5/en/#financial-product-on-chain-earn-get-order-history)
  - [ETH staking](https://www.okx.com/docs-v5/en/#financial-product-eth-staking)    - [GET / Product info](https://www.okx.com/docs-v5/en/#financial-product-eth-staking-get-product-info)
    - [POST / Purchase](https://www.okx.com/docs-v5/en/#financial-product-eth-staking-post-purchase)
    - [POST / Redeem](https://www.okx.com/docs-v5/en/#financial-product-eth-staking-post-redeem)
    - [POST / Cancel redeem](https://www.okx.com/docs-v5/en/#financial-product-eth-staking-post-cancel-redeem)
    - [GET / Balance](https://www.okx.com/docs-v5/en/#financial-product-eth-staking-get-balance)
    - [GET / Purchase&Redeem history](https://www.okx.com/docs-v5/en/#financial-product-eth-staking-get-purchase-amp-redeem-history)
    - [GET / APY history (Public)](https://www.okx.com/docs-v5/en/#financial-product-eth-staking-get-apy-history-public)
  - [SOL staking](https://www.okx.com/docs-v5/en/#financial-product-sol-staking)    - [GET / Product info](https://www.okx.com/docs-v5/en/#financial-product-sol-staking-get-product-info)
    - [POST / Purchase](https://www.okx.com/docs-v5/en/#financial-product-sol-staking-post-purchase)
    - [POST / Redeem](https://www.okx.com/docs-v5/en/#financial-product-sol-staking-post-redeem)
    - [GET / Balance](https://www.okx.com/docs-v5/en/#financial-product-sol-staking-get-balance)
    - [GET / Purchase&Redeem history](https://www.okx.com/docs-v5/en/#financial-product-sol-staking-get-purchase-amp-redeem-history)
    - [GET / APY history (Public)](https://www.okx.com/docs-v5/en/#financial-product-sol-staking-get-apy-history-public)
  - [Stable Rewards](https://www.okx.com/docs-v5/en/#financial-product-stable-rewards)    - [GET / Product info](https://www.okx.com/docs-v5/en/#financial-product-stable-rewards-get-product-info)
    - [GET / Balance](https://www.okx.com/docs-v5/en/#financial-product-stable-rewards-get-balance)
    - [GET / APY history](https://www.okx.com/docs-v5/en/#financial-product-stable-rewards-get-apy-history)
  - [OKUSD](https://www.okx.com/docs-v5/en/#financial-product-okusd)    - [GET / OKUSD limits](https://www.okx.com/docs-v5/en/#financial-product-okusd-get-okusd-limits)
    - [POST / Subscribe OKUSD](https://www.okx.com/docs-v5/en/#financial-product-okusd-post-subscribe-okusd)
    - [POST / Redeem OKUSD](https://www.okx.com/docs-v5/en/#financial-product-okusd-post-redeem-okusd)
    - [GET / Get OKUSD Account](https://www.okx.com/docs-v5/en/#financial-product-okusd-get-get-okusd-account)
    - [GET / Get Subscription History](https://www.okx.com/docs-v5/en/#financial-product-okusd-get-get-subscription-history)
    - [GET / Get Redemption History](https://www.okx.com/docs-v5/en/#financial-product-okusd-get-get-redemption-history)
    - [GET / Get Rewards History](https://www.okx.com/docs-v5/en/#financial-product-okusd-get-get-rewards-history)
    - [GET / Get APR History](https://www.okx.com/docs-v5/en/#financial-product-okusd-get-get-apr-history)
  - [Simple earn flexible](https://www.okx.com/docs-v5/en/#financial-product-simple-earn-flexible)    - [GET / Saving balance](https://www.okx.com/docs-v5/en/#financial-product-simple-earn-flexible-get-saving-balance)
    - [POST / Savings purchase/redemption](https://www.okx.com/docs-v5/en/#financial-product-simple-earn-flexible-post-savings-purchase-redemption)
    - [GET / Lending history](https://www.okx.com/docs-v5/en/#financial-product-simple-earn-flexible-get-lending-history)
    - [GET / Public borrow info (public)](https://www.okx.com/docs-v5/en/#financial-product-simple-earn-flexible-get-public-borrow-info-public)
    - [GET / Public borrow history (public)](https://www.okx.com/docs-v5/en/#financial-product-simple-earn-flexible-get-public-borrow-history-public)
  - [Flexible loan](https://www.okx.com/docs-v5/en/#financial-product-flexible-loan)    - [GET / Borrowable currencies](https://www.okx.com/docs-v5/en/#financial-product-flexible-loan-get-borrowable-currencies)
    - [GET / Collateral assets](https://www.okx.com/docs-v5/en/#financial-product-flexible-loan-get-collateral-assets)
    - [POST / Maximum loan amount](https://www.okx.com/docs-v5/en/#financial-product-flexible-loan-post-maximum-loan-amount)
    - [GET / Maximum collateral redeem amount](https://www.okx.com/docs-v5/en/#financial-product-flexible-loan-get-maximum-collateral-redeem-amount)
    - [POST / Adjust collateral](https://www.okx.com/docs-v5/en/#financial-product-flexible-loan-post-adjust-collateral)
    - [POST / Borrow](https://www.okx.com/docs-v5/en/#financial-product-flexible-loan-post-borrow)
    - [POST / Repay](https://www.okx.com/docs-v5/en/#financial-product-flexible-loan-post-repay)
    - [GET / E-Mode info](https://www.okx.com/docs-v5/en/#financial-product-flexible-loan-get-e-mode-info)
    - [GET / Loan info](https://www.okx.com/docs-v5/en/#financial-product-flexible-loan-get-loan-info)
    - [GET / Loan history](https://www.okx.com/docs-v5/en/#financial-product-flexible-loan-get-loan-history)
    - [GET / Accrued interest](https://www.okx.com/docs-v5/en/#financial-product-flexible-loan-get-accrued-interest)
  - [Dual investment](https://www.okx.com/docs-v5/en/#financial-product-dual-investment)    - [GET / Currency pairs](https://www.okx.com/docs-v5/en/#financial-product-dual-investment-get-currency-pairs)
    - [GET / Product info](https://www.okx.com/docs-v5/en/#financial-product-dual-investment-get-product-info)
    - [POST / Request for quote](https://www.okx.com/docs-v5/en/#financial-product-dual-investment-post-request-for-quote)
    - [POST / Trade](https://www.okx.com/docs-v5/en/#financial-product-dual-investment-post-trade)
    - [POST / Request for redeem quote](https://www.okx.com/docs-v5/en/#financial-product-dual-investment-post-request-for-redeem-quote)
    - [POST / Redeem](https://www.okx.com/docs-v5/en/#financial-product-dual-investment-post-redeem)
    - [GET / Order state](https://www.okx.com/docs-v5/en/#financial-product-dual-investment-get-order-state)
    - [GET / Order history](https://www.okx.com/docs-v5/en/#financial-product-dual-investment-get-order-history)
- [Affiliate](https://www.okx.com/docs-v5/en/#affiliate)  - [REST API](https://www.okx.com/docs-v5/en/#affiliate-rest-api)    - [Get performance summary](https://www.okx.com/docs-v5/en/#affiliate-rest-api-get-performance-summary)
    - [Get the invitee's detail](https://www.okx.com/docs-v5/en/#affiliate-rest-api-get-the-invitee-39-s-detail)
    - [Get invitee list](https://www.okx.com/docs-v5/en/#affiliate-rest-api-get-invitee-list)
    - [Get link list](https://www.okx.com/docs-v5/en/#affiliate-rest-api-get-link-list)
    - [Get co-inviter link list](https://www.okx.com/docs-v5/en/#affiliate-rest-api-get-co-inviter-link-list)
    - [Get sub-affiliate list](https://www.okx.com/docs-v5/en/#affiliate-rest-api-get-sub-affiliate-list)
- [Status](https://www.okx.com/docs-v5/en/#status)  - [GET / Status](https://www.okx.com/docs-v5/en/#status-get-status)
  - [WS / Status channel](https://www.okx.com/docs-v5/en/#status-ws-status-channel)
- [Announcement](https://www.okx.com/docs-v5/en/#announcement)  - [GET / Announcements](https://www.okx.com/docs-v5/en/#announcement-get-announcements)
  - [GET / Announcement types](https://www.okx.com/docs-v5/en/#announcement-get-announcement-types)
- [Error Code](https://www.okx.com/docs-v5/en/#error-code)  - [REST API](https://www.okx.com/docs-v5/en/#error-code-rest-api)    - [Public](https://www.okx.com/docs-v5/en/#error-code-rest-api-public)
    - [Finance](https://www.okx.com/docs-v5/en/#error-code-rest-api-finance)
    - [Convert](https://www.okx.com/docs-v5/en/#error-code-rest-api-convert)
    - [Futures](https://www.okx.com/docs-v5/en/#error-code-rest-api-futures)
    - [Swap](https://www.okx.com/docs-v5/en/#error-code-rest-api-swap)
    - [Option](https://www.okx.com/docs-v5/en/#error-code-rest-api-option)
    - [Funding](https://www.okx.com/docs-v5/en/#error-code-rest-api-funding)
    - [Account](https://www.okx.com/docs-v5/en/#error-code-rest-api-account)
    - [Block Trading and Spread Orderbook](https://www.okx.com/docs-v5/en/#error-code-rest-api-block-trading-and-spread-orderbook)
    - [Copy trading](https://www.okx.com/docs-v5/en/#error-code-rest-api-copy-trading)
    - [Trading bot](https://www.okx.com/docs-v5/en/#error-code-rest-api-trading-bot)
  - [WebSocket](https://www.okx.com/docs-v5/en/#error-code-websocket)    - [Public](https://www.okx.com/docs-v5/en/#error-code-websocket-public)

# Overview

Welcome to our API documentation. OKX provides REST and WebSocket APIs to suit your trading needs.

## API Resources and Support

### Tutorials

- Learn how to trade with API: [Best practice to OKX’s API](https://www.okx.com/docs-v5/trick_en/#instrument-configuration)
- Learn python spot trading step by step: [Python Spot Trading Tutorial](https://www.okx.com/help/how-can-i-do-spot-trading-with-the-jupyter-notebook)
- Learn python derivatives trading step by step: [Python Derivatives Trading Tutorial](https://www.okx.com/help/how-can-i-do-derivatives-trading-with-the-jupyter-notebook)

### Python libraries

- Use Python SDK for easier integration: [Python SDK](https://pypi.org/project/python-okx/)
- Get access to our market maker python sample code [Python market maker sample](https://github.com/okxapi/okx-sample-market-maker)

### Customer service

- Please take 1 minute to help us improve: [API Satisfaction Survey](https://forms.gle/Ehou2xFv5GE1xUGr9)
- If you have any API-related inquiries, you can reach out to us by scanning the code below via the OKX APP.

![API Technical Support QR Code](https://www.okx.com/docs-v5/en/images/APISupport-117c8d03.jpeg)

## API key Creation

Please refer to [my api page](https://www.okx.com/account/my-api) regarding API Key creation.

### Generating an API key

Create an API key on the website before signing any requests. After creating an API key, keep the following information safe:

- API key
- Secret key
- Passphrase

The system returns randomly-generated API keys and SecretKeys. You will need to provide the Passphrase to access the API. We store the salted hash of your Passphrase for authentication. We cannot recover the Passphrase if you have lost it. You will need to create a new set of API key.

### API key permissions

There are three permissions below that can be associated with an API key. One or more permission can be assigned to any key.

- `Read` : Can request and view account info such as bills and order history which need read permission
- `Trade` : Can place and cancel orders, funding transfer, make settings which need write permission
- `Withdraw` : Can make withdrawals

### API key security

- Each API key can bind up to 20 IP addresses, which support IPv4/IPv6 and network segment formats.


- Only when the user calls an API that requires API key authentication will it be considered as the API key is used.
- Calling an API that does not require API key authentication will not be considered used even if API key information is passed in.
- For websocket, only operation of logging in will be considered to have used the API key. Any operation though the connection after logging in (such as subscribing/placing an order) will not be considered to have used the API key. Please pay attention.

Users can get the usage records of the API key with `trade` or `withdraw` permissions but unlinked to any IP address though [Security Center](https://www.okx.com/account/security).

## REST Authentication

### Making Requests

All private REST requests must contain the following headers:

- `OK-ACCESS-KEY` The API key as a String.

- `OK-ACCESS-SIGN` The Base64-encoded signature (see Signing Messages subsection for details).

- `OK-ACCESS-TIMESTAMP` Request timestamp in ISO 8601 UTC format with millisecond precision, e.g. `2020-12-08T09:08:57.715Z`. The server rejects requests where this differs from server time by more than 30 seconds (error 50102). Always use UTC — local timezone offset is the most common cause of error 50102. Synchronise with GET /api/v5/public/time before placing orders.

- `OK-ACCESS-PASSPHRASE` The passphrase you specified when creating the API key.


Request bodies should have content type `application/json` and be in valid JSON format.

### Signature

> Signing Messages

The `OK-ACCESS-SIGN` header is generated as follows:

- Create a pre-hash string of timestamp + method + requestPath + body (where + represents String concatenation).
- Prepare the SecretKey.
- Sign the pre-hash string with the SecretKey using the HMAC SHA256.
- Encode the signature in the Base64 format.

Example: `sign=CryptoJS.enc.Base64.stringify(CryptoJS.HmacSHA256(timestamp + 'GET' + '/api/v5/account/balance?ccy=BTC', SecretKey))`

The `timestamp` value is the same as the `OK-ACCESS-TIMESTAMP` header with millisecond ISO format, e.g. `2020-12-08T09:08:57.715Z`.

The request method should be in UPPERCASE: e.g. `GET` and `POST`.

The `requestPath` is the path of requesting an endpoint.

Example: `/api/v5/account/balance`

The `body` refers to the String of the request body. It can be omitted if there is no request body (frequently the case for `GET` requests).

Example: `{"instId":"BTC-USDT","lever":"5","mgnMode":"isolated"}`

The SecretKey is generated when you create an API key.

Example: `22582BD0CFF14C41EDBF1AB98506286D`

## WebSocket

### Overview

WebSocket is a new HTML5 protocol that achieves full-duplex data transmission between the client and server, allowing data to be transferred effectively in both directions. A connection between the client and server can be established with just one handshake. The server will then be able to push data to the client according to preset rules. Its advantages include:

- The WebSocket request header size for data transmission between client and server is only 2 bytes.
- Either the client or server can initiate data transmission.
- There's no need to repeatedly create and delete TCP connections, saving resources on bandwidth and server.

### Connect

**Connection limit**: 3 requests per second (based on IP)

When subscribing to a public channel, use the address of the public service. When subscribing to a private channel, use the address of the private service

**Request limit**:

The total number of 'subscribe'/'unsubscribe'/'login' requests per connection is limited to 480 times per hour.

### Connection count limit

The limit will be set at 30 WebSocket connections per specific WebSocket channel per sub-account. Each WebSocket connection is identified by the unique `connId`.

The WebSocket channels subject to this limitation are as follows:

1. [Orders channel](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-order-channel)
2. [Account channel](https://www.okx.com/docs-v5/en/#trading-account-websocket-account-channel)
3. [Positions channel](https://www.okx.com/docs-v5/en/#trading-account-websocket-positions-channel)
4. [Balance and positions channel](https://www.okx.com/docs-v5/en/#trading-account-websocket-balance-and-position-channel)
5. [Position risk warning channel](https://www.okx.com/docs-v5/en/#trading-account-websocket-position-risk-warning)
6. [Account greeks channel](https://www.okx.com/docs-v5/en/#trading-account-websocket-account-greeks-channel)

If users subscribe to the same channel through the same WebSocket connection through multiple arguments, for example, by using `{"channel": "orders", "instType": "ANY"}` and `{"channel": "orders", "instType": "SWAP"}`, it will be counted once only. If users subscribe to the listed channels (such as orders and accounts) using either the same or different connections, it will not affect the counting, as these are considered as two different channels. The system calculates the number of WebSocket connections per channel.

The platform will send the number of active connections to clients through the `channel-conn-count` event message **to new channel subscriptions**.

> Connection count update

```
Copy to Clipboard
{
    "event":"channel-conn-count",
    "channel":"orders",
    "connCount": "2",
    "connId":"abcd1234"
}
```

When the limit is breached, generally the latest connection that sends the subscription request will be rejected. Client will receive the usual subscription acknowledgement followed by the `channel-conn-count-error` from the connection that the subscription has been terminated. In exceptional circumstances the platform may unsubscribe existing connections.

> Connection limit error

```
Copy to Clipboard
{
    "event": "channel-conn-count-error",
    "channel": "orders",
    "connCount": "30",
    "connId":"a4d3ae55"
}
```

Order operations through WebSocket, including place, amend and cancel orders, are not impacted through this change.

### Login

> Request Example

```
Copy to Clipboard
{
  "op": "login",
  "args": [\
    {\
      "apiKey": "******",\
      "passphrase": "******",\
      "timestamp": "1538054050",\
      "sign": "7L+zFQ+CEgGu5rzCj4+BdV2/uUHGqddA9pI6ztsRRPs="\
    }\
  ]
}
```

#### Request Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| op | String | Yes | Operation<br>`login` |
| args | Array of objects | Yes | List of account to login |
| \> apiKey | String | Yes | API Key |
| \> passphrase | String | Yes | API Key password |
| \> timestamp | String | Yes | Unix Epoch time, the unit is seconds |
| \> sign | String | Yes | Signature string |

> Successful Response Example

```
Copy to Clipboard
{
  "event": "login",
  "code": "0",
  "msg": "",
  "connId": "a4d3ae55"
}
```

> Failure Response Example

```
Copy to Clipboard
{
  "event": "error",
  "code": "60009",
  "msg": "Login failed.",
  "connId": "a4d3ae55"
}
```

#### Response parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| event | String | Yes | Operation<br>`login`<br>`error` |
| code | String | No | Error code |
| msg | String | No | Error message |
| connId | String | Yes | WebSocket connection ID |

**apiKey**: Unique identification for invoking API. Requires user to apply one manually.

**passphrase**: API Key password

**timestamp**: the Unix Epoch time, the unit is seconds, e.g. 1704876947

**sign**: signature string, the signature algorithm is as follows:

First concatenate `timestamp`, `method`, `requestPath`, strings, then use HMAC SHA256 method to encrypt the concatenated string with SecretKey, and then perform Base64 encoding.

**secretKey**: The security key generated when the user applies for API key, e.g. `22582BD0CFF14C41EDBF1AB98506286D`

**Example of timestamp**: const timestamp = '' + Date.now() / 1,000

**Among sign example**: sign=CryptoJS.enc.Base64.stringify(CryptoJS.HmacSHA256(timestamp +'GET'+'/users/self/verify', secretKey))

**method**: always 'GET'.

**requestPath** : always '/users/self/verify'

### Subscribe

**Subscription Instructions**

> Request format description

```
Copy to Clipboard
{
  "id": "1512",
  "op": "subscribe",
  "args": ["<SubscriptionTopic>"]
}
```

WebSocket channels are divided into two categories: `public` and `private` channels.

`Public channels` \-\- No authentication is required, include tickers channel, K-Line channel, limit price channel, order book channel, and mark price channel etc.

`Private channels` \-\- including account channel, order channel, and position channel, etc -- require log in.

Users can choose to subscribe to one or more channels, and the total length of multiple channels cannot exceed 64 KB.

Below is an example of subscription parameters. The requirement of subscription parameters for each channel is different. For details please refer to the specification of each channels.

> Request Example

```
Copy to Clipboard
{
    "id": "1512",
    "op":"subscribe",
    "args":[\
        {\
            "channel":"tickers",\
            "instId":"BTC-USDT"\
        }\
    ]
}
```

**Request parameters**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| id | String | No | Unique identifier of the message <br>Provided by client. It will be returned in response message for identifying the corresponding request. <br>A combination of case-sensitive alphanumerics, all numbers, or all letters of up to 32 characters. |
| op | String | Yes | Operation<br>`subscribe` |
| args | Array of objects | Yes | List of subscribed channels |
| \> channel | String | Yes | Channel name |
| \> instType | String | No | Instrument type<br>`SPOT`<br>`MARGIN`<br>`SWAP`<br>`FUTURES`<br>`OPTION`<br>`ANY` |
| \> instFamily | String | No | Instrument family<br>Applicable to `FUTURES`/`SWAP`/`OPTION` |
| \> instId | String | No | Instrument ID |

> Response Example

```
Copy to Clipboard
{
    "id": "1512",
    "event": "subscribe",
    "arg": {
        "channel": "tickers",
        "instId": "BTC-USDT"
    },
    "connId": "accb8e21"
}
```

**Return parameters**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| id | String | No | Unique identifier of the message |
| event | String | Yes | Event<br>`subscribe`<br>`error` |
| arg | Object | No | Subscribed channel |
| \> channel | String | Yes | Channel name |
| \> instType | String | No | Instrument type<br>`SPOT`<br>`MARGIN`<br>`SWAP`<br>`FUTURES`<br>`OPTION`<br>`ANY` |
| \> instFamily | String | No | Instrument family<br>Applicable to `FUTURES`/`SWAP`/`OPTION` |
| \> instId | String | No | Instrument ID |
| code | String | No | Error code |
| msg | String | No | Error message |
| connId | String | Yes | WebSocket connection ID |

### Unsubscribe

Unsubscribe from one or more channels.

> Request format description

```
Copy to Clipboard
{
  "op": "unsubscribe",
  "args": ["< SubscriptionTopic> "]
}
```

> Request Example

```
Copy to Clipboard
{
  "op": "unsubscribe",
  "args": [\
    {\
      "channel": "tickers",\
      "instId": "BTC-USDT"\
    }\
  ]
}
```

**Request parameters**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| op | String | Yes | Operation<br>`unsubscribe` |
| args | Array of objects | Yes | List of channels to unsubscribe from |
| \> channel | String | Yes | Channel name |
| \> instType | String | No | Instrument type<br>`SPOT`<br>`MARGIN`<br>`SWAP`<br>`FUTURES`<br>`OPTION`<br>`ANY` |
| \> instFamily | String | No | Instrument family<br>Applicable to `FUTURES`/`SWAP`/`OPTION` |
| \> instId | String | No | Instrument ID |

> Response Example

```
Copy to Clipboard
{
    "event": "unsubscribe",
    "arg": {
        "channel": "tickers",
        "instId": "BTC-USDT"
    },
    "connId": "d0b44253"
}
```

**Response parameters**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| event | String | Yes | Event<br>`unsubscribe`<br>`error` |
| arg | Object | No | Unsubscribed channel |
| \> channel | String | Yes | Channel name |
| \> instType | String | No | Instrument type<br>`SPOT`<br>`MARGIN`<br>`SWAP`<br>`FUTURES`<br>`OPTION` |
| \> instFamily | String | No | Instrument family<br>Applicable to `FUTURES`/`SWAP`/`OPTION` |
| \> instId | String | No | Instrument ID |
| code | String | No | Error code |
| msg | String | No | Error message |

### Notification

WebSocket has introduced a new message type (event = `notice`).

Client will receive the information in the following scenarios:

- Websocket disconnect for service upgrade


60 seconds prior to the upgrade of the WebSocket service, the notification message will be sent to users indicating that the connection will soon be disconnected.
Users are encouraged to establish a new connection to prevent any disruptions caused by disconnection.

> Response Example

```
Copy to Clipboard
{
    "event": "notice",
    "code": "64008",
    "msg": "The connection will soon be closed for a service upgrade. Please reconnect.",
    "connId": "a4d3ae55"
}
```

- WebSocket port 8443 retirement


When a connection is established on port 8443, the notification message will be sent once after the handshake succeeds, indicating that port 8443 will soon be retired. The connection stays open.
Users are encouraged to migrate to port 443.

> Response Example

```
Copy to Clipboard
{
    "event": "notice",
    "code": "64010",
    "msg": "WebSocket port 8443 will be retired soon. Please migrate to port 443.",
    "connId": "d7d6f1f5"
}
```

The `notice` message type is supported by all WebSocket endpoints (/ws/v5/public, /ws/v5/private, /ws/v5/business, and /ws/v5/public-sbe).

## Account mode

To facilitate your trading experience, please set the appropriate account mode before starting trading.

In the trading account trading system, 4 account modes are supported: `Spot mode`, `Futures mode`, `Multi-currency margin mode`, and `Portfolio margin mode`.

You need to set on the Web/App for the first set of every account mode.

## Production Trading Services

The Production Trading URL:

- REST: `https://openapi.okx.com`

- Public WebSocket: `wss://ws.okx.com/ws/v5/public`

- Private WebSocket: `wss://ws.okx.com/ws/v5/private`
- Business WebSocket: `wss://ws.okx.com/ws/v5/business`

## Demo Trading Services

Currently, the API works for Demo Trading, but some functions are not supported, such as `withdraw`,`deposit`,`purchase/redemption`, etc.

The Demo Trading URL:

- REST: `https://openapi.okx.com`

- Public WebSocket: `wss://wspap.okx.com/ws/v5/public`

- Private WebSocket: `wss://wspap.okx.com/ws/v5/private`

- Business WebSocket: `wss://wspap.okx.com/ws/v5/business`

OKX account can be used for login on Demo Trading. If you already have an OKX account, you can log in directly.

Start API Demo Trading by the following steps:

Login OKX —> Trade —> Demo Trading —> Personal Center —> Demo Trading API -> Create Demo Trading API Key —> Start your Demo Trading

> Http Header Example

```
Copy to Clipboard
Content-Type: application/json

OK-ACCESS-KEY: 37c541a1-****-****-****-10fe7a038418

OK-ACCESS-SIGN: leaVRETrtaoEQ3yI9qEtI1CZ82ikZ4xSG5Kj8gnl3uw=

OK-ACCESS-PASSPHRASE: 1****6

OK-ACCESS-TIMESTAMP: 2020-03-28T12:21:41.274Z

x-simulated-trading: 1
```

## General Info

**The rules for placing orders at the exchange level are as follows:**

- The maximum number of pending orders (including post only orders, limit orders and taker orders that are being processed): 4,000
- The maximum number of pending orders per trading symbol is 500, the limit of 500 pending orders applies to the following **order types**:

  - Limit
  - Market
  - Post only
  - Fill or Kill (FOK)
  - Immediate or Cancel (IOC)
  - Market order with Immediate-or-Cancel order (optimal limit IOC)
  - Take Profit / Stop Loss (TP/SL)
  - Limit and market orders triggered under the order types below:

    - Take Profit / Stop Loss (TP/SL)
    - Trigger
    - Trailing stop
    - Arbitrage
    - Iceberg
    - TWAP
    - Recurring buy
- The maximum number of pending spread orders: 500 across all spreads

- The maximum number of pending algo orders:

  - TP/SL order: 100 per instrument
  - Trigger order: 500
  - Trailing order: 50
  - Iceberg order: 100
  - TWAP order: 20
- The maximum number of grid trading

  - Spot grid: 100
  - Contract grid: 100

**The rules for trading are as follows:**

- When the number of maker orders matched with a taker order exceeds the maximum number limit of 1000, the taker order will be canceled.

  - The limit orders will only be executed with a portion corresponding to 1000 maker orders and the remainder will be canceled.
  - Fill or Kill (FOK) orders will be canceled directly.

**The rules for the returning data are as follows:**

- `code` and `msg` represent the request result or error reason when the return data has `code`, and has not `sCode`;

- It is `sCode` and `sMsg` that represent the request result or error reason when the return data has `sCode` rather than `code` and `msg`.


**`instFamily` and `uly` parameter explanation:**

- The following explanation is based on the `BTC` contract, other contracts are similar.
- `uly` is the index, like "BTC-USD", and there is a one-to-many relationship with the settlement and margin currency (`settleCcy`).
- `instFamily` is the trading instrument family, like `BTC-USD_UM`, and there is a one-to-one relationship with the settlement and margin currency (`settleCcy`).
- The following table shows the corresponding relationship of `uly`, `instFamily`, `settleCcy` and `instId`.

| **Contract Type** | **uly** | **instFamily** | **settleCcy** | **Delivery contract instId** | **Swap contract instId** |
| --- | --- | --- | --- | --- | --- |
| USDT-margined contract | BTC-USDT | BTC-USDT | USDT | BTC-USDT-250808 | BTC-USDT-SWAP |
| USDC-margined contract | BTC-USDC | BTC-USDC | USDC | BTC-USDC-250808 | BTC-USDC-SWAP |
| USD-margined contract | BTC-USD | **BTC-USD\_UM** | **USDⓈ** | **BTC-USD\_UM-250808** | **BTC-USD\_UM-SWAP** |
| Coin-margined contract | BTC-USD | **BTC-USD** | **BTC** | **BTC-USD-250808** | **BTC-USD-SWAP** |

Note:

1\. USDⓈ represents USD and multiple USD stable coins, like USDC, USDG.

2\. The settlement and margin currency refers to the `settleCcy` field returned by the [Get instruments](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-instruments) endpoint.

## Transaction Timeouts

Orders may not be processed in time due to network delay or busy OKX servers. You can configure the expiry time of the request using `expTime` if you want the order request to be discarded after a specific time.

If `expTime` is specified in the requests for Place (multiple) orders or Amend (multiple) orders, the request will not be processed if the current system time of the server is after the `expTime`.

### REST API

Set the following parameters in the request header

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| expTime | String | No | Request effective deadline. Unix timestamp format in milliseconds, e.g. `1597026383085` |

The following endpoints are supported:

- [Place order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-place-order)
- [Place multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-place-multiple-orders)
- [Amend order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-amend-order)
- [Amend multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-amend-multiple-orders)
- [POST / Place sub order](https://www.okx.com/docs-v5/en/#order-book-trading-signal-bot-trading-post-place-sub-order) under signal bot trading

> Request Example

```
Copy to Clipboard
curl -X 'POST' \
  'https://openapi.okx.com/api/v5/trade/order' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'OK-ACCESS-KEY: *****' \
  -H 'OK-ACCESS-SIGN: *****'' \
  -H 'OK-ACCESS-TIMESTAMP: *****'' \
  -H 'OK-ACCESS-PASSPHRASE: *****'' \
  -H 'expTime: 1597026383085' \   // request effective deadline
  -d '{
  "instId": "BTC-USDT",
  "tdMode": "cash",
  "side": "buy",
  "ordType": "limit",
  "px": "1000",
  "sz": "0.01"
}'
```

### WebSocket

The following parameters are set in the request

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| expTime | String | No | Request effective deadline. Unix timestamp format in milliseconds, e.g. `1597026383085` |

The following endpoints are supported:

- [Place order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-place-order)
- [Place multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-place-multiple-orders)
- [Amend order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-amend-order)
- [Amend multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-amend-multiple-orders)

> Request Example

```
Copy to Clipboard
{
    "id": "1512",
    "op": "order",
    "expTime":"1597026383085",  // request effective deadline
    "args": [{\
        "side": "buy",\
        "instId": "BTC-USDT",\
        "tdMode": "isolated",\
        "ordType": "market",\
        "sz": "100"\
    }]
}
```

## Rate Limits

Our REST and WebSocket APIs use rate limits to protect our APIs against malicious usage so our trading platform can operate reliably and fairly.

When a request is rejected by our system due to rate limits, the system returns error code 50011 (Rate limit reached. Please refer to API documentation and throttle requests accordingly).

The rate limit is different for each endpoint. You can find the limit for each endpoint from the endpoint details. Rate limit definitions are detailed below:

- WebSocket login and subscription rate limits are based on connection.

- Public unauthenticated REST rate limits are based on IP address.

- Private REST rate limits are based on User ID (sub-accounts have individual User IDs).

- WebSocket order management rate limits are based on User ID (sub-accounts have individual User IDs).


### Trading-related APIs

For Trading-related APIs (place order, cancel order, and amend order) the following conditions apply:

- Rate limits are shared across the REST and WebSocket channels.

- Rate limits for placing orders, amending orders, and cancelling orders are independent from each other.

- Rate limits are defined on the Instrument ID level (except Options)

- Rate limits for Options are defined based on the Instrument Family level. Refer to the [Get instruments](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-instruments) endpoint to view Instrument Family information.

- Rate limits for a multiple order endpoint and a single order endpoint are also independent, with the exception being when there is only one order sent to a multiple order endpoint, the order will be counted as a single order and adopt the single order rate limit.

- An order can have at most 3 amend requests in progress at the same time. A further amend request submitted while 3 are still in progress is rejected with error code 51513.


### Sub-account rate limit

At the sub-account level, we allow a maximum of 1000 order requests per 2 seconds. Only new order requests and amendment order requests will be counted towards this limit. The limit encompasses all requests from the endpoints below. For batch order requests consisting of multiple orders, each order will be counted individually. Error code 50061 is returned when the sub-account rate limit is exceeded. The existing rate limit rule per instrument ID remains unchanged and the existing rate limit and sub-account rate limit will operate in parallel. If clients require a higher rate limit, clients can trade via multiple sub-accounts.

- [POST / Place order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-place-order)
- [POST / Place multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-place-multiple-orders)
- [POST / Amend order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-amend-order)
- [POST / Amend multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-amend-multiple-orders)

- [WS / Place order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-place-order)

- [WS / Place multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-place-multiple-orders)

- [WS / Amend order](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-amend-order)

- [WS / Amend multiple orders](https://www.okx.com/docs-v5/en/#order-book-trading-trade-ws-amend-multiple-orders)


### Fill ratio based sub-account rate limit

This is only applicable to >= VIP5 customers.

As an incentive for more efficient trading, the exchange will offer a higher sub-account rate limit to clients with a high trade fill ratio.

The exchange calculates two ratios based on the transaction data from the past 7 days at 00:00 UTC.

1. Sub-account fill ratio: This ratio is determined by dividing (the trade volume in USDT of the sub-account) by (sum of (new and amendment request count per symbol \* symbol multiplier) of the sub-account). Note that the master trading account itself is also considered as a sub-account in this context.
2. Master account aggregated fill ratio: This ratio is calculated by dividing (the trade volume in USDT on the master account level) by (the sum (new and amendment count per symbol \* symbol multiplier\] of all sub-accounts).

The symbol multiplier allows for fine-tuning the weight of each symbol. A smaller symbol multiplier (<1) is used for smaller pairs that require more updates per trading volume. All instruments have a default symbol multiplier, and some instruments will have overridden symbol multipliers.

| InstType | Override rule | Overridden symbol multiplier | Default symbol multiplier |
| --- | --- | --- | --- |
| Perpetual Futures | Per instrument ID | `1`<br>Instrument ID: <br>BTC-USDT-SWAP <br>BTC-USD-SWAP <br>ETH-USDT-SWAP <br>ETH-USD-SWAP | `0.2` |
| Expiry Futures | Per instrument Family | `0.3`<br>Instrument Family: <br>BTC-USDT <br>BTC-USD <br>ETH-USDT <br>ETH-USD | `0.1` |
| Spot | Per instrument ID | `0.5`<br>Instrument ID: <br>BTC-USDT <br>ETH-USDT | `0.1` |
| Options | Per instrument Family |  | `0.1` |

The fill ratio computation excludes block trading, spread trading, MMP and fiat orders for order count; and excludes block trading, spread trading for trade volume. Only successful order requests (sCode=0) are considered.

At 08:00 UTC, the system will use the maximum value between the sub-account fill ratio and the master account aggregated fill ratio based on the data snapshot at 00:00 UTC to determine the sub-account rate limit based on the table below. For broker (non-disclosed) clients, the system considers the sub-account fill ratio only.

|  | Fill ratio\[x<=ratio<y) | Sub-account rate limit per 2 seconds(new and amendment) |\
| --- | --- | --- |\
| Tier 1 | \[0,1) | 1,000 |\
| Tier 2 | \[1,2) | 1,250 |\
| Tier 3 | \[2,3) | 1,500 |\
| Tier 4 | \[3,5) | 1,750 |\
| Tier 5 | \[5,10) | 2,000 |\
| Tier 6 | \[10,20) | 2,500 |\
| Tier 7 | \[20,50) | 3,000 |\
| Tier 8 | >= 50 | 10,000 |\
\
If there is an improvement in the fill ratio and rate limit to be uplifted, the uplift will take effect immediately at 08:00 UTC. However, if the fill ratio decreases and the rate limit needs to be lowered, a one-day grace period will be granted, and the lowered rate limit will only be implemented on T+1 at 08:00 UTC. On T+1, if the fill ratio improves, the higher rate limit will be applied accordingly. In the event of client demotion to VIP4, their rate limit will be downgraded to Tier 1, accompanied by a one-day grace period.\
\
If the 7-day trading volume of a sub-account is less than 1,000,000 USDT, the fill ratio of the master account will be applied to it.\
\
For newly created sub-accounts, the Tier 1 rate limit will be applied at creation until T+1 8am UTC, at which the normal rules will be applied.\
\
Block trading, spread trading, MMP and spot/margin orders are exempted from the sub-account rate limit.\
\
The exchange offers [GET / Account rate limit](https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-account-rate-limit) endpoint that provides ratio and rate limit data, which will be updated daily at 8am UTC. It will return the sub-account fill ratio, the master account aggregated fill ratio, current sub-account rate limit and sub-account rate limit on T+1 (applicable if the rate limit is going to be demoted).\
\
The fill ratio and rate limit calculation example is shown below. Client has 3 accounts, symbol multiplier for BTC-USDT-SWAP = 1 and XRP-USDT = 0.1.\
\
1. Account A (master account):\
\
1. BTC-USDT-SWAP trade volume = 100 USDT, order count = 10;\
2. XRP-USDT trade volume = 20 USDT, order count = 15;\
3. Sub-account ratio = (100+20) / (10 \* 1 + 15 \* 0.1) = 10.4\
2. Account B (sub-account):\
\
1. BTC-USDT-SWAP trade volume = 200 USDT, order count = 100;\
2. XRP-USDT trade volume = 20 USDT, order count = 30;\
3. Sub-account ratio = (200+20) / (100 \* 1 + 30 \* 0.1) = 2.13\
3. Account C (sub-account):\
\
1. BTC-USDT-SWAP trade volume = 300 USDT, order count = 1000;\
2. XRP-USDT trade volume = 20 USDT, order count = 45;\
3. Sub-account ratio = (300+20) / (100 \* 1 + 45 \* 0.1) = 3.06\
4. Master account aggregated fill ratio = (100+20+200+20+300+20) / (10 \* 1 + 15 \* 0.1 + 100 \* 1 + 30 \* 0.1 + 100 \* 1 + 45 \* 0.1) = 3.01\
5. Rate limit of accounts\
\
1. Account A = max(10.4, 3.01) = 10.4 -> 2500 order requests/2s\
2. Account B = max(2.13, 3.01) = 3.01 -> 1750 order requests/2s\
3. Account C = max(3.06, 3.01) = 3.06 -> 1750 order requests/2s\
\
### Best practices\
\
If you require a higher request rate than our rate limit, you can set up different sub-accounts to batch request rate limits. We recommend this method for throttling or spacing out requests in order to maximize each accounts' rate limit and avoid disconnections or rejections.\
\
## Market Maker Program\
\
High-caliber trading teams are welcomed to work with OKX as market makers in providing a liquid, fair, and orderly platform to all users. OKX market makers could enjoy favourable fees in return for meeting the market making obligations.\
\
Prerequisites (Satisfy any condition):\
\
- VIP 2 or above on fee schedule\
\
- Qualified Market Maker on other exchange\
\
\
Interested parties can reach out to us at `Institutional@okx.com`\
\
Remarks:\
\
Market making obligations and trading fees will be shared to successful parties only.\
\
## Broker Program\
\
If your business platform offers cryptocurrency services, you can apply to join the OKX Broker Program, become our partner broker, enjoy exclusive broker services, and earn high rebates through trading fees generated by OKX users.\
\
The Broker Program includes, and is not limited to, integrated trading platforms, trading bots, copy trading platforms, trading bot providers, quantitative strategy institutions, asset management platforms etc.\
\
- [Click to apply](https://www.okx.com/broker/home)\
- [Broker rules](https://www.okx.com/help/introduction-of-rules-on-okx-brokers)\
- If you have any questions, feel free to contact our customer support.\
\
Relevant information for specific Broker Program documentation and product services will be provided following successful applications.\
\
# Trading Account\
\
The API endpoints of `Account` require authentication.\
\
## REST API\
\
### Get instruments\
\
Retrieve available instruments info of current account.\
\
#### Rate Limit: 20 requests per 2 seconds\
\
#### Rate limit rule: User ID + Instrument Type\
\
#### HTTP Request\
\
`GET /api/v5/account/instruments`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/instruments?instType=SPOT\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1" # Production trading: 0, Demo trading: 1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
result = accountAPI.get_instruments(instType="SPOT")\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| instType | String | Yes | Instrument type<br>`SPOT`: Spot<br>`MARGIN`: Margin<br>`SWAP`: Perpetual Futures<br>`FUTURES`: Expiry Futures<br>`OPTION`: Option<br>`EVENTS`: Event Contracts |\
| seriesId | String | Conditional | Series ID, e.g. `BTC-ABOVE-DAILY`. Required when instType is `EVENTS` |\
| instFamily | String | Conditional | Instrument family<br>Only applicable to `FUTURES`/`SWAP`/`OPTION`. If instType is `OPTION`, `instFamily` is required. |\
| instId | String | No | Instrument ID |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "auctionEndTime": "",\
            "baseCcy": "BTC",\
            "ctMult": "",\
            "ctType": "",\
            "ctVal": "",\
            "ctValCcy": "",\
            "contTdSwTime": "1704876947000",\
            "rpi": "0",\
            "expTime": "",\
            "futureSettlement": false,\
            "groupId": "4",\
            "instFamily": "",\
            "instId": "BTC-EUR",\
            "instType": "SPOT",\
            "lever": "",\
            "listTime": "1704876947000",\
            "lotSz": "0.00000001",\
            "maxIcebergSz": "9999999999.0000000000000000",\
            "maxLmtAmt": "1000000",\
            "maxLmtSz": "9999999999",\
            "maxMktAmt": "1000000",\
            "maxMktSz": "1000000",\
            "maxPlatOILmt": "1000000000",\
            "maxPlatOICoinLmt": "",\
            "maxStopSz": "1000000",\
            "maxTriggerSz": "9999999999.0000000000000000",\
            "maxTwapSz": "9999999999.0000000000000000",\
            "minSz": "0.00001",\
            "optType": "",\
            "openType": "call_auction",\
            "preMktSwTime": "",\
            "posLmtPct": "30",\
            "posLmtAmt": "2500000",\
            "quoteCcy": "EUR",\
            "tradeQuoteCcyList": [\
                "EUR"\
            ],\
            "settleCcy": "",\
            "state": "live",\
            "ruleType": "normal",\
            "stk": "",\
            "tickSz": "1",\
            "uly": "",\
            "instIdCode": 1000000000,\
            "instCategory": "1",\
            "initPxLmtPct": "0.05",\
            "floatPxLmtPct": "0.03",\
            "maxPxLmtPct": "0.15",\
            "upcChg": [\
                {\
                    "param": "tickSz",\
                    "newValue": "0.0001",\
                    "effTime": "1704876947000"\
                }\
            ]\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| instType | String | Instrument type |\
| seriesId | String | Series ID, e.g. `BTC-ABOVE-DAILY`. Only applicable to `EVENTS` |\
| instId | String | Instrument ID, e.g. `BTC-USD-SWAP` |\
| uly | String | Underlying, e.g. `BTC-USD`<br>Only applicable to `MARGIN/FUTURES`/`SWAP`/`OPTION` |\
| groupId | String | Instrument trading fee group ID<br>Spot:<br>`3`: Spot TRY<br>`5`: Spot BRL<br>`7`: Spot AED<br>`8`: Spot AUD<br>`10`: Spot SGD<br>`11`: Spot zero<br>`12`: Spot group one<br>`13`: Spot group two<br>`14`: Spot group three<br>`15`: Spot special rule<br>`17`: Spot stablecoin<br>`22`: Spot RWA group two<br>Expiry futures:<br>`5`: Expiry futures group one<br>`6`: Expiry futures group two<br>`8`: XPERP group two<br>`10`: XPERP RWA group two<br>Perpetual futures:<br>`4`: Perpetual futures group one<br>`5`: Perpetual futures group two<br>`6`: SWAP RWA group one<br>`7`: SWAP RWA group two<br>Options:<br>`1`: Options crypto-margined<br>**instType and groupId should be used together to determine a trading fee group. Users should use this endpoint together with [fee rates endpoint](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-fee-rates) to get the trading fee of a specific symbol.**<br>**Some enum values may not apply to you; the actual return values shall prevail.** |\
| instFamily | String | Instrument family, e.g. `BTC-USD`<br>Only applicable to `MARGIN/FUTURES`/`SWAP`/`OPTION` |\
| baseCcy | String | Base currency, e.g. `BTC` in`BTC-USDT`<br>Only applicable to `SPOT`/`MARGIN` |\
| quoteCcy | String | Quote currency, e.g. `USDT` in `BTC-USDT`<br>Only applicable to `SPOT`/`MARGIN` |\
| settleCcy | String | Settlement and margin currency, e.g. `BTC`<br>Only applicable to `FUTURES`/`SWAP`/`OPTION` |\
| ctVal | String | Contract value <br>Only applicable to `FUTURES`/`SWAP`/`OPTION` |\
| ctMult | String | Contract multiplier <br>Only applicable to `FUTURES`/`SWAP`/`OPTION` |\
| ctValCcy | String | Contract value currency <br>Only applicable to `FUTURES`/`SWAP`/`OPTION` |\
| optType | String | Option type, `C`: Call `P`: put <br>Only applicable to `OPTION` |\
| stk | String | Strike price <br>Only applicable to `OPTION` |\
| listTime | String | Listing time, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| auctionEndTime | String | ~~The end time of call auction, Unix timestamp format in milliseconds, e.g. `1597026383085`<br>Only applicable to `SPOT` that are listed through call auctions, return "" in other cases (deprecated, use contTdSwTime)~~ |\
| contTdSwTime | String | Continuous trading switch time. The switch time from call auction, prequote to continuous trading, Unix timestamp format in milliseconds. e.g. `1597026383085`.<br> Only applicable to `SPOT`/`MARGIN` that are listed through call auction or prequote, return "" in other cases. |\
| preMktSwTime | String | The time a pre-market instrument switched to normal trading, Unix timestamp format in milliseconds, e.g. `1597026383085`. <br> Only applicable to pre-market `SWAP` and pre-market X-Perp `FUTURES`. Populated when a pre-market X-Perp converts to a normal X-Perp |\
| openType | String | Open type<br>`fix_price`: fix price opening<br>`pre_quote`: pre-quote<br>`call_auction`: call auction <br>Only applicable to `SPOT`/`MARGIN`, return "" for all other business lines |\
| rpi | String | RPI maker permission.<br>`0`: not enabled for this instrument<br>`1`: enabled, but the current user has no permission to place RPI orders<br>`2`: enabled and permitted<br>A `1`/`2` value does not imply RPI liquidity is present. |\
| expTime | String | Expiry time <br>Applicable to `SPOT`/`MARGIN`/`FUTURES`/`SWAP`/`OPTION`. For `FUTURES`/`OPTION`, it is natural delivery/exercise time. It is the instrument offline time when there is `SPOT/MARGIN/FUTURES/SWAP/` manual offline. Update once change. |\
| lever | String | Max Leverage, <br>Not applicable to `SPOT`, `OPTION` |\
| tickSz | String | Tick size, e.g. `0.0001`.<br>For `OPTION`/`EVENTS`, it is the minimum tickSz among tick band. Use "Get instrument tick bands" endpoint with the corresponding `instType` for accurate tickSz per price range. |\
| lotSz | String | Lot size<br>If it is a derivatives contract, the value is the number of contracts.<br>If it is `SPOT`/`MARGIN`, the value is the quantity in `base currency`. |\
| minSz | String | Minimum order size<br>If it is a derivatives contract, the value is the number of contracts.<br>If it is `SPOT`/`MARGIN`, the value is the quantity in `base currency`. |\
| ctType | String | Contract type<br>`linear`: linear contract<br>`inverse`: inverse contract <br>Only applicable to `FUTURES`/`SWAP` |\
| state | String | Instrument status<br>`live`<br>`suspend`<br>`rebase`: can't be traded during rebasing<br>`post_only`: only post-only orders are accepted; existing post-only orders can be amended and cancelled. Other order types (market, IOC, FOK, normal limit) are rejected.<br>`preopen` e.g. Futures and options contracts rollover from generation to trading start; certain symbols before they go live<br>`test`: Test pairs, can't be traded<br>`settling`: Settling, only applicable to `EVENTS` |\
| ruleType | String | Trading rule types<br>`normal`: normal trading<br>`pre_market`: pre-market trading, including pre-market X-Perp `FUTURES`<br>`rebase_contract`: pre-market rebase contract<br>`xperp`: perpetual-style futures, only applicable to certain `FUTURES` contracts. A pre-market X-Perp changes from `pre_market` to `xperp` after it converts to a normal X-Perp |\
| posLmtAmt | String | Maximum position value (USD) for this instrument at the user level (shared across master and sub-accounts), based on the notional value of all same-direction open positions and resting orders. The effective user limit is max(posLmtAmt, oiUSD × posLmtPct). Applicable to `SWAP`/`FUTURES`. |\
| posLmtPct | String | Maximum position ratio (e.g., 30 for 30%) a user (shared across master and sub-accounts) may hold relative to the platform's current total position value. The effective user limit is max(posLmtAmt, oiUSD × posLmtPct). Applicable to `SWAP`/`FUTURES`. |\
| maxPlatOILmt | String | Platform-wide maximum position value (USD) for this instrument. If the platform total open interest (USD) reaches or exceeds this value, all users’ new opening orders for this instrument are rejected; otherwise, orders pass.<br>Applicable to `SWAP`/`FUTURES` |\
| maxPlatOICoinLmt | String | Platform-wide maximum position value (coins) for this instrument. If the platform total open interest (coins) reaches or exceeds this value, all users’ new opening orders for this instrument are rejected; otherwise, orders pass.<br>Applicable to `SWAP`/`FUTURES` |\
| longPosRemainingQuota | String | The remaining long position value (USD) the user is permitted to open, netting all existing long positions and resting buy orders. The quota is shared across the master account and all subaccounts. |\
| shortPosRemainingQuota | String | The remaining short position value (USD) the user is permitted to open, netting all existing short positions and resting sell orders. The quota is shared across the master account and all subaccounts. |\
| maxLmtSz | String | The maximum order quantity of a single limit order.<br>If it is a derivatives contract, the value is the number of contracts.<br>If it is `SPOT`/`MARGIN`, the value is the quantity in `base currency`. |\
| maxMktSz | String | The maximum order quantity of a single market order.<br>If it is a derivatives contract, the value is the number of contracts.<br>If it is `SPOT`/`MARGIN`, the value is the quantity in `USDT`. |\
| maxLmtAmt | String | Max USD amount for a single limit order |\
| maxMktAmt | String | Max USD amount for a single market order <br>Only applicable to `SPOT`/`MARGIN` |\
| maxTwapSz | String | The maximum order quantity of a single TWAP order.<br>If it is a derivatives contract, the value is the number of contracts.<br>If it is `SPOT`/`MARGIN`, the value is the quantity in `base currency`. <br> The minimum order quantity of a single TWAP order is minSz\*2 |\
| maxIcebergSz | String | The maximum order quantity of a single iceBerg order.<br>If it is a derivatives contract, the value is the number of contracts.<br>If it is `SPOT`/`MARGIN`, the value is the quantity in `base currency`. |\
| maxTriggerSz | String | The maximum order quantity of a single trigger order.<br>If it is a derivatives contract, the value is the number of contracts.<br>If it is `SPOT`/`MARGIN`, the value is the quantity in `base currency`. |\
| maxStopSz | String | The maximum order quantity of a single stop market order.<br>If it is a derivatives contract, the value is the number of contracts.<br>If it is `SPOT`/`MARGIN`, the value is the quantity in `USDT`. |\
| futureSettlement | Boolean | Whether daily settlement for expiry feature is enabled<br>Applicable to `FUTURES``cross` |\
| tradeQuoteCcyList | Array of strings | List of quote currencies available for trading, e.g. \["USD", "USDC"\]. |\
| instIdCode | Integer | Instrument ID code. <br>For simple binary encoding, you must use `instIdCode` instead of `instId`.<br>For the same `instId`, it's value may be different between production and demo trading. <br> It is `null` when the value is not generated. |\
| instCategory | String | The asset category of the instrument’s base asset (the first segment of the instrument ID). For example, for `BTC-USDT-SWAP`, the `instCategory` represents the asset category of `BTC`. <br>`1`: Crypto <br>`3`: Stocks <br>`4`: Commodities <br>`5`: Forex <br>`6`: Bonds <br>`""`: Not available |\
| initPxLmtPct | String | Initial price-limit band applied during the first 10 minutes after contract listing, e.g. `0.05` represents 5%. Use GET /api/v5/public/price-limit for the computed price limits.<br>Only applicable to `SPOT`/`MARGIN`/`SWAP`/`FUTURES`, returns `""` for `OPTION` and `EVENTS`. |\
| floatPxLmtPct | String | Floating price-limit band during normal trading, e.g. `0.03` represents 3%. Use GET /api/v5/public/price-limit for the computed price limits.<br>Only applicable to `SPOT`/`MARGIN`/`SWAP`/`FUTURES`, returns `""` for `OPTION` and `EVENTS`. |\
| maxPxLmtPct | String | Maximum price-limit cap (hard ceiling on order-price deviation from the index price), e.g. `0.15` represents 15%. Use GET /api/v5/public/price-limit for the computed price limits.<br>Only applicable to `SPOT`/`MARGIN`/`SWAP`/`FUTURES`, returns `""` for `OPTION` and `EVENTS`. |\
| upcChg | Array of objects | Upcoming changes. It is \[\] when there is no upcoming change. |\
| \> param | String | The parameter name to be updated. <br>`tickSz`<br>`minSz`: For `FUTURES`/`SWAP`, `lotSz` will be modified synchronously.<br>`maxMktSz` |\
| \> newValue | String | The parameter value that will replace the current one. |\
| \> effTime | String | Effective time. Unix timestamp format in milliseconds, e.g. `1597026383085` |\
\
### Get balance\
\
Retrieve a list of assets (with non-zero balance), remaining balance, and available amount in the trading account.\
\
#### Rate Limit: 10 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/balance`\
\
> Request Example\
\
```\
Copy to Clipboard\
# Get the balance of all assets in the account\
GET /api/v5/account/balance\
\
# Get the balance of BTC and ETH assets in the account\
GET /api/v5/account/balance?ccy=BTC,ETH\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get account balance\
result = accountAPI.get_account_balance()\
print(result)\
```\
\
#### Request Parameters\
\
| **Parameters** | **Types** | **Required** | **Description** |\
| --- | --- | --- | --- |\
| ccy | String | No | Single currency or multiple currencies (no more than 20) separated with comma, e.g. `BTC` or `BTC,ETH`. |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "adjEq": "55415.624719833286",\
            "availEq": "55415.624719833286",\
            "borrowFroz": "0",\
            "delta": "0",\
            "deltaLever": "0",\
            "deltaNeutralStatus": "0",\
            "details": [\
                {\
                    "autoLendStatus": "off",\
                    "autoLendMtAmt": "0",\
                    "availBal": "4834.317093622894",\
                    "availEq": "4834.3170936228935",\
                    "borrowFroz": "0",\
                    "cashBal": "4850.435693622894",\
                    "ccy": "USDT",\
                    "crossLiab": "0",\
                    "colRes": "0",\
                    "collateralEnabled": false,\
                    "collateralRestrict": false,\
                    "colBorrAutoConversion": "0",\
                    "disEq": "4991.542013297616",\
                    "eq": "4992.890093622894",\
                    "eqUsd": "4991.542013297616",\
                    "smtSyncEq": "0",\
                    "spotCopyTradingEq": "0",\
                    "fixedBal": "0",\
                    "frozenBal": "158.573",\
                    "frpType": "0",\
                    "imr": "",\
                    "interest": "0",\
                    "isoEq": "0",\
                    "isoLiab": "0",\
                    "isoUpl": "0",\
                    "liab": "0",\
                    "maxLoan": "0",\
                    "mgnRatio": "",\
                    "mmr": "",\
                    "notionalLever": "",\
                    "ordFrozen": "0",\
                    "rewardBal": "0",\
                    "spotInUseAmt": "",\
                    "clSpotInUseAmt": "",\
                    "maxSpotInUse": "",\
                    "spotIsoBal": "0",\
                    "stgyEq": "150",\
                    "twap": "0",\
                    "uTime": "1705449605015",\
                    "upl": "-7.545600000000006",\
                    "uplLiab": "0",\
                    "spotBal": "",\
                    "openAvgPx": "",\
                    "accAvgPx": "",\
                    "spotUpl": "",\
                    "spotUplRatio": "",\
                    "totalPnl": "",\
                    "totalPnlRatio": ""\
                }\
            ],\
            "imr": "0",\
            "isoEq": "0",\
            "mgnRatio": "",\
            "mmr": "0",\
            "notionalUsd": "0",\
            "notionalUsdForBorrow": "0",\
            "notionalUsdForFutures": "0",\
            "notionalUsdForOption": "0",\
            "notionalUsdForSwap": "0",\
            "ordFroz": "",\
            "totalEq": "55837.43556134779",\
            "uTime": "1705474164160",\
            "upl": "0"\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| **Parameters** | **Types** | **Description** |\
| --- | --- | --- |\
| uTime | String | Update time of account information, millisecond format of Unix timestamp, e.g. `1597026383085` |\
| totalEq | String | Total account assets denominated in `USD` |\
| isoEq | String | Isolated margin equity in `USD`<br>Applicable to `Futures mode`/`Multi-currency margin`/`Portfolio margin` |\
| adjEq | String | Adjusted equity in `USD`: `totalEq` minus haircut discounts applied to non-stablecoin collateral assets. This is the operative value used in the margin ratio calculation (`mgnRatio` = `adjEq` / `mmr`). <br>The net fiat value of the assets in the account that can provide margins for spot, expiry futures, perpetual futures and options under the cross-margin mode. <br>In multi-ccy or PM mode, the asset and margin requirement will all be converted to USD value to process the order check or liquidation. <br>Due to the volatility of each currency market, our platform calculates the actual USD value of each currency based on discount rates to balance market risks. <br>Applicable to `Spot mode`/`Multi-currency margin` and `Portfolio margin` |\
| availEq | String | Account level available equity, excluding currencies that are restricted due to the collateralized borrowing limit.<br> Applicable to `Multi-currency margin`/`Portfolio margin` |\
| ordFroz | String | Cross margin frozen for pending orders in `USD`<br>Only applicable to `Spot mode`/`Multi-currency margin`/`Portfolio margin` |\
| imr | String | Initial Margin Requirement (IMR) in `USD`: equity locked across all open cross-margin positions. The sum of initial margins of all open positions and pending orders under cross-margin mode. Formula per position: position size × markPx × initial margin rate (= 1/lever). Returns empty string in Simple mode. <br>Applicable to `Spot mode`/`Multi-currency margin`/`Portfolio margin` |\
| mmr | String | Maintenance Margin Requirement (MMR) in `USD`: the minimum equity required to avoid forced liquidation. The sum of maintenance margins of all open positions and pending orders under cross-margin mode. When `adjEq` ≤ `mmr` (equivalently, `mgnRatio` ≤ 1.0), the system begins forced liquidation of positions. Subscribe to the position-risk-warning WebSocket channel for proactive alerts. <br>Applicable to `Spot mode`/`Multi-currency margin`/`Portfolio margin` |\
| borrowFroz | String | Potential borrowing IMR of the account in `USD`<br>Only applicable to `Spot mode`/`Multi-currency margin`/`Portfolio margin`. It is "" for other margin modes. |\
| mgnRatio | String | Account-level margin ratio = `adjEq` / `mmr`. Values at or below 1.0 indicate the account is at or past the liquidation boundary. Monitor this field or subscribe to the position-risk-warning WebSocket channel for proactive alerts. <br>Applicable to `Spot mode`/`Multi-currency margin`/`Portfolio margin` |\
| notionalUsd | String | Gross notional value of all open derivative positions converted to USD. Linear contracts: sz × ctVal × markPx. Inverse contracts: sz × ctVal (USD-denominated face value). Gross = long and short are not netted. <br>Applicable to `Spot mode`/`Multi-currency margin`/`Portfolio margin` |\
| notionalUsdForBorrow | String | Notional value for `Borrow` in USD<br>Applicable to `Spot mode`/`Multi-currency margin`/`Portfolio margin` |\
| notionalUsdForSwap | String | Notional value of positions for `Perpetual Futures` in USD<br>Applicable to `Multi-currency margin`/`Portfolio margin` |\
| notionalUsdForFutures | String | Notional value of positions for `Expiry Futures` in USD<br>Applicable to `Multi-currency margin`/`Portfolio margin` |\
| notionalUsdForOption | String | Notional value of positions for `Option` in USD<br>Applicable to `Spot mode`/`Multi-currency margin`/`Portfolio margin` |\
| upl | String | Unrealized PnL across all open cross-margin positions at the account level, in `USD`. Calculated using mark price (not last trade price). Positive = unrealized gain; negative = unrealized loss. Returns empty string in Simple mode and Single-currency margin mode.<br>Applicable to `Multi-currency margin`/`Portfolio margin` |\
| delta | String | Delta (USD) |\
| deltaLever | String | Delta neutral strategy account level delta leverage<br>deltaLever = delta / totalEq |\
| deltaNeutralStatus | String | Delta risk status<br>`0`: normal<br>`1`: transfer restricted<br>`2`: delta reducing - cancel all pending orders if delta is greater than 5000 USD, only one delta reducing order allowed per index (spot, futures, swap) |\
| details | Array of objects | Detailed asset information in all currencies |\
| \> ccy | String | Currency |\
| \> eq | String | Equity of currency |\
| \> cashBal | String | Cash balance |\
| \> uTime | String | Update time of currency balance information, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| \> isoEq | String | Isolated margin equity of currency<br>Applicable to `Futures mode`/`Multi-currency margin`/`Portfolio margin` |\
| \> availEq | String | Available equity of currency<br>Applicable to `Futures mode`/`Multi-currency margin`/`Portfolio margin` |\
| \> disEq | String | Discount equity of currency in `USD`.<br>Applicable to `Spot mode`(enabled spot borrow)/`Multi-currency margin`/`Portfolio margin` |\
| \> fixedBal | String | Frozen balance for `Dip Sniper` and `Peak Sniper` |\
| \> availBal | String | Available balance of currency |\
| \> frozenBal | String | Frozen balance of currency |\
| \> ordFrozen | String | Margin frozen for open orders<br>Applicable to `Spot mode`/`Futures mode`/`Multi-currency margin` |\
| \> liab | String | Liabilities of currency<br>It is a positive value, e.g. `21625.64`<br>Applicable to `Spot mode`/`Multi-currency margin`/`Portfolio margin` |\
| \> upl | String | The sum of the unrealized profit & loss of all margin and derivatives positions of currency. <br>Applicable to `Futures mode`/`Multi-currency margin`/`Portfolio margin` |\
| \> uplLiab | String | Liabilities due to Unrealized loss of currency<br>Applicable to `Multi-currency margin`/`Portfolio margin` |\
| \> crossLiab | String | Cross liabilities of currency<br>Applicable to `Spot mode`/`Multi-currency margin`/`Portfolio margin` |\
| \> rewardBal | String | Trial fund balance |\
| \> isoLiab | String | Isolated liabilities of currency<br>Applicable to `Multi-currency margin`/`Portfolio margin` |\
| \> mgnRatio | String | Cross maintenance margin ratio of currency <br>The index for measuring the risk of a certain asset in the account. <br>Applicable to `Futures mode` and when there is cross position |\
| \> imr | String | Cross initial margin requirement at the currency level<br>Applicable to `Futures mode` and when there is cross position |\
| \> mmr | String | Cross maintenance margin requirement at the currency level<br>Applicable to `Futures mode` and when there is cross position |\
| \> interest | String | Accrued interest of currency<br>It is a positive value, e.g. `9.01`<br>Applicable to `Spot mode`/`Multi-currency margin`/`Portfolio margin` |\
| \> twap | String | Risk indicator of forced repayment<br>Divided into multiple levels from 0 to 5, the larger the number, the more likely the forced repayment will be triggered. <br>Applicable to `Spot mode`/`Multi-currency margin`/`Portfolio margin` |\
| \> frpType | String | Forced repayment (FRP) type<br>`0`: no FRP<br>`1`: user based FRP<br>`2`: platform based FRP<br> Return `1`/`2` when twap is >= 1, applicable to `Spot mode`/`Multi-currency margin`/`Portfolio margin` |\
| \> maxLoan | String | Maximum borrowable amount for the currency under the current account conditions. Affects the amount available for margin borrowing and transfers.<br>Applicable to `cross` of `Spot mode`/`Multi-currency margin`/`Portfolio margin` |\
| \> eqUsd | String | Equity in `USD` of currency |\
| \> borrowFroz | String | Potential borrowing IMR of currency in `USD`<br>Applicable to `Multi-currency margin`/`Portfolio margin`. It is "" for other margin modes. |\
| \> notionalLever | String | Leverage of currency<br>Applicable to `Futures mode` |\
| \> stgyEq | String | Total equity allocated to trading bots for the currency. Covers Spot Grid, Futures Grid, Signal Bot, Futures Martingale, Spot Martingale, Infinite Grid, and Recurring Buy strategies. |\
| \> isoUpl | String | Isolated unrealized profit and loss of currency<br>Applicable to `Futures mode`/`Multi-currency margin`/`Portfolio margin` |\
| \> spotInUseAmt | String | Actual spot hedging amount in use for the currency. <br>Applicable to `Portfolio margin` |\
| \> clSpotInUseAmt | String | User-defined spot hedging amount for the currency. Applicable to `Portfolio margin` |\
| \> maxSpotInUse | String | System-calculated maximum possible spot hedging amount for the currency.<br>Applicable to `Portfolio margin` |\
| \> spotIsoBal | String | Balance acquired through spot copy trading (as a follower or lead trader), including amounts currently frozen by open orders. For example, if 1 BTC was purchased via copy trading and 0.4 BTC is frozen in an open sell order, `spotIsoBal` returns `1`, not `0.6`.<br>Applicable to copy trading. Applicable to `Spot mode`/`Futures mode`. |\
| \> smtSyncEq | String | Smart sync equity<br>The default is "0", only applicable to copy trader. |\
| \> spotCopyTradingEq | String | Spot smart sync equity. <br>The default is "0", only applicable to copy trader. |\
| \> spotBal | String | Spot balance. The unit is currency, e.g. BTC. [More details](https://www.okx.com/help/i-introduction-of-spot) |\
| \> openAvgPx | String | Spot average cost price. The unit is USD. [More details](https://www.okx.com/help/i-introduction-of-spot) |\
| \> accAvgPx | String | Spot accumulated cost price. The unit is USD. [More details](https://www.okx.com/help/i-introduction-of-spot) |\
| \> spotUpl | String | Spot unrealized profit and loss. The unit is USD. [More details](https://www.okx.com/help/i-introduction-of-spot) |\
| \> spotUplRatio | String | Spot unrealized profit and loss ratio. [More details](https://www.okx.com/help/i-introduction-of-spot) |\
| \> totalPnl | String | Spot accumulated profit and loss. The unit is USD. [More details](https://www.okx.com/help/i-introduction-of-spot) |\
| \> totalPnlRatio | String | Spot accumulated profit and loss ratio. [More details](https://www.okx.com/help/i-introduction-of-spot) |\
| \> colRes | String | Platform level collateral restriction status<br>`0`: The restriction is not enabled.<br>`1`: The restriction is not enabled. But the crypto is close to the platform's collateral limit.<br>`2`: The restriction is enabled. This crypto can't be used as margin for your new orders. This may result in failed orders. But it will still be included in the account's adjusted equity and doesn't impact margin ratio.<br> Refer to [Introduction to the platform collateralized borrowing limit](https://www.okx.com/help/introduction-to-the-platforms-collateralized-borrowing-limit-mechanism) for more details. |\
| \> colBorrAutoConversion | String | Risk indicator of auto conversion. Divided into multiple levels from 1-5, the larger the number, the more likely the repayment will be triggered. The default will be 0, indicating there is no risk currently. 5 means this user is undergoing auto conversion now, 4 means this user will undergo auto conversion soon whereas 1/2/3 indicates there is a risk for auto conversion.<br> Applicable to `Spot mode`/`Futures mode`/`Multi-currency margin`/`Portfolio margin`<br> When the total liability for each crypto set as collateral exceeds a certain percentage of the platform's total limit, the auto-conversion mechanism may be triggered. This may result in the automatic sale of excess collateral crypto if you've set this crypto as collateral and have large borrowings. To lower this risk, consider reducing your use of the crypto as collateral or reducing your liabilities.<br> Refer to [Introduction to the platform collateralized borrowing limit](https://www.okx.com/help/introduction-to-the-platforms-collateralized-borrowing-limit-mechanism) for more details. |\
| \> collateralRestrict | Boolean | ~~Platform level collateralized borrow restriction<br>`true`<br>`false`~~(deprecated, use colRes instead) |\
| \> collateralEnabled | Boolean | `true`: Collateral enabled<br>`false`: Collateral disabled<br>Applicable to `Multi-currency margin` |\
| \> autoLendStatus | String | Auto lend status<br>`unsupported`: auto lend is not supported by this currency<br>`off`: auto lend is supported but turned off<br>`pending`: auto lend is turned on but pending matching<br>`active`: auto lend is turned on and matched |\
| \> autoLendMtAmt | String | Auto lend currency matched amount<br> Return "0" when autoLendStatus is `unsupported/off/pending`. Return matched amount when autoLendStatus is `active` |\
\
- Regarding more parameter details, you can refer to product documentations below:\
\
[Futures mode: cross margin trading](https://www.okx.com/help/iii-single-currency-margin-cross-margin-trading)\
\
[Multi-currency margin mode: cross margin trading](https://www.okx.com/help/iv-multi-currency-margin-mode-cross-margin-trading)\
\
[Multi-currency margin mode vs. Portfolio margin mode](https://www.okx.com/help/vi-multi-currency-margin-mode-vs-portfolio-margin-mode)\
\
\
Distribution of applicable fields under each account level are as follows:\
\
| **Parameters** | **Spot mode** | **Futures mode** | **Multi-currency margin mode** | **Portfolio margin mode** |\
| --- | --- | --- | --- | --- |\
| uTime | Yes | Yes | Yes | Yes |\
| totalEq | Yes | Yes | Yes | Yes |\
| isoEq |  | Yes | Yes | Yes |\
| adjEq | Yes |  | Yes | Yes |\
| availEq |  |  | Yes | Yes |\
| ordFroz | Yes |  | Yes | Yes |\
| imr | Yes |  | Yes | Yes |\
| mmr | Yes |  | Yes | Yes |\
| borrowFroz | Yes |  | Yes | Yes |\
| mgnRatio | Yes |  | Yes | Yes |\
| notionalUsd | Yes |  | Yes | Yes |\
| notionalUsdForSwap |  |  | Yes | Yes |\
| notionalUsdForFutures |  |  | Yes | Yes |\
| notionalUsdForOption | Yes |  | Yes | Yes |\
| notionalUsdForBorrow | Yes |  | Yes | Yes |\
| upl |  |  | Yes | Yes |\
| details | Yes | Yes | Yes | Yes |\
| \> ccy | Yes | Yes | Yes | Yes |\
| \> eq | Yes | Yes | Yes | Yes |\
| \> cashBal | Yes | Yes | Yes | Yes |\
| \> uTime | Yes | Yes | Yes | Yes |\
| \> isoEq |  | Yes | Yes | Yes |\
| \> availEq |  | Yes | Yes | Yes |\
| \> disEq | Yes |  | Yes | Yes |\
| \> availBal | Yes | Yes | Yes | Yes |\
| \> frozenBal | Yes | Yes | Yes | Yes |\
| \> ordFrozen | Yes | Yes | Yes | Yes |\
| \> liab | Yes |  | Yes | Yes |\
| \> upl |  | Yes | Yes | Yes |\
| \> uplLiab |  |  | Yes | Yes |\
| \> crossLiab | Yes |  | Yes | Yes |\
| \> isoLiab |  |  | Yes | Yes |\
| \> mgnRatio |  | Yes |  |  |\
| \> interest | Yes |  | Yes | Yes |\
| \> twap | Yes |  | Yes | Yes |\
| \> maxLoan | Yes |  | Yes | Yes |\
| \> eqUsd | Yes | Yes | Yes | Yes |\
| \> borrowFroz | Yes |  | Yes | Yes |\
| \> notionalLever |  | Yes |  |  |\
| \> stgyEq | Yes | Yes | Yes | Yes |\
| \> isoUpl |  | Yes | Yes | Yes |\
| \> spotInUseAmt |  |  |  | Yes |\
| \> clSpotInUseAmt |  |  |  | Yes |\
| \> maxSpotInUse |  |  |  | Yes |\
| \> spotIsoBal | Yes | Yes |  |  |\
| \> imr |  | Yes |  |  |\
| \> mmr |  | Yes |  |  |\
| \> smtSyncEq | Yes | Yes | Yes | Yes |\
| \> spotCopyTradingEq | Yes | Yes | Yes | Yes |\
| \> spotBal | Yes | Yes | Yes | Yes |\
| \> openAvgPx | Yes | Yes | Yes | Yes |\
| \> accAvgPx | Yes | Yes | Yes | Yes |\
| \> spotUpl | Yes | Yes | Yes | Yes |\
| \> spotUplRatio | Yes | Yes | Yes | Yes |\
| \> totalPnl | Yes | Yes | Yes | Yes |\
| \> totalPnlRatio | Yes | Yes | Yes | Yes |\
| \> collateralEnabled |  |  | Yes |  |\
\
### Get positions\
\
Retrieve information on your positions. When the account is in `net` mode, `net` positions will be displayed, and when the account is in `long/short` mode, `long` or `short` positions will be displayed. Return in reverse chronological order using ctime.\
\
#### Rate Limit: 10 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/positions`\
\
> Request Example\
\
```\
Copy to Clipboard\
# Query BTC-USDT position information\
GET /api/v5/account/positions?instId=BTC-USDT\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get positions information\
result = accountAPI.get_positions()\
print(result)\
```\
\
#### Request Parameters\
\
| **Parameter** | **Type** | **Required** | **Description** |\
| --- | --- | --- | --- |\
| instType | String | No | Instrument type<br>`MARGIN`<br>`SWAP`<br>`FUTURES`<br>`OPTION`<br>`EVENTS`<br>`instId` will be checked against `instType` when both parameters are passed. |\
| instId | String | No | Instrument ID, e.g. `BTC-USDT-SWAP`. Single instrument ID or multiple instrument IDs (no more than 10) separated with comma |\
| posId | String | No | Single position ID or multiple position IDs (no more than 20) separated with comma. <br>There is attribute expiration, the posId and position information will be cleared if it is more than 30 days after the last full close position. |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "adl": "1",\
            "availPos": "0.00190433573",\
            "avgPx": "62961.4",\
            "baseBal": "",\
            "baseBorrowed": "",\
            "baseInterest": "",\
            "bePx": "",\
            "bizRefId": "",\
            "bizRefType": "",\
            "cTime": "1724740225685",\
            "ccy": "BTC",\
            "clSpotInUseAmt": "",\
            "closeOrderAlgo": [],\
            "deltaBS": "",\
            "deltaPA": "",\
            "fee": "",\
            "fundingFee": "",\
            "gammaBS": "",\
            "gammaPA": "",\
            "hedgedPos": "",\
            "idxPx": "62890.5",\
            "imr": "",\
            "instId": "BTC-USDT",\
            "instType": "MARGIN",\
            "interest": "0",\
            "last": "62892.9",\
            "lever": "5",\
            "liab": "-99.9998177776581948",\
            "liabCcy": "USDT",\
            "liqPenalty": "",\
            "liqPx": "53615.448336593756",\
            "margin": "0.000317654",\
            "markPx": "62891.9",\
            "maxSpotInUseAmt": "",\
            "mgnMode": "isolated",\
            "mgnRatio": "9.404143929947395",\
            "mmr": "0.0000318005395854",\
            "notionalUsd": "119.756628017499",\
            "optVal": "",\
            "pendingCloseOrdLiabVal": "0",\
            "pnl": "",\
            "pos": "0.00190433573",\
            "posCcy": "BTC",\
            "posId": "1752810569801498626",\
            "posSide": "net",\
            "quoteBal": "",\
            "quoteBorrowed": "",\
            "quoteInterest": "",\
            "realizedPnl": "",\
            "spotInUseAmt": "",\
            "spotInUseCcy": "",\
            "thetaBS": "",\
            "thetaPA": "",\
            "tradeId": "785524470",\
            "uTime": "1724742632153",\
            "upl": "-0.0000033452492717",\
            "uplLastPx": "-0.0000033199677697",\
            "uplRatio": "-0.0105311101755551",\
            "uplRatioLastPx": "-0.0104515220008934",\
            "usdPx": "",\
            "vegaBS": "",\
            "vegaPA": "",\
            "nonSettleAvgPx":"",\
            "settledPnl":""\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| instType | String | Instrument type<br>`MARGIN`<br>`SWAP`<br>`FUTURES`<br>`OPTION`<br>`EVENTS` |\
| mgnMode | String | Margin mode<br>`cross`<br>`isolated` |\
| posId | String | Position ID |\
| posSide | String | Position side<br>`long`, `pos` is positive <br>`short`, `pos` is positive <br>`net` (`FUTURES`/`SWAP`/`OPTION`: positive `pos` means long position and negative `pos` means short position. For `MARGIN`, `pos` is always positive, `posCcy` being base currency means long position, `posCcy` being quote currency means short position.) |\
| pos | String | Position quantity. Unit: number of contracts for SWAP/FUTURES/OPTIONS; base currency amount for MARGIN. Sign (net mode): positive = long, negative = short. In long/short mode, separate records are returned per side — check `posSide`. In the isolated margin mode, when doing manual transfers, a position with pos of `0` will be generated after the deposit is transferred (represents a funded-but-empty position record created after a margin deposit). |\
| hedgedPos | String | Hedged position size<br>Only return for accounts in delta neutral strategy, stgyType:1. Return "" for accounts in general strategy. |\
| baseBal | String | ~~Base currency balance, only applicable to `MARGIN`（Quick Margin Mode）~~(Deprecated) |\
| quoteBal | String | ~~Quote currency balance, only applicable to `MARGIN`（Quick Margin Mode）~~(Deprecated) |\
| baseBorrowed | String | ~~Base currency amount already borrowed, only applicable to MARGIN(Quick Margin Mode）~~(Deprecated) |\
| baseInterest | String | ~~Base Interest, undeducted interest that has been incurred, only applicable to MARGIN(Quick Margin Mode）~~(Deprecated) |\
| quoteBorrowed | String | ~~Quote currency amount already borrowed, only applicable to MARGIN(Quick Margin Mode）~~(Deprecated) |\
| quoteInterest | String | ~~Quote Interest, undeducted interest that has been incurred, only applicable to MARGIN(Quick Margin Mode）~~(Deprecated) |\
| posCcy | String | Position currency, only applicable to `MARGIN` positions. |\
| availPos | String | Position that can be closed <br>Only applicable to `MARGIN` and `OPTION`.<br>For `MARGIN` position, the rest of sz will be `SPOT` trading after the liability is repaid while closing the position. Please get the available reduce-only amount from "Get maximum available tradable amount" if you want to reduce the amount of `SPOT` trading as much as possible. |\
| avgPx | String | Volume-weighted average entry price of the current open position. Denominated in quote currency for linear contracts (e.g., USDT for BTC-USDT-SWAP) and in USD for inverse contracts (e.g., BTC-USD-SWAP). Recalculated after each fill that changes position size.<br>Under cross-margin mode, the entry price of expiry futures will update at settlement to the last settlement price, and when the position is opened or increased. |\
| nonSettleAvgPx | String | Non-settlement entry price<br>The non-settlement entry price only reflects the average price at which the position is opened or increased.<br>Applicable to `cross``FUTURES` positions. |\
| markPx | String | Latest Mark price |\
| upl | String | Unrealized PnL for this position, denominated in the instrument's settlement currency (see `ccy`). Formula: (markPx − avgPx) × pos × ctVal for linear; (1/avgPx − 1/markPx) × pos × ctVal for inverse. For account-level USD total, see `upl` in GET /api/v5/account/balance. |\
| uplRatio | String | Unrealized profit and loss ratio calculated by mark price. |\
| uplLastPx | String | Unrealized profit and loss calculated by last price. Main usage is showing, actual value is upl. |\
| uplRatioLastPx | String | Unrealized profit and loss ratio calculated by last price. |\
| instId | String | Instrument ID, e.g. `BTC-USDT-SWAP` |\
| lever | String | Leverage<br> Not applicable to `OPTION` and positions of cross margin mode under `Portfolio margin` |\
| liqPx | String | Estimated mark price at which this position would be forcibly liquidated. This is an estimate based on current equity and margin rates — the actual liquidation price can change quickly due to funding rate accrual, other position changes, or rapid market moves. <br>Not applicable to `OPTION` |\
| imr | String | Initial margin requirement for this specific cross-margin position, in USD. Formula: position size × markPx × initial margin rate (1/lever). For total account IMR, see `imr` in GET /api/v5/account/balance. Empty string for isolated positions. Only applicable to `cross`. |\
| margin | String | Margin, can be added or reduced. Only applicable to `isolated`. |\
| mgnRatio | String | Maintenance margin ratio |\
| mmr | String | Maintenance margin requirement |\
| liab | String | Liabilities, only applicable to `MARGIN`. |\
| liabCcy | String | Liabilities currency, only applicable to `MARGIN`. |\
| interest | String | Interest. Undeducted interest that has been incurred. |\
| tradeId | String | Last trade ID |\
| optVal | String | Option Value, only applicable to `OPTION`. |\
| pendingCloseOrdLiabVal | String | The amount of close orders of isolated margin liability. |\
| notionalUsd | String | Notional value of positions in `USD` |\
| adl | String | Auto-Deleveraging (ADL) indicator. Range: 0–5, where 0 = lowest ADL priority (least likely to be forcibly deleveraged) and 5 = highest priority (first in queue if the insurance fund is depleted). Priority increases with higher unrealized profit and higher leverage. <br>Only applicable to `FUTURES/SWAP/OPTION` |\
| ccy | String | Currency used for margin |\
| last | String | Latest traded price |\
| idxPx | String | Latest underlying index price |\
| usdPx | String | Latest USD price of the `ccy` on the market, only applicable to `FUTURES`/`SWAP`/`OPTION` |\
| bePx | String | Breakeven price |\
| deltaBS | String | delta: Black-Scholes Greeks in dollars, only applicable to `OPTION` |\
| deltaPA | String | delta: Greeks in coins, only applicable to `OPTION` |\
| gammaBS | String | gamma: Black-Scholes Greeks in dollars, only applicable to `OPTION` |\
| gammaPA | String | gamma: Greeks in coins, only applicable to `OPTION` |\
| thetaBS | String | theta：Black-Scholes Greeks in dollars, only applicable to `OPTION` |\
| thetaPA | String | theta：Greeks in coins, only applicable to `OPTION` |\
| vegaBS | String | vega：Black-Scholes Greeks in dollars, only applicable to `OPTION` |\
| vegaPA | String | vega：Greeks in coins, only applicable to `OPTION` |\
| spotInUseAmt | String | Spot in use amount<br>Applicable to `Portfolio margin` |\
| spotInUseCcy | String | Spot in use unit, e.g. `BTC`<br>Applicable to `Portfolio margin` |\
| clSpotInUseAmt | String | User-defined spot risk offset amount<br>Applicable to `Portfolio margin` |\
| maxSpotInUseAmt | String | Max possible spot risk offset amount<br>Applicable to `Portfolio margin` |\
| bizRefId | String | External business id, e.g. experience coupon id |\
| bizRefType | String | External business type |\
| realizedPnl | String | Realized profit and loss<br>Only applicable to `FUTURES`/`SWAP`/`OPTION`<br>`realizedPnl`=`pnl`+`fee`+`fundingFee`+`liqPenalty`+`settledPnl` |\
| settledPnl | String | Accumulated settled profit and loss (calculated by settlement price)<br>Only applicable to `cross``FUTURES` |\
| pnl | String | Accumulated pnl of closing order(s) (excluding the fee). |\
| fee | String | Accumulated fee since the current position was opened. Resets to 0 when the position is fully closed. For per-fill fees, use GET /api/v5/trade/fills.<br>Negative number represents the user transaction fee charged by the platform. Positive number represents rebate. |\
| fundingFee | String | Accumulated funding fee |\
| liqPenalty | String | Accumulated liquidation penalty. It is negative when there is a value. |\
| closeOrderAlgo | Array of objects | Close position algo orders attached to the position. This array will have values only after you request "Place algo order" with `closeFraction`=1. |\
| \> algoId | String | Algo ID |\
| \> slTriggerPx | String | Stop-loss trigger price. |\
| \> slTriggerPxType | String | Stop-loss trigger price type. <br>`last`: last price<br>`index`: index price<br>`mark`: mark price |\
| \> tpTriggerPx | String | Take-profit trigger price. |\
| \> tpTriggerPxType | String | Take-profit trigger price type. <br>`last`: last price<br>`index`: index price<br>`mark`: mark price |\
| \> closeFraction | String | Fraction of position to be closed when the algo order is triggered. |\
| cTime | String | Creation time, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| uTime | String | Latest time position was adjusted, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
\
### Get positions history\
\
Retrieve the updated position data for the last 3 months. Return in reverse chronological order using utime. Getting positions history is supported under Portfolio margin mode since **04:00 AM (UTC) on November 11, 2024**.\
\
#### Rate Limit: 10 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/positions-history`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/positions-history\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get positions history\
result = accountAPI.get_positions_history()\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| instType | String | No | Instrument type<br>`MARGIN`<br>`SWAP`<br>`FUTURES`<br>`OPTION`<br>`EVENTS` |\
| instId | String | No | Instrument ID, e.g. `BTC-USD-SWAP` |\
| mgnMode | String | No | Margin mode<br>`cross``isolated` |\
| type | String | No | The type of latest close position<br>`1`: Close position partially;`2`：Close all;`3`：Liquidation;`4`：Partial liquidation; `5`：ADL - position not fully closed; `6`：ADL - position fully closed<br>It is the latest type if there are several types for the same position. |\
| posId | String | No | Position ID. There is attribute expiration. The posId will be expired if it is more than 30 days after the last full close position, then position will use new posId. |\
| after | String | No | Pagination of data to return records earlier than the requested `uTime`, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| before | String | No | Pagination of data to return records newer than the requested `uTime`, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| limit | String | No | Number of results per request. The maximum is 100. The default is 100. All records that have the same `uTime` will be returned at the current request |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "cTime": "1654177169995",\
            "ccy": "BTC",\
            "closeAvgPx": "29786.5999999789081085",\
            "closeTotalPos": "1",\
            "instId": "BTC-USD-SWAP",\
            "instType": "SWAP",\
            "lever": "10.0",\
            "mgnMode": "cross",\
            "openAvgPx": "29783.8999999995535393",\
            "openMaxPos": "1",\
            "realizedPnl": "0.001",\
            "fee": "-0.0001",\
            "fundingFee": "0",\
            "liqPenalty": "0",\
            "pnl": "0.0011",\
            "pnlRatio": "0.000906447858888",\
            "posId": "452587086133239818",\
            "posSide": "long",\
            "direction": "long",\
            "triggerPx": "",\
            "type": "1",\
            "uTime": "1654177174419",\
            "uly": "BTC-USD",\
            "nonSettleAvgPx":"",\
            "settledPnl":""\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| instType | String | Instrument type<br>`MARGIN`<br>`SWAP`<br>`FUTURES`<br>`OPTION`<br>`EVENTS` |\
| instId | String | Instrument ID |\
| mgnMode | String | Margin mode<br>`cross``isolated` |\
| type | String | The type of latest close position<br>`1`：Close position partially;`2`：Close all;`3`：Liquidation;`4`：Partial liquidation; `5`：ADL; <br>It is the latest type if there are several types for the same position. |\
| cTime | String | Created time of position |\
| uTime | String | Updated time of position |\
| openAvgPx | String | Average price of opening position<br>Under cross-margin mode, the entry price of expiry futures will update at settlement to the last settlement price, and when the position is opened or increased. |\
| nonSettleAvgPx | String | Non-settlement entry price<br>The non-settlement entry price only reflects the average price at which the position is opened or increased.<br>Only applicable to `cross``FUTURES` |\
| closeAvgPx | String | Average price of closing position |\
| posId | String | Position ID |\
| openMaxPos | String | Max quantity of position |\
| closeTotalPos | String | Position's cumulative closed volume |\
| realizedPnl | String | Realized profit and loss<br>Only applicable to `FUTURES`/`SWAP`/`OPTION`<br>`realizedPnl`=`pnl`+`fee`+`fundingFee`+`liqPenalty`+`settledPnl` |\
| settledPnl | String | Accumulated settled profit and loss (calculated by settlement price)<br>Only applicable to `cross``FUTURES` |\
| pnlRatio | String | Realized P&L ratio |\
| fee | String | Accumulated fee<br>Negative number represents the user transaction fee charged by the platform.Positive number represents rebate. |\
| fundingFee | String | Accumulated funding fee |\
| liqPenalty | String | Accumulated liquidation penalty. It is negative when there is a value. |\
| pnl | String | Profit and loss (excluding the fee). |\
| posSide | String | Position mode side<br>`long`: Hedge mode long<br>`short`: Hedge mode short<br>`net`: Net mode |\
| lever | String | Leverage |\
| direction | String | Direction: `long``short`<br>Only applicable to `MARGIN/FUTURES/SWAP/OPTION` |\
| triggerPx | String | trigger mark price. There is value when `type` is equal to `3`, `4` or `5`. It is "" when `type` is equal to `1` or `2` |\
| uly | String | Underlying |\
| ccy | String | Currency used for margin |\
\
### Get account and position risk\
\
Get account and position risk\
\
#### Rate Limit: 10 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/account-position-risk`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/account-position-risk\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get account and position risk\
result = accountAPI.get_account_position_risk()\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| instType | String | No | Instrument type<br>`MARGIN`<br>`SWAP`<br>`FUTURES`<br>`OPTION` |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code":"0",\
    "data":[\
        {\
            "adjEq":"174238.6793649711331679",\
            "balData":[\
                {\
                    "ccy":"BTC",\
                    "disEq":"78846.7803721021362242",\
                    "eq":"1.3863533369419636"\
                },\
                {\
                    "ccy":"USDT",\
                    "disEq":"73417.2495112863300127",\
                    "eq":"73323.395564963177146"\
                }\
            ],\
            "posData":[\
                {\
                    "baseBal": "0.4",\
                    "ccy": "",\
                    "instId": "BTC-USDT",\
                    "instType": "MARGIN",\
                    "mgnMode": "isolated",\
                    "notionalCcy": "0",\
                    "notionalUsd": "0",\
                    "pos": "0",\
                    "posCcy": "",\
                    "posId": "310388685292318723",\
                    "posSide": "net",\
                    "quoteBal": "0"\
                }\
            ],\
            "ts":"1620282889345"\
        }\
    ],\
    "msg":""\
}\
```\
\
#### Response Parameters\
\
| **Parameters** | **Types** | **Description** |\
| --- | --- | --- |\
| ts | String | Update time of account information, millisecond format of Unix timestamp, e.g. `1597026383085` |\
| adjEq | String | Adjusted / Effective equity in `USD`<br>Applicable to `Multi-currency margin` and `Portfolio margin` |\
| balData | Array of objects | Detailed asset information in all currencies |\
| \> ccy | String | Currency |\
| \> eq | String | Equity of currency |\
| \> disEq | String | Discount equity of currency in `USD`. |\
| posData | Array of objects | Detailed position information in all currencies |\
| \> instType | String | Instrument type |\
| \> mgnMode | String | Margin mode<br>`cross`<br>`isolated` |\
| \> posId | String | Position ID |\
| \> instId | String | Instrument ID, e.g. `BTC-USDT-SWAP` |\
| \> pos | String | Quantity of positions `contract`. In the isolated margin mode, when doing manual transfers, a position with pos of `0` will be generated after the deposit is transferred |\
| \> baseBal | String | ~~Base currency balance, only applicable to `MARGIN`（Quick Margin Mode）~~(Deprecated) |\
| \> quoteBal | String | ~~Quote currency balance, only applicable to `MARGIN`（Quick Margin Mode）~~(Deprecated) |\
| \> posSide | String | Position side<br>`long`<br>`short`<br>`net` (`FUTURES`/`SWAP`/`OPTION`: positive `pos` means long position and negative `pos` means short position. `MARGIN`: `posCcy` being base currency means long position, `posCcy` being quote currency means short position.) |\
| \> posCcy | String | Position currency, only applicable to `MARGIN` positions. |\
| \> ccy | String | Currency used for margin |\
| \> notionalCcy | String | Notional value of positions in `coin` |\
| \> notionalUsd | String | Notional value of positions in `USD` |\
\
### Get bills details (last 7 days)\
\
Retrieve the bills of the account. The bill refers to all transaction records that result in changing the balance of an account. Pagination is supported, and the response is sorted with the most recent first. This endpoint can retrieve data from the last 7 days.\
\
#### Rate Limit: 5 requests per second\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/bills`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/bills\
\
GET /api/v5/account/bills?instType=MARGIN\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get bills details (last 7 days)\
result = accountAPI.get_account_bills()\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| instType | String | No | Instrument type<br>`SPOT`<br>`MARGIN`<br>`SWAP`<br>`FUTURES`<br>`OPTION`<br>`EVENTS` |\
| instId | String | No | Instrument ID, e.g. `BTC-USDT` |\
| ccy | String | No | Bill currency |\
| mgnMode | String | No | Margin mode<br>`isolated`<br>`cross` |\
| ctType | String | No | Contract type<br>`linear`<br>`inverse`<br>Only applicable to `FUTURES`/`SWAP` |\
| type | String | No | Bill type<br> Please refer to [Get bill types](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-bill-types) for the list of available types. |\
| subType | String | No | Bill subtype<br>Please refer to [Get bill types](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-bill-types) for the list of available types. |\
| after | String | No | Pagination of data to return records earlier than the requested bill ID. |\
| before | String | No | Pagination of data to return records newer than the requested bill ID. |\
| begin | String | No | Filter with a begin timestamp `ts`. Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| end | String | No | Filter with an end timestamp `ts`. Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| limit | String | No | Number of results per request. The maximum is `100`. The default is `100`. |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "msg": "",\
    "data": [{\
        "bal": "8694.2179403378290202",\
        "balChg": "0.0219338232210000",\
        "billId": "623950854533513219",\
        "ccy": "USDT",\
        "clOrdId": "",\
        "earnAmt": "",\
        "earnApr": "",\
        "execType": "T",\
        "fee": "-0.000021955779",\
        "fillFwdPx": "",\
        "fillIdxPx": "27104.1",\
        "fillMarkPx": "",\
        "fillMarkVol": "",\
        "fillPxUsd": "",\
        "fillPxVol": "",\
        "fillTime": "1695033476166",\
        "from": "",\
        "instId": "BTC-USDT",\
        "instType": "SPOT",\
        "interest": "0",\
        "mgnMode": "isolated",\
        "notes": "",\
        "ordId": "623950854525124608",\
        "pnl": "0",\
        "posBal": "0",\
        "posBalChg": "0",\
        "px": "27105.9",\
        "subType": "1",\
        "sz": "0.021955779",\
        "tag": "",\
        "to": "",\
        "tradeId": "586760148",\
        "ts": "1695033476167",\
        "type": "2"\
    }]\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| instType | String | Instrument type |\
| billId | String | Bill ID |\
| type | String | Bill type |\
| subType | String | Bill subtype |\
| ts | String | The time when the balance complete update, Unix timestamp format in milliseconds, e.g.`1597026383085` |\
| balChg | String | Signed change in account balance for this event, in the currency specified by the `ccy` field. Positive: balance increased (e.g., received funding fee rebate, closed profitable trade). Negative: balance decreased (e.g., paid trading fee, settled a loss). |\
| posBalChg | String | Change in balance amount at the position level |\
| bal | String | Balance at the account level |\
| posBal | String | Balance at the position level |\
| sz | String | Quantity<br>For `FUTURES`/`SWAP`/`OPTION`, it is fill quantity or position quantity, the unit is contract. The value is always positive.<br>For other scenarios. the unit is account balance currency(`ccy`). |\
| px | String | Price which related to subType<br>Trade filled price for<br>`1`: Buy `2`: Sell `3`: Open long `4`: Open short `5`: Close long `6`: Close short `204`: block trade buy `205`: block trade sell `206`: block trade open long `207`: block trade open short `208`: block trade close long `209`: block trade close short `114`: Forced repayment buy `115`: Forced repayment sell<br>Liquidation Price for<br>`100`: Partial liquidation close long `101`: Partial liquidation close short `102`: Partial liquidation buy `103`: Partial liquidation sell `104`: Liquidation long `105`: Liquidation short `106`: Liquidation buy `107`: Liquidation sell `16`: Repay forcibly `17`: Repay interest by borrowing forcibly `110`: Liquidation transfer in `111`: Liquidation transfer out<br>Delivery price for<br>`112`: Delivery long `113`: Delivery short<br>Exercise price for<br>`170`: Exercised `171`: Counterparty exercised `172`: Expired OTM<br>Mark price for<br>`173`: Funding fee expense `174`: Funding fee income |\
| ccy | String | Account balance currency |\
| pnl | String | Profit and loss |\
| fee | String | Fee<br>Negative number represents the user transaction fee charged by the platform.<br>Positive number represents rebate.<br>[Trading fee rule](https://www.okx.com/en/fees) |\
| earnAmt | String | Auto earn amount<br> Only applicable when type is 381 |\
| earnApr | String | Auto earn APR<br> Only applicable when type is 381 |\
| mgnMode | String | Margin mode<br>`isolated``cross``cash`<br>When bills are not generated by trading, the field returns "" |\
| instId | String | Instrument ID, e.g. `BTC-USDT` |\
| ordId | String | Order ID<br>Return order ID when the type is `2`/`5`/`9`<br>Return "" when there is no order. |\
| execType | String | Liquidity taker or maker<br>`T`: taker<br>`M`: maker |\
| from | String | The remitting account<br>`6`: Funding account<br>`18`: Trading account<br>Only applicable to `transfer`. When bill type is not `transfer`, the field returns "". |\
| to | String | The beneficiary account<br>`6`: Funding account<br>`18`: Trading account<br>Only applicable to `transfer`. When bill type is not `transfer`, the field returns "". |\
| notes | String | Notes |\
| interest | String | Interest |\
| tag | String | Order tag |\
| fillTime | String | Last filled time |\
| tradeId | String | Last traded ID |\
| clOrdId | String | Client Order ID as assigned by the client<br>A combination of case-sensitive alphanumerics, all numbers, or all letters of up to 32 characters. |\
| fillIdxPx | String | Index price at the moment of trade execution<br>For cross currency spot pairs, it returns baseCcy-USDT index price. For example, for LTC-ETH, this field returns the index price of LTC-USDT. |\
| fillMarkPx | String | Mark price when filled<br>Applicable to FUTURES/SWAP/OPTIONS, return "" for other instrument types |\
| fillPxVol | String | Implied volatility when filled<br>Only applicable to options; return "" for other instrument types |\
| fillPxUsd | String | Options price when filled, in the unit of USD<br>Only applicable to options; return "" for other instrument types |\
| fillMarkVol | String | Mark volatility when filled<br>Only applicable to options; return "" for other instrument types |\
| fillFwdPx | String | Forward price when filled<br>Only applicable to options; return "" for other instrument types |\
\
### Get bills details (last 3 months)\
\
Retrieve the account’s bills. The bill refers to all transaction records that result in changing the balance of an account. Pagination is supported, and the response is sorted with most recent first. This endpoint can retrieve data from the last 3 months.\
\
#### Rate Limit: 5 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/bills-archive`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/bills-archive\
\
GET /api/v5/account/bills-archive?instType=MARGIN\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get bills details (last 3 months)\
result = accountAPI.get_account_bills_archive()\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| instType | String | No | Instrument type<br>`SPOT`<br>`MARGIN`<br>`SWAP`<br>`FUTURES`<br>`OPTION`<br>`EVENTS` |\
| instId | String | No | Instrument ID, e.g. `BTC-USDT` |\
| ccy | String | No | Bill currency |\
| mgnMode | String | No | Margin mode<br>`isolated`<br>`cross` |\
| ctType | String | No | Contract type<br>`linear`<br>`inverse`<br>Only applicable to `FUTURES`/`SWAP` |\
| type | String | No | Bill type<br> Please refer to [Get bill types](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-bill-types) for the list of available types. |\
| subType | String | No | Bill subtype<br>Please refer to [Get bill types](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-bill-types) for the list of available types. |\
| after | String | No | Pagination of data to return records earlier than the requested bill ID. |\
| before | String | No | Pagination of data to return records newer than the requested bill ID. |\
| begin | String | No | Filter with a begin timestamp `ts`. Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| end | String | No | Filter with an end timestamp `ts`. Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| limit | String | No | Number of results per request. The maximum is `100`. The default is `100`. |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "msg": "",\
    "data": [{\
        "bal": "8694.2179403378290202",\
        "balChg": "0.0219338232210000",\
        "billId": "623950854533513219",\
        "ccy": "USDT",\
        "clOrdId": "",\
        "earnAmt": "",\
        "earnApr": "",\
        "execType": "T",\
        "fee": "-0.000021955779",\
        "fillFwdPx": "",\
        "fillIdxPx": "27104.1",\
        "fillMarkPx": "",\
        "fillMarkVol": "",\
        "fillPxUsd": "",\
        "fillPxVol": "",\
        "fillTime": "1695033476166",\
        "from": "",\
        "instId": "BTC-USDT",\
        "instType": "SPOT",\
        "interest": "0",\
        "mgnMode": "isolated",\
        "notes": "",\
        "ordId": "623950854525124608",\
        "pnl": "0",\
        "posBal": "0",\
        "posBalChg": "0",\
        "px": "27105.9",\
        "subType": "1",\
        "sz": "0.021955779",\
        "tag": "",\
        "to": "",\
        "tradeId": "586760148",\
        "ts": "1695033476167",\
        "type": "2"\
    }]\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| instType | String | Instrument type |\
| billId | String | Bill ID |\
| type | String | Bill type |\
| subType | String | Bill subtype |\
| ts | String | The time when the balance complete update, Unix timestamp format in milliseconds, e.g.`1597026383085` |\
| balChg | String | Change in balance amount at the account level |\
| posBalChg | String | Change in balance amount at the position level |\
| bal | String | Balance at the account level |\
| posBal | String | Balance at the position level |\
| sz | String | Quantity<br>For `FUTURES`/`SWAP`/`OPTION`, it is fill quantity or position quantity, the unit is contract. The value is always positive.<br>For other scenarios. the unit is account balance currency(`ccy`). |\
| px | String | Price which related to subType<br>Trade filled price for<br>`1`: Buy `2`: Sell `3`: Open long `4`: Open short `5`: Close long `6`: Close short `204`: block trade buy `205`: block trade sell `206`: block trade open long `207`: block trade open short `208`: block trade close long `209`: block trade close short `114`: Forced repayment buy `115`: Forced repayment sell<br>Liquidation Price for<br>`100`: Partial liquidation close long `101`: Partial liquidation close short `102`: Partial liquidation buy `103`: Partial liquidation sell `104`: Liquidation long `105`: Liquidation short `106`: Liquidation buy `107`: Liquidation sell `16`: Repay forcibly `17`: Repay interest by borrowing forcibly `110`: Liquidation transfer in `111`: Liquidation transfer out<br>Delivery price for<br>`112`: Delivery long `113`: Delivery short<br>Exercise price for<br>`170`: Exercised `171`: Counterparty exercised `172`: Expired OTM<br>Mark price for<br>`173`: Funding fee expense `174`: Funding fee income |\
| ccy | String | Account balance currency |\
| pnl | String | Profit and loss |\
| fee | String | Fee<br>Negative number represents the user transaction fee charged by the platform. <br>Positive number represents rebate.<br>[Trading fee rule](https://www.okx.com/en/fees) |\
| earnAmt | String | Auto earn amount<br> Only applicable when type is 381 |\
| earnApr | String | Auto earn APR<br> Only applicable when type is 381 |\
| mgnMode | String | Margin mode<br>`isolated``cross``cash`<br>When bills are not generated by trading, the field returns "" |\
| instId | String | Instrument ID, e.g. `BTC-USDT` |\
| ordId | String | Order ID<br>Return order ID when the type is `2`/`5`/`9`<br>Return "" when there is no order. |\
| execType | String | Liquidity taker or maker<br>`T`: taker `M`: maker |\
| from | String | The remitting account<br>`6`: Funding account<br>`18`: Trading account<br>Only applicable to `transfer`. When bill type is not `transfer`, the field returns "". |\
| to | String | The beneficiary account<br>`6`: Funding account<br>`18`: Trading account<br>Only applicable to `transfer`. When bill type is not `transfer`, the field returns "". |\
| notes | String | Notes |\
| interest | String | Interest |\
| tag | String | Order tag |\
| fillTime | String | Last filled time |\
| tradeId | String | Last traded ID |\
| clOrdId | String | Client Order ID as assigned by the client <br>A combination of case-sensitive alphanumerics, all numbers, or all letters of up to 32 characters. |\
| fillIdxPx | String | Index price at the moment of trade execution <br>For cross currency spot pairs, it returns baseCcy-USDT index price. For example, for LTC-ETH, this field returns the index price of LTC-USDT. |\
| fillMarkPx | String | Mark price when filled <br>Applicable to FUTURES/SWAP/OPTIONS, return "" for other instrument types |\
| fillPxVol | String | Implied volatility when filled <br>Only applicable to options; return "" for other instrument types |\
| fillPxUsd | String | Options price when filled, in the unit of USD <br>Only applicable to options; return "" for other instrument types |\
| fillMarkVol | String | Mark volatility when filled <br>Only applicable to options; return "" for other instrument types |\
| fillFwdPx | String | Forward price when filled <br>Only applicable to options; return "" for other instrument types |\
\
### Apply bills details (since 2021)\
\
Apply for bill data since 1 February, 2021 except for the current quarter.\
\
#### Rate Limit: 12 requests per day\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`POST /api/v5/account/bills-history-archive`\
\
> Request Example\
\
```\
Copy to Clipboard\
POST /api/v5/account/bills-history-archive\
body\
{\
    "year":"2023",\
    "quarter":"Q1"\
}\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| year | String | Yes | 4 digits year |\
| quarter | String | Yes | Quarter, valid value is `Q1`, `Q2`, `Q3`, `Q4` |\
| type | String | No | Bill type. Multiple values are supported, separated by commas, e.g. `1,2,3`. If not specified, all types are returned.<br>Please refer to [Get bill types](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-bill-types) for the list of available types. |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "result": "true",\
            "ts": "1646892328000"\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| result | String | Whether there is already a download link for this section <br>`true`: Existed, can check from "Get bills details (since 2021)". <br>`false`: Does not exist and is generating, can check the download link after 2 hours<br> The data of file is in reverse chronological order using `billId`. |\
| ts | String | The first request time when the server receives. Unix timestamp format in milliseconds, e.g. `1597026383085` |\
\
### Get bills details (since 2021)\
\
Apply for bill data since 1 February, 2021 except for the current quarter.\
\
#### Rate Limit: 10 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/bills-history-archive`\
\
> Response Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/bills-history-archive?year=2023&quarter=Q4\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| year | String | Yes | 4 digits year |\
| quarter | String | Yes | Quarter, valid value is `Q1`, `Q2`, `Q3`, `Q4` |\
| type | String | No | Bill type. Multiple values are supported, separated by commas, e.g. `1,2,3`. If not specified, all types are returned.<br>Please refer to [Get bill types](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-bill-types) for the list of available types. |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "fileHref": "http://xxx",\
            "state": "finished",\
            "ts": "1646892328000"\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| fileHref | String | Download file link. <br>The expiration of every link is 5 and a half hours. If you already apply the files for the same quarter, then it don’t need to apply again within 30 days. |\
| ts | String | The first request time when the server receives. Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| state | String | Download link status <br>"finished" "ongoing" "failed": Failed, please apply again |\
\
#### Field descriptions in the decompressed CSV file\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| instType | String | Instrument type |\
| billId | String | Bill ID |\
| subType | String | Bill subtype |\
| ts | String | The time when the balance complete update, Unix timestamp format in milliseconds, e.g.`1597026383085` |\
| balChg | String | Change in balance amount at the account level |\
| posBalChg | String | Change in balance amount at the position level |\
| bal | String | Balance at the account level |\
| posBal | String | Balance at the position level |\
| sz | String | Quantity |\
| px | String | Price which related to subType<br>Trade filled price for<br>`1`: Buy `2`: Sell `3`: Open long `4`: Open short `5`: Close long `6`: Close short `204`: block trade buy `205`: block trade sell `206`: block trade open long `207`: block trade open short `208`: block trade close long `209`: block trade close short `114`: Forced repayment buy `115`: Forced repayment sell<br>Liquidation Price for<br>`100`: Partial liquidation close long `101`: Partial liquidation close short `102`: Partial liquidation buy `103`: Partial liquidation sell `104`: Liquidation long `105`: Liquidation short `106`: Liquidation buy `107`: Liquidation sell `16`: Repay forcibly `17`: Repay interest by borrowing forcibly `110`: Liquidation transfer in `111`: Liquidation transfer out<br>Delivery price for<br>`112`: Delivery long `113`: Delivery short<br>Exercise price for<br>`170`: Exercised `171`: Counterparty exercised `172`: Expired OTM<br>Mark price for<br>`173`: Funding fee expense `174`: Funding fee income |\
| ccy | String | Account balance currency |\
| pnl | String | Profit and loss |\
| fee | String | Fee<br>Negative number represents the user transaction fee charged by the platform. <br>Positive number represents rebate.<br>[Trading fee rule](https://www.okx.com/en/fees) |\
| mgnMode | String | Margin mode<br>`isolated``cross``cash`<br>When bills are not generated by trading, the field returns "" |\
| instId | String | Instrument ID, e.g. `BTC-USDT` |\
| ordId | String | Order ID<br>Return order ID when the type is `2`/`5`/`9`<br>Return "" when there is no order. |\
| execType | String | Liquidity taker or maker<br>`T`: taker `M`: maker |\
| interest | String | Interest |\
| tag | String | Order tag |\
| fillTime | String | Last filled time |\
| tradeId | String | Last traded ID |\
| clOrdId | String | Client Order ID as assigned by the client <br>A combination of case-sensitive alphanumerics, all numbers, or all letters of up to 32 characters. |\
| fillIdxPx | String | Index price at the moment of trade execution <br>For cross currency spot pairs, it returns baseCcy-USDT index price. For example, for LTC-ETH, this field returns the index price of LTC-USDT. |\
| fillMarkPx | String | Mark price when filled <br>Applicable to FUTURES/SWAP/OPTIONS, return "" for other instrument types |\
| fillPxVol | String | Implied volatility when filled <br>Only applicable to options; return "" for other instrument types |\
| fillPxUsd | String | Options price when filled, in the unit of USD <br>Only applicable to options; return "" for other instrument types |\
| fillMarkVol | String | Mark volatility when filled <br>Only applicable to options; return "" for other instrument types |\
| fillFwdPx | String | Forward price when filled <br>Only applicable to options; return "" for other instrument types |\
\
### Get bill types\
\
Get all bill types, and the mapping of bill type and subType.\
\
#### Rate limit: 20 requests per 2 seconds\
\
#### Rate limit rule: UserId\
\
#### HTTP request\
\
`GET /api/v5/account/subtypes`\
\
> Request example\
\
```\
Copy to Clipboard\
GET /api/v5/account/subtypes\
```\
\
#### Request parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| type | String | No | Bill type. Multiple values are supported, separated by commas, e.g. `1,2,3`. If not specified, all types are returned. |\
\
> Response example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "type": "1",\
            "typeDesc": "Transfer",\
            "subTypeDetails": [\
                {\
                    "subType": "11",\
                    "subTypeDesc": "Transfer in"\
                },\
                {\
                    "subType": "12",\
                    "subTypeDesc": "Transfer out"\
                }\
            ]\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| type | String | Bill type |\
| typeDesc | String | Bill type description, "" means the type is not enabled. |\
| subTypeDetails | Array of objects | Sub-type details |\
| \> subType | String | Sub-type |\
| \> subTypeDesc | String | Sub-type description, "" means the type is not enabled. |\
\
### Get account configuration\
\
Retrieve current account configuration.\
\
#### Rate Limit: 5 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/config`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/config\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Retrieve current account configuration\
result = accountAPI.get_account_config()\
print(result)\
```\
\
#### Request Parameters\
\
none\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "acctLv": "2",\
            "acctStpMode": "cancel_maker",\
            "autoLoan": false,\
            "ctIsoMode": "automatic",\
            "enableSpotBorrow": false,\
            "greeksType": "PA",\
            "feeType": "0",\
            "ip": "",\
            "type": "0",\
            "kycLv": "3",\
            "label": "v5 test",\
            "level": "Lv1",\
            "levelTmp": "",\
            "liquidationGear": "-1",\
            "mainUid": "44705892343619584",\
            "mgnIsoMode": "automatic",\
            "opAuth": "1",\
            "perm": "read_only,withdraw,trade",\
            "posMode": "long_short_mode",\
            "roleType": "0",\
            "spotBorrowAutoRepay": false,\
            "spotOffsetType": "",\
            "spotRoleType": "0",\
            "spotTraderInsts": [],\
            "stgyType": "0",\
            "traderInsts": [],\
            "uid": "44705892343619584",\
            "settleCcy": "USDC",\
            "settleCcyList": ["USD", "USDC", "USDG"]\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| uid | String | Account ID of current request. |\
| mainUid | String | Main Account ID of current request. <br>The current request account is main account if uid = mainUid.<br>The current request account is sub-account if uid != mainUid. |\
| acctLv | String | Account mode <br>`1`: Spot mode<br>`2`: Futures mode<br>`3`: Multi-currency margin<br>`4`: Portfolio margin |\
| acctStpMode | String | Account self-trade prevention mode <br>`cancel_maker`<br>`cancel_taker`<br>`cancel_both`<br>The default value is `cancel_maker`. Users can log in to the webpage through the master account to modify this configuration |\
| posMode | String | Position mode<br>`long_short_mode`: long/short, only applicable to `FUTURES`/`SWAP`<br>`net_mode`: net |\
| autoLoan | Boolean | Whether to borrow coins automatically<br>`true`: borrow coins automatically<br>`false`: not borrow coins automatically |\
| greeksType | String | Current display type of Greeks<br>`PA`: Greeks in coins<br>`BS`: Black-Scholes Greeks in dollars |\
| feeType | String | Fee type<br>`0`: fee is charged in the currency you receive from the trade<br>`1`: fee is always charged in the quote currency of the trading pair |\
| level | String | The user level of the current real trading volume on the platform, e.g `Lv1`, which means regular user level. |\
| levelTmp | String | Temporary experience user level of special users, e.g `Lv1` |\
| ctIsoMode | String | Contract isolated margin trading settings<br>`automatic`: Auto transfers<br>`autonomy`: Manual transfers |\
| mgnIsoMode | String | Margin isolated margin trading settings<br>`auto_transfers_ccy`: New auto transfers, enabling both base and quote currency as the margin for isolated margin trading<br>`automatic`: Auto transfers<br>`quick_margin`: Quick Margin Mode (For new accounts, including subaccounts, some defaults will be `automatic`, and others will be `quick_margin`) |\
| spotOffsetType | String | ~~Risk offset type<br>`1`: Spot-Derivatives(USDT) to be offsetted<br>`2`: Spot-Derivatives(Coin) to be offsetted<br>`3`: Only derivatives to be offsetted<br>Only applicable to `Portfolio margin`~~<br>(Deprecated) |\
| stgyType | String | Strategy type<br>`0`: general strategy<br>`1`: delta neutral strategy |\
| roleType | String | Role type<br>`0`: General user<br>`1`: Leading trader<br>`2`: Copy trader |\
| traderInsts | Array of strings | Leading trade instruments, only applicable to Leading trader |\
| spotRoleType | String | SPOT copy trading role type.<br>`0`: General user；`1`: Leading trader；`2`: Copy trader |\
| spotTraderInsts | Array of strings | Spot lead trading instruments, only applicable to lead trader |\
| opAuth | String | Whether the optional trading was activated<br>`0`: not activate<br>`1`: activated |\
| kycLv | String | Main account KYC level<br>`0`: No verification<br>`1`: level 1 completed<br>`2`: level 2 completed<br>`3`: level 3 completed<br>If the request originates from a subaccount, kycLv is the KYC level of the main account. <br>If the request originates from the main account, kycLv is the KYC level of the current account. |\
| label | String | API key note of current request API key. No more than 50 letters (case sensitive) or numbers, which can be pure letters or pure numbers. |\
| ip | String | IP addresses that linked with current API key, separate with commas if more than one, e.g. `117.37.203.58,117.37.203.57`. It is an empty string "" if there is no IP bonded. |\
| perm | String | The permission of the current requesting API key or Access token<br>`read_only`: Read<br>`trade`: Trade<br>`withdraw`: Withdraw |\
| liquidationGear | String | The maintenance margin ratio level of liquidation alert<br>`3` and `-1` means that you will get hourly liquidation alerts on app and channel "Position risk warning" when your margin level drops to or below 300%. `-1` is the initial value which has the same effect as `-3`<br>`0` means that there is not alert |\
| enableSpotBorrow | Boolean | Whether borrow is allowed or not in `Spot mode`<br>`true`: Enabled<br>`false`: Disabled |\
| spotBorrowAutoRepay | Boolean | Whether auto-repay is allowed or not in `Spot mode`<br>`true`: Enabled<br>`false`: Disabled |\
| type | String | Account type <br>`0`: Main account <br>`1`: Standard sub-account <br>`2`: Managed trading sub-account <br>`5`: Custody trading sub-account - Copper<br>`9`: Managed trading sub-account - Copper<br>`12`: Custody trading sub-account - Komainu |\
| settleCcy | String | Current account's USD-margined contract settle currency |\
| settleCcyList | String | Current account's USD-margined contract settle currency list, like \["USD", "USDC", "USDG"\]. |\
\
### Set position mode\
\
Futures mode and Multi-currency mode: `FUTURES` and `SWAP` support both `long/short` mode and `net` mode. In `net` mode, users can only have positions in one direction; In `long/short` mode, users can hold positions in long and short directions.\
\
Portfolio margin mode: `FUTURES` and `SWAP` only support `net` mode\
\
#### Rate Limit: 5 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`POST /api/v5/account/set-position-mode`\
\
> Request Example\
\
```\
Copy to Clipboard\
POST /api/v5/account/set-position-mode\
body\
{\
    "posMode":"long_short_mode"\
}\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Set position mode\
result = accountAPI.set_position_mode(\
    posMode="long_short_mode"\
)\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| posMode | String | Yes | Position mode<br>`long_short_mode`: long/short, only applicable to `FUTURES`/`SWAP`<br>`net_mode`: net |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "msg": "",\
    "data": [{\
        "posMode": "long_short_mode"\
    }]\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| posMode | String | Position mode |\
\
### Set leverage\
\
There are 10 different scenarios for leverage setting:\
\
1\. Set leverage for `MARGIN` instruments under `isolated-margin` trade mode at pairs level.\
\
2\. Set leverage for `MARGIN` instruments under `cross-margin` trade mode and Spot mode (enabled borrow) at currency level.\
\
3\. Set leverage for `MARGIN` instruments under `cross-margin` trade mode and Futures mode account mode at pairs level.\
\
4\. Set leverage for `MARGIN` instruments under `cross-margin` trade mode and Multi-currency margin at currency level.\
\
5\. Set leverage for `MARGIN` instruments under `cross-margin` trade mode and Portfolio margin at currency level.\
\
6\. Set leverage for `FUTURES` instruments under `cross-margin` trade mode at underlying level.\
\
7\. Set leverage for `FUTURES` instruments under `isolated-margin` trade mode and buy/sell position mode at contract level.\
\
8\. Set leverage for `FUTURES` instruments under `isolated-margin` trade mode and long/short position mode at contract and position side level.\
\
9\. Set leverage for `SWAP` instruments under `cross-margin` trade at contract level.\
\
10\. Set leverage for `SWAP` instruments under `isolated-margin` trade mode and buy/sell position mode at contract level.\
\
11\. Set leverage for `SWAP` instruments under `isolated-margin` trade mode and long/short position mode at contract and position side level.\
\
Note that the request parameter `posSide` is only required when margin mode is isolated in long/short position mode for FUTURES/SWAP instruments (see scenario 8 and 11 above).\
\
Please refer to the request examples on the right for each case.\
\
#### Rate limit: 20 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`POST /api/v5/account/set-leverage`\
\
> Request Example\
\
```\
Copy to Clipboard\
# 1. Set leverage for `MARGIN` instruments under `isolated-margin` trade mode at pairs level.\
POST /api/v5/account/set-leverage\
body\
{\
    "instId":"BTC-USDT",\
    "lever":"5",\
    "mgnMode":"isolated"\
}\
\
# 2. Set leverage for `MARGIN` instruments under `cross-margin` trade mode and Spot mode (enabled borrow) at currency level.\
POST /api/v5/account/set-leverage\
body\
{\
    "ccy":"BTC",\
    "lever":"5",\
    "mgnMode":"cross"\
}\
\
# 3. Set leverage for `MARGIN` instruments under `cross-margin` trade mode and Futures mode account mode at pairs level.\
POST /api/v5/account/set-leverage\
body\
{\
    "instId":"BTC-USDT",\
    "lever":"5",\
    "mgnMode":"cross"\
}\
\
# 4. Set leverage for `MARGIN` instruments under `cross-margin` trade mode and Multi-currency margin at currency level.\
POST /api/v5/account/set-leverage\
body\
{\
    "ccy":"BTC",\
    "lever":"5",\
    "mgnMode":"cross"\
}\
\
# 5. Set leverage for `MARGIN` instruments under `cross-margin` trade mode and Portfolio margin at currency level.\
POST /api/v5/account/set-leverage\
body\
{\
    "ccy":"BTC",\
    "lever":"5",\
    "mgnMode":"cross"\
}\
\
# 6. Set leverage for `FUTURES` instruments under `cross-margin` trade mode at underlying level.\
POST /api/v5/account/set-leverage\
body\
{\
    "instId":"BTC-USDT-200802",\
    "lever":"5",\
    "mgnMode":"cross"\
}\
\
# 7. Set leverage for `FUTURES` instruments under `isolated-margin` trade mode and buy/sell order placement mode at contract level.\
POST /api/v5/account/set-leverage\
body\
{\
    "instId":"BTC-USDT-200802",\
    "lever":"5",\
    "mgnMode":"isolated"\
}\
\
# 8. Set leverage for `FUTURES` instruments under `isolated-margin` trade mode and long/short order placement mode at contract and position side level.\
POST /api/v5/account/set-leverage\
body\
{\
    "instId":"BTC-USDT-200802",\
    "lever":"5",\
    "posSide":"long",\
    "mgnMode":"isolated"\
}\
\
# 9. Set leverage for `SWAP` instruments under `cross-margin` trade at contract level.\
POST /api/v5/account/set-leverage\
body\
{\
    "instId":"BTC-USDT-SWAP",\
    "lever":"5",\
    "mgnMode":"cross"\
}\
\
# 10. Set leverage for `SWAP` instruments under `isolated-margin` trade mode and buy/sell order placement mode at contract level.\
POST /api/v5/account/set-leverage\
body\
{\
    "instId":"BTC-USDT-SWAP",\
    "lever":"5",\
    "mgnMode":"isolated"\
}\
\
# 11. Set leverage for `SWAP` instruments under `isolated-margin` trade mode and long/short order placement mode at contract and position side level.\
POST /api/v5/account/set-leverage\
body\
{\
    "instId":"BTC-USDT-SWAP",\
    "lever":"5",\
    "posSide":"long",\
    "mgnMode":"isolated"\
}\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Set leverage for MARGIN instruments under isolated-margin trade mode at pairs level.\
result = accountAPI.set_leverage(\
    instId="BTC-USDT",\
    lever="5",\
    mgnMode="isolated"\
)\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| instId | String | Conditional | Instrument ID<br> Only applicable to `cross``FUTURES``SWAP` of `Spot mode`/`Multi-currency margin`/`Portfolio margin`, `cross``MARGIN``FUTURES``SWAP` and `isolated` position.<br> And required in applicable scenarios. |\
| ccy | String | Conditional | Currency used for margin, used for the leverage setting for the currency in auto borrow.<br>Only applicable to `cross``MARGIN` of `Spot mode`/`Multi-currency margin`/`Portfolio margin`.<br> And required in applicable scenarios. |\
| lever | String | Yes | Leverage |\
| mgnMode | String | Yes | Margin mode<br>`isolated``cross`<br>Can only be `cross` if `ccy` is passed. |\
| posSide | String | Conditional | Position side<br>`long``short`<br>Only required when margin mode is `isolated` in `long/short` mode for `FUTURES`/`SWAP`. |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
  "code": "0",\
  "msg": "",\
  "data": [\
    {\
      "lever": "30",\
      "mgnMode": "isolated",\
      "instId": "BTC-USDT-SWAP",\
      "posSide": "long"\
    }\
  ]\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| lever | String | Leverage |\
| mgnMode | String | Margin mode<br>`cross``isolated` |\
| instId | String | Instrument ID |\
| posSide | String | Position side |\
\
### Get maximum order quantity\
\
The maximum quantity to buy or sell. It corresponds to the "sz" from placement.\
\
#### Rate Limit: 20 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/max-size`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/max-size?instId=BTC-USDT&tdMode=isolated\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get maximum buy/sell amount or open amount\
result = accountAPI.get_max_order_size(\
    instId="BTC-USDT",\
    tdMode="isolated"\
)\
print(result)\
```\
\
#### Request Parameters\
\
| **Parameter** | **Type** | Required | Description |\
| --- | --- | --- | --- |\
| instId | String | Yes | Single instrument or multiple instruments (no more than 5) in the same instrument type separated with comma, e.g. `BTC-USDT,ETH-USDT` |\
| tdMode | String | Yes | Trade mode<br>`cross`<br>`isolated`<br>`cash`<br>`spot_isolated`: only applicable to `Futures mode`. |\
| ccy | String | Conditional | Currency used for margin <br>Applicable to `isolated``MARGIN` and `cross``MARGIN` orders in `Futures mode`. |\
| px | String | No | Price<br>When the price is not specified, it will be calculated according to the current limit price for `FUTURES` and `SWAP`, the last traded price for other instrument types.<br>The parameter will be ignored when multiple instruments are specified. |\
| leverage | String | No | Leverage for instrument<br>The default is current leverage<br>Only applicable to `MARGIN/FUTURES/SWAP` |\
| tradeQuoteCcy | String | No | The quote currency used for trading. Only applicable to `SPOT`. <br> The default value is the quote currency of the `instId`, for example: for `BTC-USD`, the default is `USD`. |\
| outcome | String | No | Market outcome to trade on.<br>`yes`<br>`no`<br>Only applicable and optional for `EVENTS`, the default value is `yes` |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "msg": "",\
    "data": [{\
        "ccy": "BTC",\
        "instId": "BTC-USDT",\
        "maxBuy": "0.0500695098559788",\
        "maxSell": "64.4798671570072269"\
  }]\
}\
```\
\
#### Response Parameters\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| instId | String | Instrument ID |\
| ccy | String | Currency used for margin |\
| maxBuy | String | `SPOT`/`MARGIN`: The maximum quantity in base currency that you can buy<br>The cross-margin order under `Futures mode` mode, quantity of coins is based on base currency.<br>`FUTURES`/`SWAP`/`OPTIONS`: The maximum quantity of contracts that you can buy<br>In long/short position mode, the position tier limit uses the long-side remaining for `FUTURES`/`SWAP` |\
| maxSell | String | `SPOT`/`MARGIN`: The maximum quantity in quote currency that you can sell<br>The cross-margin order under `Futures mode` mode, quantity of coins is based on base currency.<br>`FUTURES`/`SWAP`/`OPTIONS`: The maximum quantity of contracts that you can sell<br>In long/short position mode, the position tier limit uses the short-side remaining for `FUTURES`/`SWAP` |\
\
### Get maximum available balance/equity\
\
Available balance for isolated margin positions and SPOT, available equity for cross margin positions.\
\
#### Rate Limit: 20 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/max-avail-size`\
\
> Request Example\
\
```\
Copy to Clipboard\
# Query maximum available transaction amount when cross MARGIN BTC-USDT use BTC as margin\
GET /api/v5/account/max-avail-size?instId=BTC-USDT&tdMode=cross&ccy=BTC\
\
# Query maximum available transaction amount for SPOT BTC-USDT\
GET /api/v5/account/max-avail-size?instId=BTC-USDT&tdMode=cash\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get maximum available transaction amount for SPOT BTC-USDT\
result = accountAPI.get_max_avail_size(\
    instId="BTC-USDT",\
    tdMode="cash"\
)\
print(result)\
```\
\
#### Request Parameters\
\
| **Parameter** | **Type** | Required | Description |\
| --- | --- | --- | --- |\
| instId | String | Yes | Single instrument or multiple instruments (no more than 5) separated with comma, e.g. `BTC-USDT,ETH-USDT` |\
| ccy | String | Conditional | Currency used for margin<br>Applicable to `isolated``MARGIN` and `cross``MARGIN` in `Futures mode`. |\
| tdMode | String | Yes | Trade mode<br>`cross`<br>`isolated`<br>`cash`<br>`spot_isolated`: only applicable to `Futures mode` |\
| reduceOnly | Boolean | No | Whether to reduce position only <br>Only applicable to `MARGIN` |\
| px | String | No | The price of closing position. <br>Only applicable to reduceOnly `MARGIN`. |\
| tradeQuoteCcy | String | No | The quote currency used for trading. Only applicable to `SPOT`. <br> The default value is the quote currency of the `instId`, for example: for `BTC-USD`, the default is `USD`. |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
  "code": "0",\
  "msg": "",\
  "data": [\
    {\
      "instId": "BTC-USDT",\
      "availBuy": "100",\
      "availSell": "1"\
    }\
  ]\
}\
```\
\
#### Response Parameters\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| instId | String | Instrument ID |\
| availBuy | String | Maximum available balance/equity to buy.<br>In long/short position mode, the position tier limit uses the long-side remaining for `FUTURES`/`SWAP` |\
| availSell | String | Maximum available balance/equity to sell.<br>In long/short position mode, the position tier limit uses the short-side remaining for `FUTURES`/`SWAP` |\
\
### Increase/decrease margin\
\
Increase or decrease the margin of the isolated position. Margin reduction may result in the change of the actual leverage.\
\
#### Rate Limit: 20 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`POST /api/v5/account/position/margin-balance`\
\
> Request Example\
\
```\
Copy to Clipboard\
POST /api/v5/account/position/margin-balance\
body\
{\
    "instId":"BTC-USDT-200626",\
    "posSide":"short",\
    "type":"add",\
    "amt":"1"\
}\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Increase margin\
result = accountAPI.adjustment_margin(\
    instId="BTC-USDT-SWAP",\
    posSide="short",\
    type= "add",\
    amt="1"\
)\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| instId | String | Yes | Instrument ID |\
| posSide | String | Yes | Position side, the default is `net`<br>`long`<br>`short`<br>`net` |\
| type | String | Yes | `add`: add margin <br>`reduce`: reduce margin |\
| amt | String | Yes | Amount to be increased or decreased. |\
| ccy | String | Conditional | Currency <br>Applicable to `isolated``MARGIN` orders |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "msg": "",\
    "data": [{\
            "amt": "0.3",\
            "ccy": "BTC",\
            "instId": "BTC-USDT",\
            "leverage": "",\
            "posSide": "net",\
            "type": "add"\
        }]\
}\
```\
\
#### Response Parameters\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| instId | String | Instrument ID |\
| posSide | String | Position side, `long``short` |\
| amt | String | Amount to be increase or decrease |\
| type | String | `add`: add margin<br>`reduce`: reduce margin |\
| leverage | String | Real leverage after the margin adjustment |\
| ccy | String | Currency |\
\
### Get leverage\
\
#### Rate Limit: 20 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/leverage-info`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/leverage-info?instId=BTC-USDT-SWAP&mgnMode=cross\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get leverage\
result = accountAPI.get_leverage(\
    instId="BTC-USDT-SWAP",\
    mgnMode="cross"\
)\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| instId | String | Conditional | Instrument ID<br>Single instrument ID or multiple instrument IDs (no more than 20) separated with comma |\
| ccy | String | Conditional | Currency，used for getting leverage of currency level.<br>Applicable to `cross``MARGIN` of `Spot mode`/`Multi-currency margin`/`Portfolio margin`.<br>Supported single currency or multiple currencies (no more than 20) separated with comma. |\
| mgnMode | String | Yes | Margin mode<br>`cross``isolated` |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "msg": "",\
    "data": [{\
        "ccy":"",\
        "instId": "BTC-USDT-SWAP",\
        "mgnMode": "cross",\
        "posSide": "long",\
        "lever": "10"\
    },{\
        "ccy":"",\
        "instId": "BTC-USDT-SWAP",\
        "mgnMode": "cross",\
        "posSide": "short",\
        "lever": "10"\
    }]\
}\
```\
\
#### Response Parameters\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| instId | String | Instrument ID |\
| ccy | String | Currency，used for getting leverage of currency level.<br>Applicable to `cross``MARGIN` of `Spot mode`/`Multi-currency margin`/`Portfolio margin`. |\
| mgnMode | String | Margin mode |\
| posSide | String | Position side<br>`long`<br>`short`<br>`net`<br>In `long/short` mode, the leverage in both directions `long`/`short` will be returned. |\
| lever | String | Leverage |\
\
### Get leverage estimated info\
\
#### Rate Limit: 5 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/adjust-leverage-info`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/adjust-leverage-info?instType=MARGIN&mgnMode=isolated&lever=3&instId=BTC-USDT\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| instType | String | Yes | Instrument type<br>`MARGIN`<br>`SWAP`<br>`FUTURES` |\
| mgnMode | String | Yes | Margin mode<br>`isolated`<br>`cross` |\
| lever | String | Yes | Leverage |\
| instId | String | Conditional | Instrument ID, e.g. BTC-USDT<br>It is required for these scenarioes: `SWAP` and `FUTURES`, Margin isolation, Margin cross in `Futures mode`. |\
| ccy | String | Conditional | Currency used for margin, e.g. BTC<br>It is required for isolated margin and cross margin in `Futures mode`, `Multi-currency margin` and `Portfolio margin` |\
| posSide | String | No | Position side<br>`net`: The default value<br>`long`<br>`short`<br>In long/short position mode, it is recommended to specify `long` or `short` for accurate direction-specific results |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "estAvailQuoteTrans": "",\
            "estAvailTrans": "1.1398040558348279",\
            "estLiqPx": "",\
            "estMaxAmt": "10.6095865868904898",\
            "estMgn": "0.0701959441651721",\
            "estQuoteMaxAmt": "176889.6871254563042714",\
            "estQuoteMgn": "",\
            "existOrd": false,\
            "maxLever": "10",\
            "minLever": "0.01"\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| estAvailQuoteTrans | String | The estimated margin(in quote currency) can be transferred out under the corresponding leverage<br>For cross, it is the maximum quantity that can be transferred from the trading account.<br>For isolated, it is the maximum quantity that can be transferred from the isolated position<br>Only applicable to `MARGIN` |\
| estAvailTrans | String | The estimated margin can be transferred out under the corresponding leverage.<br>For cross, it is the maximum quantity that can be transferred from the trading account.<br>For isolated, it is the maximum quantity that can be transferred from the isolated position<br> The unit is base currency for `MARGIN`<br> It is not applicable to the scenario when increasing leverage for isolated position under `FUTURES` and `SWAP` |\
| estLiqPx | String | The estimated liquidation price under the corresponding leverage. Only return when there is a position. |\
| estMgn | String | The estimated margin needed by position under the corresponding leverage.<br>For the `MARGIN` position, it is margin in base currency |\
| estQuoteMgn | String | The estimated margin (in quote currency) needed by position under the corresponding leverage |\
| estMaxAmt | String | For `MARGIN`, it is the estimated maximum loan in base currency under the corresponding leverage<br>For `SWAP` and `FUTURES`, it is the estimated maximum quantity of contracts that can be opened under the corresponding leverage.<br>In long/short position mode, the position tier limit is calculated based on the direction specified by `posSide` |\
| estQuoteMaxAmt | String | The `MARGIN` estimated maximum loan in quote currency under the corresponding leverage. |\
| existOrd | Boolean | Whether there is pending orders <br>`true`<br>`false` |\
| maxLever | String | Maximum leverage |\
| minLever | String | Minimum leverage |\
\
### Get the maximum loan of instrument\
\
#### Rate Limit: 20 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/max-loan`\
\
> Request Example\
\
```\
Copy to Clipboard\
# Max loan of cross `MARGIN` for currencies of trading pair in `Spot mode` (enabled borrowing)\
GET  /api/v5/account/max-loan?instId=BTC-USDT&mgnMode=cross\
\
# Max loan for currency in `Spot mode` (enabled borrowing)\
GET  /api/v5/account/max-loan?ccy=USDT&mgnMode=cross\
\
# Max loan of isolated `MARGIN` in `Futures mode`\
GET  /api/v5/account/max-loan?instId=BTC-USDT&mgnMode=isolated\
\
# Max loan of cross `MARGIN` in `Futures mode` (Margin Currency is BTC)\
GET  /api/v5/account/max-loan?instId=BTC-USDT&mgnMode=cross&mgnCcy=BTC\
\
# Max loan of cross `MARGIN` in `Multi-currency margin`\
GET  /api/v5/account/max-loan?instId=BTC-USDT&mgnMode=cross\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Max loan of cross MARGIN in Futures mode (Margin Currency is BTC)\
result = accountAPI.get_max_loan(\
    instId="BTC-USDT",\
    mgnMode="cross",\
    mgnCcy="BTC"\
)\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| mgnMode | String | Yes | Margin mode<br>`isolated``cross` |\
| instId | String | Conditional | Single instrument or multiple instruments (no more than 5) separated with comma, e.g. `BTC-USDT,ETH-USDT` |\
| ccy | String | Conditional | Currency<br>Applicable to get Max loan of manual borrow for the currency in `Spot mode` (enabled borrowing) |\
| mgnCcy | String | Conditional | Margin currency<br>Applicable to `isolated``MARGIN` and `cross``MARGIN` in `Futures mode`. |\
| tradeQuoteCcy | String | No | The quote currency for trading. Only applicable to `SPOT`.<br>The default value is the quote currency of `instId`, e.g. `USD` for `BTC-USD`. |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
  "code": "0",\
  "msg": "",\
  "data": [\
    {\
      "instId": "BTC-USDT",\
      "mgnMode": "isolated",\
      "mgnCcy": "",\
      "maxLoan": "0.1",\
      "ccy": "BTC",\
      "side": "sell"\
    },\
    {\
      "instId": "BTC-USDT",\
      "mgnMode": "isolated",\
      "mgnCcy": "",\
      "maxLoan": "0.2",\
      "ccy": "USDT",\
      "side": "buy"\
    }\
  ]\
}\
```\
\
#### Response Parameters\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| instId | String | Instrument ID |\
| mgnMode | String | Margin mode |\
| mgnCcy | String | Margin currency |\
| maxLoan | String | Max loan |\
| ccy | String | Currency |\
| side | String | Order side<br>`buy``sell` |\
\
### Get fee rates\
\
#### Rate Limit: 5 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/trade-fee`\
\
> Request Example\
\
```\
Copy to Clipboard\
# Query trade fee rate of SPOT BTC-USDT\
GET /api/v5/account/trade-fee?instType=SPOT&instId=BTC-USDT\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get trading fee rates of current account\
result = accountAPI.get_fee_rates(\
    instType="SPOT",\
    instId="BTC-USDT"\
)\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| instType | String | Yes | Instrument type<br>`SPOT`<br>`MARGIN`<br>`SWAP`<br>`FUTURES`<br>`OPTION`<br>`EVENTS` |\
| instId | String | No | Instrument ID, e.g. `BTC-USDT`<br>Applicable to `SPOT`/`MARGIN`<br>Specifying this parameter returns the correct applicable fee rates (e.g., market maker rates for users in incentive programs). |\
| instFamily | String | No | Instrument family, e.g. `BTC-USD`<br>Applicable to `FUTURES`/`SWAP`/`OPTION` |\
| groupId | String | No | Instrument trading fee group ID<br> Only one of groupId and instId/instFamily can be passed in<br> Users can use instruments endpoint to fetch the mapping of an instrument ID and its trading fee group ID |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "category": "1",\
            "delivery": "",\
            "exercise": "",\
            "feeGroup": [\
                {\
                    "rpiMaker": "-0.0008",\
                    "groupId": "1",\
                    "maker": "-0.0008",\
                    "taker": "-0.001"\
                }\
            ],\
            "fiat": [],\
            "instType": "SPOT",\
            "level": "Lv1",\
            "maker": "-0.0008",\
            "makerU": "",\
            "makerUSDC": "",\
            "ruleType": "normal",\
            "taker": "-0.001",\
            "takerU": "",\
            "takerUSDC": "",\
            "ts": "1763979985847"\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| level | String | Fee rate Level |\
| feeGroup | Array of objects | Fee groups. <br>Applicable to `SPOT/MARGIN/SWAP/FUTURES/OPTION/EVENTS` |\
| \> taker | String | Taker fee<br>K1 parameter for `EVENTS` taker fee formula: `K1 × C × (P × (1-P))` (C = number of contracts, P = price) |\
| \> maker | String | Maker fee<br>K2 parameter for `EVENTS` maker fee formula: `K2 × C × (P × (1-P))` (C = number of contracts, P = price) |\
| \> groupId | String | Instrument trading fee group ID<br>**instType and groupId should be used together to determine a trading fee group. Users should use this endpoint together with [instruments endpoint](https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-instruments) to get the trading fee of a specific symbol.** |\
| \> rpiMaker | String | RPI maker effective fee rate. Returns `""` if RPI is not applicable to the instrument. |\
| delivery | String | Delivery fee rate |\
| exercise | String | Fee rate for exercising the option |\
| instType | String | Instrument type |\
| ts | String | Data return time, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| taker | String | ~~For `SPOT`/`MARGIN`, it is taker fee rate of the USDT trading pairs. <br>For `FUTURES`/`SWAP`/`OPTION`, it is the fee rate of crypto-margined contracts~~(deprecated) |\
| maker | String | ~~For `SPOT`/`MARGIN`, it is maker fee rate of the USDT trading pairs. <br>For `FUTURES`/`SWAP`/`OPTION`, it is the fee rate of crypto-margined contracts~~(deprecated) |\
| takerU | String | ~~Taker fee rate of USDT-margined contracts, only applicable to `FUTURES`/`SWAP`~~(deprecated) |\
| makerU | String | ~~Maker fee rate of USDT-margined contracts, only applicable to `FUTURES`/`SWAP`~~(deprecated) |\
| takerUSDC | String | ~~For `SPOT`/`MARGIN`, it is taker fee rate of the USDⓈ&Crypto trading pairs.<br>For `FUTURES`/`SWAP`, it is the fee rate of USDC-margined contracts~~(deprecated) |\
| makerUSDC | String | ~~For `SPOT`/`MARGIN`, it is maker fee rate of the USDⓈ&Crypto trading pairs.<br>For `FUTURES`/`SWAP`, it is the fee rate of USDC-margined contracts~~(deprecated) |\
| ruleType | String | ~~Trading rule types<br>`normal`: normal trading<br>`pre_market`: pre-market trading~~(deprecated) |\
| category | String | ~~Currency category.~~(deprecated) |\
| fiat | Array of objects | ~~Details of fiat fee rate~~(deprecated) |\
| \> ccy | String | Fiat currency. |\
| \> taker | String | Taker fee rate |\
| \> maker | String | Maker fee rate |\
| settle | String | Settlement fee rate for users whose positions match the event contract settlement result. Users holding the opposite positions will not be charged during settlement. Only applicable to `EVENTS` |\
\
### Get interest accrued data\
\
Get the interest accrued data for the past year\
\
#### Rate Limit: 5 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/interest-accrued`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/interest-accrued\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get interest accrued data\
result = accountAPI.get_interest_accrued()\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| type | String | No | Loan type<br>`2`: Market loans<br>Default is `2` |\
| ccy | String | No | Loan currency, e.g. `BTC`<br>Only applicable to `Market loans`<br>Only applicable to`MARGIN` |\
| instId | String | No | Instrument ID, e.g. `BTC-USDT`<br>Only applicable to `Market loans` |\
| mgnMode | String | No | Margin mode<br>`cross`<br>`isolated`<br>Only applicable to `Market loans` |\
| after | String | No | Pagination of data to return records earlier than the requested timestamp, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| before | String | No | Pagination of data to return records newer than the requested, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| limit | String | No | Number of results per request. The maximum is `100`. The default is `100`. |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "ccy": "USDT",\
            "instId": "",\
            "interest": "0.0003960833333334",\
            "interestRate": "0.0000040833333333",\
            "liab": "97",\
            "totalLiab": "",\
            "interestFreeLiab": "",\
            "mgnMode": "",\
            "ts": "1637312400000",\
            "type": "1"\
        },\
        {\
            "ccy": "USDT",\
            "instId": "",\
            "interest": "0.0004083333333334",\
            "interestRate": "0.0000040833333333",\
            "liab": "100",\
            "mgnMode": "",\
            "ts": "1637049600000",\
            "type": "1"\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| type | String | Loan type<br>`2`: Market loans |\
| ccy | String | Loan currency, e.g. `BTC` |\
| instId | String | Instrument ID, e.g. `BTC-USDT`<br>Only applicable to `Market loans` |\
| mgnMode | String | Margin mode<br>`cross`<br>`isolated` |\
| interest | String | Interest accrued |\
| interestRate | String | Hourly borrowing interest rate |\
| liab | String | Liability |\
| totalLiab | String | Total liability for current account |\
| interestFreeLiab | String | Interest-free liability for current account |\
| ts | String | Timestamp for interest accrued, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
\
### Get interest rate\
\
Get the user's current leveraged currency borrowing market interest rate\
\
#### Rate Limit: 5 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/interest-rate`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/interest-rate\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get the user's current leveraged currency borrowing interest rate\
result = accountAPI.get_interest_rate()\
print(result)\
```\
\
#### Request Parameters\
\
| **Parameters** | **Types** | **Required** | **Description** |\
| --- | --- | --- | --- |\
| ccy | String | No | Currency, e.g. `BTC` |\
\
```\
Copy to Clipboard\
{\
    "code":"0",\
    "msg":"",\
    "data":[\
        {\
            "ccy":"BTC",\
            "interestRate":"0.0001"\
        },\
        {\
            "ccy":"LTC",\
            "interestRate":"0.0003"\
        }\
    ]\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| interestRate | String | Hourly borrowing interest rate |\
| ccy | String | Currency |\
\
### Set fee type\
\
Set the fee type.\
\
#### Rate Limit: 5 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`POST /api/v5/account/set-fee-type`\
\
> Request Example\
\
```\
Copy to Clipboard\
POST /api/v5/account/set-fee-type\
body\
{\
    "feeType":"0"\
}\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| feeType | String | Yes | Fee type<br>`0`: fee is charged in the currency you receive from the trade (default)<br>`1`: fee is always charged in the quote currency of the trading pair (only effective for Spot) |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "msg": "",\
    "data": [\
        {\
            "feeType": "0"\
        }\
    ]\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| feeType | String | Fee type<br>`0`: fee is charged in the currency you receive from the trade<br>`1`: fee is always charged in the quote currency of the trading pair |\
\
### Set greeks (PA/BS)\
\
Set the display type of Greeks.\
\
#### Rate Limit: 5 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`POST /api/v5/account/set-greeks`\
\
> Request Example\
\
```\
Copy to Clipboard\
POST /api/v5/account/set-greeks\
body\
{\
    "greeksType":"PA"\
}\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Set greeks (PA/BS)\
result = accountAPI.set_greeks(greeksType="PA")\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| greeksType | String | Yes | Display type of Greeks.<br>`PA`: Greeks in coins <br>`BS`: Black-Scholes Greeks in dollars |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "msg": "",\
    "data": [{\
        "greeksType": "PA"\
    }]\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| greeksType | String | Display type of Greeks. |\
\
### Isolated margin trading settings\
\
You can set the currency margin and futures/perpetual Isolated margin trading mode\
\
#### Rate Limit: 5 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`POST /api/v5/account/set-isolated-mode`\
\
> Request Example\
\
```\
Copy to Clipboard\
POST /api/v5/account/set-isolated-mode\
body\
{\
    "isoMode":"automatic",\
    "type":"MARGIN"\
}\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Isolated margin trading settings\
result = accountAPI.set_isolated_mode(\
    isoMode="automatic",\
    type="MARGIN"\
)\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| isoMode | String | Yes | Isolated margin trading settings<br>`auto_transfers_ccy`: New auto transfers, enabling both base and quote currency as the margin for isolated margin trading. Only applicable to `MARGIN`.<br>`automatic`: Auto transfers |\
| type | String | Yes | Instrument type<br>`MARGIN`<br>`CONTRACTS` |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "isoMode": "automatic"\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| isoMode | String | Isolated margin trading settings<br>`automatic`: Auto transfers |\
\
### Get maximum withdrawals\
\
Retrieve the maximum transferable amount from trading account to funding account. If no currency is specified, the transferable amount of all owned currencies will be returned.\
\
#### Rate Limit: 20 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/max-withdrawal`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/max-withdrawal\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get maximum withdrawals\
result = accountAPI.get_max_withdrawal()\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| ccy | String | No | Single currency or multiple currencies (no more than 20) separated with comma, e.g. `BTC` or `BTC,ETH`. |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "msg": "",\
    "data": [{\
            "ccy": "BTC",\
            "maxWd": "124",\
            "maxWdEx": "125",\
            "spotOffsetMaxWd": "",\
            "spotOffsetMaxWdEx": ""\
        },\
        {\
            "ccy": "ETH",\
            "maxWd": "10",\
            "maxWdEx": "12",\
            "spotOffsetMaxWd": "",\
            "spotOffsetMaxWdEx": ""\
        }\
    ]\
}\
```\
\
#### Response Parameters\
\
| **Parameter** | **Type** | **Description** |\
| --- | --- | --- |\
| ccy | String | Currency |\
| maxWd | String | Max withdrawal (excluding borrowed assets under `Spot mode`/`Multi-currency margin`/`Portfolio margin`) |\
| maxWdEx | String | Max withdrawal (including borrowed assets under `Spot mode`/`Multi-currency margin`/`Portfolio margin`) |\
| spotOffsetMaxWd | String | Max withdrawal under Spot-Derivatives risk offset mode (excluding borrowed assets under `Portfolio margin`)<br>Applicable to `Portfolio margin` |\
| spotOffsetMaxWdEx | String | Max withdrawal under Spot-Derivatives risk offset mode (including borrowed assets under `Portfolio margin`)<br>Applicable to `Portfolio margin` |\
\
### Get account risk state\
\
Only applicable to Portfolio margin account\
\
#### Rate Limit: 10 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/risk-state`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/risk-state\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get account risk state\
result = accountAPI.get_account_position_risk()\
print(result)\
```\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "atRisk": false,\
            "atRiskIdx": [],\
            "atRiskMgn": [],\
            "ts": "1635745078794"\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| **Parameters** | **Types** | **Description** |\
| --- | --- | --- |\
| atRisk | Boolean | Account risk status in auto-borrow mode <br>true: the account is currently in a specific risk state <br>false: the account is currently not in a specific risk state |\
| atRiskIdx | Array of strings | derivatives risk unit list |\
| atRiskMgn | Array of strings | margin risk unit list |\
| ts | String | Unix timestamp format in milliseconds, e.g.`1597026383085` |\
\
### Get borrow interest and limit\
\
#### Rate Limit: 5 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/interest-limits`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/interest-limits?ccy=BTC\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
# Get borrow interest and limit\
result = accountAPI.get_interest_limits(\
    ccy="BTC"\
)\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| type | String | No | Loan type<br>`2`: Market loans<br>Default is `2` |\
| ccy | String | No | Loan currency, e.g. `BTC` |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "debt": "0.85893159114900247077000000000000",\
            "interest": "0.00000000000000000000000000000000",\
            "loanAlloc": "",\
            "nextDiscountTime": "1729490400000",\
            "nextInterestTime": "1729490400000",\
            "records": [\
                {\
                    "availLoan": "",\
                    "avgRate": "",\
                    "ccy": "BTC",\
                    "interest": "0",\
                    "loanQuota": "175.00000000",\
                    "posLoan": "",\
                    "rate": "0.0000276",\
                    "surplusLmt": "175.00000000",\
                    "surplusLmtDetails": {},\
                    "usedLmt": "0.00000000",\
                    "usedLoan": "",\
                    "interestFreeLiab": "",\
                    "potentialBorrowingAmt": ""\
                }\
            ]\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| debt | String | Current debt in `USD` |\
| interest | String | Current interest in `USD`, the unit is `USD`<br>Only applicable to `Market loans` |\
| nextDiscountTime | String | Next deduct time, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| nextInterestTime | String | Next accrual time, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| loanAlloc | String | VIP Loan allocation for the current trading account<br>1\. The unit is percent(%). Range is \[0, 100\]. Precision is 0.01%<br>2\. If master account did not assign anything, then "0"<br>3\. "" if shared between master and sub-account |\
| records | Array of objects | Details for currencies |\
| \> ccy | String | Loan currency, e.g. `BTC` |\
| \> rate | String | Current daily borrowing rate |\
| \> loanQuota | String | Borrow limit of master account<br>If loan allocation has been assigned, then it is the borrow limit of the current trading account |\
| \> surplusLmt | String | Available amount across all sub-accounts<br>If loan allocation has been assigned, then it is the available amount to borrow by the current trading account |\
| \> usedLmt | String | Borrowed amount for current account<br>If loan allocation has been assigned, then it is the borrowed amount by the current trading account |\
| \> interest | String | Interest to be deducted<br>Only applicable to `Market loans` |\
| \> interestFreeLiab | String | Interest-free liability for current account |\
| \> potentialBorrowingAmt | String | Potential borrowing amount for current account |\
| \> surplusLmtDetails | Object | ~~The details of available amount across all sub-accounts<br>The value of `surplusLmt` is the minimum value within this array. It can help you judge the reason that `surplusLmt` is not enough.<br>Only applicable to `VIP loans`~~ Deprecated |\
| >\> allAcctRemainingQuota | String | ~~Total remaining quota for master account and sub-accounts~~ Deprecated |\
| >\> curAcctRemainingQuota | String | ~~The remaining quota for the current account.<br>Only applicable to the case in which the sub-account is assigned the loan allocation~~ Deprecated |\
| >\> platRemainingQuota | String | ~~Remaining quota for the platform.<br>The format like "600" will be returned when it is more than `curAcctRemainingQuota` or `allAcctRemainingQuota`~~ Deprecated |\
| \> posLoan | String | ~~Frozen amount for current account (Within the locked quota) <br>Only applicable to `VIP loans`~~ Deprecated |\
| \> availLoan | String | ~~Available amount for current account (Within the locked quota)<br>Only applicable to `VIP loans`~~ Deprecated |\
| \> usedLoan | String | ~~Borrowed amount for current account<br>Only applicable to `VIP loans`~~ Deprecated |\
| \> avgRate | String | ~~Average hourly interest of borrowed coin<br>only applicable to `VIP loans`~~ Deprecated |\
\
### Manual borrow / repay\
\
Only applicable to `Spot mode` (enabled borrowing)\
\
#### Rate Limit: 1 request per 3 seconds\
\
#### Rate limit rule: Master Account User ID\
\
#### HTTP Request\
\
`POST /api/v5/account/spot-manual-borrow-repay`\
\
> Request Example\
\
```\
Copy to Clipboard\
POST /api/v5/account/spot-manual-borrow-repay\
body\
{\
    "ccy":"USDT",\
    "side":"borrow",\
    "amt":"100"\
}\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
result = accountAPI.spot_manual_borrow_repay(ccy="USDT", side="borrow", amt= "1")\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| ccy | String | Yes | Currency, e.g. `BTC` |\
| side | String | Yes | Side<br>`borrow`<br>`repay` |\
| amt | String | Yes | Amount |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "ccy":"USDT",\
            "side":"borrow",\
            "amt":"100"\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| ccy | String | Currency, e.g. `BTC` |\
| side | String | Side<br>`borrow`<br>`repay` |\
| amt | String | Actual amount |\
\
### Set auto repay\
\
Only applicable to `Spot mode` (enabled borrowing)\
\
#### Rate Limit: 5 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`POST /api/v5/account/set-auto-repay`\
\
> Request Example\
\
```\
Copy to Clipboard\
POST /api/v5/account/set-auto-repay\
body\
{\
    "autoRepay": true\
}\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
result = accountAPI.set_auto_repay(autoRepay=True)\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| autoRepay | Boolean | Yes | Whether auto repay is allowed or not under `Spot mode`<br>`true`: Enable auto repay<br>`false`: Disable auto repay |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "msg": "",\
    "data": [\
        {\
            "autoRepay": true\
        }\
    ]\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| autoRepay | Boolean | Whether auto repay is allowed or not under `Spot mode`<br>`true`: Enable auto repay<br>`false`: Disable auto repay |\
\
### Get borrow/repay history\
\
Retrieve the borrow/repay history under `Spot mode`\
\
#### Rate Limit: 5 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`GET /api/v5/account/spot-borrow-repay-history`\
\
> Request Example\
\
```\
Copy to Clipboard\
GET /api/v5/account/spot-borrow-repay-history\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"   # Production trading:0 , demo trading:1\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
result = accountAPI.spot_borrow_repay_history(ccy="USDT", type="auto_borrow")\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| ccy | String | No | Currency, e.g. `BTC` |\
| type | String | No | Event type<br>`auto_borrow`<br>`auto_repay`<br>`manual_borrow`<br>`manual_repay` |\
| after | String | No | Pagination of data to return records earlier than the requested `ts` (included), Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| before | String | No | Pagination of data to return records newer than the requested `ts`(included), Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| limit | String | No | Number of results per request. The maximum is 100. The default is 100. |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "accBorrowed": "0",\
            "amt": "6764.802661157592",\
            "ccy": "USDT",\
            "ts": "1725330976644",\
            "type": "auto_repay"\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| Parameter | Type | Description |\
| --- | --- | --- |\
| ccy | String | Currency, e.g. `BTC` |\
| type | String | Event type<br>`auto_borrow`<br>`auto_repay`<br>`manual_borrow`<br>`manual_repay` |\
| amt | String | Amount |\
| accBorrowed | String | Accumulated borrow amount |\
| ts | String | Timestamp for the event, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
\
### Position builder (new)\
\
Calculates portfolio margin information for virtual position/assets or current position of the user.\
\
You can add up to 200 virtual positions and 200 virtual assets in one request.\
\
#### Rate Limit: 2 requests per 2 seconds\
\
#### Rate limit rule: User ID\
\
#### HTTP Request\
\
`POST /api/v5/account/position-builder`\
\
> Request Example\
\
```\
Copy to Clipboard\
# Both real and virtual positions and assets are calculated\
POST /api/v5/account/position-builder\
body\
{\
    "inclRealPosAndEq": false,\
    "simPos":[\
         {\
            "pos":"-10",\
            "instId":"BTC-USDT-SWAP",\
            "avgPx":"100000"\
         },\
         {\
            "pos":"10",\
            "instId":"LTC-USDT-SWAP",\
            "avgPx":"8000"\
         }\
    ],\
    "simAsset":[\
        {\
            "ccy": "USDT",\
            "amt": "100"\
        }\
    ],\
    "greeksType":"CASH"\
}\
\
# Only existing real positions are calculated\
POST /api/v5/account/position-builder\
body\
{\
   "inclRealPosAndEq":true\
}\
\
# Only virtual positions are calculated\
POST /api/v5/account/position-builder\
body\
{\
    "acctLv": "4",\
    "inclRealPosAndEq": false,\
    "simPos":[\
        {\
            "pos":"10",\
            "instId":"BTC-USDT-SWAP",\
            "avgPx":"100000"\
        },\
        {\
            "pos":"10",\
            "instId":"LTC-USDT-SWAP",\
            "avgPx":"8000"\
        }\
    ]\
}\
\
# Switch to Multi-currency margin mode\
POST /api/v5/account/position-builder\
body\
{\
    "acctLv": "3",\
    "lever":"10",\
    "simPos":[\
        {\
            "pos":"10",\
            "instId":"BTC-USDT-SWAP",\
            "avgPx":"100000",\
            "lever":"5"\
        },\
        {\
            "pos":"10",\
            "instId":"LTC-USDT-SWAP",\
            "avgPx":"8000"\
        }\
    ]\
}\
```\
\
```\
Copy to Clipboard\
import okx.Account as Account\
\
# API initialization\
apikey = "YOUR_API_KEY"\
secretkey = "YOUR_SECRET_KEY"\
passphrase = "YOUR_PASSPHRASE"\
\
flag = "1"  # Production trading:0 , demo trading:1\
\
accountAPI = Account.AccountAPI(apikey, secretkey, passphrase, False, flag)\
\
result = accountAPI.position_builder(\
    inclRealPosAndEq=True,\
    simPos=[\
        {\
            "pos": "10",\
            "instId": "BTC-USDT-SWAP"\
        },\
        {\
            "pos": "10",\
            "instId": "LTC-USDT-SWAP"\
        }\
    ]\
)\
print(result)\
```\
\
#### Request Parameters\
\
| Parameter | Type | Required | Description |\
| --- | --- | --- | --- |\
| acctLv | String | No | Switch to account mode<br>`3`: Multi-currency margin<br>`4`: Portfolio margin<br>The default is `4` |\
| inclRealPosAndEq | Boolean | No | Whether import existing positions and assets<br>The default is `true` |\
| lever | String | No | Cross margin leverage in Multi-currency margin mode, the default is `1`.<br>If the allowed leverage is exceeded, set according to the maximum leverage.<br>Only applicable to `Multi-currency margin` |\
| simPos | Array of objects | No | List of simulated positions |\
| \> instId | String | Yes | Instrument ID, e.g. `BTC-USDT-SWAP`<br>Applicable to `SWAP`/`FUTURES`/`OPTION` |\
| \> pos | String | Yes | Quantity of positions |\
| \> avgPx | String | Yes | Average open price |\
| \> lever | String | No | leverage<br>Only applicable to `Multi-currency margin`<br>The default is `1`<br>If the allowed leverage is exceeded, set according to the maximum leverage. |\
| simAsset | Array of objects | No | List of simulated assets<br>When `inclRealPosAndEq` is `true`, only real assets are considered and virtual assets are ignored |\
| \> ccy | String | Yes | Currency, e.g. `BTC` |\
| \> amt | String | Yes | Currency amount |\
| greeksType | String | No | Greeks type<br>`BS`: Black-Scholes Model Greeks<br>`PA`: Crypto Greeks<br>`CASH`: Empirical Greeks<br>The default is `BS` |\
| idxVol | String | No | Price volatility percentage, indicating what this price change means towards each of the values. In decimal form, range -0.99 ~ 1, in 0.01 increment.<br> Default 0 |\
\
> Response Example\
\
```\
Copy to Clipboard\
{\
    "code": "0",\
    "data": [\
        {\
            "acctLever": "-0.1364949794742562",\
            "assets": [\
                {\
                    "availEq": "0",\
                    "borrowImr": "0",\
                    "borrowMmr": "",\
                    "ccy": "BTC",\
                    "spotInUse": "0"\
                },\
                {\
                    "availEq": "0",\
                    "borrowImr": "0",\
                    "borrowMmr": "",\
                    "ccy": "LTC",\
                    "spotInUse": "0"\
                },\
                {\
                    "availEq": "0",\
                    "borrowImr": "0",\
                    "borrowMmr": "",\
                    "ccy": "USDC",\
                    "spotInUse": "0"\
                },\
                {\
                    "availEq": "-78589.37",\
                    "borrowImr": "7855.32188898",\
                    "borrowMmr": "",\
                    "ccy": "USDT",\
                    "spotInUse": "0"\
                }\
            ],\
            "borrowMmr": "1571.064377796",\
            "derivMmr": "1375.4837063088003",\
            "eq": "-78553.21888979999",\
            "marginRatio": "-25.95365779811705",\
            "positions": [],\
            "riskUnitData": [\
                {\
                    "delta": "-9704.903689800001",\
                    "gamma": "0",\
                    "imrBf": "",\
                    "imr": "1538.9669514070802",\
                    "mmrBf": "",\
                    "mmr": "1183.8207318516002",\
                    "mr1": "1164.4109244719994",\
                    "mr1FinalResult": {\
                        "pnl": "-1164.4109244719994",\
                        "spotShock": "0.12",\
                        "volShock": "up"\
                    },\
                    "mr1Scenarios": {\
                        "volSame": {\
                            "0": "0",\
                            "0.08": "-776.2739496480004",\
                            "-0.08": "776.2739496480004",\
                            "0.04": "-388.1369748240002",\
                            "0.12": "-1164.4109244719994",\
                            "-0.12": "1164.4109244719994",\
                            "-0.04": "388.1369748240002"\
                        },\
                        "volShockDown": {\
                            "0": "0",\
                            "0.08": "-776.2739496480004",\
                            "-0.08": "776.2739496480004",\
                            "0.04": "-388.1369748240002",\
                            "0.12": "-1164.4109244719994",\
                            "-0.12": "1164.4109244719994",\
                            "-0.04": "388.1369748240002"\
                        },\
                        "volShockUp": {\
                            "0": "0",\
                            "0.08": "-776.2739496480004",\
                            "-0.08": "776.2739496480004",\
                            "0.04": "-388.1369748240002",\
                            "0.12": "-1164.4109244719994",\
                            "-0.12": "1164.4109244719994",\
                            "-0.04": "388.1369748240002"\
                        }\
                    },\
                    "mr2": "0",\
                    "mr3": "0",\
                    "mr4": "19.4098073796",\
                    "mr5": "0",\
                    "mr6": "1164.4109244720003",\
                    "mr6FinalResult": {\
                        "pnl": "-2328.8218489440005",\
                        "spotShock": "0.24"\
                    },\
                    "mr7": "43.67206660410001",\
                    "mr8": "1571.064377796",\
                    "mr9": "0",\
                    "portfolios": [\
                        {\
                            "amt": "-10",\
                            "avgPx": "100000",\
                            "delta": "-9704.903689800001",\
                            "floatPnl": "290.6300000000003",\
                            "gamma": "0",\
                            "instId": "BTC-USDT-SWAP",\
                            "instType": "SWAP",\
                            "isRealPos": false,\
                            "markPxBf": "",\
                            "markPx": "97093.7",\
                            "notionalUsd": "9703.22",\
                            "posSide": "net",\
                            "theta": "0",\
                            "vega": "0"\
                        }\
                    ],\
                    "riskUnit": "BTC",\
                    "theta": "0",\
                    "upl": "290.49631020000027",\
                    "vega": "0"\
                },\
                {\
                    "delta": "1019.5308",\
                    "gamma": "0",\
                    "imrBf": "",\
                    "imr": "249.16186679436",\
                    "mmrBf": "",\
                    "mmr": "191.6629744572",\
                    "mr1": "183.50672805719995",\
                    "mr1FinalResult": {\
                        "pnl": "-183.50672805719995",\
                        "spotShock": "-0.18",\
                        "volShock": "up"\
                    },\
                    "mr1Scenarios": {\
                        "volSame": {\
                            "0": "0",\
                            "-0.06": "-61.168909352399936",\
                            "0.06": "61.168909352399936",\
                            "-0.18": "-183.50672805719995",\
                            "0.18": "183.50672805719995",\
                            "0.12": "122.33781870480001",\
                            "-0.12": "-122.33781870480001"\
                        },\
                        "volShockDown": {\
                            "0": "0",\
                            "-0.06": "-61.168909352399936",\
                            "0.06": "61.168909352399936",\
                            "-0.18": "-183.50672805719995",\
                            "0.18": "183.50672805719995",\
                            "0.12": "122.33781870480001",\
                            "-0.12": "-122.33781870480001"\
                        },\
                        "volShockUp": {\
                            "0": "0",\
                            "-0.06": "-61.168909352399936",\
                            "0.06": "61.168909352399936",\
                            "-0.18": "-183.50672805719995",\
                            "0.18": "183.50672805719995",\
                            "0.12": "122.33781870480001",\
                            "-0.12": "-122.33781870480001"\
                        }\
                    },\
                    "mr2": "0",\
                    "mr3": "0",\
                    "mr4": "8.1562464",\
                    "mr5": "0",\
                    "mr6": "183.5067280572",\
                    "mr6FinalResult": {\
                        "pnl": "-367.0134561144",\
                        "spotShock": "-0.36"\
                    },\
                    "mr7": "7.1367156",\
                    "mr8": "1571.064377796",\
                    "mr9": "0",\
                    "portfolios": [\
                        {\
                            "amt": "10",\
                            "avgPx": "8000",\
                            "delta": "1019.5308",\
                            "floatPnl": "-78980",\
                            "gamma": "0",\
                            "instId": "LTC-USDT-SWAP",\
                            "instType": "SWAP",\
                            "isRealPos": false,\
                            "markPxBf": "",\
                            "markPx": "102",\
                            "notionalUsd": "1018.9",\
                            "posSide": "net",\
                            "theta": "0",\
                            "vega": "0"\
                        }\
                    ],\
                    "riskUnit": "LTC",\
                    "theta": "0",\
                    "upl": "-78943.6692",\
                    "vega": "0"\
                }\
            ],\
            "totalImr": "9643.45070718144",\
            "totalMmr": "2946.5480841048",\
            "ts": "1736936801642",\
            "upl": "-78653.1728898"\
        }\
    ],\
    "msg": ""\
}\
```\
\
#### Response Parameters\
\
| **Parameters** | **Types** | **Description** |\
| --- | --- | --- |\
| eq | String | Adjusted equity (`USD`) for the account |\
| totalMmr | String | Total MMR (`USD`) for the account |\
| totalImr | String | Total IMR (`USD`) for the account |\
| borrowMmr | String | Borrow MMR (`USD`) for the account |\
| derivMmr | String | Derivatives MMR (`USD`) for the account |\
| marginRatio | String | Cross maintenance margin ratio for the account |\
| upl | String | UPL for the account |\
| acctLever | String | Leverage of the account |\
| ts | String | Update time for the account, Unix timestamp format in milliseconds, e.g. `1597026383085` |\
| assets | Array of objects | Asset info |\
| \> ccy | String | Currency, e.g. `BTC` |\
| \> availEq | String | Currency equity |\
| \> spotInUse | String | Spot in use |\
| \> borrowMmr | String | ~~Borrowing MMR (`USD`)~~(Deprecated) |\
| \> borrowImr | String | Borrowing IMR (`USD`) |\
| riskUnitData | Array of objects | Risk unit info |\
| \> riskUnit | String | Risk unit, e.g. `BTC` |\
| \> mmrBf | String | Risk unit MMR before volatility (`USD`)<br> Return "" if users don't pass in idxVol |\
| \> mmr | String | Risk unit MMR (`USD`) |\
| \> imrBf | String | Risk unit IMR before volatility (`USD`)<br> Return
…[truncated]