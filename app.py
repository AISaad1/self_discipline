import os
import json
import uuid
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
HABITS_FILE = os.path.join(DATA_DIR, "habits.json")
TRACKING_FILE = os.path.join(DATA_DIR, "tracking.json")


def load_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def get_stats():
    habits = load_json(HABITS_FILE)["habits"]
    tracking = load_json(TRACKING_FILE)["entries"]
    stats = {}
    for habit in habits:
        hid = habit["id"]
        entries = [e for e in tracking if e["habit_id"] == hid]
        wins = sum(1 for e in entries if e["outcome"] == "win")
        losses = sum(1 for e in entries if e["outcome"] == "loss")
        total = wins + losses
        streak = 0
        for entry in sorted(entries, key=lambda x: x["date"], reverse=True):
            if entry["outcome"] == "win":
                streak += 1
            else:
                break
        stats[hid] = {
            "wins": wins,
            "losses": losses,
            "total": total,
            "win_rate": round(wins / total * 100) if total > 0 else 0,
            "streak": streak,
        }
    return stats


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/habits", methods=["GET"])
def get_habits():
    data = load_json(HABITS_FILE)
    stats = get_stats()
    habits = data["habits"]
    for habit in habits:
        habit["stats"] = stats.get(habit["id"], {"wins": 0, "losses": 0, "total": 0, "win_rate": 0, "streak": 0})
    return jsonify(habits)


@app.route("/api/habits", methods=["POST"])
def add_habit():
    body = request.json
    data = load_json(HABITS_FILE)
    new_habit = {
        "id": f"h{uuid.uuid4().hex[:8]}",
        "name": body["name"],
        "category": body.get("category", "General"),
        "description": body.get("description", ""),
        "triggers": body.get("triggers", []),
        "consequences": {
            "short_term": body.get("short_term_consequences", []),
            "long_term": body.get("long_term_consequences", []),
        },
        "benefits_of_resisting": body.get("benefits", []),
        "interruption_message": body.get("interruption_message", ""),
        "active": True,
    }
    data["habits"].append(new_habit)
    save_json(HABITS_FILE, data)
    return jsonify(new_habit), 201


@app.route("/api/habits/<habit_id>", methods=["PUT"])
def update_habit(habit_id):
    body = request.json
    data = load_json(HABITS_FILE)
    for habit in data["habits"]:
        if habit["id"] == habit_id:
            habit.update(body)
            save_json(HABITS_FILE, data)
            return jsonify(habit)
    return jsonify({"error": "Habit not found"}), 404


@app.route("/api/habits/<habit_id>", methods=["DELETE"])
def delete_habit(habit_id):
    data = load_json(HABITS_FILE)
    data["habits"] = [h for h in data["habits"] if h["id"] != habit_id]
    save_json(HABITS_FILE, data)
    return jsonify({"success": True})


@app.route("/api/tracking", methods=["POST"])
def add_tracking():
    body = request.json
    data = load_json(TRACKING_FILE)
    entry = {
        "id": uuid.uuid4().hex[:8],
        "habit_id": body["habit_id"],
        "date": body.get("date", date.today().isoformat()),
        "outcome": body["outcome"],
        "note": body.get("note", ""),
        "timestamp": datetime.now().isoformat(),
    }
    data["entries"].append(entry)
    save_json(TRACKING_FILE, data)
    return jsonify(entry), 201


@app.route("/api/stats", methods=["GET"])
def get_all_stats():
    habits = load_json(HABITS_FILE)["habits"]
    stats = get_stats()
    tracking = load_json(TRACKING_FILE)["entries"]

    total_wins = sum(1 for e in tracking if e["outcome"] == "win")
    total_losses = sum(1 for e in tracking if e["outcome"] == "loss")
    total = total_wins + total_losses

    habit_stats = []
    for habit in habits:
        if habit["active"]:
            s = stats.get(habit["id"], {})
            habit_stats.append({
                "id": habit["id"],
                "name": habit["name"],
                "category": habit["category"],
                **s,
            })

    return jsonify({
        "overall": {
            "total_wins": total_wins,
            "total_losses": total_losses,
            "total_battles": total,
            "win_rate": round(total_wins / total * 100) if total > 0 else 0,
        },
        "by_habit": habit_stats,
        "recent": sorted(tracking, key=lambda x: x["timestamp"], reverse=True)[:10],
    })


@app.route("/api/claude-context", methods=["POST"])
def claude_context():
    """
    Builds a context prompt Saad can paste into Claude.ai (with voice or text).
    No API key needed — this just prepares the conversation starter.
    """
    body = request.json
    habit_id = body.get("habit_id")
    situation = body.get("situation", "")

    habits_data = load_json(HABITS_FILE)
    stats = get_stats()
    tracking = load_json(TRACKING_FILE)["entries"]

    total_wins = sum(1 for e in tracking if e["outcome"] == "win")
    total_losses = sum(1 for e in tracking if e["outcome"] == "loss")

    lines = []
    lines.append("You are my personal accountability partner. My name is Saad.")
    lines.append("")
    lines.append("About me: I'm working on becoming a better man — a great father, a loving husband, and someone who lives with honor and discipline.")
    lines.append("")
    lines.append(f"Today is {date.today().strftime('%B %d, %Y')}.")
    lines.append(f"My overall record: {total_wins} wins, {total_losses} losses across all habits.")
    lines.append("")
    lines.append("My habits I'm actively working on:")

    focused_habit = None
    for habit in habits_data["habits"]:
        if not habit["active"]:
            continue
        s = stats.get(habit["id"], {})
        marker = " ← I AM DEALING WITH THIS RIGHT NOW" if habit["id"] == habit_id else ""
        lines.append(f"\n### {habit['name']} ({habit['category']}){marker}")
        lines.append(f"Record: {s.get('wins', 0)} wins / {s.get('losses', 0)} losses | Current win streak: {s.get('streak', 0)}")
        lines.append(f"Triggers: {', '.join(habit['triggers'])}")
        lines.append(f"Short-term consequences if I give in: {'; '.join(habit['consequences']['short_term'][:3])}")
        lines.append(f"Long-term consequences: {'; '.join(habit['consequences']['long_term'][:2])}")
        lines.append(f"Benefits of resisting: {'; '.join(habit['benefits_of_resisting'][:2])}")
        if habit["id"] == habit_id:
            focused_habit = habit

    lines.append("")
    lines.append("---")
    lines.append("")

    if focused_habit:
        lines.append(f"RIGHT NOW I am being tempted by: {focused_habit['name']}")
        if situation:
            lines.append(f"Here's what's happening: {situation}")
        lines.append("")
        lines.append("Please be my accountability partner right now. Be direct, real, and firm — not a lecture, just a real talk. Remind me of what matters. Keep it short and powerful.")
    elif situation:
        lines.append(f"Here's what I want to talk about: {situation}")
        lines.append("")
        lines.append("Please be my accountability partner. Be direct, real, and caring.")
    else:
        lines.append("I want to check in with you as my accountability partner. Review my progress and give me honest feedback.")

    context = "\n".join(lines)
    return jsonify({"context": context})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
