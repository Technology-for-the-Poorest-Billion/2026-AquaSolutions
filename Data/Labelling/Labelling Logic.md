This document discusses the principles that will be taken with respect to taking illness reports and labelling the data.


Pipeline:

1. For each sensor reading timestamp, collect all illness reports for that station
2. Each report within 7 days contributes a decayed score: 1 * (1 - log(t+1) / log(8))
   where t = fractional days between report and sensor reading
3. Reports older than 7 days contribute 0 (prevents score inflation over time)
4. Decayed scores are summed across all reports
5. Summed score is labelled via score tiers with a confidence reading:
       < 0.5  → safe  → 0.1 (absence of reports doesn't mean confirmed safe; low weight reflects uncertainty)
     0.5–1.5  → risky → 0.3 (single fresh report, or a few old ones)
     1.5–2.5  → risky → 0.6 (multiple reports or strong recent signal)
       2.5+   → risky → 0.9 (sustained or clustered reporting)
    Note that these thresholds have been arbitrarily chosen and should be calibrated as the data comes in. Specifically, the 0.5 safe threshold is designed to filter out background illness reports that occur even when water is uncontaminated.
6. The previous 7-day window represents the period during which the water was likely contaminated. These are the sensor readings that should be labelled unsafe.

Justification for 7-day window:
    WHO cholera incubation: 12 hours to 5 days.
    incubation = time between a person being exposed to a pathogen and showing symptoms
    Window = incubation maximum (5 days) + conservative reporting lag (2 days).

Justification for logarithmic decay:
    Signal strength drops sharply in first 48 hours (most cases present within 2 days)
    then flattens — matching the shape of a log curve rather than linear decay.

Justification for confidence tiers:
    Discrete tiers are a transparent design choice. Floor of 0.3 acknowledges that a single report carries some signal. Ceiling of 0.9 (not 1.0) acknowledges that illness reports are only a proxy signal and we can't be certain the cause i water contamination. Future work could derive weights by symptom specificity or water contamination flagging success.

Risk persistence:
    Because the 7-day window is rolling, a label may remain elevated for up to 7 days after the last report. 