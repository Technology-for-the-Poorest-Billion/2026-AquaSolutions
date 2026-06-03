# DHIS2

While conducting research on digital health programs in Zimbabwe, we discovered the DHIS2 Android Collector app which is very strongly suited to our needs. 
It is open-source and can be customised into tailored applications. As such, we could develop our own version focused on medical health and water data. 
Alternatively, if there are existing implementations of this app in Zimbabwe, we would simply need to propose a water quality amendment. This could be done using QR codes on boreholes. 
We would still need to design a robust ML algorithm as well. We would also still need to design the data pipeline from sensor to algorithm output.

Depending on the level of connectivity of a community, a TinyML model may not be required. In certain cases, with live data transmission, we could run a larger model and relay the results to the senor. 

To be specific, the DHIS2 Android Collector app parameters that make it suitable for our use case are as follows: 
- Map: Can locate each borehole relative to individuals that drink from it. Can also visualise coverage of a city/region or illustrate contamination trends. 
- Live data upload directly to central healthcare system. If internet is inaccessible, then the worker can still record the data which will be automatically updated when connectivity is reached.
- SMS capability to send data, request results, ask for support, etc.
- QR codes provide a convenient way to check a borehole's status (potability risk level) and recent reports.
- Simple interface that has been used across many programs in developing countries. Some workers have already been trained to use it.

## Tracker and Events Programmes
- Event and Tracker programs allow DHIS2 platforms to track individual patients across data.
- Tracker programs follow a specific person over time (e.g. a child's medical records from birth as they age). Events collect information on individual occurences.
- DHIS2 has partnered with the WHO. They have developed the DHIS2 Health Data toolkit to align national implementations of digital healthcare programs with international WHO standards while still retaining customisability for specific local needs. 

## Mapping Relationships Using Tracker
- Tracker can be used to map relationships between different people. This would be a useful feature to disease monitoring as contamination can be modeled using networks and graph theory.

## Using DHIS2 to support HIV reduction for at-risk populations in Zimbabwe
- Source: https://dhis2.org/zimbabwe-hiv-agyw-tracker/
- Several entities came together to develop the AGYW HIV Community Health Information System (CHIS) using the DHIS2 Tracker. It can be implemented with Zimbabwe's other HIV trackers and data collection programs to allow for efficient information management.
- Impilo also exists in Zimbabwe. They are often used at different levels of the healthcare system. Impilo collects individual data, which is then compiled into DHIS2. Impilo sits in the role of the Tracker and Event configurations for DHIS2.
