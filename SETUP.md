# Smart Email Prioritization — Local Prototype Setup

This folder contains three standalone tools plus a shared backend. They all run **entirely on your own machine** — nothing is sent to a third-party AI, and your Gmail password never leaves your computer.

| File | Who runs it | What it does |
|---|---|---|
| `backend/app.py` | Everyone | The shared model: cold-start rules + an online logistic-regression-style classifier. Everything else talks to this over `localhost:8000`. |
| `email_priority_demo.html` | Whoever is presenting | The click-through demo: label a batch, watch AI predict the next batch, correct it, repeat. Good for a live walkthrough. |
| `email_extractor.html` | **Every teammate, on their own inbox** | Fetches a batch of your own emails, you label each Keep / Skip / Skip (privacy), then it exports a small `.json` file. |
| `email_priority_test.html` | Whoever is compiling results | Imports one or more `.json` files exported by the extractor (from any number of teammates), pools them, and automatically replays the learning curve across many random shuffles to produce a chart + CSV. No Gmail needed here. |

The point of splitting extractor vs. test tool: data collection (slow, manual, needs your own Gmail) and statistical testing (fast, automatic, needs no credentials) are decoupled. Label once, then anyone can re-run experiments with different batch sizes/trial counts on the same data without re-labeling.

## 1. One-time setup (each person does this on their own machine)

**Requirements:** Python 3.9+, a personal Gmail account (recommended — school Google Workspace accounts sometimes have IMAP/app-passwords disabled by the admin).

```bash
cd backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### Generate a Gmail App Password (only needed if you'll fetch your own inbox with the extractor)

1. Turn on 2-Step Verification: https://myaccount.google.com/security
2. Generate an app password: https://myaccount.google.com/apppasswords — name it anything (e.g. "email-priority"), copy the 16-character password **immediately** (Google only shows it once — if you lose it, delete it there and generate a new one).
3. In `backend/`, copy the template and fill it in yourself (don't paste the password into Slack/email — just edit the file directly):
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```
   GMAIL_ADDRESS=your_email@gmail.com
   GMAIL_APP_PASSWORD=your16digitpassword
   ```

If you only plan to use `email_priority_test.html` (importing files someone else collected), you can skip the app password entirely — that tool never touches Gmail.

## 2. Run the backend

```bash
cd backend
venv/bin/uvicorn app:app --port 8000 --reload
```

Leave this running. Check it's alive: open http://127.0.0.1:8000/health in a browser — should show `{"status":"ok"}`.

## 3. Serve the HTML files

From the project root (a separate terminal, backend still running):
```bash
python3 -m http.server 5500
```
Then open in your browser:
- http://127.0.0.1:5500/email_extractor.html — to collect your own labeled data
- http://127.0.0.1:5500/email_priority_test.html — to run experiments on collected data
- http://127.0.0.1:5500/email_priority_demo.html — the presentation demo

Use this `http.server` route rather than double-clicking the files open — opening them directly as `file://` pages is not guaranteed to work (some browsers block or restrict fetch() calls from `file://` origins) and hasn't been tested.

## 4. Collecting data (each teammate)

1. Open `email_extractor.html`.
2. Enter your name (used in the exported filename).
3. Pick "My real Gmail inbox," choose how many emails to fetch (try 40–60 to start), click fetch.
4. Every email defaults to **Skip** — you don't need to click anything for most of them. Only click **Keep** for emails you'd actually want surfaced, or **Skip (privacy)** for anything you don't want counted or shared (note: the subject/snippet text is still stored in the exported file even for privacy-skips, so if an email is genuinely sensitive, open the exported `.json` afterward and delete that entry by hand before sending it on).
5. Click **Export labeled data** at any point — no need to review every card first, downloads a `labeled_<yourname>_<count>.json` file.
6. Send that file to whoever is compiling results (Slack, email, shared drive — it contains subject lines and short snippets, not full email bodies or your password).

## 5. Running experiments (whoever compiles results)

1. Open `email_priority_test.html`.
2. Import as many teammates' `.json` files as you have — they get pooled into one combined dataset.
3. Set batch size (emails per round) and number of random-shuffle trials (8 is a reasonable default; more trials = smoother average, slower run).
4. Click **Run experiment**. It calls the backend once per round per trial — no more clicking needed.
5. Read the chart/table, and click **Download raw CSV** — one row per (trial, round), so you can pool multiple experiment runs (e.g. different batch sizes) in Excel/pandas for the report.

## Troubleshooting

- **"Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD"** — you haven't filled in `backend/.env`, or the backend was started before you saved it (restart uvicorn after editing `.env`).
- **"Gmail login failed"** — the app password was revoked/retyped wrong, or 2-Step Verification got turned off. Generate a fresh app password.
- **Fetching 200 emails is slow** — expected, roughly 30–40 seconds; the UI shows a spinner. It's one batched IMAP call, not one-per-email, so it won't be much slower than that regardless of count up to the 200 cap.
- **Import fails in the test tool** — the file must be the exact JSON the extractor produced (has an `emails` array with `from`/`subject`/`snippet`/`label` per item). Don't hand-edit the structure, just individual entries if removing something sensitive.
- **"Not enough labeled emails for even one round"** — you need at least `2 × batch size` usable (non-privacy-skip) labels in the combined pool. Import more data or lower the batch size.
