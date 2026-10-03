"""Study logging, streaks, achievements, calendar events, and GitHub-style grid rendering.

All user activity lives in a single JSON file (``data/user_state.json``) so the
dashboard survives restarts without needing a database::

    {
      "courses":   ["BIO 181", ...],
      "sessions":  [{"id", "start" (ISO datetime), "minutes", "course", "notes"}],
      "events":    [{"id", "title", "course", "date" (ISO), "type", "done"}],
      "materials": [{"id", "name", "course", "path", "text_path", "chars", "uploaded_at", ...}],
      "quizzes":   [{"id", "material_id", "course", "score", "questions", "taken_at"}],
      "flashcards_reviewed": {"BIO 181": 42, ...},
      "grades":    {"BIO 181": [{"item", "type", "weight", "score"}]},  # see utils/grades.py
      "profile":   {self-reported fields used by the risk model},
      "pet":       {tokens, owned/equipped items, tickets...}  # see utils/pet.py
      "active_timer": null | {"course", "notes", "first_start", "start", "accum", "running"}
    }
"""

from __future__ import annotations

import html
import io
import json
import random
import shutil
import uuid
import zipfile
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from . import grades

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "data" / "user_state.json"
UPLOAD_DIR = ROOT / "data" / "uploads"
ARCHIVE_STATE_NAME = "user_state.json"

EVENT_TYPES = ["Exam", "Deadline", "Quiz", "Milestone", "Study"]  # "Study" = a planned study session
# Minutes thresholds for grid intensity levels 1-4 (level 0 = no study).
LEVEL_THRESHOLDS = [1, 30, 60, 120]
LEVEL_COLORS = ["rgba(140,140,140,0.18)", "#9be9a8", "#40c463", "#30a14e", "#216e39"]


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
def default_state(courses: list[str] | None = None) -> dict[str, Any]:
    return {
        "courses": list(courses or []),
        "sessions": [],
        "events": [],
        "materials": [],
        "quizzes": [],
        "flashcards_reviewed": {},
        "grades": {},
        "study_plans": {},
        "profile": {},
        "pet": {},
        "active_timer": None,
    }


