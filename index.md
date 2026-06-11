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
    * Widely used, tried and tested​
    * Many VHWs already trained to use it​
    * Incorporates SMS capabilities and offline use 

- SMS - anyone can report without visiting a clinic or using a smartphone

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
XGBoost pipeline trained on synthetic data, ready to retrain when field data accumulates​. Easily understandable performance evaluation metrics are built in, including a Classification report, Confusion matrix, ROC Curve, AUC Score and SHAP Feature analysis. Each has a non-technical user friendly explanation attached. Note that the classifier carries out near perfect classification on the synthetic test set but this does not completely reflect its ability to cope with real data, except for validating that XGBoost is capable of detecting non-linear trends.

<div style="display:flex; gap:20px">
  <img src="www/Confusion.png" width="25%">
  <img src="www/SHAP.png" width="65%">
</div>

The confusion matrix (left) shows the model's predictions against the true labels for each reading in the test set. The most important cell is bottom left. A missed risk means contaminated water goes unflagged without triggering an alert. The goal is to minimise this number as much as possible. The SHAP feature analysis (right) indicates how much each metric influenced the prediction of risk (positive indicates pushed towards).

Model exported to C via m2cgen for offline inference on the sensor node. Below is one tree (of 100), it can be easily followed through a simple if not else structure:

<div style="text-align:center">
  <img src="www/C tree.png" width="500">
</div>

### Dashboard


The UI, composed of two dashboards for each of the governance and medical side of the healthcare system, went through two iterations. The first was developed using HTML. Screenshots of the dashboard are presented below, but it can also be accessed [here](gm2aquasolutions-production-aff9.up.railway.app). 

**Government Dashboard:**
<img width="880" height="380" alt="image" src="https://github.com/user-attachments/assets/4158ff1c-a6cd-4e46-bff4-1bfdf820b0dd" />

- Live water quality data which was simulated using [simulation.py](App/dhis2/etl/simulate.py) at each borehole. Each of these, based on previous medical reports, is also labelled as safe or unsafe using the green or red status pill. There are a few fake buttons for sending teams to collect a lab sample or shut down the borehole. These buttons are not functional, but were used as demonstrations of what could be done if the system were integrated into a multi-departmental organisation.
- On the right hand side, the history of medical reports and SMS notifications at various boreholes are summarised. Each of these contains a mini dataset obtained at the time of the event, but which has not yet been through our proposed labelling pipeline. 

**Medical Dashboard:**
<img width="880" height="313" alt="image" src="https://github.com/user-attachments/assets/eec7f260-233c-484d-99c0-6f78ea510210" />

- The medical dashboard illustrates a map of Harare and all of the simulated boreholes we have placed throughout the city. Each one is weighted, both in size and opacity, by the number of illness reports at each of these locations. A tab offers the opportunity to fill out a health form, and a summary of the previous reports is located at the bottom of the dashboard. 

### DHIS2 Webpage

After some further research into the digital healthcare situation in Zimbabwe and feedback from both GM2 supervisors and Mr.Chafa, we developed a second version of the UI. 
- We focused on improving the visibility and usability.
- How can we use the space more efficiently to communicate key health and water quality metrics? Can we route VHWs directly to the medical form to reduce friction in the UX? How can we make the UI more engaging?

**Government Dashboard:**
<img width="880" height="326" alt="image" src="https://github.com/user-attachments/assets/ba2532a8-0a59-43ed-acf8-705e2a3d5392" />

**Medical Dashboard:**
<img width="880" height="338" alt="image" src="https://github.com/user-attachments/assets/a9dbdf0b-e96f-472a-80e9-17c227d891ef" />

- The DHIS2 open-source software was chosen due to its documented case studies across developing countries. Many VHWs have already been trained to use it, making it very compatible with the local digital ecosystem in Harare. 
- To configure the dashboard, we used the Maintenance, User, Data Visualisation, and Map Apps. The changes we made relative to Version 1 presented the data in a more space efficient, impactful manner in order to draw the attention of decision-makers towards certain key metrics. However, other features such as SMS compatability still need to be integrated into the new webpage.

