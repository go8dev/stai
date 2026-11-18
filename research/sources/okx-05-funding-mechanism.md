Source: https://www.okx.com/en-us/help/perps-funding-fee-mechanism
Title: Perpetual funding fee mechanism | OKX United States
Fetched: 2026-11-18T09:29:19.233Z

Not all products mentioned are available in all jurisdictions.

[Support center](https://www.okx.com/en-us/help)

[Product documentation](https://www.okx.com/en-us/help/category/product-documentation)

Article

# Perpetual funding fee mechanism

Published on Dec 21, 2020Updated on Oct 28, 20269 min read

This information may not apply to all customers

Log in to check if the products, features, rules, and terms in this article apply to you.

At OKX, our perpetual futures adopt a funding fee mechanism designed to align the market price of the perpetual market with the index price.

When the funding rate is positive, traders with long positions pay a funding fee to traders with short positions. Conversely, when the funding rate is negative, traders with short positions pay a funding fee to traders with long positions. Note that our platform only facilitates the exchange of funds between traders and doesn’t charge any service fees under this mechanism.

The funding fee will be charged or paid out every 8 hours (00:00, 08:00, and 16:00 UTC) by default, unless specified otherwise (i.e. every 1, 2 or 4 hours). For each perpetual futures contract, fees are assessed within milliseconds and trading won’t be interrupted. You’re obligated to pay or receive the funding fee if you hold open positions at the point of fee assessment. If you close your position before the funding fee assessment, you’re exempt from paying or collecting the fee. Additionally, if a perpetual futures contract is delisted before the assessment, the current cycle’s funding fee becomes void. The actual fee assessment may take up to a minute. For example, if you open a position at 00:00:20 UTC, you could still be subject to the funding fee (either collecting or distributing the funding fee) if the fee assessment has yet to end.

The funding fee settlement time and funding rate cap/floor may be adjusted in real-time according to market conditions.

## Funding rate calculation

Funding rate = clamp \[ ( Average premium index + clamp ( Interest rate − Average premium index, 0.05%, −0.05% ) ) / ( 8 / N ), Funding rate cap, Funding rate floor \]

- Interest rate = 0.01% (fixed across all settlement intervals)

- N = the contract's funding settlement interval, in hours. Supported values are N ∈ {1, 2, 4, 8}. The (8 / N) divisor normalizes the per-period rate so that the daily-equivalent funding cost remains consistent across all supported settlement cycles.

- Effect of the 8 / N interval factor by settlement cycle:

  - 8h cycle (N=8): ÷ 1

  - 4h cycle (N=4): ÷ 2

  - 2h cycle (N=2): ÷ 4

  - 1h cycle (N=1): ÷ 8
- For more information on the cap and floor, refer to this [page](https://www.okx.com/en-us/trade-market/funding/swap).

- Premium index = \[Max (0, Impact bid price – Index price) – Max (0, Index price – Impact ask price)\] / Index price

- The average premium index is calculated using a weighted moving average of the premium index over the last settlement interval.

  - For example: Average premium index at Tn = (1 × Premium index at T1 + 2 × Premium index at T2 + ... + n × Premium index at Tn) / (1 + 2 + ... + n). Assuming the settlement interval of a perpetual futures contract is 8 hours, the funding rate at 07:59 will be calculated using the premium index for every minute between 00:00 to 07:59. In other words, n = 480.
- Impact bid/ask price is the average fill price to execute the impact value on the bid/ask price.

  - Impact bid/ask price = Impact value / Total base amount required to meet impact value

    - Impact value = 200 × Max leverage allowed for this perpetual
- The funding rate used to calculate the funding fee during fee assessment will be the most recent funding rate that was calculated in the previous minute before fee assessment.

  - For example, the fee assessment at 16:00 will use the funding rate calculated at 15:59.

**Impact bid price calculation using BTCUSDT perpetual as an example:**

Assuming impact value = 20,000 USDT

|     |     |     |     |
| --- | --- | --- | --- |
| Bid order book level | Bid price | Base amount in each order book level (BTC) | Calculation |
| 1 | 90,000 | 0.02 | Value of orders up to this level = 90,000 × 0.02 = 1,800 USDT<br>The entire base amount of 0.02 BTC at this level will be used for impact bid price calculation. |
| 2 | 89,900 | 0.06 | Value of orders up to this level = Value of orders in bid 2 + Value of orders in bid 1 = 89,900 × 0.06 + 1,800 = 7,194 USDT<br>The entire base amount of 0.06 BTC at this level will be used for impact bid price calculation. |
| 3 | 89,700 | 0.16 | Value of orders up to this level = Value of orders in bid 3 + Value of orders in bid 1 and 2 = 89,700 × 0.16 + 7,194 = 21,546 USDT<br>Impact value required for this level = 20,000 – 7,194 = 12,806 USDT<br>Amount required from this level (BTC) = 12,806 / 89,700 = 0.14276 BTC<br>Impact bid price = 20,000 / (0.02 + 0.06 + 0.14276) = 89,780.8 USDT |

**Impact ask price calculation using BTCUSDT perpetual as an example:**

|     |     |     |     |
| --- | --- | --- | --- |
| Ask order book level | Ask price | Base amount in each order book level (BTC) | Calculation |
| 1 | 90,000 | 0.02 | Value of orders up to this level = 90,000 × 0.02 = 1,800 USDT<br>The entire base amount of 0.02 BTC at this level will be used for impact ask price calculation. |
| 2 | 90,100 | 0.06 | Value of orders up to this level = Value of orders in ask 2 + Value of orders in ask 1 = 90,100 × 0.06 + 1,800 = 7,206 USDT<br>The entire base amount of 0.06 BTC at this level will be used for impact ask price calculation. |
| 3 | 90,200 | 0.16 | Value of orders up to this level = Value of orders in ask 3 + Value of orders in ask 1 and 2 = 90,200 × 0.16 + 7,206 = 21,638 USDT<br>Impact value required for this level = 20,000 – 7,206 = 12,794 USDT<br>Amount required from this level (BTC) = 12,794 / 90,200 = 0.14184 BTC<br>Impact ask price = 20,000 / (0.02 + 0.06 + 0.14184) = 90,154.9 USDT |

### Worked example — 1-hour-cycle perpetual

Assume a perpetual contract with a 1-hour settlement cycle (N = 1) and an average premium index of 0.10% in the latest settlement window.

- Interest rate = 0.01% (fixed)

- Interest − Premium = 0.01% − 0.10% = −0.09% → clamped to −0.05%

- Pre-divisor rate = 0.10% + (−0.05%) = 0.05%

- Funding rate = 0.05% / (8 / 1) = 0.00625% per 1-hour period (assume within funding rate cap/floor)


## Funding fee calculation

Funding fee = Position value × Funding rate

### USDT-margined/USDC-margined perpetual futures

Position value = Number of contracts × Contract size × Contract multiplier × Mark price

**Example:**

You have a long position of 10 BTCUSDT perpetual futures contract with a current mark price of 60,000 USDT, 0.01 BTC face value per contract, and the funding rate is 0.1%.

Position value = 60,000 × 10 × 0.01 × 1 = 6,000 USDT

Funding fee (platform collects) = 6,000 × 0.1% = 6 USDT

### Crypto-margined perpetual futures

Position value = Number of contracts × Contract size × Contract multiplier / Mark price

**Example:**

You have a short position of 100 ETHUSD Perpetual contracts with a current mark price of 4,000 USD, 10 USD face value per contract, and the funding rate is 0.1%.

Position value = 100 × 10 × 1 / 4,000 = 0.25 ETH

Funding fee (platform distributes) = 0.25 × 0.1% = 0.00025 ETH

## Collection and distribution of funding fees

Funding fees are settled directly between users holding long and short positions. OKX does not collect or retain any portion of the funding fee.

**Funding Fee Collection**

The full funding fee will be deducted from the paying user's position. A reduction in account equity following deduction may trigger position size reduction or liquidation.

- Isolated margin mode: The funding fee is deducted from the isolated margin of the position. No pending orders will be cancelled upon deduction.

- Cross margin mode (Single-currency, Cross-currency, Portfolio margin): The funding fee is deducted from the currency equity of the cross margin account. No pending orders will be cancelled upon deduction.


**Funding Fee Distribution**

The full funding fee will be credited to the receiving user's position.

- Isolated margin mode: The funding fee is credited to the isolated margin of the position.

- Cross margin mode (Single-currency, Cross-currency, Portfolio margin): The funding fee is credited to the currency equity of the cross margin account.


## Automatic adjustment of funding fee settlement frequency

Beyond the periodic settlement described above, OKX automatically adjusts a perpetual contract's funding fee settlement frequency based on market conditions, and reverts it once conditions normalize.When the funding rate reaches its cap or floor at settlement, the settlement frequency is escalated by one level at a time. The available settlement frequency levels are:

|     |     |
| --- | --- |
| Settlement Frequency | Settlement Times (UTC) |
| 8 hours | 00:00, 08:00, 16:00 |
| 4 hours | 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 |
| 2 hours | 00:00, 02:00, 04:00, ..., 22:00 (every 2 hours) |
| 1 hour | 00:00, 01:00, 02:00, ..., 23:00 (every hour) |

Whether the frequency is escalated or reverted, the first settlement afterwards always falls on the next settlement time of the new frequency listed above. No settlement takes place outside those times.

**OKX only evaluates whether to revert the settlement frequency at a settlement time on the contract’s default settlement schedule. If, at that time, the funding rate at every settlement during the preceding 12 consecutive hours was within +/-0.20% (20 bps), OKX will revert the settlement frequency to the contract’s default without further notice.**

### Worked example — automatic frequency escalation

Suppose the XYZUSDT perpetual contract has a default settlement frequency of 4 hours and a funding rate cap/floor of +/-0.375%:

1. If the XYZUSDT funding rate reaches 0.375% (cap) at 16:00 UTC, the system escalates the settlement frequency from 4 hours to 2 hours. The next settlement will be at 18:00 UTC.

2. If the funding rate hits the cap again at 18:00 UTC, the system escalates the frequency from 2 hours to 1 hour. The next settlement will be at 19:00 UTC.

3. If the above condition is met by 02:00 UTC, the system won’t revert the frequency immediately because 02:00 UTC isn’t a settlement time on the contract’s default 4-hour schedule. The system will evaluate the condition again at 04:00 UTC, the next settlement time on the default schedule. If the condition is still met, the settlement frequency will revert to 4 hours.


**Please note:**

1. OKX reserves the right to disable the automatic frequency adjustment feature for specific contracts based on market conditions.

2. Refer to the Perpetual Contract Information page or the API endpoint GET /api/v5/public/funding-rate for the latest settlement frequency, and adjust your trading strategies accordingly.

3. Automatic frequency adjustment applies only to crypto perpetual contracts (including X-Perps). Perpetual contracts on traditional financial assets — including equities, ETFs, and commodities — are excluded, and their funding fee settlement frequency always stays at the contract's default.


![empty](https://9kqz97863bi7xwebs27abpg374qw7eynuhwsgfqq09e59bf2b3ac0894alp.g.aa.online-metrix.net/n0hUrMKBxKOcRWr4?53b4c56fdabfa023=GbcYoVUG4iTaCUVrNF5PCfQxH69ipJLsTBF774Z-a668LtfznMAY0bJwSA7IcSxr5nFuwhlgl87tlxnQmQLVXNs0OhuQ1JEC_F6XL-GdDuxqNY4T3QOsiksCvKEyoXXI4loFUU-VXH5TnnzSa6fc1A)![empty](https://contentmx.okcoin.com/KEdra0vEczsLWpgY?77902db9031a1deb=nDXMfRfcMlqkkzQ7n4mOP063q00t12b9o7USS5GKHbYGIaeqyfxj48qHpFclCPWSvhS7XApdsaxkh-Tx-ndygbZidoM9p87AojUfUh-PGpCI79N5YsYr38unZN0gHsYpDTg8M9L5ry1QHuZlROc5K0QDxvY1VAbWxZVJT5cNsolmMnKZDmOosrdguwONhYkOjztp&jf=34313424716b64577a666c3774667a5f4176627c456f36494972704b613347742e7b616c5564637c6535313731363b34373b363724716b665f7c71786d3777676a3a6d63647b6324736b665f6b677b3f31303d313b383b33323e303f3261303436386167336432303233303e38303a6b38343c386b65336c323130333237303136303230383c3c3b3238343a366931393c3535343b67316634366131316e6e386b3b37306e353e37313d3a34396164636631663764333b3d3d316e37603c646c38623034636634313538353b636630396d3d6d3835673c653038633c3137646337656532343136303f6e3c3c3f30363e62316436383b67663b303765633a3036373d6b396b3e267161645773696f3f313036373032303230613038313a3f6b63643a373136653f673438363465316434673238693d30313a663a3e353f653630603234366366356737326763383f3e3f3d30373d373d30303a303330326134613b3b3634366e396a6a3f35356c663c37633a3761393630643767663231656b383c3c6f306739633f35643d31323867373065333b6334356b6d3e6b3336247b696e723d38)

![empty](https://contentmx.okcoin.com/wkFdmI_lGziBJK49?954f17832b257f5b=eQhOYzKK2e0l5BavXMwoHpwK9Q4uXQViKW1WNOaODDceOK1o-ixa7DnEVnbYN4tOiH9Fr0TkLPeIsvHMRm88fdhSYi6kU764R2KuK-uRyTMHfExqxUwgFOlLwrVVUWM0GpNY36VI1tspAumLtwrIJ8QB)

empty

empty

empty

Chat with us