def load_state(path: Path = STATE_PATH) -> dict[str, Any]:
    """Load saved activity (empty on first run), filling in any keys added since the file was written."""
    state = default_state()
    if path.exists():
        try:
            state.update(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    _register_used_courses(state)
    return state


def _register_used_courses(state: dict[str, Any]) -> None:
    """Make sure every course referenced by data also appears in the course list."""
    for key in ("sessions", "events", "materials", "quizzes"):
        for item in state[key]:
            course = item.get("course")
            if course and course not in state["courses"]:
                state["courses"].append(course)


def save_state(state: dict[str, Any], path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def new_id() -> str:
    return uuid.uuid4().hex[:10]


# --------------------------------------------------------------------------- #
# Courses
# --------------------------------------------------------------------------- #
MAX_COURSE_NAME = 40


def _validate_course_name(state: dict[str, Any], name: str, ignore: str | None = None) -> tuple[str, str | None]:
    """Normalize a course name and return (name, error message or None)."""
    name = " ".join(name.split())
    if not name:
        return name, "Enter a course name."
    if len(name) > MAX_COURSE_NAME:
        return name, f"Keep course names under {MAX_COURSE_NAME} characters."
    taken = {c.lower() for c in state["courses"] if c != ignore}
    if name.lower() in taken:
        return name, f"{name} is already in your course list."
    return name, None


def add_course(state: dict[str, Any], name: str) -> tuple[bool, str]:
    name, error = _validate_course_name(state, name)
    if error:
        return False, error
    state["courses"].append(name)
    return True, f"Added {name}"


def course_usage(state: dict[str, Any], course: str) -> dict[str, float]:
    """How much data is attached to a course (shown before renaming or removing it)."""
    sessions = [s for s in state["sessions"] if s["course"] == course]
    return {
        "sessions": len(sessions),
        "hours": sum(s["minutes"] for s in sessions) / 60,
        "events": sum(1 for e in state["events"] if e["course"] == course),
        "materials": sum(1 for m in state["materials"] if m["course"] == course),
        "quizzes": sum(1 for q in state["quizzes"] if q["course"] == course),
        "grades": len(state["grades"].get(course, [])),
    }


def rename_course(state: dict[str, Any], old: str, new: str) -> tuple[bool, str]:
    """Rename a course everywhere it is referenced."""
    new, error = _validate_course_name(state, new, ignore=old)
    if error:
        return False, error
    if new == old:
        return True, "No changes"
    state["courses"] = [new if c == old else c for c in state["courses"]]
    for key in ("sessions", "events", "materials", "quizzes"):
        for item in state[key]:
            if item.get("course") == old:
                item["course"] = new
    for key in ("flashcards_reviewed", "grades"):
        if old in state[key]:
            state[key][new] = state[key].pop(old)
    if state.get("active_timer") and state["active_timer"]["course"] == old:
        state["active_timer"]["course"] = new
    for plan in state.get("study_plans", {}).values():
        if plan.get("course") == old:
            plan["course"] = new
    return True, f"Renamed {old} to {new}"


def remove_course(state: dict[str, Any], course: str) -> str:
    """Remove a course and everything attached to it (sessions, events, quizzes, uploaded files)."""
    for material in state["materials"]:
        if material["course"] == course:
            for key in ("path", "text_path"):
                (ROOT / material[key]).unlink(missing_ok=True)
    state["courses"] = [c for c in state["courses"] if c != course]
    for key in ("sessions", "events", "materials", "quizzes"):
        state[key] = [item for item in state[key] if item.get("course") != course]
    state["flashcards_reviewed"].pop(course, None)
    state["grades"].pop(course, None)
    state["study_plans"] = {k: p for k, p in state.get("study_plans", {}).items() if p.get("course") != course}
    if state.get("active_timer") and state["active_timer"]["course"] == course:
        state["active_timer"] = None
    return f"Removed {course}"


# --------------------------------------------------------------------------- #
# Archives (move your dashboard between computers)
# --------------------------------------------------------------------------- #
def export_archive(state: dict[str, Any]) -> bytes:
    """Zip the activity state plus uploaded materials into a portable archive."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(ARCHIVE_STATE_NAME, json.dumps({**state, "active_timer": None}, indent=2, default=str))
        for material in state["materials"]:
            for key in ("path", "text_path"):
                path = ROOT / material[key]
                if path.exists():
                    zf.write(path, f"uploads/{path.name}")
    return buf.getvalue()


def import_archive(data: bytes) -> dict[str, Any]:
    """Load an archive made by :func:`export_archive`, replacing the current uploads folder.

    Only ``user_state.json`` and flat ``uploads/<file>`` entries are read, so a crafted
    archive cannot write outside ``data/uploads``.
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ValueError("That file is not a Wolf Tracks archive (.zip).") from exc
    with zf:
        if ARCHIVE_STATE_NAME not in zf.namelist():
            raise ValueError(f"Archive is missing {ARCHIVE_STATE_NAME}.")
        loaded = json.loads(zf.read(ARCHIVE_STATE_NAME).decode("utf-8"))
        if not isinstance(loaded, dict) or not isinstance(loaded.get("sessions", []), list):
            raise ValueError("Archive data is not in the expected format.")

        if UPLOAD_DIR.exists():
            shutil.rmtree(UPLOAD_DIR)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        for name in zf.namelist():
            parts = name.split("/")
            if len(parts) == 2 and parts[0] == "uploads" and parts[1] and parts[1] not in (".", ".."):
                (UPLOAD_DIR / parts[1]).write_bytes(zf.read(name))

    state = default_state()
    state.update(loaded)
    state["active_timer"] = None
    _register_used_courses(state)
    for material in state["materials"]:  # re-point files at this computer's uploads folder
        for key in ("path", "text_path"):
            material[key] = (UPLOAD_DIR / Path(material[key]).name).relative_to(ROOT).as_posix()
    return state


# --------------------------------------------------------------------------- #
# Study sessions
# --------------------------------------------------------------------------- #
def log_session(state: dict[str, Any], course: str, minutes: float, notes: str = "",
                start: datetime | None = None) -> dict[str, Any]:
    """Record a study session and return it."""
    session = {
        "id": new_id(),
        "start": (start or datetime.now() - timedelta(minutes=minutes)).isoformat(timespec="seconds"),
        "minutes": round(float(minutes), 1),
        "course": course,
        "notes": notes.strip(),
    }
    state["sessions"].append(session)
    state["sessions"].sort(key=lambda s: s["start"])
    return session


def delete_session(state: dict[str, Any], session_id: str) -> None:
    state["sessions"] = [s for s in state["sessions"] if s["id"] != session_id]


def _session_start(session: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(session["start"])


def daily_minutes(state: dict[str, Any], course: str | None = None) -> dict[date, float]:
    """Total study minutes per calendar day (optionally for one course)."""
    totals: dict[date, float] = defaultdict(float)
    for s in state["sessions"]:
        if course is None or s["course"] == course:
            totals[_session_start(s).date()] += s["minutes"]
    return dict(totals)


def streaks(daily: dict[date, float], today: date) -> tuple[int, int]:
    """Return (current streak, longest streak) in consecutive study days.

    The current streak stays alive through today if the student studied yesterday
    but hasn't logged anything yet today.
    """
    days = sorted(d for d, m in daily.items() if m > 0)
    longest = run = 0
    prev = None
    for d in days:
        run = run + 1 if prev is not None and d - prev == timedelta(days=1) else 1
        longest = max(longest, run)
        prev = d

    active = set(days)
    cursor = today if today in active else today - timedelta(days=1)
    current = 0
    while cursor in active:
        current += 1
        cursor -= timedelta(days=1)
    return current, longest


def total_minutes(state: dict[str, Any], since: date | None = None) -> float:
    return sum(s["minutes"] for s in state["sessions"] if since is None or _session_start(s).date() >= since)


def late_night_share(sessions: list[dict[str, Any]]) -> float | None:
    """Share of study minutes in sessions that started between midnight and 4 a.m."""
    total = sum(s["minutes"] for s in sessions)
    if not total:
        return None
    late = sum(s["minutes"] for s in sessions if 0 <= _session_start(s).hour < 4)
    return late / total


# --------------------------------------------------------------------------- #
# GitHub-style contribution grid
# --------------------------------------------------------------------------- #
def intensity_level(minutes: float) -> int:
    level = 0
    for i, threshold in enumerate(LEVEL_THRESHOLDS, start=1):
        if minutes >= threshold:
            level = i
    return level


def contribution_grid_html(daily: dict[date, float], today: date, weeks: int = 53) -> str:
    """Render a GitHub-style year grid: one column per week (Sun–Sat), one square per day."""
    days_since_sunday = (today.weekday() + 1) % 7
    start = today - timedelta(days=days_since_sunday) - timedelta(weeks=weeks - 1)
    cell, gap = 11, 3

    cells = []
    for i in range(weeks * 7):
        day = start + timedelta(days=i)
        if day > today:
            cells.append('<div class="cg-cell" style="background:transparent"></div>')
            continue
        minutes = daily.get(day, 0.0)
        tip = (f"{minutes / 60:.1f} h studied on {day:%a, %b %d %Y}" if minutes
               else f"No study logged on {day:%a, %b %d %Y}")
        cells.append(f'<div class="cg-cell" style="background:{LEVEL_COLORS[intensity_level(minutes)]}" '
                     f'title="{html.escape(tip)}"></div>')

    # Month labels sit above the first week column that starts in a new month.
    starts, last_month = [], None
    for w in range(weeks):
        first = start + timedelta(weeks=w)
        if first.month != last_month:
            starts.append((w, first))
            last_month = first.month
    # Skip labels that would collide with the next one (e.g. a partial first month) or the grid's end.
    months = [
        f'<span style="grid-column:{w + 1}">{first:%b}</span>'
        for i, (w, first) in enumerate(starts)
        if (starts[i + 1][0] if i + 1 < len(starts) else weeks) - w >= 3
    ]

    day_labels = "".join(f"<span>{d}</span>" for d in ["", "Mon", "", "Wed", "", "Fri", ""])
    legend = "".join(f'<div class="cg-cell" style="background:{c}"></div>' for c in LEVEL_COLORS)
    year_minutes = sum(m for d, m in daily.items() if start <= d <= today)
    active_days = sum(1 for d, m in daily.items() if start <= d <= today and m > 0)

    return (
        "<style>"
        ".cg-wrap{font-family:inherit;font-size:11px;color:inherit;overflow-x:auto;padding-bottom:4px}"
        f".cg-cell{{width:{cell}px;height:{cell}px;border-radius:2px;outline:1px solid rgba(27,31,36,0.06);outline-offset:-1px}}"
        f".cg-months{{display:grid;grid-template-columns:repeat({weeks},{cell}px);column-gap:{gap}px;"
        f"margin-left:32px;height:15px;opacity:.75;white-space:nowrap}}"
        ".cg-body{display:flex;gap:4px}"
        f".cg-days{{display:grid;grid-template-rows:repeat(7,{cell}px);row-gap:{gap}px;width:28px;opacity:.75;line-height:{cell}px}}"
        f".cg-grid{{display:grid;grid-template-rows:repeat(7,{cell}px);grid-auto-flow:column;"
        f"grid-auto-columns:{cell}px;gap:{gap}px}}"
        ".cg-foot{display:flex;justify-content:space-between;align-items:center;margin:8px 0 0 32px;"
        f"max-width:{weeks * (cell + gap)}px;opacity:.85}}"
        ".cg-legend{display:flex;gap:3px;align-items:center}"
        "</style>"
        '<div class="cg-wrap">'
        f'<div class="cg-months">{"".join(months)}</div>'
        f'<div class="cg-body"><div class="cg-days">{day_labels}</div>'
        f'<div class="cg-grid">{"".join(cells)}</div></div>'
        f'<div class="cg-foot"><span><b>{year_minutes / 60:.1f} hours</b> across <b>{active_days}</b> '
        f'study days in the last year</span>'
        f'<span class="cg-legend">Less {legend} More</span></div>'
        "</div>"
    )


# --------------------------------------------------------------------------- #
# Calendar events
# --------------------------------------------------------------------------- #
def add_event(state: dict[str, Any], title: str, course: str, when: date, kind: str) -> dict[str, Any]:
    event = {"id": new_id(), "title": title.strip(), "course": course,
             "date": when.isoformat(), "type": kind, "done": False}
    state["events"].append(event)
    state["events"].sort(key=lambda e: e["date"])
    return event


def delete_event(state: dict[str, Any], event_id: str) -> None:
    state["events"] = [e for e in state["events"] if e["id"] != event_id]


def set_event_done(state: dict[str, Any], event_id: str, done: bool) -> None:
    for e in state["events"]:
        if e["id"] == event_id:
            e["done"] = done


def upcoming_events(state: dict[str, Any], today: date, days: int = 14) -> list[dict[str, Any]]:
    horizon = today + timedelta(days=days)
    return [e for e in state["events"] if today <= date.fromisoformat(e["date"]) <= horizon]


# --------------------------------------------------------------------------- #
# Engagement metrics -> risk-model features
# --------------------------------------------------------------------------- #
def avg_days_started_before_exam(state: dict[str, Any], course: str | None, today: date) -> float | None:
    """For each exam, days between the first related session in the prior 14 days and the exam."""
    exams = [e for e in state["events"]
             if e["type"] == "Exam" and (course is None or e["course"] == course)]
    if not exams:
        return None
    leads = []
    for exam in exams:
        exam_day = date.fromisoformat(exam["date"])
        window = [
            _session_start(s).date() for s in state["sessions"]
            if s["course"] == exam["course"] and exam_day - timedelta(days=14) <= _session_start(s).date() <= exam_day
        ]
        leads.append((exam_day - min(window)).days if window else 0)
    return sum(leads) / len(leads)


def deadline_stats(state: dict[str, Any], course: str | None, today: date) -> tuple[float | None, int]:
    """(on-time rate, missed count) over deadlines whose due date has passed."""
    past = [e for e in state["events"]
            if e["type"] in ("Deadline", "Quiz") and date.fromisoformat(e["date"]) < today
            and (course is None or e["course"] == course)]
    if not past:
        return None, 0
    done = sum(1 for e in past if e.get("done"))
    return done / len(past), len(past) - done


def dashboard_profile(state: dict[str, Any], today: date, course: str | None = None) -> dict[str, Any]:
    """Derive the model's engagement features from the student's own logged activity."""
    sessions = [s for s in state["sessions"] if course is None or s["course"] == course]
    if sessions:
        first = min(_session_start(s).date() for s in sessions)
        weeks = max(1.0, ((today - first).days + 1) / 7)
        weekly_hours = sum(s["minutes"] for s in sessions) / 60 / weeks
    else:
        weekly_hours = 0.0
    quizzes = [q for q in state["quizzes"] if course is None or q["course"] == course]
    materials = [m for m in state["materials"] if course is None or m["course"] == course]
    cards = state["flashcards_reviewed"]
    on_time, missed = deadline_stats(state, course, today)

    return {
        "avg_weekly_study_hours": round(weekly_hours, 1),
        "study_sessions_logged": len(sessions),
        "materials_uploaded": len(materials),
        "practice_quizzes_taken": len(quizzes),
        "avg_practice_quiz_score": (sum(q["score"] for q in quizzes) / len(quizzes)) if quizzes else None,
        "flashcards_reviewed": cards.get(course, 0) if course else sum(cards.values()),
        "avg_days_started_before_exam": avg_days_started_before_exam(state, course, today),
        "on_time_submission_rate": on_time,
        "missed_deadlines": missed,
        "late_night_study_pct": late_night_share(sessions),
    }


# --------------------------------------------------------------------------- #
# Achievements
# --------------------------------------------------------------------------- #
ACHIEVEMENT_CATEGORIES = ["Getting started", "Consistency", "Study time", "Healthy habits", "Mastery",
                          "Organization"]


def achievements(state: dict[str, Any], today: date) -> list[dict[str, Any]]:
    """Every badge with its category, unlock status and progress (0–1)."""
    sessions = state["sessions"]
    starts = [_session_start(s) for s in sessions]
    daily = daily_minutes(state)
    _, longest = streaks(daily, today)
    hours = total_minutes(state) / 60
    week_ago = today - timedelta(days=6)
    week_hours = sum(m for d, m in daily.items() if d >= week_ago) / 60

    quizzes = state["quizzes"]
    strong_quizzes = sum(1 for q in quizzes if q["score"] >= 80)
    perfect_quizzes = sum(1 for q in quizzes if q["score"] >= 100)
    cards = sum(state["flashcards_reviewed"].values())
    materials = state["materials"]
    summaries = sum(1 for m in materials if m.get("summary"))
    decks = sum(1 for m in materials if m.get("flashcards"))

    on_time = sum(1 for e in state["events"] if e["type"] in ("Deadline", "Quiz") and e.get("done"))
    early_exam = (avg_days_started_before_exam(state, None, today) or 0) >= 7
    graded_courses = [c for c, items in state.get("grades", {}).items() if items]
    projected = [grades.summarize(items)["projected"] for items in state.get("grades", {}).values() if items]
    best_projection = max((p for p in projected if p is not None), default=0)

    early_sessions = sum(1 for t in starts if t.hour < 9)
    marathon = sum(1 for s in sessions if s["minutes"] >= 120)
    focus_sprints = sum(1 for s in sessions if 25 <= s["minutes"] <= 50)
    weekend_days = len({t.date() for t in starts if t.weekday() >= 5})
    no_late_night = 0  # longest run of consecutive sessions that didn't start between midnight and 4 a.m.
    run = 0
    for t in sorted(starts):
        run = 0 if t.hour < 4 else run + 1
        no_late_night = max(no_late_night, run)
    recent_courses = {s["course"] for s, t in zip(sessions, starts) if t.date() >= week_ago}
    courses_this_week = len(recent_courses & set(state["courses"]))
    course_goal = max(2, len(state["courses"]))

    def badge(key, category, icon, name, desc, value, goal):
        return {"key": key, "category": category, "icon": icon, "name": name, "desc": desc,
                "unlocked": value >= goal, "progress": min(1.0, value / goal), "value": value, "goal": goal}

    badges = [
        badge("first", "Getting started", "🌱", "First Steps", "Log your first study session", len(sessions), 1),
        badge("courses", "Getting started", "🎒", "Full Course Load", "Add 4 courses", len(state["courses"]), 4),
        badge("first_upload", "Getting started", "📄", "Note Taker", "Upload your first study material",
              len(materials), 1),
        badge("first_quiz", "Getting started", "📝", "Quiz Rookie", "Take your first practice quiz", len(quizzes), 1),
        badge("grades", "Getting started", "📈", "Grade Tracker", "Enter graded work for a course",
              len(graded_courses), 1),

        badge("streak3", "Consistency", "✨", "Warming Up", "Study 3 days in a row", longest, 3),
        badge("streak7", "Consistency", "🔥", "7-Day Study Streak", "Study 7 days in a row", longest, 7),
        badge("streak14", "Consistency", "⚡", "Two-Week Tear", "Study 14 days in a row", longest, 14),
        badge("streak30", "Consistency", "🏆", "Unstoppable", "Study 30 days in a row", longest, 30),
        badge("weekend", "Consistency", "🛡️", "Weekend Warrior", "Study on 8 different weekend days",
              weekend_days, 8),
        badge("all_courses", "Consistency", "🧭", "Well-Rounded", "Study every one of your courses (2+) in one week",
              courses_this_week, course_goal),

        badge("hours10", "Study time", "⏱️", "10-Hour Club", "Log 10 total study hours", hours, 10),
        badge("hours50", "Study time", "⏳", "Half-Century", "Log 50 total study hours", hours, 50),
        badge("hours100", "Study time", "📚", "Century Scholar", "Log 100 total study hours", hours, 100),
        badge("week10", "Study time", "💪", "Power Week", "Study 10+ hours in the last 7 days", week_hours, 10),
        badge("marathon", "Study time", "🏃", "Marathoner", "Complete a single 2-hour study session", marathon, 1),

        badge("sprints", "Healthy habits", "🍅", "Focus Sprinter", "Log 10 focused 25–50 minute sessions",
              focus_sprints, 10),
        badge("early_riser", "Healthy habits", "🌅", "Early Riser", "Start 5 sessions before 9 a.m.",
              early_sessions, 5),
        badge("sleep", "Healthy habits", "😴", "Well Rested", "Log 20 sessions in a row without studying "
              "between midnight and 4 a.m.", no_late_night, 20),
        badge("early", "Healthy habits", "🐦", "Early Bird", "Start exam prep 7+ days ahead (on average)",
              1 if early_exam else 0, 1),

        badge("quiz", "Mastery", "🧠", "Quiz Master", "Score 80%+ on 5 practice quizzes", strong_quizzes, 5),
        badge("perfect", "Mastery", "💯", "Perfect Score", "Score 100% on a practice quiz", perfect_quizzes, 1),
        badge("cards", "Mastery", "🃏", "Flashcard Fiend", "Review 100 flashcards", cards, 100),
        badge("cards500", "Mastery", "🎴", "Memory Palace", "Review 500 flashcards", cards, 500),
        badge("a_track", "Mastery", "🅰️", "On Track for an A", "Have a course projected at 90% or higher",
              best_projection, 90),

        badge("library", "Organization", "📂", "Librarian", "Upload 5 study materials", len(materials), 5),
        badge("summaries", "Organization", "🗒️", "Summarizer", "Generate summaries for 3 materials", summaries, 3),
        badge("decks", "Organization", "🗂️", "Deck Builder", "Create flashcards for 3 materials", decks, 3),
        badge("planner", "Organization", "🗓️", "Planner", "Add 10 events to your calendar",
              len(state["events"]), 10),
        badge("deadlines", "Organization", "✅", "Deadline Crusher", "Complete 5 deadlines on time", on_time, 5),
    ]
    unlocked = sum(b["unlocked"] for b in badges)
    badges.append(badge("hunter", "Mastery", "🌟", "Achievement Hunter", "Unlock 20 other achievements",
                        unlocked, 20))
    return badges


# --------------------------------------------------------------------------- #
# Demo data
# --------------------------------------------------------------------------- #
def seed_demo_data(state: dict[str, Any], today: date, courses: list[str], seed: int = 7) -> None:
    """Fill the state with ~5 months of realistic-looking activity (used by examples/make_examples.py)."""
    rng = random.Random(seed)
    picks = courses[:4] if len(courses) >= 4 else courses
    for offset in range(150, 0, -1):
        day = today - timedelta(days=offset)
        # Busier mid-week, quieter weekends, with a few multi-day breaks.
        p = 0.45 if day.weekday() >= 5 else 0.72
        if 60 <= offset <= 66:
            p = 0.1
        if rng.random() > p:
            continue
        for _ in range(rng.choice([1, 1, 1, 2, 2, 3])):
            hour = rng.choice([9, 10, 13, 15, 16, 19, 20, 21, 22, 1])
            start = datetime.combine(day, time(hour, rng.choice([0, 15, 30, 45])))
            log_session(state, rng.choice(picks), rng.choice([25, 30, 45, 50, 60, 75, 90, 120]),
                        rng.choice(["Problem set", "Lecture review", "Read chapter", "Practice exam", ""]), start)
    # A streak leading up to today so streak badges show up.
    for offset in range(8, 0, -1):
        start = datetime.combine(today - timedelta(days=offset), time(18, 0))
        log_session(state, rng.choice(picks), rng.choice([45, 60, 90]), "Streak session", start)

    for i, course in enumerate(picks):
        add_event(state, "Midterm exam", course, today - timedelta(days=40 - i * 3), "Exam")
        add_event(state, "Final exam", course, today + timedelta(days=21 + i * 2), "Exam")
        add_event(state, "Problem set 4", course, today - timedelta(days=12 + i), "Deadline")
        add_event(state, "Problem set 5", course, today + timedelta(days=3 + i), "Deadline")
        add_event(state, "Project milestone", course, today + timedelta(days=9 + i), "Milestone")
    for e in state["events"]:
        if date.fromisoformat(e["date"]) < today and e["type"] == "Deadline":
            e["done"] = rng.random() < 0.85

    for _ in range(6):
        state["quizzes"].append({"id": new_id(), "material_id": None, "course": rng.choice(picks),
                                 "score": rng.choice([70, 80, 85, 90, 100]), "questions": 5,
                                 "taken_at": (datetime.now() - timedelta(days=rng.randint(1, 30))).isoformat()})
    for course in picks:
        state["flashcards_reviewed"][course] = state["flashcards_reviewed"].get(course, 0) + rng.randint(20, 60)
