"""Wolf Tracks API — the Python brain (risk model, tracker, grades, planner, Gemini) behind the React front end.

Run with:  uvicorn api:app --reload --port 8000
The React app in ``web/`` proxies ``/api`` to this server during development.
"""

from __future__ import annotations

import io
import math
import re
import shutil
import asyncio
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from utils import ai_helper, grades, pet as wolf, planner, tracker
from utils import model as risk_model

load_dotenv(tracker.ROOT / ".env")
UPLOAD_DIR = tracker.UPLOAD_DIR


# --------------------------------------------------------------------------- #
# JSON that survives NaN / numpy
# --------------------------------------------------------------------------- #
def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return None if math.isnan(number) or math.isinf(number) else number
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


class CleanJSON(JSONResponse):
    def render(self, content: Any) -> bytes:
        return super().render(clean(content))


app = FastAPI(title="Wolf Tracks API", default_response_class=CleanJSON)
_LOCK = asyncio.Lock()


@app.middleware("http")
async def _serialize(request, call_next):
    """One request at a time: the state file is shared and the browser fires requests in parallel."""
    async with _LOCK:
        return await call_next(request)


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_dataset: pd.DataFrame | None = None
_bundle: dict | None = None
_state: dict | None = None
_gemini_key: dict[str, str | None] = {"value": None}


def dataset() -> pd.DataFrame:
    global _dataset
    if _dataset is None:
        _dataset = risk_model.load_data()
    return _dataset


def bundle() -> dict:
    global _bundle
    if _bundle is None:
        _bundle = risk_model.load_or_train()
    return _bundle


def state() -> dict:
    global _state
    if _state is None:
        _state = tracker.load_state()
        wolf.ensure(_state)
    return _state


def save() -> None:
    tracker.save_state(state())


def client():
    return ai_helper.get_client(ai_helper.resolve_api_key(_gemini_key["value"]))


def has_key() -> bool:
    return bool(ai_helper.resolve_api_key(_gemini_key["value"]))


def fail(message: str, code: int = 400):
    raise HTTPException(status_code=code, detail=message)


def need_course(course: str) -> None:
    if course not in state()["courses"]:
        fail(f"Unknown course: {course}", 404)


