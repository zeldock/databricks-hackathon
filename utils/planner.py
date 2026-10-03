"""Study plans for upcoming tests.

The schedule itself is built deterministically from evidence-based habits that the risk model also rewards:
start early (avg_days_started_before_exam), spread the work out (spacing effect), practice retrieval
(quizzes and flashcards), avoid late-night cramming and rest the night before. Gemini, when available,
only fills in course-specific focus topics and tasks for each day.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

# Total study time to aim for, before adjusting for risk.
BASE_HOURS = {"Exam": 8.0, "Quiz": 3.0}
RISK_MULTIPLIER = {"at_risk": 1.5, "watch": 1.25, "on_track": 1.0}
DEFAULT_LEAD_DAYS = {"Exam": 7, "Quiz": 3}
MIN_SESSION = 20  # minutes
FINAL_DAY_CAP = 45  # minutes


def _phase(index: int, count: int) -> str:
    remaining = count - index  # 1 = the day before the test
    if remaining == 1:
        return "final"
    if remaining == 2:
        return "rehearsal"
    return "learn" if index < (count - 2) / 2 else "practice"


PHASES = {
    "learn": ("Rebuild understanding", [
        "Re-read your lecture notes and the AI summary for this unit",
        "Make or update flashcards for new terms and formulas",
        "Work through worked examples before trying problems on your own",
    ]),
    "practice": ("Active practice", [
        "Do practice problems without looking at the answers first",
        "Review flashcards — focus on the ones you missed last time",
        "Take an AI practice quiz and note every topic you got wrong",
    ]),
    "rehearsal": ("Full rehearsal", [
        "Take a timed practice test under exam conditions",
        "Review every mistake and rework those problems",
        "Write a one-page summary sheet of key ideas",
    ]),
    "final": ("Light review and rest", [
        "Skim your summary sheet and flashcards (no new material)",
        "Pack what you need for the test (calculator, ID, pencils)",
        "Get 7–9 hours of sleep — memory consolidates overnight",
    ]),
}


def recommended_hours(kind: str, tier: str) -> float:
    return BASE_HOURS.get(kind, BASE_HOURS["Exam"]) * RISK_MULTIPLIER.get(tier, 1.0)


def build_plan(test_date: date, today: date, kind: str, tier: str, lead_days: int, max_minutes: int,
               busy: dict[date, list[str]] | None = None) -> dict[str, Any]:
    """Day-by-day plan from max(today, test - lead_days) up to the day before the test."""
    busy = busy or {}
    first = max(today, test_date - timedelta(days=lead_days))
    days = [first + timedelta(days=i) for i in range((test_date - first).days)]
    target_minutes = recommended_hours(kind, tier) * 60
    if not days:
        return {"days": [], "target_minutes": target_minutes, "planned_minutes": 0,
                "note": "The test is today — do a light review of your summary sheet and flashcards."}

    # Ramp up toward the test, keep the last day light, and halve days that already have other deadlines.
    weights = []
    for i, day in enumerate(days):
        weight = 1 + i / max(1, len(days) - 1)
        if i == len(days) - 1 and len(days) > 1:
            weight = 0.6
        if busy.get(day):
            weight *= 0.5
        weights.append(weight)
    scale = target_minutes / sum(weights)

    plan = []
    for i, (day, weight) in enumerate(zip(days, weights)):
        phase = _phase(i, len(days))
        minutes = min(max_minutes, max(MIN_SESSION, round(weight * scale / 5) * 5))
        if phase == "final":
            minutes = min(minutes, FINAL_DAY_CAP)  # the night before is for light review and sleep
        focus, tasks = PHASES[phase]
        note = f"Also due: {', '.join(busy[day])}" if busy.get(day) else ""
        plan.append({"date": day.isoformat(), "minutes": minutes, "focus": focus, "tasks": list(tasks),
                     "note": note, "phase": phase, "topics": []})
    planned = sum(d["minutes"] for d in plan)
    note = ""
    if planned < target_minutes * 0.9:
        note = (f"With {len(days)} day(s) and at most {max_minutes} min/day you can fit {planned / 60:.1f} h of the "
                f"recommended {target_minutes / 60:.1f} h — start earlier or allow more time per day if you can.")
    return {"days": plan, "target_minutes": target_minutes, "planned_minutes": planned, "note": note}


# --------------------------------------------------------------------------- #
# Topics on the test
# --------------------------------------------------------------------------- #
IMPORTANCE_ORDER = {"high": 0, "medium": 1, "low": 2}
CONFIDENCE_LEVELS = ["Shaky", "OK", "Confident"]
_SKIP_TITLES = ("practice", "check your understanding", "try it", "workshop", "questions", "review", "agenda",
                "outline", "summary", "references", "answers")


def _clean(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def offline_topics(materials: list[tuple[str, str]], note: str = "", max_topics: int = 10) -> list[dict]:
    """Topics from slide titles and short heading-like lines (no AI needed), plus anything the student typed."""
    topics: list[dict] = []
    for name, text in materials:
        candidates: list[tuple[str, str]] = []
        if "--- Slide" in text:
            for block in text.split("--- Slide")[2:]:  # skip the title slide
                lines = [ln.strip() for ln in block.splitlines()[1:] if ln.strip()]
                if lines:
                    candidates.append((lines[0], lines[1] if len(lines) > 1 else ""))
        else:
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            for i, line in enumerate(lines):
                heading = line.lstrip("#").strip()
                looks_like_heading = (line.startswith("#") or (3 <= len(line) <= 60 and line[-1] not in ".:;,?!"
                                      and line[0].isupper() and not line.startswith(("•", "-"))))
                if looks_like_heading and i + 1 < len(lines):
                    candidates.append((heading, lines[i + 1]))
        for title, detail in candidates:
            if any(title.lower().startswith(skip) for skip in _SKIP_TITLES):
                continue
            topics.append({"name": _clean(title, 60), "summary": _clean(detail, 140), "importance": "medium",
                           "source": name})
    topics = normalize_topics(topics, 60)
    # Topics the student typed: mark a matching material topic as high importance (keeping learning order),
    # otherwise add it at the end.
    for line in [t.strip(" -•\t") for chunk in note.splitlines() for t in chunk.split(",")]:
        if not line:
            continue
        match = next((t for t in topics if line.lower() in t["name"].lower() or t["name"].lower() in line.lower()),
                     None)
        if match:
            match["importance"] = "high"
        else:
            topics.append({"name": _clean(line, 60), "summary": "You noted this is on the test.",
                           "importance": "high", "source": "Your notes", "confidence": None})
    # Trim to max_topics, dropping later medium topics first so noted (high) ones always stay.
    while len(topics) > max_topics:
        drop = next((i for i in range(len(topics) - 1, -1, -1) if topics[i]["importance"] != "high"), None)
        if drop is None:
            break
        topics.pop(drop)
    return topics


def normalize_topics(raw: list[dict], max_topics: int = 12) -> list[dict]:
    topics, seen = [], set()
    for t in raw:
        name = _clean(str(t.get("name", "")), 60)
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        importance = str(t.get("importance", "medium")).lower()
        topics.append({"name": name, "summary": _clean(str(t.get("summary", "")), 160),
                       "importance": importance if importance in IMPORTANCE_ORDER else "medium",
                       "source": str(t.get("source", "")), "confidence": t.get("confidence")})
    return topics[:max_topics]


def _priority(topic: dict) -> tuple[int, int]:
    confidence = {"Shaky": 0, None: 1, "OK": 2, "Confident": 3}.get(topic.get("confidence"), 1)
    return confidence, IMPORTANCE_ORDER.get(topic["importance"], 1)


def assign_topics(plan: dict[str, Any], topics: list[dict]) -> dict[str, Any]:
    """Spread the test's topics over the plan: learn each once, then revisit weak / important ones."""
    days = plan["days"]
    if not days or not topics:
        return plan
    names = [t["name"] for t in topics]
    learn = [d for d in days if d["phase"] == "learn"]
    practice = [d for d in days if d["phase"] == "practice"]
    if not learn:  # short plan: learn on whatever days come before the rehearsal
        learn, practice = practice, []
    if not learn:
        learn = [d for d in days if d["phase"] == "rehearsal"] or days[:1]

    per_day = -(-len(names) // len(learn))  # ceiling division
    for i, day in enumerate(learn):
        chunk = names[i * per_day:(i + 1) * per_day]
        day["topics"] = chunk
        if chunk:
            day["focus"] = "Learn: " + ", ".join(chunk)
            day["tasks"] = ([f"Study “{n}” from your notes and slides, then explain it in your own words"
                             for n in chunk] + ["Make flashcards for the key terms and formulas"])
    revisit = [t["name"] for t in sorted(topics, key=_priority) if t.get("confidence") != "Confident"] or names
    if practice:
        per_practice = max(1, -(-len(revisit) // len(practice)))
        for i, day in enumerate(practice):
            chunk = revisit[i * per_practice:(i + 1) * per_practice] or revisit[:per_practice]
            day["topics"] = chunk
            day["focus"] = "Practice: " + ", ".join(chunk)
            day["tasks"] = ([f"Work practice problems on “{n}” without notes, then check" for n in chunk]
                            + ["Take a short AI practice quiz and note what you missed"])
    for day in days:
        if day["phase"] == "rehearsal" and day not in learn:
            day["topics"] = names
            day["focus"] = "Full rehearsal — all topics"
        elif day["phase"] == "final":
            day["topics"] = revisit[:3]
            day["tasks"] = ([f"Quick review of “{n}”" for n in revisit[:3]]
                            + ["Skim flashcards — no new material", "Get 7–9 hours of sleep"])
    return plan


def next_topic(plan: dict[str, Any], today_iso: str) -> tuple[dict, str | None] | None:
    """The topic to study now: the first not-yet-confident topic in plan order, with its next planned day."""
    topics = {t["name"]: t for t in plan.get("topics", [])}
    for day in plan["days"]:
        if day["date"] < today_iso:
            continue
        for name in day.get("topics", []):
            topic = topics.get(name)
            if topic and topic.get("confidence") != "Confident":
                return topic, day["date"]
    leftover = [t for t in topics.values() if t.get("confidence") != "Confident"]
    return (sorted(leftover, key=_priority)[0], None) if leftover else None


def merge_ai_details(plan: dict[str, Any], ai_days: list[dict[str, Any]]) -> dict[str, Any]:
    """Replace generic focus/tasks with course-specific ones from Gemini, matched by date."""
    by_date = {d["date"]: d for d in ai_days}
    for day in plan["days"]:
        ai = by_date.get(day["date"])
        if ai and ai.get("tasks"):
            day["tasks"] = ai["tasks"][:4]
            if ai.get("focus") and not day.get("topics"):  # topic days keep their "Learn: …" / "Practice: …" focus
                day["focus"] = ai["focus"]
    return plan


def to_markdown(title: str, plan: dict[str, Any]) -> str:
    lines = [f"# Study plan — {title}", "",
             f"Planned: {plan['planned_minutes'] / 60:.1f} h (recommended {plan['target_minutes'] / 60:.1f} h)", ""]
    if plan.get("topics"):
        lines.append("## Topics on this test")
        lines += [f"- [ ] **{t['name']}** ({t['importance']}) — {t['summary']}" for t in plan["topics"]]
        lines.append("")
    for day in plan["days"]:
        d = date.fromisoformat(day["date"])
        lines.append(f"## {d:%A, %B} {d.day} — {day['minutes']} min · {day['focus']}")
        lines += [f"- [ ] {task}" for task in day["tasks"]]
        if day.get("note"):
            lines.append(f"- _{day['note']}_")
        lines.append("")
    return "\n".join(lines)
