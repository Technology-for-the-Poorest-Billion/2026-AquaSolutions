# DEMO.md — walking the Gen-1 pipeline live

For the demo on **2026-05-28**. Estimated total setup time: ~30 minutes.

## What you are showing

Three things, in this order:

1. The **sensor leg** — a simulated field node POSTing readings into the central server. The dashboard fills with rows.
2. The **reporting leg** — text the Twilio number from your own phone with a station ID. The Flask `/sms` webhook fires, the trailing window of readings at that station gets labelled `unsafe`, the dashboard updates, and Twilio sends you an acknowledgement.
3. The **audit trail** — a one-line SQLite query shows exactly which readings were labelled by which report, with the rule that was applied.

The framing line throughout: this is *faecal-contamination + community illness signal*, **not** a cholera detector.

## One-time setup

### 1. Python environment (~2 min)

```bash
cd App/backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Local config (~1 min)

```bash
cp .env.example .env
# edit .env and set DEVICE_SECRET to any long random string
# e.g. DEVICE_SECRET=$(openssl rand -hex 24)
# leave TWILIO_VALIDATE_SIGNATURES=false until step 5
```

### 3. Twilio trial account (~10 min)

1. Sign up at <https://www.twilio.com/try-twilio>. Verify your real phone number — Twilio's trial only lets you message verified numbers, so this is also the phone you'll demo from.
2. On the console, navigate **Phone Numbers → Manage → Buy a number** and acquire a free trial number with SMS capability.
3. Copy your **Account SID** and **Auth Token** from the console homepage. Put the Auth Token into `.env`:
   ```env
   TWILIO_AUTH_TOKEN=your-token-here
   ```
4. Trial-account limit: outbound messages have a "Sent from your Twilio trial account" prefix and inbound is free. Do not worry about it for the demo.

### 4. ngrok (~5 min)

1. Install ngrok: `brew install ngrok` (macOS) or download from <https://ngrok.com/download>.
2. Sign up at <https://ngrok.com/> and run `ngrok config add-authtoken <token>`.
3. Test: `ngrok http 5000`. Copy the `https://abc123.ngrok.io` URL it prints.

### 5. Wire ngrok URL into Twilio

1. In Twilio console, go **Phone Numbers → Manage → Active Numbers**, click your trial number.
2. Under **Messaging Configuration → A message comes in**, set:
   - **Webhook**: `https://<ngrok-id>.ngrok.io/sms`
   - **HTTP**: `POST`
3. Save.
4. Back in `.env`, set:
   ```env
   TWILIO_VALIDATE_SIGNATURES=true
   PUBLIC_BASE_URL=https://<ngrok-id>.ngrok.io
   ```

## Running the demo (~3 terminals)

Open three terminals all in `App/backend/` with the venv active and `.env` loaded.

**Terminal 1 — Flask:**
```bash
python app.py
# Server starts on http://localhost:5000
# Database auto-creates at data/water_safety.db
```

**Terminal 2 — ngrok (keep running):**
```bash
ngrok http 5000
```

**Terminal 3 — sensor simulator:**
```bash
cd ../scripts
python simulate_sensor.py --secret "$DEVICE_SECRET" --interval 3
```

> For a live Railway ingest target, run:
> ```bash
> python simulate_sensor.py --url https://gm2aquasolutions-production.up.railway.app --secret "$DEVICE_SECRET" --interval 3
> ```

Open the dashboard: <http://localhost:5000/dashboard>. You should see rows arriving every 3 seconds across the four seeded stations.

## Live demo flow (~3 min)

1. **Show the dashboard filling.** Point out the disclaimer and that no readings are labelled yet — everything is "clear."
2. **Text your Twilio number** from your verified phone: `4` (or any seeded station 1–4). Say what you are doing as you do it.
3. **Watch the dashboard.** Within ~5 seconds (auto-refresh) you should see:
   - A new row in **Recent illness reports** with the station name parsed out, your phone number, and a non-zero `Labelled` count.
   - Rows in the trailing 7-day window for that station flip to the **unsafe** pill.
4. **Show the acknowledgement SMS** on your phone — the auto-reply from Twilio.
5. **(Optional) Show the audit trail.** In a fourth terminal:
   ```bash
   sqlite3 App/backend/data/water_safety.db \
     "SELECT rl.reading_id, rl.label, rl.rule_description, ir.raw_message
        FROM reading_labels rl
        JOIN illness_reports ir ON ir.report_id = rl.report_id
        ORDER BY rl.label_id DESC LIMIT 5;"
   ```
   The `rule_description` shows exactly which window rule applied — making the labelling reproducible and auditable.

## Failure modes likely to bite

These are the things that will *actually* go wrong during the demo. Each has a fast recovery.

- **ngrok URL rotated.** Free-tier ngrok rotates the URL on restart. If you restarted ngrok after configuring Twilio, the Twilio webhook is now pointing nowhere. Recovery: paste the new ngrok URL into Twilio webhook config; update `PUBLIC_BASE_URL` in `.env`; restart Flask.
- **Signature validation rejects the request.** 403 on `/sms` means the URL Twilio signed does not match what Flask reconstructed. Check `PUBLIC_BASE_URL` matches the current ngrok URL exactly (including https). For an emergency demo, set `TWILIO_VALIDATE_SIGNATURES=false` and restart — but never run that way on a real deployment.
- **Trial credit exhausted.** Each outbound SMS costs ~$0.0075 from trial credit. Plenty for a demo. If exhausted: top up or skip the auto-reply demo (the labelling still works).
- **Twilio cannot reach your trial number.** Trial accounts can only message *verified* numbers. The phone you demo from must be verified in the Twilio console.
- **`DEVICE_SECRET` mismatch.** Simulator returns 401. Recovery: ensure the terminal running `simulate_sensor.py` reads from the same `.env` (or pass `--secret` explicitly).
- **Database locked.** Two writers contend on SQLite. WAL mode is on, so this is rare; if it happens, stop the simulator briefly.
- **Empty dashboard despite simulator running.** Check the simulator's terminal — `ERR status=401` means `DEVICE_SECRET` mismatch, `ERR status=400` means a payload issue, `ERR status=0` means Flask is not actually running.

## Have a screencast ready

Record the working demo once before the live one and keep the video on your laptop. If anything breaks live, switch to the recording, narrate it, and treat the breakage as a teaching moment about why production needs a stable host (Railway) instead of ngrok.

## After the demo

1. Stop the simulator and Flask.
2. **Set `TWILIO_VALIDATE_SIGNATURES=true`** if you ever turned it off — never leave an internet-exposed `/sms` route unsigned.
3. Wipe or back up `data/water_safety.db` depending on whether you want to keep the demo's labelled rows.
