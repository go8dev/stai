Source: https://www.sciencedirect.com/science/article/pii/S1059056024003010
Title: Are simple technical trading rules profitable in bitcoin markets? - ScienceDirect
Fetched: 2026-11-18T09:28:49.267Z

[Skip to main content](https://www.sciencedirect.com/science/article/abs/pii/S1059056024003010#main) [Skip to article](https://www.sciencedirect.com/science/article/abs/pii/S1059056024003010#article)

[![International Review of Economics & Finance](https://ars.els-cdn.com/content/image/1-s2.0-S1059056024X00040-cov200h.gif)](https://www.sciencedirect.com/journal/international-review-of-economics-and-finance/vol/93/part/PB)

## [International Review of Economics & Finance](https://www.sciencedirect.com/journal/international-review-of-economics-and-finance "Go to International Review of Economics & Finance on ScienceDirect")

Date: June 2024

Pages: 858-874

Volume: [Volume 93, Part B](https://www.sciencedirect.com/journal/international-review-of-economics-and-finance/vol/93/part/PB "Go to table of contents for this volume/issue")

View accessibility information

## Published by: Elsevier

### Published by

[![Elsevier](https://www.sciencedirect.com/eu-west-1/prod/5f6716225f1159fc4ed76eb0fbb2dfd9d1034a4b/image/elsevier-non-solus.svg)](https://www.sciencedirect.com/journal/international-review-of-economics-and-finance "Go to International Review of Economics & Finance on ScienceDirect")

Show more

Research article

[Get rights and content](https://s100.copyright.com/AppDispatchServlet?publisherName=ELS&contentID=S1059056024003010&orderBeanReset=true)

# Are simple technical trading rules profitable in bitcoin markets?

Author links open overlay panelNiekDeprez, [MichaelFrömmel](https://www.sciencedirect.com/author/56069047700/michael-frommel)

Show more

Cite

Add to Mendeley

Share

[10.1016/j.iref.2024.05.003](https://doi.org/10.1016/j.iref.2024.05.003)

[Access through **your organization**](https://www.sciencedirect.com/user/institution/login?targetUrl=%2Fscience%2Farticle%2Fpii%2FS1059056024003010) [Purchase PDF](https://www.sciencedirect.com/getaccess/pii/S1059056024003010/purchase)

More actions

## Article preview

- [Abstract](https://www.sciencedirect.com/science/article/abs/pii/S1059056024003010#abstracts)
- [Introduction](https://www.sciencedirect.com/science/article/abs/pii/S1059056024003010#introduction)
- [Section snippets](https://www.sciencedirect.com/science/article/abs/pii/S1059056024003010#section-snippets)
- [References (38)](https://www.sciencedirect.com/science/article/abs/pii/S1059056024003010#references)

## Abstract

This paper examines the profitability of simple [technical trading rules](https://www.sciencedirect.com/topics/economics-econometrics-and-finance/behavioural-finance) in [bitcoin](https://www.sciencedirect.com/topics/economics-econometrics-and-finance/bitcoin) markets comprehensively, by taking into account realistic investor behaviour and transaction costs, and [data mining](https://www.sciencedirect.com/topics/earth-and-planetary-sciences/data-mining) problems. Realistic investor behaviour is replicated by first employing 75,360 simple [technical trading rules](https://www.sciencedirect.com/topics/economics-econometrics-and-finance/behavioural-finance), divided over 6 commonly used trading rule classes and daily and intraday frequencies. Next, we select the best performing rules after transaction costs using a multiple hypothesis procedure. Finally, we form portfolios combining the selected rules and analyse their out-of-sample performance. We find that, especially risk–return wise, simple technical trading rules can outperform a buy-and-hold strategy in the [bitcoin](https://www.sciencedirect.com/topics/economics-econometrics-and-finance/bitcoin) market out-of-sample.

## JEL classification

G11

;

G14

;

G17

## Keywords

Bitcoin

;

Technical analysis

;

False discovery rate

;

Intraday

- [Previous article in this issue](https://www.sciencedirect.com/science/article/pii/S1059056024003186)
- [Next article in this issue](https://www.sciencedirect.com/science/article/pii/S1059056024002922)

## Introduction

In 2008 in the midst of the global financial crisis and amidst growing public distrust in financial institutions, Satoshi Nakamoto (2008) introduced a peer-to-peer electronic cash system, named Bitcoin. Two key characteristics of Bitcoin are that it does not need any trusted third party in order to process electronic payments, and that it has a supply regulated by a fixed, known algorithm, attempting to reduce the influence of financial intermediaries and central authorities. More than a decade since its inception, Bitcoin is well known by the general public, mainly due to its exponential increase in value. However, as a relatively new asset without any apparent intrinsic value, the bitcoin market has been plagued by high volatility, market inefficiencies and bubbles (Bariviera et al., 2017, Cheah and Fry, 2015, Kristoufek, 2018, Nadarajah and Chu, 2017, Sensoy, 2019, Urquhart, 2016). Following the efficient market hypothesis, these circumstances in the market should theoretically make bitcoin returns more predictable and the use of technical analysis profitable.

At the time of writing some research has already been done regarding profitability of technical trading rules in bitcoin markets. A short overview of the existing literature is given in Table 1. First we take a look at the studies using daily price data. Gerritsen et al. (2020) examine the Sharpe ratios of 7 trend-following indicators between 2010 and 2018 using daily price data. They find that mainly support-and-resistance (S&R) rules outperform a buy-and-hold strategy in terms of risk-adjusted measures during their full sample period, mainly during bull or bear markets. Grobys et al. (2020) test a small set of moving average (MA) rules between 2016 and 2018 across 11 cryptocurrencies using a multivariate test. They find return predictability across different cryptocurrencies, irrespective of whether bitcoin is accounted for. Detzel et al. (2021) propose a new equilibrium theory that shows that price-to-MA ratios can forecast returns of assets with hard-to-value fundamentals. To confirm their model empirically, a study evaluating a limited sample of MA strategies between 2010 and 2018 is conducted. They find that simple MA rules outperform, with mainly a significant Sharpe ratio and/or alpha, a buy-and-hold strategy out-of-sample (OOS). The trading rules have a better performance before 2014, which is in line with the literature finding that the bitcoin market is becoming more efficient over time. Hudson and Urquhart (2021) test 14,919 technical trading rules using multiple hypothesis procedures between 2010 and 2017. They compare 5 classes of trading rules and find that all classes improve the risk-adjusted performance in cryptocurrency markets, with filter and channel breakout (CB) rules having the best performance. After calculating break-even transaction costs, they conclude that their results for S&R rules would not hold in realistic market conditions. However, they do not find out-of-sample (OOS) outperformance for bitcoin. As far as we know, three studies assess the profitability using high-frequency trading data. Corbet et al. (2019) test a small set of MA rules and S&R rules using different intraday price data between 2014 and 2018. They find that the variable MA strategy is most profitable on the 1-minute trading frequency. Miller et al. (2019) use 1-minute high frequency data between February and March 2018 to identify various possible chart patterns (e.g. head-and-shoulders pattern). They find that some patterns result in great absolute returns over a buy-and-hold benchmark. Svogun and Bazán-Palomino (2022) test 69 MA and S&R rules on the 1-minute and daily trading frequencies for 5 different cryptocurrencies between 2016 and November 2021. They look at performance after transaction costs, which are approximated by fees paid to miners1. They find that technical trading rules can outperform a buy-and-hold benchmark in the bitcoin market, and furthermore that trading on a daily basis is more robust to transaction costs. For bitcoin, trading rules are more likely to outperform the benchmark during downturns and not during bubbles.

Generally these studies show that there is evidence of profitability of technical trading rules for different trading frequencies and technical trading rule classes in the bitcoin market. However, looking at Table 1 we see some possibilities to extend the existing literature. First, only one study has a sample period that ends after 2018. Bitcoin, being a relatively new asset, has undergone various changes, most interestingly in terms of market efficiency and conditions, availability of derivatives and regulations, throughout the years. The popularity of bitcoin soared at the end of 2017,2 and although the general public interest reached its peak in 2017, it stayed at a more elevated level than before 2017. Various studies find that the bitcoin market is becoming more efficient over time (Bariviera et al., 2017, Nadarajah and Chu, 2017, Sensoy, 2019), and shorting, margin and derivative trading have been introduced on various exchanges after 2017, therefore an updated, longer sample period may be of interest. Second, research has shown that technical analysis is used by professionals in the foreign exchange market mainly on the short and medium term (Menkhoff and Taylor, 2007, Park and Irwin, 2007). Despite this, only 3 studies use intraday price data, but at a very high frequency (1-minute). Third, when evaluating the performance of the trading rules, not all studies take into account: (1) The risk-adjusted performance, which may be of interest for portfolio management (2) Transaction costs, which severely limit the profitability of trading rules with many transactions. Typically there is a trade-off between more closely following the price due to more trading signals and higher transaction costs. A recent study shows that omitting costs from your analysis can inflate false discoveries (Anghel, 2022) (3) OOS performance and multiple hypothesis tests, which help in limiting spurious results from data mining. (4) some studies look at a limited set of trading rules, while there exists many popular classes with a limitless amount of parameterizations. Realistically, investors combine signals from these different trading rules and trading frequencies, usually selecting the best performing rules after transaction costs and after good OOS performance. We add to the existing literature by combining a wide range of technical trading rules across intraday and daily trading frequencies, mimicking more realistic investor behaviour, and testing their profitability after transaction costs and OOS, while taking into account data mining.

## Organizational access

Get full-text access by signing in with your organisation [Access through **your organization**](https://www.sciencedirect.com/user/institution/login?targetUrl=%2Fscience%2Farticle%2Fpii%2FS1059056024003010)

### Other access options

[Purchase PDF](https://www.sciencedirect.com/getaccess/pii/S1059056024003010/purchase)

[Need help with access?](https://service.elsevier.com/app/answers/list/c/10543/supporthub/sciencedirect/)

## Section snippets

### Data

We use tick-by-tick transaction data from Bitstamp3, a online cryptocurrency exchange, which contains the volume and exchange rate of each trade of the BTC-USD pair between 2012 and 2022. After cleaning the data with the method described in Brownlees and Gallo (2006)4

### Methodology

In this paper we attempt to mimic more realistic investor behaviour and circumstances. Technical traders usually use various classes of technical trading rules and various trading horizons and frequencies concurrently. By combining the input from these two dimensions they decide whether to buy or sell a certain asset, giving more importance to rules with high historical outperformance (Menkhoff & Taylor, 2007). They aim to optimize their profits net of costs and OOS.

Keeping this in mind, we use

### Results

Table 3 shows the OOS-performance of our in-or-out strategy portfolios after transaction costs and the performance of the buy-and-hold benchmark. Panel (a) shows the general performance of portfolios containing the best performing rule (Best), the 50 best performing rules (Best 50), and the rules selected by the FDR+-methodology (FDR-10%) in terms of either the mean excess return or the Sharpe ratio. Starting from the left, the total (logarithmic) return shows that the three mean-return

### Discussion

Although we show that it is possible to outperform, in terms of absolute return or risk-adjusted performance measures, a buy-and-hold strategy in bitcoin using simple technical trading rules, certain remarks about our results can be made.

First, because we do not allow shorting, our technical trading rules may not be able to profit overtly from price decreases. Shorting is not possible on Bitstamp, but may have been possible on other bitcoin exchanges during our sample. Usually shorting has

### Conclusion

In this paper we study if the use of simple technical trading rules can outperform buying and holding bitcoins. We attempt to do this by first selecting outperforming rules, from a set of 75,360 possible trading rules, then combining them in different portfolios and finally assessing their performance out-of-sample after ‘realistic’ transaction costs. Compared to earlier research, which generally concludes that trading rules can outperform a buy-and-hold strategy in the bitcoin market, we apply

### CRediT authorship contribution statement

**Niek Deprez:** Conceptualization, Formal analysis, Investigation, Resources, Software, Writing – original draft, Writing – review & editing, Visualization. **Michael Frömmel:** Project administration, Resources, Funding acquisition, Supervision, Writing – original draft, Writing – review & editing.

## Acknowledgements

The computational resources (Stevin Supercomputer Infrastructure) and services used in this work were provided by the VSC (Flemish Supercomputer Center), funded by Ghent University, Belgium, FWO, Belgium and the Flemish Government – department EWI .

## References (38)

- AnghelD.G.

### [No pain, no gain: You should always incorporate trading costs for a bias-free evaluation of trading rule overperformance](https://www.sciencedirect.com/science/article/pii/S0165176522001720)




### Economics Letters



(2022)

- BajgrowiczP. _et al._

### [Technical trading revisited: False discoveries, persistence tests, and transaction costs](https://www.sciencedirect.com/science/article/pii/S0304405X1200116X)




### Journal of Financial Economics



(2012)

- BarivieraA.F. _et al._

### [Some stylized facts of the Bitcoin market](https://www.sciencedirect.com/science/article/pii/S0378437117304697)




### Physica A



(2017)

- BrownleesC.T. _et al._

### [Financial econometric analysis at ultra-high frequency: Data handling concerns](https://www.sciencedirect.com/science/article/pii/S0167947306003458)




### Computational Statistics & Data Analysis



(2006)

- CheahE.-T. _et al._

### [Speculative bubbles in Bitcoin markets? An empirical investigation into the fundamental value of Bitcoin](https://www.sciencedirect.com/science/article/pii/S0165176515000890)




### Economics Letters



(2015)

- CorbetS. _et al._

### [The effectiveness of technical trading rules in cryptocurrency markets](https://www.sciencedirect.com/science/article/pii/S1544612319300315)




### Finance Research Letters



(2019)

- GerritsenD.F. _et al._

### [The profitability of technical trading rules in the Bitcoin market](https://www.sciencedirect.com/science/article/pii/S1544612319303770)




### Finance Research Letters



(2020)

- GrobysK. _et al._

### [Technical trading rules in the cryptocurrency market](https://www.sciencedirect.com/science/article/pii/S1544612319308852)




### Finance Research Letters



(2020)

- HsuP.H. _et al._

### [Technical trading: Is it still beating the foreign exchange market?](https://www.sciencedirect.com/science/article/pii/S0022199616300472)




### Journal of International Economics



(2016)

- KristoufekL.

### [On Bitcoin markets (in)efficiency and its evolution](https://www.sciencedirect.com/science/article/pii/S0378437118302413)




### Physica A. Statistical Mechanics and its Applications



(2018)


NadarajahS. _et al._

### [On the inefficiency of Bitcoin](https://www.sciencedirect.com/science/article/pii/S0165176516304426)

### Economics Letters

(2017)

SensoyA.

### [The inefficiency of Bitcoin revisited: A high-frequency analysis with alternative currencies](https://www.sciencedirect.com/science/article/pii/S1544612318302320)

### Finance Research Letters

(2019)

SvogunD. _et al._

### [Technical analysis in cryptocurrency markets: Do transaction costs and bubbles matter?](https://www.sciencedirect.com/science/article/pii/S1042443122000816)

### Journal of International Financial Markets, Institutions and Money

(2022)

UrquhartA.

### [The inefficiency of Bitcoin](https://www.sciencedirect.com/science/article/pii/S0165176516303640)

### Economics Letters

(2016)

BarrasL. _et al._

### False discoveries in mutual fund performance: Measuring luck in estimated alphas

### The Journal of Finance

(2010)

BenjaminiY. _et al._

### Controlling the false discovery rate: A practical and powerful approach to multiple testing

### Journal of the Royal Statistical Society. Series B. Statistical Methodology

(1995)

BitstampY.

### PRESS RELEASE: Bitstamp introduces volume discount program

(2012)

BitstampY.

### Bitstamp is open for business - better than ever!

(2015)

BitstampY.

### Reduced fee schedule

(2015)

View more references

[View full text](https://www.sciencedirect.com/science/article/pii/S1059056024003010)

## Recommended articles

### Based on reading popularity

- Research articleOpen access



[Enhancing operation effectiveness by maximizing daily EBITDA as a turnaround strategy execution system to enhance operation performance and profitability](https://www.sciencedirect.com/science/article/pii/S2199853124002257)

RudySetyopurnomo, …, SubiaktoSukarno

Journal of Open Innovation: Technology, Market, and Complexity • Volume 11, Issue 1 • 2025 • Article 100431

- Research articleOpen access



[Recurrent glioblastoma in national guidelines on the diagnosis and treatment of gliomas: A matter of European practice variation](https://www.sciencedirect.com/science/article/pii/S2772529424011792)

Mark P.van Opijnen, …, Marike L.D.Broekman

Brain and Spine • Volume 4 • 2024 • Article 103923

- Review articleOpen access



[Therapeutic management of uterine tumours resembling ovarian sex cord tumours including a focus on fertility: A systematic review](https://www.sciencedirect.com/science/article/pii/S0301211524000472)

MamiShibahara, …, KiyoshiYoshino

European Journal of Obstetrics & Gynecology and Reproductive Biology • Volume 295 • 2024 • Pages 1-7

- Research articleOpen access



[Bottlenecks to glass return and refill in the United Kingdom: User Journeys to explore industry perspectives](https://www.sciencedirect.com/science/article/pii/S2666188824000479)

SteveCinderby, JeanMcKendree

Sustainable Futures • Volume 7 • 2024 • Article 100197


## Cited by (2)

- [Multi-objective genetic programming-based algorithmic trading, using directional changes and a modified sharpe ratio score for identifying optimal trading strategies](http://www.scopus.com/scopus/inward/record.url?partnerID=10&rel=3.0.0&view=basic&eid=2-s2.0-105026952806&md5=4fd5794431c336eb7ea552d1475646)

Long X., …, Papastylianou T.

Artificial Intelligence Review • Volume 59 • 2026 • Article 39

- [Bitcoin Prediction: A Hybrid Approach with Recurrent Neural Networks and GPT-Based Reasoning](http://www.scopus.com/scopus/inward/record.url?partnerID=10&rel=3.0.0&view=basic&eid=2-s2.0-105048237778&md5=7081a720abc6e813d672d098b130ad7d)

Cui Z., …, Bezbradica M.

Communications in Computer and Information Science • Volume 2950 CCIS • 2026


## Metrics

### Citations

- Citation Indexes2

### Captures

- Mendeley Readers17

![PlumX Metrics Logo](https://www.sciencedirect.com/eu-west-1/prod/5f6716225f1159fc4ed76eb0fbb2dfd9d1034a4b/logo/plumx-logo.png)[View details](https://plumx.elsevier.com/plum/a/?doi=10.1016%2Fj.iref.2024.05.003&theme=plum-sciencedirect-theme&hideUsage=true)

© 2024 Elsevier Inc. All rights reserved.

Persistent link using digital object identifier (DOI)

The Identity Selector: Persistence Service