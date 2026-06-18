# self_discipline
A self discipline tool for Saad.

## What it does
- **Habit Interrupter** — click a habit when you're tempted, it shows you the consequences and a personal message to snap you out of it
- **Win/Loss Tracker** — log whether you resisted or gave in; see your streaks and win rate per habit
- **Claude.ai Bridge** — builds a full-context prompt (your habits, stats, what you're struggling with right now) you paste into Claude.ai for a voice or text accountability session

## How to run

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000` in your browser.

## How to use with Claude voice chat

1. Open the app and select the habit you're being tempted by
2. Type what's going on in the "Check In with Claude" box (optional)
3. Click **Build Claude Prompt** — it generates a context prompt with your full habit history
4. Click **Copy to Clipboard**, then open **claude.ai** and paste it
5. Switch to voice mode on Claude.ai and talk to Claude as your accountability partner

## Adding your own habits

Use the **+ Add Habit** button in the app, or edit `data/habits.json` directly.

## Data

All tracking data lives in `data/tracking.json`. Commit this file to keep your history.