# --------------------------------------------------------------------------- #
# Profiles
# --------------------------------------------------------------------------- #
def is_missing(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def my_profile(course: str, today: date) -> dict:
    s, b = state(), bundle()
    saved = s["profile"]
    derived = tracker.dashboard_profile(s, today, course)
    profile = {"course": course, "class_year": saved.get("class_year", "Freshman")}
    for feat in risk_model.NUMERIC:
        value = derived.get(feat)
        if is_missing(value):
            value = saved.get(feat)
        if is_missing(value):
            value = b["medians"][feat]
        profile[feat] = value
    if profile["practice_quizzes_taken"] == 0:
        profile["avg_practice_quiz_score"] = float("nan")
    midterm = grades.midterm_score(s["grades"].get(course, []))
    if midterm is not None:
        profile["midterm_score"] = midterm
    return profile


def risk_payload(profile: dict) -> dict:
    result = risk_model.predict_risk(bundle(), profile)
    result["resources"] = risk_model.SUPPORT_RESOURCES if result["tier"] != "on_track" else []
    return result


def grade_payload(course: str) -> dict:
    items = grades.clean_items(state()["grades"].get(course, []))
    errors = grades.validate(items)
    summary = None if errors or not items else grades.summarize(items)
    return {"items": items, "errors": errors, "summary": summary,
            "types": grades.ITEM_TYPES}


# --------------------------------------------------------------------------- #
# Overview / dashboard
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health():
    return {"ok": True, "ai": has_key()}


@app.get("/api/state")
def get_state():
    s = state()
    materials = [{k: v for k, v in m.items() if k not in ("path", "text_path")} for m in s["materials"]]
    return {**{k: s[k] for k in ("courses", "sessions", "events", "quizzes", "flashcards_reviewed", "grades",
                                 "profile", "study_plans")},
            "materials": materials, "ai": has_key()}


@app.get("/api/dashboard")
def dashboard():
    s, today = state(), date.today()
    daily = wolf.effective_daily(s)
    current, longest = tracker.streaks(daily, today)
    week_start = today - timedelta(days=6)
    week_minutes = sum(m for d, m in daily.items() if d >= week_start)
    grid_start = today - timedelta(days=today.weekday()) - timedelta(weeks=52)
    grid = []
    day = grid_start
    while day <= today:
        minutes = daily.get(day, 0.0)
        grid.append({"date": day.isoformat(), "minutes": minutes, "level": tracker.intensity_level(minutes)})
        day += timedelta(days=1)

    weeks = []
    first = today - timedelta(days=today.weekday()) - timedelta(weeks=11)
    for i in range(12):
        ws = first + timedelta(weeks=i)
        row = {"week": ws.isoformat()}
        for c in s["courses"]:
            row[c] = round(sum(m for d, m in tracker.daily_minutes(s, c).items()
                               if ws <= d < ws + timedelta(days=7)) / 60, 2)
        weeks.append(row)

    steps = [
        {"label": "Add your courses", "done": bool(s["courses"]), "page": "courses"},
        {"label": "Add an exam or deadline", "done": bool(s["events"]), "page": "calendar"},
        {"label": "Log your first study session", "done": bool(s["sessions"]), "page": "log"},
        {"label": "Upload notes or slides", "done": bool(s["materials"]), "page": "materials"},
    ]
    snapshot = []
    for c in s["courses"]:
        p = my_profile(c, today)
        r = risk_model.predict_risk(bundle(), p)
        snapshot.append({"course": c, "probability": r["probability"], "tier": r["tier"]})
    badges = tracker.achievements(s, today)
    return {
        "today": today.isoformat(),
        "kpis": {"week_hours": week_minutes / 60, "total_hours": tracker.total_minutes(s) / 60,
                 "streak": current, "longest_streak": longest, "sessions": len(s["sessions"]),
                 "badges_unlocked": sum(b["unlocked"] for b in badges), "badges_total": len(badges)},
        "grid": grid, "weekly": weeks, "courses": s["courses"],
        "upcoming": tracker.upcoming_events(s, today, 14),
        "steps": steps, "risk": snapshot,
    }


# --------------------------------------------------------------------------- #
# Courses
# --------------------------------------------------------------------------- #
@app.get("/api/courses")
def courses():
    s = state()
    return [{"name": c, "usage": tracker.course_usage(s, c)} for c in s["courses"]]


@app.post("/api/courses")
def add_course(body: dict):
    ok, message = tracker.add_course(state(), body.get("name", ""))
    if not ok:
        fail(message)
    save()
    return {"message": message}


@app.put("/api/courses/{old}")
def rename_course(old: str, body: dict):
    ok, message = tracker.rename_course(state(), old, body.get("name", ""))
    if not ok:
        fail(message)
    save()
    return {"message": message}


@app.delete("/api/courses/{course}")
def remove_course(course: str):
    message = tracker.remove_course(state(), course)
    save()
    return {"message": message}


# --------------------------------------------------------------------------- #
# Study log & timer
# --------------------------------------------------------------------------- #
@app.post("/api/sessions")
def add_session(body: dict):
    need_course(body.get("course", ""))
    minutes = float(body.get("minutes", 0))
    if minutes <= 0:
        fail("Minutes must be greater than 0.")
    start = datetime.fromisoformat(body["start"]) if body.get("start") else None
    session = tracker.log_session(state(), body["course"], minutes, body.get("notes", ""), start)
    reward = wolf.reward_session(state(), session, date.today())
    save()
    return {**session, "reward": reward}


@app.delete("/api/sessions/{session_id}")
def remove_session(session_id: str):
    tracker.delete_session(state(), session_id)
    save()
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Calendar
# --------------------------------------------------------------------------- #
@app.post("/api/events")
def add_event(body: dict):
    need_course(body.get("course", ""))
    if not body.get("title", "").strip():
        fail("Give the event a title.")
    kind = body.get("type", "Deadline")
    if kind not in tracker.EVENT_TYPES:
        fail("Unknown event type.")
    event = tracker.add_event(state(), body["title"], body["course"], date.fromisoformat(body["date"]), kind)
    save()
    return event


@app.patch("/api/events/{event_id}")
def update_event(event_id: str, body: dict):
    done = bool(body.get("done"))
    tracker.set_event_done(state(), event_id, done)
    event = next((e for e in state()["events"] if e["id"] == event_id), None)
    tokens = wolf.reward_event_done(state(), event, date.today()) if done and event else 0
    save()
    return {"ok": True, "tokens": tokens}


@app.delete("/api/events/{event_id}")
def remove_event(event_id: str):
    tracker.delete_event(state(), event_id)
    save()
    return {"ok": True}


@app.post("/api/syllabus")
async def import_syllabus(course: str = Form(...), file: UploadFile = File(...)):
    need_course(course)
    c = client()
    if c is None:
        fail("Add a Gemini API key in Settings to read syllabi.")
    data = await file.read()
    try:
        text = ai_helper.extract_text(file.filename, data)
        return ai_helper.extract_syllabus_events(c, text, course, date.today().year, data=data,
                                                 mime=ai_helper.mime_type(file.filename))
    except Exception as exc:
        fail(f"Couldn't read dates from that file: {exc}")


# --------------------------------------------------------------------------- #
# Study materials
# --------------------------------------------------------------------------- #
def find_material(material_id: str) -> dict:
    for m in state()["materials"]:
        if m["id"] == material_id:
            return m
    fail("Material not found.", 404)


def material_text(material: dict) -> str:
    path = tracker.ROOT / material["text_path"]
    return path.read_text(encoding="utf-8") if path.exists() else ""


def public_material(m: dict, with_text: bool = False) -> dict:
    out = {k: v for k, v in m.items() if k not in ("path", "text_path")}
    if with_text:
        out["text_preview"] = material_text(m)[:4000]
    return out


@app.get("/api/materials")
def list_materials():
    return [public_material(m) for m in sorted(state()["materials"], key=lambda m: m["uploaded_at"], reverse=True)]


@app.get("/api/materials/{material_id}")
def get_material(material_id: str):
    return public_material(find_material(material_id), with_text=True)


@app.post("/api/materials")
async def upload_materials(course: str = Form(...), files: list[UploadFile] = File(...)):
    need_course(course)
    added = []
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for f in files:
        data = await f.read()
        material_id = tracker.new_id()
        path = UPLOAD_DIR / f"{material_id}_{re.sub(r'[^A-Za-z0-9._-]+', '_', f.filename)}"
        path.write_bytes(data)
        try:
            text, error = ai_helper.extract_text(f.filename, data), None
        except Exception as exc:
            text, error = "", str(exc)
        text_path = path.with_name(path.name + ".txt")
        text_path.write_text(text, encoding="utf-8")
        material = {
            "id": material_id, "name": f.filename, "course": course,
            "path": path.relative_to(tracker.ROOT).as_posix(),
            "text_path": text_path.relative_to(tracker.ROOT).as_posix(),
            "chars": len(text), "size": len(data), "error": error,
            "uploaded_at": datetime.now().isoformat(timespec="seconds"),
            "summary": None, "summary_source": None, "flashcards": [], "quiz": [],
        }
        state()["materials"].append(material)
        added.append(public_material(material))
    save()
    return added


@app.delete("/api/materials/{material_id}")
def delete_material(material_id: str):
    m = find_material(material_id)
    for key in ("path", "text_path"):
        (tracker.ROOT / m[key]).unlink(missing_ok=True)
    state()["materials"] = [x for x in state()["materials"] if x["id"] != material_id]
    save()
    return {"ok": True}


def _raw(material: dict, text: str) -> tuple[bytes | None, str]:
    mime = ai_helper.mime_type(material["name"])
    if text.strip():
        return None, mime
    path = tracker.ROOT / material["path"]
    return (path.read_bytes() if path.exists() else None), mime


@app.post("/api/materials/{material_id}/summary")
def make_summary(material_id: str):
    m = find_material(material_id)
    text = material_text(m)
    c = client()
    try:
        if c:
            raw, mime = _raw(m, text)
            m["summary"], m["summary_source"] = ai_helper.summarize(c, text, data=raw, mime=mime), "Gemini"
        else:
            m["summary"], m["summary_source"] = ai_helper.offline_summary(text), "offline mode"
    except Exception as exc:
        fail(f"Summary failed: {exc}", 502)
    save()
    return public_material(m)


@app.post("/api/materials/{material_id}/flashcards")
def make_flashcards(material_id: str, body: dict | None = None):
    m = find_material(material_id)
    n = int((body or {}).get("n", 10))
    text = material_text(m)
    c = client()
    try:
        if c:
            raw, mime = _raw(m, text)
            m["flashcards"] = ai_helper.generate_flashcards(c, text, n, data=raw, mime=mime)
        else:
            m["flashcards"] = ai_helper.offline_flashcards(text, n)
    except Exception as exc:
        fail(f"Flashcard generation failed: {exc}", 502)
    save()
    return public_material(m)


@app.post("/api/materials/{material_id}/quiz")
def make_quiz(material_id: str, body: dict | None = None):
    m = find_material(material_id)
    c = client()
    if c is None:
        fail("Practice quizzes need a Gemini API key.")
    text = material_text(m)
    try:
        raw, mime = _raw(m, text)
        m["quiz"] = ai_helper.generate_quiz(c, text, int((body or {}).get("n", 5)), data=raw, mime=mime)
    except Exception as exc:
        fail(f"Quiz generation failed: {exc}", 502)
    save()
    return public_material(m)


@app.post("/api/materials/{material_id}/quiz/submit")
def submit_quiz(material_id: str, body: dict):
    m = find_material(material_id)
    answers = body.get("answers", [])
    quiz = m["quiz"]
    if len(answers) != len(quiz):
        fail("Answer every question first.")
    correct = sum(a == q["answer_index"] for a, q in zip(answers, quiz))
    score = round(100 * correct / len(quiz), 1)
    state()["quizzes"].append({"id": tracker.new_id(), "material_id": material_id, "course": m["course"],
                               "score": score, "questions": len(quiz),
                               "taken_at": datetime.now().isoformat(timespec="seconds")})
    reward = wolf.reward_quiz(state(), score, date.today())
    save()
    return {"score": score, "correct": correct, "total": len(quiz), "reward": reward,
            "review": [{"correct": a == q["answer_index"], "answer_index": q["answer_index"],
                        "explanation": q.get("explanation", "")} for a, q in zip(answers, quiz)]}


@app.post("/api/flashcards/reviewed")
def cards_reviewed(body: dict):
    course = body.get("course", "")
    need_course(course)
    s = state()
    count = int(body.get("count", 1))
    s["flashcards_reviewed"][course] = s["flashcards_reviewed"].get(course, 0) + count
    tokens = wolf.reward_cards(s, count, date.today())
    save()
    return {"ok": True, "tokens": tokens}


# --------------------------------------------------------------------------- #
# Study plan
# --------------------------------------------------------------------------- #
@app.post("/api/plan")
def make_plan(body: dict):
    s, today = state(), date.today()
    event = next((e for e in s["events"] if e["id"] == body.get("test_id")), None)
    if not event:
        fail("Pick an upcoming exam or quiz.", 404)
    settings = {"lead": int(body.get("lead", 10)), "max_minutes": int(body.get("max_minutes", 120)),
                "use_ai": bool(body.get("use_ai", True))}
    tier = body.get("tier", "on_track")
    material_ids = body.get("material_ids", [])
    note = body.get("note", "")
    busy: dict[date, list[str]] = {}
    for e in s["events"]:
        if e["id"] != event["id"] and e["type"] != "Study" and not e["done"]:
            busy.setdefault(date.fromisoformat(e["date"]), []).append(f"{e['course']} {e['title']}")
    plan = planner.build_plan(date.fromisoformat(event["date"]), today, event["type"], tier, settings["lead"],
                              settings["max_minutes"], busy)
    materials = [m for m in s["materials"] if m["id"] in material_ids]
    pairs = [(m["name"], material_text(m)) for m in materials]
    c = client() if settings["use_ai"] else None
    topics: list[dict] | None = body.get("topics")
    if topics is None and (materials or note.strip()):
        if c:
            try:
                topics = planner.normalize_topics(ai_helper.extract_test_topics(c, event["course"], event["title"],
                                                                                pairs, note))
            except Exception:
                topics = None
        if not topics:
            topics = planner.offline_topics(pairs, note)
    topics = topics or []
    planner.assign_topics(plan, topics)
    source = "standard study tasks"
    if c and plan["days"] and (materials or topics):
        try:
            text = "\n\n".join(f"{n}\n{t[:6000]}" for n, t in pairs) or note
            plan = planner.merge_ai_details(plan, ai_helper.generate_plan_details(
                c, event["course"], event["title"], date.fromisoformat(event["date"]), plan["days"], text))
            source = "tasks written by Gemini"
        except Exception:
            pass
    plan.update({"topics": topics, "course": event["course"], "title": event["title"], "test_date": event["date"],
                 "source": source, "tier": tier,
                 "next": (lambda n: {"topic": n[0], "date": n[1]} if n else None)(
                     planner.next_topic(plan, today.isoformat()))})
    return plan


@app.post("/api/plan/events")
def plan_to_calendar(body: dict):
    s = state()
    course, added = body.get("course", ""), []
    need_course(course)
    for d in body.get("days", []):
        added.append(tracker.add_event(s, f"Study: {d['focus']}"[:80], course, date.fromisoformat(d["date"]), "Study"))
    save()
    return {"added": len(added)}


# --------------------------------------------------------------------------- #
# Risk check & grades
# --------------------------------------------------------------------------- #
@app.get("/api/risk/meta")
def risk_meta():
    b, df = bundle(), dataset()
    return {
        "labels": risk_model.LABELS, "ranges": risk_model.FEATURE_RANGES, "numeric": risk_model.NUMERIC,
        "class_years": risk_model.CLASS_YEARS, "dataset_courses": sorted(df["course"].unique()),
        "medians": b["medians"], "percent_cols": risk_model.PERCENT_COLS,
        "students": [{"id": r.student_id, "course": r.course, "class_year": r.class_year}
                     for r in df.itertuples()][:400],
    }


@app.post("/api/risk/predict")
def risk_predict(body: dict):
    profile = body.get("profile", {})
    base = {**bundle()["medians"], "course": dataset()["course"].iloc[0], "class_year": "Freshman"}
    base.update({k: (float("nan") if v is None else v) for k, v in profile.items()})
    return risk_payload(base)


@app.get("/api/risk/mine/{course}")
def risk_mine(course: str):
    need_course(course)
    profile = my_profile(course, date.today())
    derived = tracker.dashboard_profile(state(), date.today(), course)
    result, g = risk_payload(profile), grade_payload(course)
    if g["summary"] and g["summary"]["projected"] is not None:
        tone, text = grades.cross_check(g["summary"]["projected"], bool(result["prediction"]))
        g["check"] = {"tone": tone, "text": text}
    return {"profile": profile, "derived": {k: v for k, v in derived.items() if not is_missing(v)},
            "result": result, "grades": g}


@app.put("/api/profile")
def save_profile(body: dict):
    state()["profile"].update(body)
    save()
    return {"ok": True}


@app.get("/api/risk/student/{student_id}")
def risk_student(student_id: str):
    df = dataset().set_index("student_id")
    if student_id not in df.index:
        fail("Student not found.", 404)
    row = df.loc[student_id]
    profile = row.to_dict()
    actual = int(profile.pop(risk_model.TARGET))
    return {"profile": profile, "actual": actual, "result": risk_payload(profile)}


@app.put("/api/grades/{course}")
def save_grades(course: str, body: dict):
    need_course(course)
    state()["grades"][course] = grades.clean_items(body.get("items", []))
    save()
    return grade_payload(course)


@app.post("/api/grades/preview")
def grade_preview(body: dict):
    items = grades.clean_items(body.get("items", []))
    errors = grades.validate(items)
    remaining = body.get("remaining_score")
    return {"errors": errors, "summary": None if errors or not items else grades.summarize(items, remaining)}


@app.post("/api/risk/batch")
async def risk_batch(file: UploadFile = File(...)):
    data = await file.read()
    try:
        df = risk_model.load_data(io.BytesIO(data), require_target=False)
    except Exception as exc:
        fail(f"Couldn't read that CSV: {exc}")
    scored = risk_model.score_students(bundle(), df)
    metrics = risk_model.evaluate_labeled(scored)
    counts = scored["risk_tier"].value_counts().to_dict()
    cols = [c for c in ["student_id", "course", "class_year", "risk_probability", "risk_tier", "top_suggestion",
                        risk_model.TARGET] if c in scored.columns]
    return {"n": len(scored), "counts": counts, "metrics": metrics,
            "rows": scored[cols].head(500).to_dict("records")}


# --------------------------------------------------------------------------- #
# Insights
# --------------------------------------------------------------------------- #
def tree_json(max_depth: int = 3) -> dict:
    pipe = bundle()["pipeline"]
    tree = pipe.named_steps["tree"].tree_
    names = risk_model.encoded_feature_names(bundle())

    def walk(i: int, depth: int) -> dict:
        counts = tree.value[i][0]
        total = float(counts.sum()) or 1.0
        node = {"samples": int(tree.n_node_samples[i]), "risk": float(counts[1] / total) if len(counts) > 1 else 0.0}
        if tree.children_left[i] != -1 and depth < max_depth:
            raw = names[tree.feature[i]]
            for prefix, label in (("class_year_", "Class year: "), ("course_", "Course: ")):
                if raw.startswith(prefix):
                    node["feature"] = label + raw[len(prefix):]
                    break
            else:
                node["feature"] = risk_model.LABELS.get(raw, raw)
            node["threshold"] = float(tree.threshold[i])
            node["left"], node["right"] = walk(tree.children_left[i], depth + 1), walk(tree.children_right[i], depth + 1)
        return node

    return walk(0, 0)


@app.get("/api/insights")
def insights():
    b, df = bundle(), dataset()
    imp = {risk_model.LABELS.get(k, k): v for k, v in b["feature_importances"].items() if v > 0}
    by_course = df.groupby("course")[risk_model.TARGET].mean().sort_values().to_dict()
    boxes = {}
    for feat in risk_model.NUMERIC:
        boxes[feat] = {
            label: df.loc[df[risk_model.TARGET] == v, feat].dropna().describe(percentiles=[.25, .5, .75])
            .reindex(["min", "25%", "50%", "75%", "max"]).tolist()
            for label, v in (("C or better", 0), ("D/F (at risk)", 1))}
    return {"metrics": b["metrics"], "n_train": b["n_train"], "n_test": b["n_test"], "best_params": b["best_params"],
            "importances": dict(sorted(imp.items(), key=lambda kv: -kv[1])), "by_course": by_course,
            "boxes": boxes, "tree": tree_json(), "rules": risk_model.tree_rules_text(b), "labels": risk_model.LABELS,
            "numeric": risk_model.NUMERIC, "rows": len(df)}


@app.post("/api/insights/retrain")
def retrain():
    global _bundle
    _bundle = risk_model.load_or_train(force=True)
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Wolf: mood, tokens, shop, bonus games
# --------------------------------------------------------------------------- #
def _wolf_call(fn, *args, **kwargs):
    try:
        result = fn(state(), *args, **kwargs)
    except ValueError as exc:
        fail(str(exc))
    save()
    return result


@app.get("/api/pet")
def get_pet():
    data = wolf.payload(state(), date.today())
    save()
    return data


@app.post("/api/pet/checkin")
def pet_checkin():
    result = _wolf_call(wolf.checkin, date.today())
    return {**result, "pet": wolf.payload(state(), date.today())}


@app.put("/api/pet/name")
def pet_name(body: dict):
    name = " ".join(str(body.get("name", "")).split())[:20]
    if not name:
        fail("Give your wolf a name.")
    wolf.ensure(state())["name"] = name
    save()
    return {"name": name}


@app.post("/api/pet/buy")
def pet_buy(body: dict):
    item = _wolf_call(wolf.buy, body.get("item", ""))
    return {"item": item, "pet": wolf.payload(state(), date.today())}


@app.post("/api/pet/equip")
def pet_equip(body: dict):
    _wolf_call(wolf.equip, body.get("slot", ""), body.get("item"))
    return wolf.payload(state(), date.today())


@app.post("/api/quests/claim")
def quest_claim(body: dict):
    result = _wolf_call(wolf.claim_quest, body.get("id", ""), date.today())
    return {**result, "pet": wolf.payload(state(), date.today())}


@app.post("/api/quests/chest")
def quest_chest():
    result = _wolf_call(wolf.open_chest, date.today())
    return {**result, "pet": wolf.payload(state(), date.today())}


@app.post("/api/quests/weekly")
def quest_weekly():
    result = _wolf_call(wolf.open_weekly_chest, date.today())
    return {**result, "pet": wolf.payload(state(), date.today())}


@app.post("/api/games/plinko")
def game_plinko(body: dict):
    return _wolf_call(wolf.play_plinko, body.get("session_id", ""), mega=bool(body.get("mega")))


@app.post("/api/games/crossy/start")
def game_crossy_start(body: dict):
    return _wolf_call(wolf.crossy_start, body.get("session_id", ""), mega=bool(body.get("mega")))


@app.post("/api/games/crossy/hop")
def game_crossy_hop(body: dict):
    return _wolf_call(wolf.crossy_hop, body.get("session_id", ""))


@app.post("/api/games/crossy/cashout")
def game_crossy_cashout(body: dict):
    return _wolf_call(wolf.crossy_cashout, body.get("session_id", ""))


@app.post("/api/games/slot")
def game_slot(body: dict):
    return _wolf_call(wolf.play_slot, body.get("session_id", ""), mega=bool(body.get("mega")))


@app.post("/api/games/roulette")
def game_roulette(body: dict):
    return _wolf_call(wolf.play_roulette, body.get("session_id", ""), mega=bool(body.get("mega")))


# --------------------------------------------------------------------------- #
# Achievements & settings
# --------------------------------------------------------------------------- #
@app.get("/api/achievements")
def get_achievements():
    return {"badges": tracker.achievements(state(), date.today()), "categories": tracker.ACHIEVEMENT_CATEGORIES}


@app.put("/api/settings/key")
def set_key(body: dict):
    _gemini_key["value"] = (body.get("key") or "").strip() or None
    return {"ai": has_key()}


@app.get("/api/export")
def export_data():
    return Response(tracker.export_archive(state()), media_type="application/zip",
                    headers={"Content-Disposition": "attachment; filename=wolf-tracks-archive.zip"})


@app.post("/api/import")
async def import_data(file: UploadFile = File(...)):
    global _state
    try:
        _state = tracker.import_archive(await file.read())
    except ValueError as exc:
        fail(str(exc))
    wolf.ensure(_state)
    save()
    return {"ok": True}


@app.post("/api/reset")
def reset():
    global _state
    _state = tracker.default_state()
    wolf.ensure(_state)
    if UPLOAD_DIR.exists():
        shutil.rmtree(UPLOAD_DIR)
    save()
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Serve the built React app (``cd web && npm run build``) so one command runs everything
# --------------------------------------------------------------------------- #
DIST = tracker.ROOT / "web" / "dist"
if DIST.exists():
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            fail("Not found", 404)
        candidate = (DIST / path).resolve()
        if path and candidate.is_file() and DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(DIST / "index.html")
