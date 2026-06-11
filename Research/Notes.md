# Notes

## Notes: WHO Drinking Water Quality Guidelines
- Comprehensive international standards document setting acceptable limits for physical, chemical, radiological, and microbiological parameters in drinking water.
- Provides a framework for national water quality regulations, including guidance on risk assessment, monitoring strategies, and water safety plans.
- Key parameters covered include turbidity, pH, dissolved oxygen, nitrates, heavy metals, and pathogens (e.g. E. coli, total coliforms).

## Notes: Advances in Technological Research for Online and In Situ Water Quality Monitoring — A Review
- Reviews the landscape of sensor-based and IoT-enabled water quality monitoring technologies, covering both optical and electrochemical approaches.
- Optical and Electrochemical Sensors: Measure physical parameters (color, turbidity, temperature), chemical parameters (chlorine, pH, dissolved oxygen, nitrogen, metals, ORP), and biological indicators (E. Coli, total coliforms). 
- IoT Enabled: Useful for remote areas.
- Phone-Based Tools: Use phone camera, but are significantly less accurate.

## Notes: A Review of the Application of Machine Learning in Water Quality Evaluation
- Surveys supervised and unsupervised ML approaches for water quality assessment, covering the full pipeline from data collection through model validation.
- First Step: Data collection, algorithm selection, model training, model validation.
- Supervised and unsupervised learning approaches are possible. RL makes sense, but accountability is difficult.
- Local sensors measure some variables, but not all (e.g. pathogen concentration). CNN trained to infer the state of these unmeasurable variables from images of the water.
- Consider the incorporation of meteorological data.
- Time-series (LSTM) work relatively well for predicting water quality over time. 

## Notes: Allen Chafa's Publication — Design of a Real-Time IoT Water Quality Monitoring System
- Presents a complete IoT-based system for real-time borehole water quality monitoring, where sensor readings are compared against WHO standards and control actions (e.g. chemical dosing) are triggered automatically via fuzzy logic.
- UN SDG 6: Clean water and sanitation for all.
- Manual Testing Processes: Lengthy, error-prone. Laboratory Testing: Long, costly, inaccessible.
- Overview: Data collection via IoT and sensors. Values are compared to standards and an SMS is sent to the borehole's users.

### System Architecture:
- Microcontroller (Arduino) and sensors measure temperature, pH, turbidity, dissolved oxygen, hardness, and dissolved solids.
- Optical dissolved oxygen sensors work by measuring the interaction between oxygen and dyes after exposure to blue light.
- Turbidity sensors use light to measure particle concentration. Hardness is measured using a oxidation reduction potential (ORP) sensor which uses a voltage.
- The solenoid water valve is used to control the water's flow.
- Real-time data is collected (requires Wifi) and is sent to ThingSpeak (a web-based application). The decision-making process uses the fuzzy logic algorithm designed via MATLAB/SIMULINK. Deviations from the WHO standards triggers a control action, often the release of automated chemical dosing units. If the water meets the standards, it it is allowed to flow to the next step. 
- Additionally, a copy of the sensor readings is sent to the user's phone via SMS using a Global System for Mobile (GSM) module.
- Real-time data is logged. 

<img width="536" height="476" alt="Screenshot 2026-05-18 at 1 38 59 PM" src="https://github.com/user-attachments/assets/dd7432b6-dd5c-4229-bc1a-73c31217b3a6" />

<img width="489" height="634" alt="Screenshot 2026-05-18 at 1 41 54 PM" src="https://github.com/user-attachments/assets/7e55f366-dc2b-4e9b-a7f4-b6aa2345e9c6" />

### Fuzzy Logic
- Some of the six measured parameters are more important than others. For example, if the pH level is healthy, then the temperature no longer matters much. This is because temperature often varies quite a lot.
- *Fuzzy Rules*: Temperature is Hot (or) pH is Acidic/Alkaline (or) Turbidity is Bad. If any of these is satisfied, a recirculation command was triggered.

### Simulation Process for pH Correction

<img width="409" height="728" alt="Screenshot 2026-05-18 at 1 52 51 PM" src="https://github.com/user-attachments/assets/fd795247-ae8c-43c8-8b64-9191c3f67f3f" />

## Notes: XGBoost — A Scalable Tree Boosting System (Chen & Guestrin)
- Introduces XGBoost, a highly efficient gradient tree boosting framework that achieves state-of-the-art results across many ML benchmarks including Kaggle competitions.
- Key innovations include a sparsity-aware split-finding algorithm, cache-aware block structures for parallelism, and weighted quantile sketch for approximate tree learning.
- Relevant as a candidate ML model for our water quality classification task, offering strong performance on tabular sensor data with low inference overhead.

## Notes: Why Do Water Quality Monitoring Programs Succeed or Fail? — Sub-Saharan Africa (Peletz et al.)
- Qualitative comparative analysis of regulated water quality testing programs across sub-Saharan Africa, identifying institutional, financial, and operational factors that determine program success or failure.
- Key finding: programs that succeed tend to have strong institutional backing, consistent funding, trained personnel, and feedback loops between testers and water suppliers.
- Directly relevant as a framework for understanding what makes a monitoring system viable in practice, and what risks to design around for Zimbabwe deployment.

## Notes: From Vision to Action — Zimbabwe Launches its National Public Health Institute (WHO)
- Documents Zimbabwe's establishment of a National Public Health Institute (NPHI) to consolidate disease surveillance, laboratory services, and epidemiological research under a single national body.
- The NPHI replaces previously fragmented health monitoring infrastructure, improving coordinated national response to outbreaks and public health threats.
- Relevant as the institutional body that could oversee or integrate a national water quality monitoring program.

## Notes: Zimbabwe's Healthcare System — Resilience, Recovery, and Digital Transformation
- Examines the structural challenges facing Zimbabwe's healthcare system, including resource constraints, infrastructure gaps, and limited connectivity in rural areas.
- Covers ongoing digital transformation efforts and how technology is being deployed to extend healthcare reach despite these constraints.
- Relevant as context for understanding the operational environment in which our water quality monitoring system would be deployed.

## Notes: Zimbabwe Digital Health Case Study — Impilo
- Documents Zimbabwe's Impilo digital health platform and its integration with the national healthcare system via DHIS2 for patient data management.
- Highlights Village Health Workers (VHWs) using mobile devices to collect and upload data to a central system, with offline capability for low-connectivity areas.
- Demonstrates a proven model for decentralised data collection in resource-constrained environments, directly applicable to our borehole monitoring approach.
