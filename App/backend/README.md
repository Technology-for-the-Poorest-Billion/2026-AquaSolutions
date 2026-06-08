## SMS → DHIS2 demo

A completed SMS illness report can also be pushed into the DHIS2 demo as an event.

1. Start DHIS2 locally: `cd ../dhis2 && docker compose up -d` (wait for it).
2. In `App/backend/.env` set `DHIS2_BRIDGE_ENABLED=true` (and `DHIS2_BASE_URL`/creds if not the defaults).
3. Run Flask and expose it to Twilio: `ngrok http 5000`, set the Twilio number's
   SMS webhook to `<ngrok-url>/sms`.
4. Text the Twilio number a station number (e.g. `1`), then follow the prompts
   (how many sick → symptoms `1,3` → onset `today`). On "Report complete" the
   bridge creates a DHIS2 event at that borehole; it appears in the DHIS2
   dashboard/line list after the next analytics run.

The bridge never runs labelling (that is the partner's logic) and never blocks
the SMS reply — if DHIS2 is unreachable, the text conversation still completes
and a warning is logged.
