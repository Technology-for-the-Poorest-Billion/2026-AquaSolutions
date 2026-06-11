## Problem Specification: ​

80% of water consumption in Harare, Zimbabwe is from unregulated boreholes.​ Faecal contamination leads to waterborne disease outbreaks Allen's initial design involved a multi-sensor proxy based methods for detecting water contamination, a gap in the research space with lots of potential as ML methods rapidly improve.

The issues he had with his initial trial included:
- The fuzzy logic algorithm used collapsed on single sensor failure.
- The chosen proxies were insufficient to predict contamination.​
- Chlorine dosing is a high stakes output:​
    * Too much is toxic.​
    * Too little is ineffective.​






## Our Solution: A report-labelled water safety pipeline

 Informed by a literature review, data analysis and Allen Chafa's challenges with his first trial, we designed and began implementing a system architecture.

![System Architecture](www/System Architecture.png)

Decision Justification

- DHIS2 Dashboard - 

- SMS - 

- XGBoost Classifier - Capable of detecting complex, non-linear relationships between readings and water potability while natively handling missing data and sensor drift. Importantly, it is also compressable to a file size within the memory capacities of simple microcontrollers, including an Arduino.



## Technical summary

### Labelling logic

![Labelling logic](www/Label Logic.png)

Design Justification

- 7 day window - WHO Cholera incubation up to 5 days. Adding a 2 day reporting window, gives a 7 day rolling window.
- Discrete confidence tiers (thresholds are arbitrary and need calibration as data comes in)
    * Transparent and easy to update as understanding improves.
    * Sustained reporting, increases contamination likelihood. ​
    * No reports ≠ safe water. Low weighting used. ​
    * The 0.5 safe threshold is designed to filter out background illness reports.
- Logarithmic decay - Most cases present within 48 hours, so recent reports should carry more weight than older ones.

### ML pipeline

![C tree](www/C tree.png)

### Dashboard