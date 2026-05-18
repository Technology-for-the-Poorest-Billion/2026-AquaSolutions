# Notes

## Notes: Advances in Technological Research for Online and In Situ Water Quality Monitoring — A Review
- Optical and Electrochemical Sensors: Measure physical parameters (color, turbidity, temperature), chemical parameters (chlorine, pH, dissolved oxygen, nitrogen, metals, ORP), and biological indicators (E. Coli, total coliforms). 
- IoT Enabled: Useful for remote areas.
- Phone-Based Tools: Use phone camera, but are significantly less accurate.

## Notes: A review of the application of machine learning in water quality evaluation
- First Step: Data collection, algorithm selection, model training, model validation.
- Supervised and unsupervised learning approaches are possible. RL makes sense, but accountability is difficult.
- Local sensors measure some variables, but not all (e.g. pathogen concentration). CNN trained to infer the state of these unmeasurable variables from images of the water.
- Consider the incorporation of meteorological data.
- Time-series (LSTM) work relatively well for predicting water quality over time. 

# Notes: Allen Chafa's Publication
- UN SDG 6: Clean water and sanitation for all.
- Manual Testing Processes: Lengthy, error-prone. Laboratory Testing: Long, costly, inaccessible.
- Overview: Data collection via IoT and sensors. Values are compared to standards and an SMS is sent to the borehole's users.

## System Architecture:
- Microcontroller (Arduino) and sensors measure temperature, pH, turbidity, dissolved oxygen, hardness, and dissolved solids.
- Optical dissolved oxygen sensors work by measuring the interaction between oxygen and dyes after exposure to blue light.
- Turbidity sensors use light to measure particle concentration. Hardness is measured using a oxidation reduction potential (ORP) sensor which uses a voltage.
- The solenoid water valve is used to control the water's flow.
- Real-time data is collected (requires Wifi) and is sent to ThingSpeak (a web-based application). The decision-making process uses the fuzzy logic algorithm designed via MATLAB/SIMULINK. Deviations from the WHO standards triggers a control action, often the release of automated chemical dosing units. If the water meets the standards, it it is allowed to flow to the next step. 
- Additionally, a copy of the sensor readings is sent to the user's phone via SMS using a Global System for Mobile (GSM) module.
- Real-time data is logged. 

<img width="536" height="476" alt="Screenshot 2026-05-18 at 1 38 59 PM" src="https://github.com/user-attachments/assets/dd7432b6-dd5c-4229-bc1a-73c31217b3a6" />

<img width="489" height="634" alt="Screenshot 2026-05-18 at 1 41 54 PM" src="https://github.com/user-attachments/assets/7e55f366-dc2b-4e9b-a7f4-b6aa2345e9c6" />

## Fuzzy Logic
- Some of the six measured parameters are more important than others. For example, if the pH level is healthy, then the temperature no longer matters much. This is because temperature often varies quite a lot.
- *Fuzzy Rules*: Temperature is Hot (or) pH is Acidic/Alkaline (or) Turbidity is Bad. If any of these is satisfied, a recirculation command was triggered.

## Simulation Process for pH Correction

<img width="409" height="728" alt="Screenshot 2026-05-18 at 1 52 51 PM" src="https://github.com/user-attachments/assets/fd795247-ae8c-43c8-8b64-9191c3f67f3f" />
