Source: https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110
Title: Backtest overfitting in the machine learning era: A comparison of out-of-sample testing methods in a synthetic controlled environment - ScienceDirect
Fetched: 2026-11-18T09:28:23.875Z

[Skip to main content](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110#main) [Skip to article](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110#article)

[![Knowledge-Based Systems](https://ars.els-cdn.com/content/image/1-s2.0-S0950705124X00210-cov200h.gif)](https://www.sciencedirect.com/journal/knowledge-based-systems/vol/305/suppl/C)

## [Knowledge-Based Systems](https://www.sciencedirect.com/journal/knowledge-based-systems "Go to Knowledge-Based Systems on ScienceDirect")

Date: 3 December 2024

Article: 112477

Volume: [Volume 305](https://www.sciencedirect.com/journal/knowledge-based-systems/vol/305/suppl/C "Go to table of contents for this volume/issue")

View accessibility information

## Published by: Elsevier

### Published by

[![Elsevier](https://www.sciencedirect.com/us-east-1/prod/e911374836fc26c65c00085fe87e2195e64294ae/image/elsevier-non-solus.svg)](https://www.sciencedirect.com/journal/knowledge-based-systems "Go to Knowledge-Based Systems on ScienceDirect")

Show more

Research article

[Get rights and content](https://s100.copyright.com/AppDispatchServlet?publisherName=ELS&contentID=S0950705124011110&orderBeanReset=true)

# Backtest overfitting in the machine learning era: A comparison of out-of-sample testing methods in a synthetic controlled environment

Author links open overlay panelHamidArianb12, DanielNorouzi Mobarekehc23, [LuisSecoa24](https://www.sciencedirect.com/author/6603661478/luis-angel-seco)

Show more

Cite

Add to Mendeley

Share

[10.1016/j.knosys.2024.112477](https://doi.org/10.1016/j.knosys.2024.112477)

[Access through **your organization**](https://www.sciencedirect.com/user/institution/login?targetUrl=%2Fscience%2Farticle%2Fpii%2FS0950705124011110) [Purchase PDF](https://www.sciencedirect.com/getaccess/pii/S0950705124011110/purchase)

More actions

## Article preview

- [Abstract](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110#abstracts)
- [Introduction](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110#introduction)
- [Section snippets](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110#section-snippets)
- [References (34)](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110#references)

## Abstract

We present a comprehensive framework to assess these methods, considering the unique characteristics of financial data like non-stationarity, [autocorrelation](https://www.sciencedirect.com/topics/earth-and-planetary-sciences/autocorrelation), and regime shifts. Through our analysis, we unveil the marked superiority of the Combinatorial Purged (CPCV) method in mitigating overfitting risks, outperforming traditional methods as evidenced by its lower Probability of Backtest Overfitting (PBO) and superior Deflated Sharpe Ratio (DSR) test statistic. Walk-Forward, by contrast, exhibits notable shortcomings in false discovery prevention, characterized by increased temporal variability and weaker [stationarity](https://www.sciencedirect.com/topics/engineering/stationarity). This contrasts with CPCV’s demonstrable stability and efficiency. We introduce novel variants of [CPCV](https://www.sciencedirect.com/topics/social-sciences/cross-validation), including Bagged [CPCV](https://www.sciencedirect.com/topics/social-sciences/cross-validation) and Adaptive CPCV, which enhance robustness through ensemble approaches and dynamic adjustments based on market conditions. Our empirical validation using historical SP 500 data confirms these advanced cross-validation methods’ practical applicability and resilience. The analysis also suggests that choosing between Purged K-Fold and K-Fold necessitates caution due to their comparable performance and potential impact on the robustness of training data in out-of-sample testing. Our investigation utilizes a Synthetic Controlled Environment incorporating advanced models like the Heston Stochastic Volatility, Merton Jump Diffusion, and Drift-Burst Hypothesis alongside regime-switching models. This approach provides a nuanced simulation of market conditions, offering new insights into evaluating cross-validation techniques. We also address the computational aspects of these methods, demonstrating that parallelization significantly improves efficiency, making them feasible for large-scale financial datasets. Our study underscores the necessity of specialized validation methods in [financial modeling](https://www.sciencedirect.com/topics/social-sciences/financial-modelling), especially in the face of growing regulatory demands and complex market dynamics.

## Keywords

Quantitative finance

;

Machine learning

;

Cross-validation

;

Probability of backtest overfitting

- [Previous article in this issue](https://www.sciencedirect.com/science/article/pii/S0950705124012991)
- [Next article in this issue](https://www.sciencedirect.com/science/article/pii/S0950705124012905)

## Introduction

The financial sector has witnessed a paradigmatic shift by integrating sophisticated statistical models and machine learning techniques into its analytical framework. The transition from traditional quantitative methods to more advanced, data-driven approaches signifies a new epoch in financial analysis, marked by the capability to process and analyze extensive datasets, revealing intricate market patterns previously obscured by the limitations of conventional methods. A key catalyst for this transformation has been the significant advancements in computational technology and the rise of high-frequency trading practices. These developments have led to a fundamental change in market dynamics. As a result, the need for robust and reliable model evaluation methodologies, particularly in cross-validation techniques, has gained unprecedented importance. Such methods are integral to maintaining the integrity and effectiveness of financial models, which are essential in guiding decision-making processes across a spectrum of financial activities, from asset allocation to risk management, in both buy-side and sell-side institutions.5

The impetus for our research stems from a pivotal observation: despite substantial progress in financial modeling and an escalating reliance on machine learning algorithms, there is a glaring shortfall in effectively validating these models within the ambit of financial markets. This research gap becomes more pronounced when considering the extensive literature on predicting market factors. Yet, there is a conspicuous lack of discussion on tailoring cross-validation algorithms to accurately assess these models \[4\], \[5\]. Further complicating this landscape is the paucity of research dedicated to critically evaluating the backtesting and cross-validation algorithms. We hypothesize that the limited exploration in this domain is attributable to the inherent complexities of financial datasets, which are typically noisy, non-stationary, and characterized by intricate patterns shaped by various variables, from macroeconomic shifts to market sentiments. These unique dataset attributes often render traditional cross-validation methods insufficient or misleading \[4\]. The grave consequences of model inaccuracies in this context cannot be overstated, as they can lead to substantial financial losses and pose systemic risks. This highlights the critical need to develop and refine cross-validation methodologies for navigating financial data nuances. While hedge funds and investment firms might have practical approaches to address these challenges, there is a stark silence in the academic literature on this imperative issue. Our study seeks to bridge this gap, providing insights and methodologies vital for the rigorous evaluation of financial models, thereby catering to finance’s academic and practical realms.

A variety of strategies have been developed to combat overfitting in machine learning, as highlighted in the literature \[4\], \[6\], \[7\]. However, these strategies often tend to be model-specific, lacking a broader application to decision-making. This highlights the necessity for advanced out-of-sample testing methods that go beyond the limitations of individual models, promoting robust decision-making across various scenarios. The field of quantitative finance has witnessed a notable shift towards specialized cross-validation (CV) techniques, designed specifically to address the unique challenges presented by financial market data. Conventional methods like K-Fold Cross-Validation and Walk-Forward Cross-Validation, while effective in various analytical contexts, have also seen innovative extensions to enhance model selection and evaluation. Notably, the repeated double cross-validation (rdCV) method by \[8\] has been successfully employed in the context of multi-objective genetics-based machine learning, illustrating the versatility and potential of these methodologies beyond their traditional applications. Despite these successes in other domains, when applied to financial markets, these conventional methods show limitations due to their inability to adequately account for the temporal dependencies and non-stationarity inherent in financial time series. Recognizing these shortcomings, Lopez de Prado introduced advanced CV techniques specifically designed for financial applications. Purged K-Fold Cross-Validation, as outlined by \[4\], enhances the standard K-Fold method by incorporating a ‘purging’ mechanism, eliminating data from the training set that could inadvertently leak information about the test set. This approach is particularly critical in financial modeling to prevent lookahead biases. Further advancing the field, Lopez de Prado’s Combinatorial Purged Cross-Validation (CPCV) method offers a robust solution for backtesting trading strategies. Unlike traditional CV methods, CPCV creates multiple training and testing combinations, ensuring that each data segment is used for training and validation, thus providing a more comprehensive assessment of a strategy’s performance across various market scenarios. This method respects the chronological ordering of data and effectively addresses the risk of overfitting, a prevalent issue in the development of financial models.

The evolution of financial modeling has necessitated advanced methodologies to effectively address the challenges of overfitting and false discoveries in strategy evaluation. Pioneering contributions by \[9\], \[10\], \[11\], brought to the fore the need for rigorous evaluation of trading strategies. They introduced quantifiable metrics like the Probability of Backtest Overfitting (PBO) and the Deflated Sharpe Ratio (DSR), which provided a statistical basis to assess the reliability of backtested strategies. Despite these advancements, a significant gap exists in the literature: a comprehensive framework linking backtest overfitting assessment with the effectiveness of out-of-sample testing methodologies. Our study addresses this gap by proposing a novel framework that evaluates out-of-sample testing techniques through the prism of backtest overfitting. By integrating key concepts such as PBO and DSR into our analysis, we aim to provide a holistic evaluation of CV methods, ranging from traditional data science approaches to innovative financial models like those proposed by Lopez De Prado. This approach ensures financial models’ robustness and predictive power, filling a critical void in quantitative finance.

Advancements in synthetic data generation within financial analysis have seen the integration of sophisticated models that adeptly replicate complex market dynamics. Our study’s Synthetic Controlled Environment embraces this complexity by merging the Heston Stochastic Volatility Model, characterized by the stochastic differential equation dSt=μStdt+νtStdWtS \[12\], with the Merton Jump Diffusion Model \[13\], which introduces jumps in asset prices through dSt=μStdt+σStdWt+StdJt. Following this, we explore the context of speculative market bubbles (see \[14\]). \[15\] categorizes bubbles into Type-I and Type-II, with Type-I characterized by an efficient full price process S but inefficiencies in both pre-drawdown S̃ and drawdown X processes, and Type-II by an efficient drawdown process X but an overall inefficient S. This categorization provides a nuanced understanding of bubble dynamics in financial markets. Building on this foundation, our environment further incorporates the Drift Burst Hypothesis \[16\], articulating short-lived market anomalies through equations μtdb=a\|τdb−t\|−α and σtvb=b\|τdb−t\|−β, emphasizing the critical interplay between drift and volatility during such events. The addition of the Markov Chain model for regime transitions \[17\], characterized by its transition matrix P=\[Pij\], enables the simulation to adeptly mirror fluid market states adeptly, capturing the ephemeral nature of financial markets. This innovative amalgamation of stochastic volatility, jump-diffusion, bubble dynamics, and regime-switching, cohesively combined in our Synthetic Controlled Environment, sets a groundbreaking precedent in the domain of financial model testing and validation, presenting a comprehensive framework for evaluating out-of-sample testing methodologies in the nuanced and intricate world of quantitative finance.

Recent advancements in artificial intelligence and machine learning have highlighted cross-disciplinary methodologies’ need for model validation. For example, \[18\] discusses the evolving role of AI in distance learning, emphasizing how AI tools adapt to dynamic educational environments by processing and analyzing student data to suggest personalized learning materials. Their adaptive approach highlights the necessity for advanced cross-validation techniques like CPCV, which must account for the temporal dependencies and non-stationarity inherent in the models that analyze student data. One example of such heterogeneity is the COVID-19 period and how students performed. Advanced cross-validation techniques are, therefore, necessary to provide robust solutions for educational decision-making applications. As another example, \[19\] reviews supervised machine learning and deep learning techniques in computer vision, focusing on detecting and interpreting complex visual data. The methodologies used in computer vision, particularly in recognizing patterns and anomalies, can be analogously applied to financial time series, where detecting market anomalies and predicting trends are crucial (see \[20\]). By incorporating insights from these interdisciplinary studies, our framework for cross-validation may broaden its foundations and demonstrate potential applications for improving the robustness and reliability of AI models.

Despite the advancements in cross-validation techniques and market simulation models, significant limitations persist. Traditional CV methods like K-Fold and Walk-Forward Cross-Validation often fail to account for the temporal dependencies and non-stationarity inherent in financial time series, leading to potential overfitting and inaccurate performance assessments. Purged K-Fold and CPCV introduced by \[4\] address some of these issues but still require extensive validation across diverse market conditions to confirm their robustness. Similarly, market simulation models such as the Heston Stochastic Volatility and Merton Jump Diffusion Model, while sophisticated, may not fully capture the complex dynamics of real-world financial markets. Our study identifies the need for a comprehensive evaluation framework that integrates advanced out-of-sample testing methods like CPCV with a combination of diverse synthetic market simulations. This approach ensures a thorough assessment of model performance, addressing the limitations of existing methods and enhancing the reliability of financial model validation in quantitative finance.

Central to our study is a problem of increasing concern in financial analytics: developing a robust and reliable out-of-sample testing methodology congruent with the unique attributes of financial time series data. This issue is multifaceted. Firstly, financial time series are characterized by non-stationarity, autocorrelation, heteroskedasticity, and regime shifts, challenging the applicability of conventional out-of-sample testing methods. Secondly, the temporal dynamics of financial data, with intricate lead–lag relationships and evolutionary patterns, demand an out-of-sample testing approach that preserves the chronological sequence of data to avoid look-ahead bias and overfitting, issues frequently encountered in applying machine learning models in finance. Despite the remarkable advancements in integrating statistical models and machine learning techniques into financial analysis, a significant gap persists in accurately assessing these models, particularly under the challenges of backtest overfitting and the dynamic nature of financial markets. Our study specifically targets the inadequacy of existing cross-validation techniques, which, while robust in traditional data science contexts, fall short of fully capturing the temporal dependencies and non-stationarity of financial data. This gap is further widened by the lack of a comprehensive framework that integrates the assessment of backtest overfitting with the effectiveness of out-of-sample testing methodologies. The significance of this problem is not limited to theoretical modeling but has far-reaching implications in practical aspects like risk management, algorithmic trading, and portfolio optimization. Inaccuracies in model validation can lead to substantial financial risks and losses, accentuating the need for rigorous, tailored validation methods, especially under increasing regulatory scrutiny.

The central objective of our study is to develop a comprehensive evaluation framework for cross-validation methods in financial modeling, particularly in the context of evolving market complexities and the challenges of backtest overfitting. By incorporating key concepts like the PBO and the DSR, our framework holistically assesses various cross-validation approaches, ranging from traditional data science methods to more sophisticated financial models. The emphasis of this study is not inherently on the incorporation of sophisticated methodologies; rather, it centers on a critical assessment of the efficacy of these approaches when considering the distinctive attributes inherent in financial data. We aim to bridge the gap between theoretical robustness and practical reliability in financial models, enhancing their applicability in high-stakes financial decision-making, from asset allocation to risk management.

The novelty of this research is underscored by several key contributions. First, we employ a comprehensive approach that integrates both synthetic and real-world data to ensure our findings’ broad applicability and robustness. Second, the use of a Synthetic Controlled Environment allows for the simulation of various market conditions, including calm, volatile, and speculative bubble regimes, which provides a thorough validation framework that closely mimics real market dynamics. Third, we introduce novel variations of the CPCV method, such as Adaptive CPCV and Bagged CPCV, specifically designed to address the unique challenges of financial data, including non-stationarity and regime shifts. These innovative methods enhance robustness against overfitting and improve performance stability. Lastly, our study bridges the gap between theoretical robustness and practical reliability, offering insights and practical tools for financial model validation in an era characterized by complex algorithms and large datasets.

This study offers a comprehensive evaluation of cross-validation techniques within synthetic controlled environments and real-world financial data, emphasizing their robustness against backtest overfitting. The scope encompasses diverse market conditions, modeled through sophisticated approaches such as the Heston Stochastic Volatility and Merton Jump Diffusion models, along with novel empirical techniques like the Drift Burst Hypothesis and regime-switching Markov models. Our findings contribute significantly to the field of quantitative finance by providing actionable insights into selecting and implementing cross-validation methods for robust financial model validation. However, the study has certain limitations. First, while the synthetic environment allows for extensive experimentation, it may not capture all nuances of real-world market dynamics. Second, the reliance on specific models and parameters means that the results might not generalize across all market conditions or financial instruments. Additionally, the computational intensity of advanced cross-validation methods, especially CPCV, could limit their practical application in real-time trading systems without substantial computational resources. Despite these constraints, the study’s methodologies and findings offer valuable guidance for financial practitioners and researchers aiming to enhance model reliability and performance in various market scenarios.

This paper is systematically structured to explore cross-validation techniques in synthetic market environments comprehensively. The paper opens with **Introduction** 1, setting the stage by delineating the research background, objectives, and the scope of the study. Following this, the **Methodology** Section 2 explores the details of the statistical models and algorithms employed, outlining the framework for synthetic data generation and analysis. The **Empirical Results** Section 3 thoroughly examines our rigorous testing and analysis findings, providing insights into the performance and robustness of various cross-validation methods. In the **Discussion and Conclusion** Section 4, we interpret these findings, contextualizing them within the broader landscape of quantitative finance and discussing their implications. Moreover, we summarize the key takeaways, acknowledge the limitations of our study, and suggest directions for future research.

## Organizational access

Get full-text access by signing in with your organisation [Access through **your organization**](https://www.sciencedirect.com/user/institution/login?targetUrl=%2Fscience%2Farticle%2Fpii%2FS0950705124011110)

### Other access options

[Purchase PDF](https://www.sciencedirect.com/getaccess/pii/S0950705124011110/purchase)

[Need help with access?](https://service.elsevier.com/app/answers/list/c/10543/supporthub/sciencedirect/)

## Section snippets

### Methodology

The methodology section forms the backbone of our research, presenting a comprehensive and systematic approach to exploring and analyzing financial market dynamics through machine learning and statistical methods. This section outlines the construction and utilization of a Synthetic Controlled Environment, which integrates complex market models such as the Heston Stochastic Volatility and Merton Jump Diffusion models and incorporates regime-switching dynamics through Markov chains.

### Empirical results

In this section, we present a comprehensive empirical investigation designed to perform a comparative analysis of cross-validation techniques within a synthetic controlled environment. Our empirical endeavor is meticulously constructed to evaluate the robustness of these techniques against backtest overfitting—a critical pitfall in the development and validation of financial models. The exploration unfolds across a series of simulations replicating market conditions, informed by sophisticated

### Summary of key findings and interpretation of results

Our study evaluates various cross-validation techniques in mitigating backtest overfitting within a synthetic controlled environment and real-world data. Key findings include:

## Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## References (34)

- BramerMax

### [Using j-pruning to reduce overfitting in classification trees](https://www.sciencedirect.com/science/article/pii/S0950705101001630)




### Knowl.-Based Syst.



(2002)

- Beltran-RoyoCesar _et al._

### [Dc neural networks avoid overfitting in one-dimensional nonlinear regression](https://www.sciencedirect.com/science/article/pii/S0950705123009048)




### Knowl.-Based Syst.



(2024)

- IshibuchiHisao _et al._

### [Repeated double cross-validation for choosing a single solution in evolutionary multi-objective fuzzy classifier design](https://www.sciencedirect.com/science/article/pii/S0950705113003109)




### Knowl.-Based Syst.



(2013)

- MertonRobert C.

### [Option pricing when underlying stock returns are discontinuous](https://www.sciencedirect.com/science/article/pii/0304405X76900222)




### J. Financ. Econ.



(1976)

- ChristensenKim _et al._

### [The drift burst hypothesis](https://www.sciencedirect.com/science/article/pii/S0304407620303912)




### J. Econometrics



(2022)

- ArianHamid _et al._

### [Encoded value-at-risk: A machine learning approach for portfolio risk measurement](https://www.sciencedirect.com/science/article/pii/S0378475422003172)




### Math. Comput. Simulation



(2022)

- XieYurong _et al._

### [Vulnerable European option pricing in a Markov regime-switching Heston model with stochastic interest rate](https://www.sciencedirect.com/science/article/pii/S0960077922001072)




### Chaos Solitons Fractals



(2022)

- RiskLabAI

### Risklab ai python library


(2024)

- RiskLabAI

### Risklab ai julia library


(2024)

- RiskLabAI

### Python implementation of the paper: Backtest overfitting in the machine learning era


(2024)


de PradoMarcos Lopez

### Advances in Financial Machine Learning

(2018)

de PradoMarcos Lopez

### Machine Learning for Asset Managers

(2020)

BaileyDavid H. _et al._

### The probability of backtest overfitting

### J. Comput. Finance

(2016)

BaileyDavid H. _et al._

### The deflated sharpe ratio: Correcting for selection bias, backtest overfitting and non-normality

### J. Portf. Manag.

(2014)

BaileyDavid H. _et al._

### Pseudomathematics and financial charlatanism: The effects of backtest over fitting on out-of-sample performance

### Notices Amer. Math. Soc.

(2014)

HestonSteven L.

### A closed-form solution for options with stochastic volatility with applications to bond and currency options

### Rev. Financ. Stud.

(1993)

HommUlrich _et al._

### Testing for speculative bubbles in stock markets: a comparison of alternative methods

### J. Financ. Econom.

(2012)

View more references

[1](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110#bfn1)

Assistant Professor of Finance, York University, Toronto, Ontario, Canada.

[2](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110#bfn2)

Authors are listed in alphabetical order.

[3](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110#bfn3)

Quantitative Researcher, RiskLab, University of Toronto, Ontario, Canada. BSc student of Applied Mathematics & Economics, Sharif University of Technology, Tehran, Iran.

[4](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110#bfn4)

Professor, University of Toronto, Ontario, Canada.

[View full text](https://www.sciencedirect.com/science/article/pii/S0950705124011110)

## Recommended articles

### Based on reading popularity

- Research article



[An examination of the cryptocurrency pump-and-dump ecosystem](https://www.sciencedirect.com/science/article/pii/S0306457321000169)

J.T.Hamrick, …, MarieVasek

Information Processing & Management • Volume 58, Issue 4 • 2021 • Article 102506

- Research article



[Intraday portfolio risk management using VaR and CVaR:A CGARCH-EVT-Copula approach](https://www.sciencedirect.com/science/article/pii/S0169207018300360)

MadhusudanKarmakar, SamitPaul

International Journal of Forecasting • Volume 35, Issue 2 • 2019 • Pages 699-709

- Chapter



[12 - Transferable approach for cardiac disease classification using deep learning](https://www.sciencedirect.com/science/article/pii/B9780128190616000124)

P.Gopika, …, K.P.Soman

Deep Learning Techniques for Biomedical and Health Informatics • 2020 • Pages 285-303

- Research article



[Using a Duffing control approach to control the single risk factor in complex social-technical systems](https://www.sciencedirect.com/science/article/pii/S0020025522002456)

WenchengHuang, …, RuiZhang

Information Sciences • Volume 596 • 2022 • Pages 264-279

- Research articleOpen archive



[Designing fuzzy time series forecasting models: A survey](https://www.sciencedirect.com/science/article/pii/S0888613X18306376)

MahuaBose, KalyaniMali

International Journal of Approximate Reasoning • Volume 111 • 2019 • Pages 78-99

- Research articleOpen access



[DROPO: Sim-to-real transfer with offline domain randomization](https://www.sciencedirect.com/science/article/pii/S0921889023000714)

GabrieleTiboni, …, VilleKyrki

Robotics and Autonomous Systems • Volume 166 • 2023 • Article 104432


## Cited by (14)

- Review article



[A survey on neurodynamics of deep learning: A unified perspective on architectures and optimization algorithms](https://www.sciencedirect.com/science/article/pii/S0925231226014396)

Shi T., …, Jin L.

Neurocomputing • Volume 696 • 2026 • Article 134041


Show abstract




Attempts across diverse disciplines to achieve a fundamental understanding of deep learning have advanced rapidly in recent years. However, the development of a unified framework linking deep neural network (DNN) architectures, optimization, and performance remains limited. In this paper, we propose a unified analytical framework to understand deep learning from the perspective of neurodynamics. We begin by systematically reviewing the literature that studies DNN architectures from the perspective of neurodynamics. Concurrently, by surveying papers that employ neurodynamics to describe the optimization process of DNNs, we provide an in-depth analysis of the neurodynamics underlying deep learning optimization algorithms, classifying them into zero-order, first-order, and second-order algorithms. The core contribution of this work lies in moving beyond the isolated treatment of DNN architectures and optimization algorithms. Instead, we argue that they function as two mutually coupled neurodynamic systems, whose intrinsic properties—such as stability and bifurcation characteristics—collectively determine the final performance of a deep learning model, including its generalization and robustness. This unified perspective not only offers profound insights into the behavior of existing deep learning models but also guides the future co-design of novel DNN architectures and effective optimization algorithms.

- Research article



[A hybrid XGB-ANN model integrated with Lion Optimization Algorithm for improved prediction accuracy and lactic acid yield optimization](https://www.sciencedirect.com/science/article/pii/S1359511325002508)

Shi Y., …, Shen Z.

Process Biochemistry • Volume 159 • 2025


Show abstract




Machine learning (ML) has been widely applied in industrial fields in recent years. However, ML faces challenges in fermentation production due to complex features and limited data. To overcome the limitations of single models and improve the prediction accuracy and stability of lactic acid fermentation, we combined six classical ML models with Artificial Neural Networks (ANN) separately in a serial manner to construct the Classical-ANN (C-ANN) hybrid models. Meanwhile, implemented the Lion Optimization Algorithm (LOA) to systematically optimize critical fermentation parameters and conducted experimental validation. While single models showed moderate performance (Extreme Gradient Boosting (XGB) R²= 0.9197; ANN R²= 0.9295), C-ANN hybrids demonstrated superior accuracy across all metrics. The XGB-ANN model achieved exceptional performance (R²=0.9850), benefiting from XGB's robust feature selection and ANN's high-dimensional processing capabilities. SHAP analysis revealed fermentation time as the most critical yield determinant, followed by total volume and pH. Lion Optimization Algorithm parameters enabled a predicted yield of 81.21 %, with experimental validation showing only 4.72 % deviation from predictions. This study not only provides valuable assistance for optimization of fermentation production conditions in the short term but also offers an innovative and effective modeling approach for future research in this field.

- Research article



[Decoding financial markets: Empirical DGPs as the key to model selection and forecasting excellence – A proof of concept](https://www.sciencedirect.com/science/article/pii/S0378437125001943)

Vogl M., …, Stanisic N.

Physica A: Statistical Mechanics and its Applications • Volume 666 • 2025 • Article 130542


Show abstract




In this study we demonstrate whether information about the empirical data generating process (DGP) can optimise quantitative model selection and present a proof-of-concept. We derive the empirical DGP characteristics of nine (financial) time-series and interpret these as model requirements. These insights are tested via a comparative cascadic out-of-sample prediction scheme to demonstrate potential outperformance. The empirical DGP characteristics of (denoised) daily adjusted logarithmic returns are extracted with a nonlinear dynamics analysis framework. Thereinafter, various forecasting models and error metrics are implemented for the non-filtered returns. The models’ out-of-sample performance is subsequently ranked across these multiple metrics. Finally, we assess the models' alignment with the empirical DGPs. Our results show that all time-series exhibit very similar dynamics, independent of the underlying asset class. The dynamics are characterised by a mixture of deterministic (hyper-)chaotic and stochastically imbued quasi-periodic motions. Further, these dynamics are visualised through the reconstructions of the strange (fractal) attractors of the time-series. Models that capture the dynamics best outperform standard benchmarks and other state-of-the-art methods. Nonetheless, we have to state an overall lack of suitable DGP-conform models. Finally, we critically discuss the robustness, sensitivity and implications of our approach and findings.

- Research article



[Price spread prediction in high-frequency pairs trading using deep learning architectures](https://www.sciencedirect.com/science/article/pii/S1057521924007257)

Liou J.-H., …, Cheng L.-C.

International Review of Financial Analysis • Volume 96 • 2024 • Article 103793


Show abstract




High-Frequency Trading (HFT) leverages advanced algorithms and high-speed data transmission to execute a large volume of trades within extremely short timeframes and generate profit. However, predicting stock prices in this context is challenging due to the frequent fluctuations in bid and ask conditions within financial markets. Institutional investors often employ pairs trading strategies to mitigate the systemic risk associated with single products, simultaneously buying and selling highly correlated financial instruments to profit from fluctuations in abnormal price spreads. In this study, we utilized intraday continuous trading data from the Taiwan Stock Exchange, integrating commonly used stock market features relevant to HFT. By employing XGBoost for feature selection and combining it with deep learning models, we aimed to predict the relationship between price spreads and boundaries in pairs trading, thereby generating entry and exit signals. Although accurately predicting the relationship between price spreads and boundaries presents significant challenges, the model effectively learned the pattern of price spread changes. Applying the model's entry and exit signals in pairs trading demonstrated that this strategy can enhance win rates and achieve stable profits in the volatile intraday market environment. This research provides practical implications for those interested in high-frequency trading and deep learning models in the financial market, equipping them with valuable knowledge and insights.

- [Deep Reinforcement Learning in Non-Markov Market-Making](http://www.scopus.com/scopus/inward/record.url?partnerID=10&rel=3.0.0&view=basic&eid=2-s2.0-105001290089&md5=4d701a509346cfe2b2b446218873796f)

Lalor L., Swishchuk A.

Risks • Volume 13 • 2025 • Article 40

- [Event-Based Limit Order Book Simulation under a Neural Hawkes Process: Application in Market-Making](http://www.scopus.com/scopus/inward/record.url?partnerID=10&rel=3.0.0&view=basic&eid=2-s2.0-105016821072&md5=30643ca395792e432fb817e2e6d39e8)

Lalor L., Swishchuk A.

Applied Mathematical Finance • Volume 32 • 2025


[View all citing articles on Scopus](http://www.scopus.com/scopus/inward/citedby.url?partnerID=10&rel=3.0.0&eid=2-s2.0-85207935266&md5=79c444705e36953920c8514df368b86)

## Metrics

### Citations

- Citation Indexes14

### Captures

- Mendeley Readers66

![PlumX Metrics Logo](https://www.sciencedirect.com/us-east-1/prod/e911374836fc26c65c00085fe87e2195e64294ae/logo/plumx-logo.png)[View details](https://plumx.elsevier.com/plum/a/?doi=10.1016%2Fj.knosys.2024.112477&theme=plum-sciencedirect-theme&hideUsage=true)

© 2024 Elsevier B.V. All rights are reserved, including those for text and data mining, AI training, and similar technologies.

Persistent link using digital object identifier (DOI)

The Identity Selector: Persistence Service