To access the webpage, you need to have an application called Docker installed. Once this is open on your computer, follow these steps to access and edit the webpage. The relationship between different applications and data elements may require some research beforehand to understand the DHIS2 software. 

1. Get the repo. In your terminal, run the following: 

git clone git@github.com:tristanjfmartin/GM2_Aqua_Solutions.git

cd GM2_Aqua_Solutions/App/dhis2

2. Start DHIS2. 

docker compose up -d

3. The demo may take a minute to load so be patient before troubleshooting. 
4. Pull up the demo. Go to http://localhost:8080. Use the login admin, district. 

# SDG and UNICEF Digital Design Principles Reflection
This project addresses the fundamental issue of access to safe water faced in many developing countries, and therefore looks to tackle **SDG 6**; Clean Water and Sanitation. The target location was Harare, Zimbabwe but the principles and methods in this project are directly applicable to many places that rely on unreliable borehole-sourced water. While odour, taste and sufficient quantities of water are a concern, the primary issue is water-borne diseases. Reliable, fast and robust detection of water safety is essential to preventing the spread of illness and preserving the health of the people that rely on these boreholes (**SDG 3** - Good Health and Well-Being). In developing countries, illness has a wider impact than in wealthier economies as civilians lack the same medical infrastructure and financial support, resulting in the devastation of livelihoods and increasing existing inequalities (**SDG 10** - Reduced Inequality).

<img width="220" height="220" alt="image" src="https://github.com/user-attachments/assets/f075b068-3604-4ae2-9341-64faed109752" />
<img width="220" height="220" alt="image" src="https://github.com/user-attachments/assets/497b2c63-0f8d-4047-8e37-fc4b1917609c" />
<img width="220" height="220" alt="image" src="https://github.com/user-attachments/assets/783760bf-01f3-4eea-ad90-c201f6b6e62d" />
<img width="220" height="220" alt="image" src="https://github.com/user-attachments/assets/ce9bfa27-f7ec-4e1f-81fe-bd9a1cba5314" />

Our solution involved developing a sensor-based approach data collection and labelling system through community-illness reports to train an edge-ML algorithm for potability prediction (**SDG 9** - Industry, Innovation and Infrastructure). Given the digital nature of the solution, UNICEF's principles for **Digital Development** were central to our approach. In order to **understand the ecosystem**, we had regular meetings with Allen (**Design with people**) to discuss the setbacks and weaknesses of his initial design and to receive feedback on our proposed solutions. He informed us of the current water situation in Harare and we adjusted our solutions appropriately. We adapted to the infrastructure realities and explored system architecture options, particularly whether our device would function at the house or village level, and reporting mechanism alternatives, settling for a combination of SMS and a web interface. We explored the health and medical procedures currently used in Zimbabwe and were able to integrate our interface with DHIS2, a leading medical data management system in Zimbabwe. Our proposal requires participation from Village Health Workers with whom we will look to form future partnerships to enable a solution and acquire further feedback during field implementation (**SDG 17** - Partnerships for the goals).

By building off Allen's initial design, we hoped to **'share, reuse and improve'**, keeping many of the initial working design elements while replacing the fragile fuzzy logic algorithm and removing the high stakes chlorine release system. We based our repository on open-source material like the XGBoost or m2cgen libraries, met regularly with supervisors and co-designer (Allen Chafa) and documented all decision making. We wrote a clear AI Declaration and used transparent logic for work, including confidence tiers, that could be easily altered or built off (**Clear, open and transparent practices**).

**Using evidence to improve outcomes** sits at the core of XGBoost-driven solution, designed to improve as more data arrives with confidence intervals directly paired to degree of evidence. The XGBoost method has in-built performance metrics for a user to easily understand. We have looked to **anticipate and mitigate harm** through a lightly-weighted safety reading, which tackles the key issue of false negatives. Absence of reports does not equal safe water and care will need to be used when selecting labelling thresholds in future to maintain this principle. Further steps will involve matching symptoms to diseases and potentially some lab based labelling to improve evidence reliability for initial training. When devising the labelling methodology, we considered the principles of **design for inclusion** and **establishing people first data practices** by implementing SMS reporting, with no requirement for a strong internetconnection, while keeping messages anonymous to avoid privacy issues.

