"""Wolf Tracks — an AI-powered student dashboard for WolfHacks 2026.

Run with:  streamlit run app.py

Navigation (sidebar)
--------------------
Overview  · Dashboard        – getting-started checklist, KPIs, study grid, weekly hours, upcoming, risk snapshot
Study     · Study log        – live timer, manual logging, history
          · Calendar         – deadlines/exams/milestones, AI syllabus import
          · Study materials  – upload notes → AI summaries, flashcards, practice quizzes
Insights  · Risk check       – decision-tree at-risk prediction, explanation, suggestions, CSV batch scoring
          · Achievements     – badges and progress
          · Model insights   – evaluation on the held-out split, feature importance, the tree itself
Manage    · Courses          – add, rename, remove your courses
          · Settings         – Gemini key, import/export archives, reset
"""

from __future__ import annotations

import calendar as cal_lib
import html
import io
import json
import math
import random
import re
import shutil
from datetime import date, datetime, time, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sklearn.tree import plot_tree

from utils import ai_helper, grades, planner, tracker
from utils import model as risk_model

load_dotenv(tracker.ROOT / ".env")
ASSETS = tracker.ROOT / "assets"
st.set_page_config(page_title="Wolf Tracks", page_icon=str(ASSETS / "logo.png"), layout="wide")

UPLOAD_DIR = tracker.UPLOAD_DIR
GREEN = "#2da44e"
PAGE: dict = {}  # filled in main(); used for links between pages


# --------------------------------------------------------------------------- #
# Shared resources & state
# --------------------------------------------------------------------------- #
@st.cache_data
def get_dataset() -> pd.DataFrame:
    return risk_model.load_data()


@st.cache_resource(show_spinner="Training the decision tree…")
def get_bundle() -> dict:
    return risk_model.load_or_train()


def get_state() -> dict:
    if "state" not in st.session_state:
        st.session_state.state = tracker.load_state()
    return st.session_state.state


def persist() -> None:
    tracker.save_state(st.session_state.state)


def flash(message: str) -> None:
    """Queue a toast that survives the next st.rerun()."""
    st.session_state["flash"] = message


def gemini_key() -> str | None:
    key = st.session_state.get("gemini_key") or None
    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY")
        except Exception:  # no secrets.toml configured
            key = None
    return ai_helper.resolve_api_key(key)


def gemini_client():
    try:
        return ai_helper.get_client(gemini_key())
    except Exception as exc:
        st.error(f"Could not start the Gemini client: {exc}")
        return None


def is_missing(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def my_profile(state: dict, bundle: dict, today: date, course: str) -> dict:
    """Merge activity-derived features with saved self-reported ones (falling back to dataset medians)."""
    saved = state["profile"]
    derived = tracker.dashboard_profile(state, today, course)
    profile = {"course": course, "class_year": saved.get("class_year", "Freshman")}
    for feat in risk_model.NUMERIC:
        value = derived.get(feat)
        if is_missing(value):
            value = saved.get(feat)
        if is_missing(value):
            value = bundle["medians"][feat]
        profile[feat] = value
    if profile["practice_quizzes_taken"] == 0:
        profile["avg_practice_quiz_score"] = float("nan")  # matches the dataset: blank when no quizzes
    midterm = grades.midterm_score(state["grades"].get(course, []))
    if midterm is not None:
        profile["midterm_score"] = midterm
    return profile


# --------------------------------------------------------------------------- #
# Celebrations: achievement banners and task-completion confetti (pure CSS, no JavaScript)
# --------------------------------------------------------------------------- #
FX_CSS = """
<style>
/* Effect elements are fixed-position overlays; keep their Streamlit wrappers from taking up space. */
.stElementContainer:has(.sp-fx) { position: absolute; height: 0; margin: 0; padding: 0; }
.sp-confetti {
    position: fixed; top: -14px; left: var(--x); width: 8px; height: 13px; border-radius: 2px;
    background: var(--c); opacity: 0; z-index: 999990; pointer-events: none;
    animation: sp-fall var(--d) cubic-bezier(.25, .6, .45, 1) var(--delay) forwards;
}
@keyframes sp-fall {
    0%   { opacity: 1; transform: translate(0, 0) rotate(0deg); }
    85%  { opacity: 1; }
    100% { opacity: 0; transform: translate(var(--dx), var(--dy)) rotate(var(--r)); }
}
.sp-ach {
    position: fixed; right: 24px; bottom: calc(24px + var(--i) * 92px); z-index: 999995; pointer-events: none;
    display: flex; gap: 14px; align-items: center; min-width: 300px; max-width: 380px; overflow: hidden;
    padding: 12px 18px 14px 14px; border-radius: 12px; border-left: 5px solid #e3b341;
    background: #1f2328; color: #ffffff; box-shadow: 0 10px 30px rgba(0, 0, 0, .28);
    font-family: inherit; opacity: 0; transform: translateX(120%);
    animation: sp-ach-in-out 6s ease calc(var(--i) * .25s) forwards;
}
.sp-ach-icon { font-size: 34px; line-height: 1; }
.sp-ach-kicker { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: #e3b341; font-weight: 700; }
.sp-ach-name { font-size: 16px; font-weight: 700; margin-top: 1px; }
.sp-ach-desc { font-size: 12.5px; opacity: .8; margin-top: 1px; }
.sp-ach-timer {
    position: absolute; left: 0; bottom: 0; height: 3px; width: 100%; background: #e3b341;
    transform-origin: left; animation: sp-ach-timer 5.4s linear calc(var(--i) * .25s + .4s) forwards;
}
@keyframes sp-ach-in-out {
    0%   { opacity: 0; transform: translateX(120%); }
    7%   { opacity: 1; transform: translateX(0); }
    90%  { opacity: 1; transform: translateX(0); }
    100% { opacity: 0; transform: translateX(120%); }
}
@keyframes sp-ach-timer { from { transform: scaleX(1); } to { transform: scaleX(0); } }
@media (prefers-reduced-motion: reduce) {
    .sp-confetti { display: none; }
    .sp-ach { animation: sp-ach-fade 6s step-end forwards; transform: none; opacity: 1; }
    .sp-ach-timer { animation: none; }
    @keyframes sp-ach-fade { to { opacity: 0; } }
}
</style>
"""
CONFETTI_COLORS = ["#2da44e", "#1f6feb", "#e3b341", "#d1242f", "#8250df", "#fb8f44", "#3fb950"]


def celebrate() -> None:
    """Queue a small confetti burst for the next render (survives st.rerun and widget callbacks)."""
    st.session_state["_confetti"] = True


def confetti_html(pieces: int = 42) -> str:
    """A small burst of confetti falling across the middle of the screen."""
    rng = random.Random()
    bits = []
    for _ in range(pieces):
        style = (f"--x:{rng.uniform(28, 72):.1f}vw;--c:{rng.choice(CONFETTI_COLORS)};"
                 f"--d:{rng.uniform(2.3, 3.4):.2f}s;--delay:{rng.uniform(0, .35):.2f}s;"
                 f"--dx:{rng.uniform(-90, 90):.0f}px;--dy:{rng.uniform(45, 70):.0f}vh;--r:{rng.uniform(-540, 540):.0f}deg")
        bits.append(f'<div class="sp-confetti" style="{style}"></div>')
    return FX_CSS + f'<div class="sp-fx" aria-hidden="true">{"".join(bits)}</div>'


def achievement_banner_html(badges: list[dict]) -> str:
    """Bottom-right banners that slide in, show a draining timer bar, then slide away."""
    shown = badges[:3]
    cards = []
    for i, b in enumerate(shown):
        extra = f" (+{len(badges) - 3} more)" if i == 2 and len(badges) > 3 else ""
        cards.append(
            f'<div class="sp-ach" style="--i:{i}" role="status">'
            f'<div class="sp-ach-icon">{b["icon"]}</div>'
            f'<div><div class="sp-ach-kicker">Achievement unlocked{extra}</div>'
            f'<div class="sp-ach-name">{html.escape(b["name"])}</div>'
            f'<div class="sp-ach-desc">{html.escape(b["desc"])}</div></div>'
            f'<div class="sp-ach-timer"></div></div>')
    return FX_CSS + f'<div class="sp-fx">{"".join(cards)}</div>'


def render_effects() -> None:
    if st.session_state.pop("_confetti", False):
        st.html(confetti_html())


def notify_new_achievements(state: dict, today: date) -> None:
    """Show a banner (and balloons) for any badge unlocked since the previous run."""
    unlocked = {a["key"]: a for a in tracker.achievements(state, today) if a["unlocked"]}
    previous = st.session_state.get("_unlocked")
    if previous is not None and not st.session_state.pop("_suppress_achievements", False):
        new = [a for key, a in unlocked.items() if key not in previous]
        if new:
            st.html(achievement_banner_html(new))
            st.balloons()
    st.session_state["_unlocked"] = set(unlocked)


# --------------------------------------------------------------------------- #
# Reusable UI patterns
# --------------------------------------------------------------------------- #
def page_header(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def empty_state(icon: str, title: str, message: str, link_page: str | None = None, link_label: str = "") -> None:
    """Centered 'nothing here yet' panel with a single call to action."""
    with st.container(border=True):
        st.markdown(
            f"<div style='text-align:center;padding:12px 0 4px'>"
            f"<div style='font-size:40px'>{icon}</div>"
            f"<div style='font-size:18px;font-weight:600;margin-top:6px'>{html.escape(title)}</div>"
            f"<div style='opacity:.75;margin-top:4px'>{html.escape(message)}</div></div>",
            unsafe_allow_html=True,
        )
        if link_page:
            _, mid, _ = st.columns([2, 1, 2])
            with mid:
                st.page_link(PAGE[link_page], label=link_label, icon=":material/arrow_forward:")


def require_courses(state: dict, purpose: str) -> None:
    """Stop rendering the page with a helpful empty state if the user hasn't added any courses."""
    if not state["courses"]:
        empty_state("🎓", "Add a course first", f"You need at least one course to {purpose}.",
                    "courses", "Go to Courses")
        st.stop()


@st.dialog("Please confirm")
def confirm_dialog(message: str, confirm_label: str, on_confirm) -> None:
    """Standard confirmation for destructive or irreversible actions."""
    st.markdown(message)
    cancel, ok = st.columns(2)
    if cancel.button("Cancel", width="stretch"):
        st.rerun()
    if ok.button(confirm_label, type="primary", width="stretch"):
        on_confirm()
        st.rerun()


def sidebar_status(state: dict, today: date) -> None:
    """Compact status shown under the navigation on every page."""
    current, _ = tracker.streaks(tracker.daily_minutes(state), today)
    with st.sidebar:
        st.metric("Current streak", f"{current} day{'s' if current != 1 else ''}")
        timer = state.get("active_timer")
        if timer:
            st.info(f"Timer {'running' if timer['running'] else 'paused'}: **{timer['course']}**",
                    icon=":material/timer:")
            st.page_link(PAGE["log"], label="Open timer", icon=":material/arrow_forward:")
        st.caption("✅ Gemini connected" if gemini_key() else "⚪ AI offline · add a key in Settings")


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #
def getting_started(state: dict) -> None:
    """Onboarding checklist that disappears once every step is done."""
    steps = [
        ("Add your courses", bool(state["courses"]), "courses"),
        ("Add an exam or deadline to the calendar", bool(state["events"]), "calendar"),
        ("Log your first study session", bool(state["sessions"]), "log"),
        ("Upload notes or slides", bool(state["materials"]), "materials"),
    ]
    done = sum(ok for _, ok, _ in steps)
    if done == len(steps):
        return
    with st.container(border=True):
        st.subheader("Getting started")
        st.progress(done / len(steps), text=f"{done} of {len(steps)} steps complete")
        for label, ok, page in steps:
            if ok:
                st.markdown(f":material/check_circle: ~~{label}~~")
            else:
                st.page_link(PAGE[page], label=label, icon=":material/radio_button_unchecked:")
        st.caption("Just exploring? Load the example archive from **Settings → Import data** "
                   "(file: `examples/dashboard_archive/example_student_archive.zip`).")


def weekly_hours_chart(state: dict, today: date, weeks: int = 12):
    if not state["sessions"]:
        return None
    df = pd.DataFrame(state["sessions"])
    df["start"] = pd.to_datetime(df["start"])
    df["week"] = (df["start"].dt.normalize() - pd.to_timedelta(df["start"].dt.weekday, unit="D")).dt.date
    first_week = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks - 1)
    df = df[df["week"] >= first_week]
    if df.empty:
        return None
    grouped = df.groupby(["week", "course"], as_index=False)["minutes"].sum()
    grouped["hours"] = grouped["minutes"] / 60
    fig = px.bar(grouped, x="week", y="hours", color="course", labels={"week": "Week of", "hours": "Hours"})
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), legend_title_text="",
                      bargap=0.25, legend=dict(orientation="h", y=-0.25))
    return fig


def page_dashboard() -> None:
    state, bundle, today = get_state(), get_bundle(), date.today()
    page_header("Dashboard", today.strftime("%A, %B %d, %Y"))
    getting_started(state)

    daily = tracker.daily_minutes(state)
    current, longest = tracker.streaks(daily, today)
    badges = tracker.achievements(state, today)
    week_start = today - timedelta(days=today.weekday())
    cols = st.columns(5)
    cols[0].metric("This week", f"{tracker.total_minutes(state, week_start) / 60:.1f} h")
    cols[1].metric("Total studied", f"{tracker.total_minutes(state) / 60:.1f} h")
    cols[2].metric("Current streak", f"{current} 🔥")
    cols[3].metric("Longest streak", f"{longest} days")
    cols[4].metric("Badges", f"{sum(b['unlocked'] for b in badges)}/{len(badges)}")

    head, pick = st.columns([3, 1], vertical_alignment="bottom")
    head.subheader("Study activity")
    course = pick.selectbox("Course filter", ["All courses"] + state["courses"], label_visibility="collapsed")
    grid_daily = daily if course == "All courses" else tracker.daily_minutes(state, course)
    st.html(tracker.contribution_grid_html(grid_daily, today))

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.subheader("Weekly study hours")
        fig = weekly_hours_chart(state, today)
        if fig:
            st.plotly_chart(fig, width="stretch")
        else:
            st.caption("Your weekly trend appears here once you log study sessions.")

        st.subheader("Next achievements")
        in_progress = sorted((b for b in badges if not b["unlocked"]), key=lambda b: -b["progress"])[:3]
        for b in in_progress:
            st.markdown(f"{b['icon']} **{b['name']}** — {b['desc']}")
            st.progress(b["progress"])
        if not in_progress:
            st.success("Every badge unlocked. Legendary! 🏅")
        st.page_link(PAGE["achievements"], label="View all achievements", icon=":material/arrow_forward:")

    with right:
        st.subheader("Coming up (next 14 days)")
        upcoming = tracker.upcoming_events(state, today)
        if not upcoming:
            st.caption("Nothing scheduled.")
        for e in upcoming[:8]:
            due = date.fromisoformat(e["date"])
            days = (due - today).days
            when = "today" if days == 0 else "tomorrow" if days == 1 else f"in {days} days"
            icon = {"Exam": "🔴", "Deadline": "🟠", "Quiz": "🟣", "Milestone": "🔵", "Study": "🟢"}.get(e["type"], "⚪")
            done = " ✅" if e.get("done") else ""
            st.markdown(f"{icon} **{e['course']}** · {e['title']} — {due:%a %b %d} ({when}){done}")
        st.page_link(PAGE["calendar"], label="Open calendar", icon=":material/arrow_forward:")

        st.subheader("Risk snapshot")
        if state["courses"]:
            snap_course = st.selectbox("Course", state["courses"], key="snap_course")
            result = risk_model.predict_risk(bundle, my_profile(state, bundle, today, snap_course))
            render_alert(result)
            summary = grades.summarize(state["grades"].get(snap_course, []))
            if summary["projected"] is not None:
                st.markdown(f"Expected grade: **{summary['projected_letter']}** ({summary['projected']:.1f}%)")
            else:
                st.caption("Add your graded work in Risk check to see your expected grade.")
            st.caption("Based on your logged activity and saved profile.")
            st.page_link(PAGE["risk"], label="See why and what to do", icon=":material/arrow_forward:")
        else:
            st.caption("Add a course to see your risk snapshot.")


# --------------------------------------------------------------------------- #
# Study log
# --------------------------------------------------------------------------- #
def timer_elapsed(timer: dict) -> float:
    seconds = float(timer["accum"])
    if timer["running"]:
        seconds += (datetime.now() - datetime.fromisoformat(timer["start"])).total_seconds()
    return max(0.0, seconds)


@st.fragment(run_every=1)
def live_timer_display() -> None:
    timer = st.session_state.state.get("active_timer")
    if not timer:
        return
    h, rem = divmod(int(timer_elapsed(timer)), 3600)
    m, s = divmod(rem, 60)
    status = "● Recording" if timer["running"] else "❚❚ Paused"
    color = GREEN if timer["running"] else "#bf8700"
    st.markdown(
        f"<div style='font-size:64px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1.1'>"
        f"{h:02d}:{m:02d}:{s:02d}</div><div style='color:{color};font-weight:600'>{status}</div>",
        unsafe_allow_html=True,
    )


def page_log() -> None:
    state, today = get_state(), date.today()
    page_header("Study log", "Time a study session live, or record one you already did.")
    require_courses(state, "log study time")
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.subheader("Timer")
        timer = state.get("active_timer")
        with st.container(border=True):
            if timer is None:
                course = st.selectbox("Course", state["courses"], key="timer_course")
                notes = st.text_input("What are you working on? (optional)", key="timer_notes",
                                      placeholder="e.g. Chapter 7 problem set")
                if st.button("Start timer", type="primary", icon=":material/play_arrow:", width="stretch"):
                    now = datetime.now().isoformat(timespec="seconds")
                    state["active_timer"] = {"course": course, "notes": notes, "first_start": now,
                                             "start": now, "accum": 0.0, "running": True}
                    persist()
                    st.rerun()
            else:
                st.markdown(f"**{timer['course']}** — {html.escape(timer['notes']) or '_no notes_'}")
                live_timer_display()
                b1, b2, b3 = st.columns(3)
                if timer["running"]:
                    if b1.button("Pause", icon=":material/pause:", width="stretch"):
                        timer["accum"], timer["running"] = timer_elapsed(timer), False
                        persist()
                        st.rerun()
                elif b1.button("Resume", icon=":material/play_arrow:", width="stretch"):
                    timer["start"], timer["running"] = datetime.now().isoformat(timespec="seconds"), True
                    persist()
                    st.rerun()
                if b2.button("Stop & save", type="primary", icon=":material/stop:", width="stretch"):
                    minutes = timer_elapsed(timer) / 60
                    if minutes < 1:
                        st.warning("Sessions shorter than one minute aren't saved — keep going!")
                    else:
                        tracker.log_session(state, timer["course"], minutes, timer["notes"],
                                            datetime.fromisoformat(timer["first_start"]))
                        state["active_timer"] = None
                        persist()
                        flash(f"Saved {minutes:.0f} min of {timer['course']} 🎉")
                        celebrate()
                        st.rerun()
                if b3.button("Discard", icon=":material/close:", width="stretch"):
                    def discard():
                        state["active_timer"] = None
                        persist()
                    confirm_dialog("Discard this timer? The time won't be saved.", "Discard", discard)
        st.caption("The timer keeps running if you switch pages or refresh.")

    with right:
        st.subheader("Add a past session")
        with st.form("manual_log", clear_on_submit=True):
            course = st.selectbox("Course", state["courses"])
            c1, c2 = st.columns(2)
            day = c1.date_input("Date", today, max_value=today)
            start = c2.time_input("Start time", time(19, 0))
            minutes = st.number_input("Duration (minutes)", min_value=5, max_value=600, value=60, step=5)
            notes = st.text_input("Notes (optional)")
            if st.form_submit_button("Save session", type="primary", icon=":material/add:", width="stretch"):
                tracker.log_session(state, course, minutes, notes, datetime.combine(day, start))
                persist()
                flash(f"Saved {minutes} min of {course}")
                celebrate()
                st.rerun()

    st.subheader("Last 30 days")
    if not state["sessions"]:
        st.caption("No sessions yet — your history will appear here.")
        return
    df = pd.DataFrame(state["sessions"])
    df["start"] = pd.to_datetime(df["start"])
    recent = df[df["start"].dt.date >= today - timedelta(days=29)].copy()
    if not recent.empty:
        recent["day"] = recent["start"].dt.date
        by_day = recent.groupby(["day", "course"], as_index=False)["minutes"].sum()
        by_day["hours"] = by_day["minutes"] / 60
        fig = px.bar(by_day, x="day", y="hours", color="course", labels={"day": "", "hours": "Hours"})
        fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), legend_title_text="")
        st.plotly_chart(fig, width="stretch")
    else:
        st.caption("No sessions in the last 30 days.")

    st.subheader("History")
    history = df.sort_values("start", ascending=False).reset_index(drop=True)
    table = pd.DataFrame({
        "Date": history["start"].dt.strftime("%a %b %d, %Y"),
        "Start": history["start"].dt.strftime("%I:%M %p"),
        "Course": history["course"],
        "Minutes": history["minutes"],
        "Notes": history["notes"],
    })
    event = st.dataframe(table, hide_index=True, width="stretch", height=300,
                         on_select="rerun", selection_mode="multi-row", key="history_table")
    selected = event.selection.rows if event else []
    if st.button(f"Delete selected ({len(selected)})", icon=":material/delete:", disabled=not selected):
        ids = history.loc[selected, "id"].tolist()

        def delete_sessions():
            for sid in ids:
                tracker.delete_session(state, sid)
            persist()
            flash(f"Deleted {len(ids)} session(s)")
        confirm_dialog(f"Delete **{len(ids)}** study session(s)? This can't be undone.", "Delete",
                       delete_sessions)
    st.caption("Tip: select rows in the table to delete them.")


# --------------------------------------------------------------------------- #
# Calendar
# --------------------------------------------------------------------------- #
EVENT_MD_COLORS = {"Exam": "red", "Deadline": "orange", "Quiz": "violet", "Milestone": "blue", "Study": "green"}
CAL_VIEWS = ["Month", "Week"]


def _toggle_event(event_id: str, widget_key: str) -> None:
    state = st.session_state.state
    done = st.session_state[widget_key]
    tracker.set_event_done(state, event_id, done)
    persist()
    event = next((e for e in state["events"] if e["id"] == event_id), None)
    if event:
        flash(f"{'Completed' if done else 'Marked not done'}: {event['title']}")
        if done:
            celebrate()


def _shift_calendar(offset_key: str, delta: int) -> None:
    st.session_state[offset_key] = st.session_state.get(offset_key, 0) + delta


def _today_calendar() -> None:
    st.session_state["cal_offset"] = st.session_state["week_offset"] = 0


def event_checkbox(event: dict, prefix: str, today: date, detailed: bool = False) -> None:
    """An event you can click to mark complete. Always reflects the saved state, wherever it's shown."""
    key = f"{prefix}-{event['id']}"
    st.session_state[key] = bool(event["done"])  # keep every copy of this checkbox in sync with the data
    due = date.fromisoformat(event["date"])
    safe_title = event["title"].replace("[", "(").replace("]", ")")
    text = (f"**{event['type']}** · {event['course']} — {safe_title}" if detailed
            else f"{event['course']}: {safe_title}")
    label = f":{EVENT_MD_COLORS.get(event['type'], 'gray')}[●] " + (f"~~{text}~~" if event["done"] else text)
    if due < today and not event["done"] and event["type"] in ("Deadline", "Quiz", "Milestone"):
        label += " :red[(overdue)]"
    # Compact cells (month grid) skip the help icon so titles have room.
    st.checkbox(label, key=key, on_change=_toggle_event, args=(event["id"], key),
                help=(f"{event['type']} on {due:%a %b %d} — click to mark "
                      f"{'not done' if event['done'] else 'complete'}") if detailed else None)


def _events_by_day(state: dict) -> dict:
    grouped: dict = {}
    for e in state["events"]:
        grouped.setdefault(date.fromisoformat(e["date"]), []).append(e)
    return grouped


# Calendar cells get a key ("calday-…"), which Streamlit exposes as a CSS class we can style.
CALENDAR_CSS = """
<style>
div[class*="st-key-calday-today"] {
    border: 2px solid #2da44e !important;
    background: rgba(45, 164, 78, 0.10);
    box-shadow: 0 0 0 3px rgba(45, 164, 78, 0.18);
}
div[class*="st-key-calday-out"] {
    background: repeating-linear-gradient(135deg, rgba(128, 128, 128, 0.10) 0 6px, rgba(128, 128, 128, 0.16) 6px 12px);
    opacity: 0.55;
}
</style>
"""


def _cell_key(day: date, today: date, in_period: bool = True) -> str:
    kind = "today" if day == today else ("in" if in_period else "out")
    return f"calday-{kind}-{day.isoformat()}"


def _day_label(day: date, today: date, text: str, in_period: bool = True) -> str:
    if day == today:
        return f":green-background[**{text}**] :green[**Today**]"
    return f"**{text}**" if in_period else f":gray[{text}]"


def month_view(state: dict, year: int, month: int, today: date) -> None:
    daily = tracker.daily_minutes(state)
    by_day = _events_by_day(state)
    header = st.columns(7, gap="small")
    for col, name in zip(header, ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
        col.markdown(f"<div style='text-align:center;opacity:.7;font-weight:600'>{name}</div>",
                     unsafe_allow_html=True)
    for week in cal_lib.Calendar(firstweekday=6).monthdatescalendar(year, month):
        cols = st.columns(7, gap="small")
        for col, day in zip(cols, week):
            with col.container(border=True, height=150, key=_cell_key(day, today, day.month == month)):
                minutes = daily.get(day, 0)
                study = f" :green[⏱ {minutes / 60:.1f}h]" if minutes else ""
                st.markdown(_day_label(day, today, str(day.day), day.month == month) + study)
                for event in by_day.get(day, []):
                    event_checkbox(event, "m", today)


def week_view(state: dict, week_start: date, today: date) -> None:
    by_day = _events_by_day(state)
    sessions_by_day: dict = {}
    for s in state["sessions"]:
        sessions_by_day.setdefault(datetime.fromisoformat(s["start"]).date(), []).append(s)
    cols = st.columns(7, gap="small")
    for i, col in enumerate(cols):
        day = week_start + timedelta(days=i)
        with col.container(border=True, height=440, key=_cell_key(day, today)):
            st.markdown(_day_label(day, today, f"{day:%a} {day:%b} {day.day}"))
            events = by_day.get(day, [])
            for event in events:
                event_checkbox(event, "w", today, detailed=True)
            sessions = sorted(sessions_by_day.get(day, []), key=lambda s: s["start"])
            if sessions:
                total = sum(s["minutes"] for s in sessions)
                st.markdown(f":green[**⏱ {total / 60:.1f}h studied**]")
                for s in sessions:
                    start = datetime.fromisoformat(s["start"])
                    st.caption(f"{start:%I:%M %p} · {s['course']} · {s['minutes']:.0f} min")
            if not events and not sessions:
                st.caption("Nothing scheduled")


def syllabus_importer(state: dict, today: date) -> None:
    with st.expander("Import dates from a syllabus (AI)", icon=":material/auto_awesome:"):
        client = gemini_client()
        if client is None:
            st.info("Add a Gemini API key in Settings to pull dates out of a syllabus automatically.")
            st.page_link(PAGE["settings"], label="Open Settings", icon=":material/arrow_forward:")
            return
        course = st.selectbox("Course", state["courses"], key="syl_course")
        upload = st.file_uploader("Syllabus file", type=ai_helper.SUPPORTED_TYPES, key="syl_file")
        if upload and st.button("Find dates", icon=":material/search:"):
            data = upload.getvalue()
            try:
                text = ai_helper.extract_text(upload.name, data)
                with st.spinner("Reading the syllabus…"):
                    st.session_state["syl_candidates"] = ai_helper.extract_syllabus_events(
                        client, text, course, today.year, data=data, mime=ai_helper.mime_type(upload.name))
                st.session_state["syl_candidates_course"] = course
            except Exception as exc:
                st.error(f"Couldn't read dates from that file: {exc}")

        candidates = st.session_state.get("syl_candidates")
        if candidates is not None:
            if not candidates:
                st.warning("No dated items were found in that syllabus.")
                return
            st.caption("Review the dates below, untick anything you don't want, then add them.")
            edited = st.data_editor(
                pd.DataFrame([{"add": True, **c} for c in candidates]),
                column_config={
                    "add": st.column_config.CheckboxColumn("Add?"),
                    "date": st.column_config.DateColumn("Date"),
                    "type": st.column_config.SelectboxColumn("Type", options=tracker.EVENT_TYPES),
                },
                hide_index=True, width="stretch", key="syl_editor",
            )
            if st.button("Add selected to calendar", type="primary", icon=":material/add:"):
                chosen = edited[edited["add"]]
                for _, row in chosen.iterrows():
                    tracker.add_event(state, row["title"], st.session_state["syl_candidates_course"],
                                      pd.Timestamp(row["date"]).date(), row["type"])
                persist()
                st.session_state.pop("syl_candidates", None)
                flash(f"Added {len(chosen)} events from the syllabus")
                st.rerun()


def page_calendar() -> None:
    state, today = get_state(), date.today()
    page_header("Calendar", "Track exams, deadlines and milestones. Click an event to mark it complete.")
    require_courses(state, "add calendar events")

    view = st.segmented_control("View", CAL_VIEWS, default="Month", key="cal_view") or "Month"
    if view == "Month":
        offset_key = "cal_offset"
        year, month0 = divmod(today.year * 12 + today.month - 1 + st.session_state.get(offset_key, 0), 12)
        month = month0 + 1
        period_start = date(year, month, 1)
        period_end = date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1)
        title = f"{period_start:%B %Y}"
    else:
        offset_key = "week_offset"
        this_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        period_start = this_sunday + timedelta(weeks=st.session_state.get(offset_key, 0))
        period_end = period_start + timedelta(days=6)
        title = (f"{period_start:%b} {period_start.day} – {period_end:%b} {period_end.day}, {period_end.year}")

    nav = st.columns([1, 1, 4, 1], vertical_alignment="center")
    nav[0].button("Previous", icon=":material/chevron_left:", on_click=_shift_calendar, args=(offset_key, -1),
                  width="stretch", help=f"Previous {view.lower()}")
    nav[1].button("Today", on_click=_today_calendar, width="stretch")
    nav[2].markdown(f"<h3 style='text-align:center;margin:0'>{title}</h3>", unsafe_allow_html=True)
    nav[3].button("Next", icon=":material/chevron_right:", on_click=_shift_calendar, args=(offset_key, 1),
                  width="stretch", help=f"Next {view.lower()}")

    st.html(CALENDAR_CSS)
    if view == "Month":
        month_view(state, year, month, today)
    else:
        week_view(state, period_start, today)
    st.caption(" ".join(f":{c}[●] {t}" for t, c in EVENT_MD_COLORS.items())
               + " · :green[⏱] hours studied · **click an event to mark it complete** (click again to undo)")

    left, right = st.columns([2, 3], gap="large")
    with left:
        st.subheader("Add an event")
        with st.form("add_event", clear_on_submit=True):
            title_text = st.text_input("Title", placeholder="e.g. Lab report 3")
            course = st.selectbox("Course", state["courses"])
            c1, c2 = st.columns(2)
            when = c1.date_input("Date", today)
            kind = c2.selectbox("Type", tracker.EVENT_TYPES)
            if st.form_submit_button("Add to calendar", type="primary", icon=":material/add:", width="stretch"):
                if title_text.strip():
                    tracker.add_event(state, title_text, course, when, kind)
                    persist()
                    flash(f"Added {kind.lower()}: {title_text}")
                    st.rerun()
                else:
                    st.error("Please enter a title for the event.")
        syllabus_importer(state, today)

    with right:
        st.subheader(f"Manage events · {title}")
        period_events = [e for e in state["events"]
                         if period_start <= date.fromisoformat(e["date"]) <= period_end]
        if not period_events:
            st.caption(f"No events this {view.lower()}.")
        for e in period_events:
            due = date.fromisoformat(e["date"])
            c1, c2, c3 = st.columns([2, 10, 1], vertical_alignment="center")
            c1.caption(f"{due:%a %b} {due.day}")
            with c2:
                event_checkbox(e, "list", today, detailed=True)
            if c3.button(":material/delete:", key=f"del-{e['id']}", help="Delete event"):
                def delete(event_id=e["id"]):
                    tracker.delete_event(state, event_id)
                    persist()
                confirm_dialog(f"Delete **{e['title']}** ({e['course']}, {due:%b %d})?", "Delete", delete)
        st.caption("Your on-time rate feeds the risk check.")


# --------------------------------------------------------------------------- #
# Study plan
# --------------------------------------------------------------------------- #
def _materials_text(materials: list[dict], limit: int = 40_000) -> str:
    """Summaries (or raw text) of materials, for AI planning."""
    parts = [f"## {m['name']}\n{m.get('summary') or material_text(m)}" for m in materials]
    return "\n\n".join(parts)[:limit]


def _add_plan_to_calendar(state: dict, test_id: str) -> None:
    plan = state["study_plans"][test_id]
    old = set(plan.get("event_ids", []))
    state["events"] = [e for e in state["events"] if e["id"] not in old]  # replace a previous copy
    plan["event_ids"] = [
        tracker.add_event(state, f"Study {day['minutes']} min: {day['focus']}", plan["course"],
                          date.fromisoformat(day["date"]), "Study")["id"]
        for day in plan["days"]]
    persist()
    flash(f"Added {len(plan['event_ids'])} study sessions to your calendar")


def _start_plan_session(course: str, focus: str) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    st.session_state.state["active_timer"] = {"course": course, "notes": focus, "first_start": now,
                                              "start": now, "accum": 0.0, "running": True}
    persist()


def _plan_materials_key(test_id: str) -> str:
    return f"plan-mats-{test_id}"


def _add_test_files(test_id: str, course: str, uploader_key: str) -> None:
    """Upload files from the study-plan page: add them to the course library and mark them as on this test."""
    files = st.session_state.get(uploader_key) or []
    if not files:
        return
    state = st.session_state.state
    added = [add_material(state, f.name, course, f.getvalue()) for f in files]
    persist()
    key = _plan_materials_key(test_id)
    st.session_state[key] = list(dict.fromkeys(st.session_state.get(key, []) + [m["id"] for m in added]))
    nonce_key = f"plan-upload-nonce-{test_id}"
    st.session_state[nonce_key] = st.session_state.get(nonce_key, 0) + 1
    failed = [m["name"] for m in added if m["error"]]
    flash(f"Added {len(added)} file(s) to {course} and marked them as on this test"
          + (f" — couldn't read {', '.join(failed)}" if failed else ""))


def _set_confidence(test_id: str, index: int, widget_key: str) -> None:
    plan = st.session_state.state["study_plans"][test_id]
    topic = plan["topics"][index]
    topic["confidence"] = st.session_state[widget_key]
    persist()
    if topic["confidence"] == "Confident":
        celebrate()
        flash(f"Nice — you're confident on {topic['name']}")


def _make_plan(state: dict, test: dict, today: date, tier: str, settings: dict, material_ids: list[str],
               note: str, client, keep_topics: list[dict] | None = None) -> dict:
    """Build the schedule, find the test's topics, spread them over the days and (optionally) add AI tasks."""
    course, test_date = test["course"], date.fromisoformat(test["date"])
    busy: dict[date, list[str]] = {}
    for e in state["events"]:
        if e["id"] != test["id"] and e["type"] != "Study" and not e["done"]:
            busy.setdefault(date.fromisoformat(e["date"]), []).append(f"{e['course']} {e['title']}")
    plan = planner.build_plan(test_date, today, test["type"], tier, settings["lead"], settings["max_minutes"], busy)

    materials = [m for m in state["materials"] if m["id"] in material_ids]
    use_ai = bool(settings["use_ai"] and client)
    topics, topic_source = keep_topics, "your earlier topic list"
    if topics is None and (materials or note.strip()):
        pairs = [(m["name"], material_text(m)) for m in materials]
        topics = None
        if use_ai:
            with st.spinner("Finding the topics in your files…"):
                try:
                    topics = planner.normalize_topics(
                        ai_helper.extract_test_topics(client, course, test["title"], pairs, note))
                    topic_source = "Gemini, from the files on this test"
                except Exception as exc:
                    st.warning(f"Couldn't use AI to find topics ({exc}) — using slide titles and headings instead.")
        if not topics:
            topics = planner.offline_topics(pairs, note)
            topic_source = "slide titles and headings in your files"
    topics = topics or []
    planner.assign_topics(plan, topics)

    task_source = "standard study tasks"
    if use_ai and plan["days"]:
        context = materials or [m for m in state["materials"] if m["course"] == course]
        if context or topics:
            with st.spinner("Writing day-by-day tasks…"):
                try:
                    ai_days = ai_helper.generate_plan_details(client, course, test["title"], test_date, plan["days"],
                                                              _materials_text(context) or note)
                    plan = planner.merge_ai_details(plan, ai_days)
                    task_source = "tasks written by Gemini"
                except Exception as exc:
                    st.warning(f"Couldn't add AI tasks ({exc}) — showing the standard tasks.")
    plan["source"] = (f"Topics from {topic_source} · {task_source}" if topics
                      else f"No test materials selected · {task_source}")
    plan.update({"topics": topics, "material_ids": material_ids, "topic_note": note, "settings": settings,
                 "course": course, "title": test["title"], "test_date": test["date"], "tier": tier,
                 "generated_at": datetime.now().isoformat(timespec="seconds"),
                 "event_ids": state["study_plans"].get(test["id"], {}).get("event_ids", [])})
    return plan


IMPORTANCE_BADGE = {"high": ":red-badge[High priority]", "medium": ":orange-badge[Medium]", "low": ":gray-badge[Low]"}


def _topic_guide(state: dict, plan: dict, test: dict, today: date) -> None:
    """'Next up' box plus the topic checklist with self-rated confidence."""
    topics = plan.get("topics", [])
    if not topics:
        return
    test_id, course = test["id"], test["course"]
    by_name = {m["name"]: m for m in state["materials"] if m["course"] == course}
    planned: dict[str, list[str]] = {}
    for day in plan["days"]:
        d = date.fromisoformat(day["date"])
        for name in day.get("topics", []):
            planned.setdefault(name, []).append(f"{d:%a %b} {d.day}")

    nxt = planner.next_topic(plan, today.isoformat())
    with st.container(border=True):
        if nxt is None:
            st.success("You're confident on every topic. Finish with a timed practice test and a good night's sleep.",
                       icon="🎉")
        else:
            topic, when = nxt
            day_text = ("today" if when == today.isoformat() else
                        f"{date.fromisoformat(when):%A}" if when else "as soon as you can")
            st.markdown(f"#### :material/flag: Next up: {topic['name']}")
            st.markdown(f"{topic['summary']}  \nPlanned for **{day_text}** · from *{topic['source']}*")
            b1, b2, _ = st.columns([1, 1, 2])
            material = by_name.get(topic["source"])
            if material and b1.button(f"Open {material['name'][:28]}", icon=":material/description:",
                                      key=f"open-{test_id}", width="stretch"):
                st.session_state["material_choice"] = material["id"]
                st.switch_page(PAGE["materials"])
            if not state.get("active_timer") and b2.button("Study it now", icon=":material/play_arrow:",
                                                           type="primary", key=f"study-{test_id}", width="stretch"):
                _start_plan_session(course, f"{test['title']}: {topic['name']}")
                st.switch_page(PAGE["log"])

    confident = sum(t.get("confidence") == "Confident" for t in topics)
    head, action = st.columns([3, 1], vertical_alignment="bottom")
    head.subheader(f"Topics on this test · {confident}/{len(topics)} confident")
    replan = action.button("Re-plan around my weak topics", icon=":material/refresh:", width="stretch",
                           help="Rebuilds the schedule so Shaky and unrated topics get the practice days")
    st.progress(confident / len(topics))
    st.caption("Rate yourself after studying each topic. Shaky topics get more practice when you re-plan.")
    for i, topic in enumerate(topics):
        with st.container(border=True):
            left, right = st.columns([3, 2], vertical_alignment="center")
            left.markdown(f"**{i + 1}. {topic['name']}** {IMPORTANCE_BADGE.get(topic['importance'], '')}")
            when = ", ".join(planned.get(topic["name"], [])) or "not scheduled"
            left.caption(f"{topic['summary']}  \nFrom *{topic['source']}* · planned: {when}")
            key = f"conf-{test_id}-{i}"
            st.session_state[key] = topic.get("confidence")  # always reflect the saved rating
            with right:
                st.segmented_control("How confident are you?", planner.CONFIDENCE_LEVELS, key=key,
                                     on_change=_set_confidence, args=(test_id, i, key),
                                     label_visibility="collapsed")
    if replan:
        plan = _make_plan(state, test, today, plan["tier"], plan["settings"], plan.get("material_ids", []),
                          plan.get("topic_note", ""), gemini_client(), keep_topics=topics)
        state["study_plans"][test_id] = plan
        persist()
        flash("Re-planned around your weak topics")
        st.rerun()


def page_plan() -> None:
    state, bundle, today = get_state(), get_bundle(), date.today()
    page_header("Study plan", "Pick an upcoming test, tell Wolf Tracks what's on it, and get a day-by-day plan that "
                              "walks you through every topic.")
    require_courses(state, "plan for a test")
    tests = sorted((e for e in state["events"] if e["type"] in ("Exam", "Quiz") and not e["done"]
                    and date.fromisoformat(e["date"]) >= today), key=lambda e: e["date"])
    if not tests:
        empty_state("🗓️", "No upcoming tests", "Add an exam or quiz to your calendar — or import a syllabus — "
                    "and it will show up here.", "calendar", "Open Calendar")
        return

    by_id = {e["id"]: e for e in tests}

    def label(test_id: str) -> str:
        e = by_id[test_id]
        d = date.fromisoformat(e["date"])
        days = (d - today).days
        when = "today" if days == 0 else "tomorrow" if days == 1 else f"in {days} days"
        return f"{e['course']} · {e['title']} — {d:%a %b} {d.day} ({when})"

    test_id = st.selectbox("Upcoming test", list(by_id), format_func=label, key="plan_test")
    test = by_id[test_id]
    test_date, course, kind = date.fromisoformat(test["date"]), test["course"], test["type"]
    saved = state["study_plans"].get(test_id)

    result = risk_model.predict_risk(bundle, my_profile(state, bundle, today, course))
    summary = grades.summarize(state["grades"].get(course, []))
    hours = planner.recommended_hours(kind, result["tier"])
    c = st.columns(4)
    c[0].metric("Days until test", (test_date - today).days)
    c[1].metric("Chance of C or higher", chance(1 - result["probability"]), help="From the Risk check model")
    c[2].metric("Expected grade", f"{summary['projected_letter']} · {summary['projected']:.0f}%"
                if summary["projected"] is not None else "—", help="From your grade table in Risk check")
    c[3].metric("Recommended study time", f"{hours:.1f} h",
                help=f"{planner.BASE_HOURS[kind]:.0f} h for {'an exam' if kind == 'Exam' else 'a quiz'}, "
                     "×1.25 on the watch list and ×1.5 when the course is at risk")

    # Step 1 — what's on the test
    with st.container(border=True):
        st.subheader("1 · What's on this test?")
        st.caption("Upload the slides, notes or study guide this test covers (several at once is fine), or pick "
                   "files you've already uploaded. Wolf Tracks finds the topics and builds your plan around them.")
        nonce = st.session_state.get(f"plan-upload-nonce-{test_id}", 0)
        uploader_key = f"plan-upload-{test_id}-{nonce}"
        files = st.file_uploader("Add files for this test", type=ai_helper.SUPPORTED_TYPES, accept_multiple_files=True,
                                 key=uploader_key)
        st.button("Add files to this test", icon=":material/upload_file:", disabled=not files,
                  on_click=_add_test_files, args=(test_id, course, uploader_key))

        course_materials = sorted((m for m in state["materials"] if m["course"] == course),
                                  key=lambda m: m["uploaded_at"], reverse=True)
        options = [m["id"] for m in course_materials]
        select_key = _plan_materials_key(test_id)
        if select_key not in st.session_state:
            st.session_state[select_key] = [i for i in (saved or {}).get("material_ids", []) if i in options]
        else:
            st.session_state[select_key] = [i for i in st.session_state[select_key] if i in options]
        names = {m["id"]: m["name"] for m in course_materials}
        material_ids = st.multiselect("Files on this test", options, key=select_key, format_func=names.get,
                                      placeholder="Choose files from your " + course + " library"
                                      if options else "Upload files above first")
        note = st.text_area("Topics your instructor said will be on it (optional)",
                            value=(saved or {}).get("topic_note", ""), key=f"plan-note-{test_id}",
                            placeholder="e.g. chain rule, related rates, optimization", height=80)

    # Step 2 — settings and generate
    client = gemini_client()
    with st.form(f"plan_settings-{test_id}", border=True):
        st.subheader("2 · Build your plan")
        previous = (saved or {}).get("settings", {})
        c1, c2, c3 = st.columns(3, vertical_alignment="bottom")
        lead = c1.number_input("Start studying this many days before", min_value=1, max_value=30,
                               value=previous.get("lead", planner.DEFAULT_LEAD_DAYS[kind]), step=1)
        max_minutes = c2.number_input("Most minutes per day", min_value=20, max_value=300,
                                      value=previous.get("max_minutes", 90), step=10)
        use_ai = c3.toggle("Use AI (Gemini)", value=bool(client), disabled=not client,
                           help="Finds topics and writes specific tasks from your files" if client else
                           "Add a Gemini key in Settings — without it, topics come from slide titles and headings")
        submitted = st.form_submit_button("Generate study plan", type="primary", icon=":material/auto_awesome:")
    if submitted:
        settings = {"lead": int(lead), "max_minutes": int(max_minutes), "use_ai": bool(use_ai)}
        state["study_plans"][test_id] = _make_plan(state, test, today, result["tier"], settings, material_ids,
                                                   note, client)
        persist()
        flash("Study plan ready")
        st.rerun()

    plan = state["study_plans"].get(test_id)
    if not plan:
        st.caption("Tell Wolf Tracks what's on the test, then click **Generate study plan**.")
        return

    # Step 3 — the guide and the schedule
    st.subheader("3 · Your study guide")
    st.caption(f"{plan['source']} · made {datetime.fromisoformat(plan['generated_at']):%b %d at %I:%M %p}")
    _topic_guide(state, plan, test, today)

    st.subheader(f"Day by day · {plan['planned_minutes'] / 60:.1f} h over {len(plan['days'])} day(s)")
    if plan.get("note"):
        st.warning(plan["note"], icon=":material/schedule:")
    for day in plan["days"]:
        d = date.fromisoformat(day["date"])
        with st.container(border=True, key=_cell_key(d, today)):
            left, right = st.columns([1, 4], vertical_alignment="top")
            left.markdown(_day_label(d, today, f"{d:%a %b} {d.day}"))
            left.markdown(f"**{day['minutes']} min**")
            right.markdown(f"**{day['focus']}**")
            right.markdown("\n".join(f"- {task}" for task in day["tasks"]))
            if day.get("note"):
                right.caption(day["note"])
            if d == today and not state.get("active_timer"):
                if right.button("Start today's session", icon=":material/play_arrow:", type="primary",
                                key=f"start-{day['date']}"):
                    _start_plan_session(course, day["focus"])
                    st.switch_page(PAGE["log"])
    st.html(CALENDAR_CSS)

    b1, b2, _ = st.columns([1, 1, 2])
    in_calendar = bool(plan.get("event_ids"))
    b1.button("Update calendar" if in_calendar else "Add sessions to calendar", icon=":material/calendar_add_on:",
              on_click=_add_plan_to_calendar, args=(state, test_id), width="stretch",
              help="Adds one green Study event per day; re-adding replaces the previous copy")
    b2.download_button("Download plan", planner.to_markdown(f"{course} · {test['title']}", plan),
                       file_name=f"study-plan-{course.replace(' ', '')}-{test['date']}.md", mime="text/markdown",
                       icon=":material/download:", width="stretch")


# --------------------------------------------------------------------------- #
# Achievements
# --------------------------------------------------------------------------- #
def page_achievements() -> None:
    state, today = get_state(), date.today()
    badges = tracker.achievements(state, today)
    unlocked = sum(b["unlocked"] for b in badges)
    page_header("Achievements", f"{unlocked} of {len(badges)} badges unlocked")
    st.progress(unlocked / len(badges))
    show = st.segmented_control("Show", ["All", "Unlocked", "Locked"], default="All", key="badge_filter") or "All"
    for category in tracker.ACHIEVEMENT_CATEGORIES:
        group = [b for b in badges if b["category"] == category
                 and (show == "All" or b["unlocked"] == (show == "Unlocked"))]
        if not group:
            continue
        done = sum(b["unlocked"] for b in badges if b["category"] == category)
        total = sum(1 for b in badges if b["category"] == category)
        st.subheader(f"{category} · {done}/{total}")
        render_badges(group)


def render_badges(badges: list[dict]) -> None:
    for row_start in range(0, len(badges), 4):
        cols = st.columns(4)
        for col, b in zip(cols, badges[row_start:row_start + 4]):
            with col.container(border=True):
                faded = "" if b["unlocked"] else "filter:grayscale(1);opacity:.45;"
                st.markdown(f"<div style='font-size:42px;{faded}'>{b['icon']}</div>", unsafe_allow_html=True)
                st.markdown(f"**{b['name']}**")
                st.caption(b["desc"])
                if b["unlocked"]:
                    st.markdown(f"<span style='color:{GREEN};font-weight:600'>✓ Unlocked</span>",
                                unsafe_allow_html=True)
                else:
                    value = b["value"]
                    shown = f"{value:.1f}" if isinstance(value, float) and not value.is_integer() else f"{int(value)}"
                    st.progress(b["progress"], text=f"{shown} / {b['goal']}")


# --------------------------------------------------------------------------- #
# Study materials
# --------------------------------------------------------------------------- #
def add_material(state: dict, name: str, course: str, data: bytes) -> dict:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    material_id = tracker.new_id()
    path = UPLOAD_DIR / f"{material_id}_{re.sub(r'[^A-Za-z0-9._-]+', '_', name)}"
    path.write_bytes(data)
    try:
        text, error = ai_helper.extract_text(name, data), None
    except Exception as exc:
        text, error = "", str(exc)
    text_path = path.with_name(path.name + ".txt")
    text_path.write_text(text, encoding="utf-8")
    material = {
        "id": material_id, "name": name, "course": course,
        "path": path.relative_to(tracker.ROOT).as_posix(),
        "text_path": text_path.relative_to(tracker.ROOT).as_posix(),
        "chars": len(text), "size": len(data), "error": error,
        "uploaded_at": datetime.now().isoformat(timespec="seconds"),
        "summary": None, "summary_source": None, "flashcards": [], "quiz": [],
    }
    state["materials"].append(material)
    return material


def material_text(material: dict) -> str:
    path = tracker.ROOT / material["text_path"]
    return path.read_text(encoding="utf-8") if path.exists() else ""


def material_bytes(material: dict) -> bytes | None:
    path = tracker.ROOT / material["path"]
    return path.read_bytes() if path.exists() else None


def _card_step(material_id: str, course: str, step: int, count_review: bool) -> None:
    idx_key, flip_key = f"card-{material_id}", f"flip-{material_id}"
    if count_review and st.session_state.get(flip_key):
        reviewed = st.session_state.state["flashcards_reviewed"]
        reviewed[course] = reviewed.get(course, 0) + 1
        persist()
    st.session_state[idx_key] = st.session_state.get(idx_key, 0) + step
    st.session_state[flip_key] = False


def _card_flip(material_id: str) -> None:
    key = f"flip-{material_id}"
    st.session_state[key] = not st.session_state.get(key, False)


def flashcard_viewer(material: dict) -> None:
    cards = material["flashcards"]
    mid = material["id"]
    i = st.session_state.get(f"card-{mid}", 0) % len(cards)
    flipped = st.session_state.get(f"flip-{mid}", False)
    card = cards[i]
    side, text = ("ANSWER", card["back"]) if flipped else ("QUESTION", card["front"])
    accent = GREEN if flipped else "#2f81f7"
    st.html(
        f"<div style='border:2px solid {accent};border-radius:16px;padding:36px 28px;min-height:200px;"
        f"display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;"
        f"color:inherit;font-family:inherit'>"
        f"<div style='font-size:12px;letter-spacing:.12em;color:{accent};font-weight:700'>{side} · "
        f"{i + 1}/{len(cards)}</div>"
        f"<div style='font-size:22px;margin-top:12px;line-height:1.4'>{html.escape(text)}</div></div>"
    )
    c = st.columns(4)
    c[0].button("Previous", key=f"prev-{mid}", icon=":material/chevron_left:", on_click=_card_step,
                args=(mid, material["course"], -1, False), width="stretch")
    c[1].button("Flip card", key=f"flip-btn-{mid}", icon=":material/flip:", on_click=_card_flip, args=(mid,),
                type="primary", width="stretch")
    c[2].button("Got it", key=f"got-{mid}", icon=":material/check:", on_click=_card_step,
                args=(mid, material["course"], 1, True), width="stretch", disabled=not flipped,
                help="Flip the card first")
    c[3].button("Next", key=f"next-{mid}", icon=":material/chevron_right:", on_click=_card_step,
                args=(mid, material["course"], 1, True), width="stretch")
    reviewed = st.session_state.state["flashcards_reviewed"].get(material["course"], 0)
    st.caption(f"Cards you flip and move past count as reviewed · {reviewed} reviewed for {material['course']}")
    with st.expander("See all cards"):
        st.dataframe(pd.DataFrame(cards).rename(columns={"front": "Front", "back": "Back"}),
                     hide_index=True, width="stretch")


def quiz_section(state: dict, material: dict) -> None:
    mid = material["id"]
    quiz = material["quiz"]
    nonce = st.session_state.get(f"quiz-nonce-{mid}", 0)
    result_key = f"quiz-result-{mid}"

    with st.form(f"quiz-{mid}-{nonce}"):
        answers = []
        for i, q in enumerate(quiz):
            answers.append(st.radio(f"**Q{i + 1}. {q['question']}**", range(len(q["options"])),
                                    format_func=lambda k, q=q: q["options"][k], index=None,
                                    key=f"q-{mid}-{nonce}-{i}"))
        submitted = st.form_submit_button("Submit answers", type="primary")

    if submitted:
        if any(a is None for a in answers):
            st.error("Please answer every question before submitting.")
        else:
            correct = sum(a == q["answer_index"] for a, q in zip(answers, quiz))
            score = round(100 * correct / len(quiz), 1)
            state["quizzes"].append({"id": tracker.new_id(), "material_id": mid, "course": material["course"],
                                     "score": score, "questions": len(quiz),
                                     "taken_at": datetime.now().isoformat(timespec="seconds")})
            persist()
            st.session_state[result_key] = {"answers": answers, "score": score, "correct": correct}
            celebrate()

    result = st.session_state.get(result_key)
    if result:
        score = result["score"]
        (st.success if score >= 80 else st.warning if score >= 60 else st.error)(
            f"You scored **{score:.0f}%** ({result['correct']}/{len(quiz)})")
        for i, (a, q) in enumerate(zip(result["answers"], quiz)):
            ok = a == q["answer_index"]
            st.markdown(f"{'✅' if ok else '❌'} **Q{i + 1}.** Correct answer: "
                        f"**{q['options'][q['answer_index']]}** — {q['explanation']}")
        if st.button("Retake quiz", icon=":material/replay:"):
            st.session_state[f"quiz-nonce-{mid}"] = nonce + 1
            st.session_state.pop(result_key, None)
            st.rerun()

    history = [q["score"] for q in state["quizzes"] if q.get("material_id") == mid]
    if history:
        st.caption(f"Past attempts on this material: {', '.join(f'{s:.0f}%' for s in history)}")


def page_materials() -> None:
    state = get_state()
    page_header("Study materials", "Upload notes, slides or PDFs and turn them into summaries, flashcards "
                                   "and practice quizzes.")
    require_courses(state, "upload study materials")
    client = gemini_client()
    if not client:
        st.info("AI is offline — summaries and flashcards use a basic offline mode and practice quizzes are "
                "unavailable. Add a Gemini API key in Settings for full AI features.", icon=":material/info:")

    with st.expander("Upload files", icon=":material/upload:", expanded=not state["materials"]):
        course = st.selectbox("Course", state["courses"], key="upload_course")
        nonce = st.session_state.get("upload_nonce", 0)
        files = st.file_uploader("PDF, PowerPoint (.pptx), Word (.docx), text or Markdown",
                                 type=ai_helper.SUPPORTED_TYPES, accept_multiple_files=True, key=f"uploader-{nonce}")
        if st.button("Add to library", type="primary", icon=":material/add:", disabled=not files):
            with st.spinner("Reading your files…"):
                added = [add_material(state, f.name, course, f.getvalue()) for f in files]
            persist()
            st.session_state["upload_nonce"] = nonce + 1
            st.session_state["material_choice"] = added[-1]["id"]
            failed = [m["name"] for m in added if m["error"]]
            flash(f"Added {len(added)} file(s)" + (f" — couldn't read {', '.join(failed)}" if failed else ""))
            st.rerun()

    materials = sorted(state["materials"], key=lambda m: m["uploaded_at"], reverse=True)
    if not materials:
        empty_state("📄", "Your library is empty", "Upload lecture notes or slides above to get started.")
        return

    by_id = {m["id"]: m for m in materials}
    if st.session_state.get("material_choice") not in by_id:
        st.session_state["material_choice"] = materials[0]["id"]
    sel, delete_col = st.columns([5, 1], vertical_alignment="bottom")
    material_id = sel.selectbox("Library", list(by_id), key="material_choice",
                                format_func=lambda i: f"{by_id[i]['name']} · {by_id[i]['course']}")
    material = by_id[material_id]
    if delete_col.button("Delete", icon=":material/delete:", width="stretch"):
        def delete():
            for key in ("path", "text_path"):
                (tracker.ROOT / material[key]).unlink(missing_ok=True)
            state["materials"] = [m for m in state["materials"] if m["id"] != material_id]
            persist()
            flash(f"Deleted {material['name']}")
        confirm_dialog(f"Delete **{material['name']}** and its summary, flashcards and quiz?", "Delete", delete)

    text = material_text(material)
    st.caption(f"{material['course']} · {material['size'] / 1024:.0f} KB · {material['chars']:,} characters of text"
               f" · uploaded {datetime.fromisoformat(material['uploaded_at']):%b %d, %Y}")
    if material.get("error"):
        st.warning(f"We couldn't read text from this file: {material['error']}")
    elif not text.strip():
        st.warning("No selectable text found (scanned document?). "
                   + ("Gemini will read the PDF directly." if client else "Add a Gemini key to read it."))
    with st.expander("Preview extracted text", icon=":material/description:"):
        st.text(text[:4000] + ("…" if len(text) > 4000 else ""))

    raw = None if text.strip() else material_bytes(material)
    mime = ai_helper.mime_type(material["name"])
    tab_sum, tab_cards, tab_quiz = st.tabs(["Summary", "Flashcards", "Practice quiz"])

    with tab_sum:
        label = "Regenerate summary" if material.get("summary") else "Generate summary"
        if st.button(label, key="gen_summary", type="primary", icon=":material/auto_awesome:"):
            with st.spinner("Summarizing…"):
                try:
                    if client:
                        material["summary"] = ai_helper.summarize(client, text, data=raw, mime=mime)
                        material["summary_source"] = "Gemini"
                    else:
                        material["summary"] = ai_helper.offline_summary(text)
                        material["summary_source"] = "offline mode"
                    persist()
                except Exception as exc:
                    st.error(f"Summary failed: {exc}")
        if material.get("summary"):
            st.markdown(material["summary"])
            st.caption(f"Generated with {material['summary_source']}")
            st.download_button("Download summary", material["summary"], icon=":material/download:",
                               file_name=f"{material['name']}-summary.md", mime="text/markdown")

    with tab_cards:
        c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
        n_cards = c1.slider("Number of cards", 5, 20, 10, key="n_cards")
        if c2.button("Generate", key="gen_cards", type="primary", icon=":material/auto_awesome:", width="stretch"):
            with st.spinner("Writing flashcards…"):
                try:
                    material["flashcards"] = (
                        ai_helper.generate_flashcards(client, text, n_cards, data=raw, mime=mime) if client
                        else ai_helper.offline_flashcards(text, n_cards))
                    st.session_state[f"card-{material_id}"] = 0
                    st.session_state[f"flip-{material_id}"] = False
                    persist()
                except Exception as exc:
                    st.error(f"Flashcard generation failed: {exc}")
        if material["flashcards"]:
            flashcard_viewer(material)
        else:
            st.caption("No flashcards yet — choose how many and click Generate.")

    with tab_quiz:
        if client:
            c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
            n_q = c1.slider("Number of questions", 3, 10, 5, key="n_questions")
            if c2.button("Generate", key="gen_quiz", type="primary", icon=":material/auto_awesome:",
                         width="stretch"):
                with st.spinner("Writing your quiz…"):
                    try:
                        material["quiz"] = ai_helper.generate_quiz(client, text, n_q, data=raw, mime=mime)
                        st.session_state.pop(f"quiz-result-{material_id}", None)
                        st.session_state[f"quiz-nonce-{material_id}"] = \
                            st.session_state.get(f"quiz-nonce-{material_id}", 0) + 1
                        persist()
                    except Exception as exc:
                        st.error(f"Quiz generation failed: {exc}")
        else:
            st.info("Practice quizzes need a Gemini API key.")
            st.page_link(PAGE["settings"], label="Add a key in Settings", icon=":material/arrow_forward:")
        if material["quiz"]:
            quiz_section(state, material)


# --------------------------------------------------------------------------- #
# Risk check
# --------------------------------------------------------------------------- #
def chance(probability: float) -> str:
    """Format a probability without overpromising: a decision-tree leaf can be 0% or 100%."""
    if probability >= 0.995:
        return ">99%"
    if probability <= 0.005:
        return "<1%"
    return f"{probability:.0%}"


def render_alert(result: dict) -> None:
    p = result["probability"]
    if result["tier"] == "at_risk":
        st.error(f"**At-Risk Alert** — {chance(p)} chance of finishing with a D or F. "
                 f"Only {chance(1 - p)} chance of a C or higher right now.", icon="🚨")
    elif result["tier"] == "watch":
        st.warning(f"**Watch List** — {chance(1 - p)} chance of a C or higher, but a {chance(p)} chance of a D or F. "
                   "A few habits could tip this either way.", icon="⚠️")
    else:
        st.success(f"**On Track** — {chance(1 - p)} chance of a C or higher. Keep it up!", icon="✅")


def risk_gauge(probability: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability * 100,
        number={"suffix": "%", "valueformat": ".0f"},
        title={"text": "At-risk probability"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#57606a"},
            "steps": [{"range": [0, 30], "color": "#9be9a8"},
                      {"range": [30, 50], "color": "#f2cc60"},
                      {"range": [50, 100], "color": "#ff8182"}],
            "threshold": {"line": {"color": "#cf222e", "width": 3}, "value": 50},
        },
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=10))
    return fig


def _sync_input(widget_key: str, value_key: str) -> None:
    st.session_state[value_key] = st.session_state[widget_key]


def feature_input(container, feat: str, base: dict, medians: dict, key: str, disabled: bool = False,
                  override: float | None = None):
    """A slider and a typeable number box that stay in sync. Percent features are shown as 0–100."""
    lo, hi, step = risk_model.FEATURE_RANGES[feat]
    pct = feat in risk_model.PERCENT_COLS
    if pct:
        lo, hi, step = round(lo * 100), round(hi * 100), 1
    is_int = pct or (float(step).is_integer() and float(lo).is_integer())
    cast = int if is_int else float

    def normalize(value: float):
        value = min(max(float(value), lo), hi)
        return int(round(value)) if is_int else round(round(value / step) * step, 2)

    value_key = f"{key}-{feat}"
    if override is not None:  # value comes from elsewhere (e.g. the grade table); show it read-only
        st.session_state[value_key] = normalize(override * 100 if pct else override)
        disabled = True
    elif value_key not in st.session_state:
        value = base.get(feat)
        if is_missing(value):
            value = medians[feat]
        st.session_state[value_key] = normalize(value * 100 if pct else value)
    st.session_state[f"{value_key}-slider"] = st.session_state[value_key]
    st.session_state[f"{value_key}-box"] = st.session_state[value_key]

    label = risk_model.LABELS[feat] + (" (%)" if pct else "")
    slider_col, box_col = container.columns([3, 1], vertical_alignment="bottom")
    slider_col.slider(label, cast(lo), cast(hi), step=cast(step), key=f"{value_key}-slider", disabled=disabled,
                      on_change=_sync_input, args=(f"{value_key}-slider", value_key))
    box_col.number_input(label, cast(lo), cast(hi), step=cast(step), key=f"{value_key}-box", disabled=disabled,
                         format="%d" if is_int else "%.1f", label_visibility="collapsed",
                         on_change=_sync_input, args=(f"{value_key}-box", value_key))
    value = st.session_state[value_key]
    return value / 100 if pct else value


def profile_form(base: dict, key: str, course_options: list[str], medians: dict,
                 midterm_override: float | None = None) -> dict:
    profile: dict = {}
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.markdown("**Academic profile**")
        course = base.get("course", course_options[0])
        options = course_options if course in course_options else course_options + [course]
        profile["course"] = st.selectbox("Course", options, index=options.index(course), key=f"{key}-course")
        year = base.get("class_year", "Freshman")
        profile["class_year"] = st.selectbox("Class year", risk_model.CLASS_YEARS,
                                             index=risk_model.CLASS_YEARS.index(year)
                                             if year in risk_model.CLASS_YEARS else 0, key=f"{key}-year")
        for feat in ["credit_hours", "work_hours_per_week", "attendance_rate", "avg_sleep_hours"]:
            profile[feat] = feature_input(st, feat, base, medians, key)
        profile["midterm_score"] = feature_input(st, "midterm_score", base, medians, key, override=midterm_override)
        if midterm_override is not None:
            st.caption("Midterm score comes from your grade table above.")
    with c2:
        st.markdown("**Study habits**")
        for feat in ["avg_weekly_study_hours", "study_sessions_logged", "avg_days_started_before_exam",
                     "late_night_study_pct", "flashcards_reviewed"]:
            profile[feat] = feature_input(st, feat, base, medians, key)
    with c3:
        st.markdown("**Dashboard engagement**")
        for feat in ["materials_uploaded", "practice_quizzes_taken"]:
            profile[feat] = feature_input(st, feat, base, medians, key)
        no_quizzes = profile["practice_quizzes_taken"] == 0
        score = feature_input(st, "avg_practice_quiz_score", base, medians, key, disabled=no_quizzes)
        profile["avg_practice_quiz_score"] = float("nan") if no_quizzes else score
        for feat in ["on_time_submission_rate", "missed_deadlines"]:
            profile[feat] = feature_input(st, feat, base, medians, key)
    return profile


@st.cache_data(show_spinner=False)
def _load_uploaded_students(data: bytes) -> pd.DataFrame:
    return risk_model.load_data(io.BytesIO(data), require_target=False)


def batch_analysis(bundle: dict):
    """Score an uploaded CSV of students; returns (profile, actual, key) for the student to drill into."""
    st.caption("Upload a CSV with the WolfHacks columns, e.g. `examples/student_csvs/heldout_students.csv`. "
               "If it includes `at_risk`, the model is also evaluated against the true outcomes.")
    upload = st.file_uploader("Student CSV", type=["csv"], key="batch_csv")
    if upload is None:
        return None
    try:
        df = _load_uploaded_students(upload.getvalue())
    except Exception as exc:
        st.error(f"Couldn't read that CSV: {exc}")
        return None
    if df.empty:
        st.warning("The CSV has no rows.")
        return None
    if "student_id" not in df.columns:
        df.insert(0, "student_id", [f"Row {i + 1}" for i in range(len(df))])
    df["student_id"] = df["student_id"].astype(str)
    scored = risk_model.score_students(bundle, df)

    tiers = scored["risk_tier"].value_counts()
    c = st.columns(4)
    c[0].metric("Students", len(scored))
    c[1].metric("At risk", int(tiers.get("at_risk", 0)))
    c[2].metric("Watch list", int(tiers.get("watch", 0)))
    c[3].metric("On track", int(tiers.get("on_track", 0)))

    evaluation = risk_model.evaluate_labeled(scored)
    if evaluation:
        st.markdown(f"**Model evaluation on this file** ({evaluation['n']} labeled students)")
        e = st.columns(5)
        e[0].metric("Accuracy", f"{evaluation['accuracy']:.1%}")
        e[1].metric("Precision", f"{evaluation['precision']:.1%}")
        e[2].metric("Recall", f"{evaluation['recall']:.1%}")
        e[3].metric("F1", f"{evaluation['f1']:.2f}")
        e[4].metric("ROC AUC", "—" if evaluation["roc_auc"] is None else f"{evaluation['roc_auc']:.2f}")

    left, right = st.columns(2, gap="large")
    with left:
        fig = px.histogram(scored, x="risk_probability", nbins=20, color="risk_tier",
                           color_discrete_map={"at_risk": "#cf222e", "watch": "#bf8700", "on_track": GREEN},
                           labels={"risk_probability": "Predicted risk", "risk_tier": "Tier"})
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), title="Risk distribution",
                          xaxis_tickformat=".0%")
        st.plotly_chart(fig, width="stretch")
    with right:
        by_course = scored.groupby("course", as_index=False)["predicted_at_risk"].mean()
        fig = px.bar(by_course.sort_values("predicted_at_risk"), x="predicted_at_risk", y="course",
                     orientation="h", labels={"predicted_at_risk": "Predicted at-risk share", "course": ""})
        fig.update_traces(marker_color="#cf222e")
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), title="By course",
                          xaxis_tickformat=".0%")
        st.plotly_chart(fig, width="stretch")

    shown = ["student_id", "course", "class_year", "risk_probability", "risk_tier", "top_suggestion"]
    if risk_model.TARGET in scored.columns:
        shown.insert(5, risk_model.TARGET)
    st.dataframe(scored[shown], hide_index=True, width="stretch", height=300,
                 column_config={"risk_probability": st.column_config.ProgressColumn(
                     "Risk", format="percent", min_value=0.0, max_value=1.0)})
    st.download_button("Download scored CSV", scored.to_csv(index=False), file_name="scored_students.csv",
                       mime="text/csv", icon=":material/download:")

    st.divider()
    indexed = scored.set_index("student_id")
    sid = st.selectbox("Look at one student in detail", indexed.index,
                       format_func=lambda s: f"{s} · {indexed.at[s, 'course']} · "
                                             f"{indexed.at[s, 'risk_probability']:.0%} risk")
    row = indexed.loc[sid]
    if isinstance(row, pd.DataFrame):  # duplicate IDs in the upload
        row = row.iloc[0]
    actual = None
    if risk_model.TARGET in row.index and not pd.isna(row[risk_model.TARGET]):
        actual = int(row[risk_model.TARGET])
    return row.to_dict(), actual, f"csv-{sid}"


GRADE_COLUMNS = ["item", "type", "weight", "score"]


def grade_editor(state: dict, course: str) -> tuple[list[dict], list[str]]:
    """Editable table of graded work for one course. Returns (cleaned items, validation errors)."""
    saved = state["grades"].get(course, [])
    df = pd.DataFrame(saved, columns=GRADE_COLUMNS).astype(
        {"item": "object", "type": "object", "weight": "float", "score": "float"})
    nonce = st.session_state.get(f"grades-nonce-{course}", 0)
    edited = st.data_editor(
        df, num_rows="dynamic", hide_index=True, width="stretch", key=f"grades-{course}-{nonce}",
        column_config={
            "item": st.column_config.TextColumn("Graded item", max_chars=60, required=True),
            "type": st.column_config.SelectboxColumn("Type", options=grades.ITEM_TYPES, default="Assignment",
                                                     required=True),
            "weight": st.column_config.NumberColumn("Weight (% of course grade)", min_value=0.0, max_value=100.0,
                                                    step=0.5, format="%.1f"),
            "score": st.column_config.NumberColumn("Your score (%)", min_value=0.0, max_value=120.0, step=0.5,
                                                   format="%.1f", help="Leave blank if it hasn't been graded yet"),
        },
    )
    items = grades.clean_items(edited.to_dict("records"))
    errors = grades.validate(items)
    unsaved = items != grades.clean_items(saved)
    save_col, note_col = st.columns([1, 3], vertical_alignment="center")
    if save_col.button("Save grades", type="primary", icon=":material/save:", disabled=not unsaved or bool(errors),
                       key=f"save-grades-{course}"):
        state["grades"][course] = items
        persist()
        st.session_state[f"grades-nonce-{course}"] = nonce + 1
        flash(f"Saved grades for {course}")
        st.rerun()
    if unsaved:
        note_col.caption(":orange[Unsaved changes] — results below already use them.")
    for error in errors:
        st.error(error)
    return items, errors


def grade_report(items: list[dict], course: str) -> dict | None:
    """Current average, expected final grade, and what's needed on remaining work."""
    remaining = st.number_input("If you average this on the remaining work (%)", min_value=0.0, max_value=120.0,
                                value=None, step=1.0, key=f"remaining-{course}",
                                placeholder="Leave blank to assume you keep your current average")
    summary = grades.summarize(items, remaining)
    if summary["current"] is None:
        st.info("Add at least one graded item with a score to calculate your expected grade.",
                icon=":material/calculate:")
        return None

    m = st.columns(3)
    m[0].metric("Current average", f"{summary['current']:.1f}%", help="Weighted average of graded work so far")
    m[1].metric("Expected final grade", f"{summary['projected_letter']} · {summary['projected']:.1f}%",
                help="Graded work plus the remaining work at the average above")
    m[2].metric("Course graded so far", f"{summary['graded_weight']:.0f}%")

    if summary["remaining_weight"] > 0:
        st.markdown(f"**To finish with each grade, average this on the remaining "
                    f"{summary['remaining_weight']:.0f}% of the course:**")
        cols = st.columns(4)
        for col, (grade, need) in zip(cols, summary["needed"].items()):
            with col.container(border=True):
                if need <= 0:
                    st.markdown(f"**{grade}** · :green[locked in]")
                elif need > 100:
                    st.markdown(f"**{grade}** · :red[out of reach]")
                    st.caption(f"Would need {need:.0f}%")
                else:
                    st.markdown(f"**{grade}** · need **{need:.0f}%**")
        st.caption(f"Possible range: {summary['worst_case']:.1f}% ({grades.letter(summary['worst_case'])}) if you "
                   f"score 0 on what's left, up to {summary['best_case']:.1f}% "
                   f"({grades.letter(summary['best_case'])}) with 100%. Scale: A ≥ 90, B ≥ 80, C ≥ 70, D ≥ 60, "
                   "F < 60.")
    if summary["unlisted_weight"] > 0.01:
        st.caption(f"{summary['unlisted_weight']:.0f}% of the course grade isn't listed yet — it's treated as "
                   "remaining work.")
    return summary


def grade_check(summary: dict | None, result: dict) -> None:
    """Verify the model's D/F prediction against the student's actual grades."""
    st.subheader("Grade check")
    level, message = grades.cross_check(summary["projected"] if summary else None, result["tier"] == "at_risk")
    {"error": st.error, "warning": st.warning, "success": st.success, "info": st.info}[level](message)


def grade_outlook(profile: dict, result: dict) -> None:
    """For profiles without a grade table: what the midterm and the model say about a D or F."""
    st.subheader("Grade outlook")
    midterm = profile["midterm_score"]
    band = grades.df_band(midterm)
    st.markdown(f"Midterm **{midterm:.0f}%** — on its own that's a **{grades.letter(midterm)}**"
                + (f", inside the {'D (60–69)' if band == 'D' else 'F (below 60)'} range." if band else "."))
    p = result["probability"]
    st.markdown(f"Model: **{chance(1 - p)}** chance of a **C or higher**, **{chance(p)}** chance of a **D or F**.")
    st.caption("The WolfHacks data labels D and F together, so the model predicts D-or-F risk. Use "
               "**My activity** with your real graded work to see your expected letter grade.")


RISK_SOURCES = ["My activity", "Upload a CSV", "Dataset student", "What-if"]

# Features the app measures from what you do, and where each one comes from.
ACTIVITY_FEATURES = {
    "avg_weekly_study_hours": "Study log",
    "study_sessions_logged": "Study log",
    "late_night_study_pct": "Study log",
    "avg_days_started_before_exam": "Study log + Calendar exams",
    "on_time_submission_rate": "Calendar deadlines",
    "missed_deadlines": "Calendar deadlines",
    "materials_uploaded": "Study materials",
    "practice_quizzes_taken": "Study materials quizzes",
    "avg_practice_quiz_score": "Study materials quizzes",
    "flashcards_reviewed": "Study materials flashcards",
}
HOW_TO_MEASURE = {
    "late_night_study_pct": "Log study sessions and this fills in automatically.",
    "avg_days_started_before_exam": "Add exams to the Calendar and log study before them.",
    "on_time_submission_rate": "Tick off deadlines in the Calendar once their due date passes.",
}


def _shown(feat: str, value) -> str:
    if feat == "avg_practice_quiz_score" and is_missing(value):
        return "No quizzes yet"
    text = risk_model.format_value(feat, value)
    return f"{text} h" if feat == "avg_weekly_study_hours" else text


def my_activity_form(state: dict, bundle: dict, today: date, course: str, midterm_override: float | None) -> dict:
    """Risk-model inputs for the student: measured ones filled in automatically, personal ones typed once."""
    medians, saved = bundle["medians"], state["profile"]
    derived = tracker.dashboard_profile(state, today, course)
    profile: dict = {"course": course}
    key = f"me-{course}"

    with st.container(border=True):
        st.subheader("From your activity")
        st.caption(f"Filled in automatically from what you do in Wolf Tracks for {course} — these update as you "
                   "study, tick off deadlines and use your study materials.")
        missing = []
        feats = list(ACTIVITY_FEATURES)
        for row in (feats[:5], feats[5:]):
            for col, feat in zip(st.columns(5), row):
                value = derived.get(feat)
                if feat == "avg_practice_quiz_score" and not derived.get("practice_quizzes_taken"):
                    value = float("nan")  # matches the dataset: blank when no quizzes
                if value is None:
                    missing.append(feat)
                    col.metric(risk_model.LABELS[feat], "No data yet", help=HOW_TO_MEASURE.get(feat))
                else:
                    profile[feat] = value
                    col.metric(risk_model.LABELS[feat], _shown(feat, value), help=f"From: {ACTIVITY_FEATURES[feat]}")
        if missing:
            st.markdown("**Not enough data yet for these — enter your best estimate:**")
            cols = st.columns(len(missing), gap="large")
            for col, feat in zip(cols, missing):
                with col:
                    profile[feat] = feature_input(st, feat, saved, medians, key)
                    st.caption(HOW_TO_MEASURE.get(feat, ""))

    with st.container(border=True):
        st.subheader("About you")
        st.caption("Only you know these. Fill them in once and click Save — drag a slider or type a number.")
        c1, c2, c3 = st.columns(3, gap="large")
        with c1:
            year = saved.get("class_year", "Freshman")
            profile["class_year"] = st.selectbox(
                "Class year", risk_model.CLASS_YEARS, key=f"{key}-year",
                index=risk_model.CLASS_YEARS.index(year) if year in risk_model.CLASS_YEARS else 0)
            profile["credit_hours"] = feature_input(st, "credit_hours", saved, medians, key)
        with c2:
            profile["work_hours_per_week"] = feature_input(st, "work_hours_per_week", saved, medians, key)
            profile["attendance_rate"] = feature_input(st, "attendance_rate", saved, medians, key)
        with c3:
            profile["avg_sleep_hours"] = feature_input(st, "avg_sleep_hours", saved, medians, key)
            profile["midterm_score"] = feature_input(st, "midterm_score", saved, medians, key,
                                                     override=midterm_override)
            if midterm_override is not None:
                st.caption("Midterm comes from your grade table above.")
        if st.button("Save", type="primary", icon=":material/save:", key=f"{key}-save"):
            keep = ["class_year", "credit_hours", "work_hours_per_week", "attendance_rate", "avg_sleep_hours",
                    "midterm_score", *missing]
            state["profile"].update({k: (None if is_missing(profile[k]) else profile[k]) for k in keep})
            persist()
            flash("Saved your profile")
            st.rerun()
    return profile


def page_risk() -> None:
    state, bundle, today = get_state(), get_bundle(), date.today()
    page_header("Risk check", "Calculates your expected grade from your graded work, and uses a decision tree "
                              "trained on the WolfHacks dataset to estimate your chance of a D or F — with the "
                              "reasons and what to do next.")
    df = get_dataset()
    medians = bundle["medians"]
    dataset_courses = sorted(df["course"].unique())

    source = st.segmented_control("Profile source", RISK_SOURCES, default=RISK_SOURCES[0], key="risk_source")
    source = source or RISK_SOURCES[0]
    actual, grade_summary, midterm_override = None, None, None
    if source == "Upload a CSV":
        picked = batch_analysis(bundle)
        if picked is None:
            return
        base, actual, key = picked
    elif source == "My activity":
        if not state["courses"]:
            empty_state("🎓", "Add a course first", "Your risk check is calculated per course.",
                        "courses", "Go to Courses")
            return
        course = st.selectbox("Course to check", state["courses"], key="risk_course")
        with st.container(border=True):
            st.subheader(f"Your grades in {course}")
            st.caption("Add each graded item with its weight from your syllabus and your score. Click a cell to "
                       "type; use the + row at the bottom to add items. Leave the score blank if it isn't graded yet.")
            items, errors = grade_editor(state, course)
            if not errors:
                grade_summary = grade_report(items, course)
                midterm_override = grades.midterm_score(items)
        profile = my_activity_form(state, bundle, today, course, midterm_override)
        key = None
    elif source == "Dataset student":
        indexed = df.set_index("student_id")
        sid = st.selectbox("Student", indexed.index,
                           format_func=lambda s: f"{s} · {indexed.at[s, 'course']} · {indexed.at[s, 'class_year']}")
        row = indexed.loc[sid]
        base = row.to_dict()
        base["course"], base["class_year"] = row["course"], row["class_year"]
        actual = int(row[risk_model.TARGET])
        key = f"ds-{sid}"
    else:
        base = {**medians, "course": dataset_courses[0], "class_year": "Freshman"}
        key = "custom"
        st.caption("Start from a typical student and move the sliders to explore what changes the prediction.")

    if source != "My activity":
        with st.container(border=True):
            profile = profile_form(base, key, dataset_courses, medians, midterm_override)

    result = risk_model.predict_risk(bundle, profile)
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.plotly_chart(risk_gauge(result["probability"]), width="stretch")
        render_alert(result)
        if actual is not None:
            correct = actual == result["prediction"]
            st.caption(f"Actual outcome: **{'D/F (at risk)' if actual else 'C or better'}** — "
                       f"model was {'✅ correct' if correct else '❌ wrong'} for this student.")
    with right:
        if source == "My activity":
            grade_check(grade_summary, result)
        else:
            grade_outlook(profile, result)
        st.subheader("Why the model decided this")
        st.markdown("\n".join(f"{i}. {rule}" for i, rule in enumerate(result["path"], start=1)))
        st.caption("These are the exact splits the decision tree followed for this profile.")

    st.subheader("Suggested next steps")
    if result["suggestions"]:
        cols = st.columns(2)
        for i, s in enumerate(result["suggestions"]):
            with cols[i % 2].container(border=True):
                st.markdown(f"**{s['label']}** — you: `{s['you']}` · on-track median: `{s['target']}`")
                st.write(s["advice"])
    else:
        st.success("No major gaps versus on-track students — keep doing what you're doing!")
    if result["tier"] != "on_track":
        st.markdown("**Academic support resources**")
        st.markdown("\n".join(f"- {r}" for r in risk_model.SUPPORT_RESOURCES))
    if source == "My activity":
        st.page_link(PAGE["plan"], label="Make a study plan for your next test", icon=":material/event_note:")


# --------------------------------------------------------------------------- #
# Model insights
# --------------------------------------------------------------------------- #
def page_insights() -> None:
    bundle = get_bundle()
    page_header("Model insights", f"DecisionTreeClassifier tuned with 5-fold cross-validation, trained on "
                                  f"{bundle['n_train']} students and tested on {bundle['n_test']} held-out "
                                  f"students it never saw.")
    m = bundle["metrics"]
    cols = st.columns(5)
    cols[0].metric("Accuracy", f"{m['accuracy']:.1%}", f"{m['accuracy'] - m['baseline_accuracy']:+.1%} vs baseline")
    cols[1].metric("Precision", f"{m['precision']:.1%}")
    cols[2].metric("Recall", f"{m['recall']:.1%}", help="Share of truly at-risk students the model catches")
    cols[3].metric("F1", f"{m['f1']:.2f}", f"CV {m['cv_f1']:.2f}", delta_color="off")
    cols[4].metric("ROC AUC", f"{m['roc_auc']:.2f}")
    st.caption(f"Best parameters: `{bundle['best_params']}`")

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Confusion matrix (held-out set)")
        fig = px.imshow(m["confusion_matrix"], text_auto=True, color_continuous_scale="Greens",
                        x=["Pred: on track", "Pred: at risk"], y=["Actual: on track", "Actual: at risk"])
        fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")
    with right:
        st.subheader("Feature importance")
        imp = pd.Series(bundle["feature_importances"]).rename(index=risk_model.LABELS)
        imp = imp[imp > 0].sort_values()
        fig = px.bar(imp, orientation="h", labels={"value": "Importance", "index": ""})
        fig.update_traces(marker_color=GREEN)
        fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
        st.plotly_chart(fig, width="stretch")

    st.subheader("The decision tree (top 3 levels)")
    fig, ax = plt.subplots(figsize=(22, 8))
    plot_tree(bundle["pipeline"].named_steps["tree"], max_depth=3, feature_names=risk_model.encoded_feature_names(bundle),
              class_names=["On track", "At risk"], filled=True, rounded=True, impurity=False, proportion=True,
              fontsize=9, ax=ax)
    st.pyplot(fig)
    plt.close(fig)
    with st.expander("Full tree rules (text)"):
        st.code(risk_model.tree_rules_text(bundle), language="text")

    st.subheader("Dataset explorer")
    df = get_dataset()
    c1, c2 = st.columns(2, gap="large")
    with c1:
        by_course = df.groupby("course", as_index=False)[risk_model.TARGET].mean().sort_values(risk_model.TARGET)
        fig = px.bar(by_course, x=risk_model.TARGET, y="course", orientation="h",
                     labels={risk_model.TARGET: "At-risk rate", "course": ""})
        fig.update_traces(marker_color="#cf222e")
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), xaxis_tickformat=".0%",
                          title="At-risk rate by course")
        st.plotly_chart(fig, width="stretch")
    with c2:
        feat = st.selectbox("Compare a feature", risk_model.NUMERIC, index=risk_model.NUMERIC.index("midterm_score"),
                            format_func=risk_model.LABELS.get)
        plot_df = df.assign(outcome=df[risk_model.TARGET].map({0: "C or better", 1: "D/F (at risk)"}))
        fig = px.box(plot_df, x="outcome", y=feat, color="outcome", labels={feat: risk_model.LABELS[feat], "outcome": ""},
                     color_discrete_map={"C or better": GREEN, "D/F (at risk)": "#cf222e"})
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
        st.plotly_chart(fig, width="stretch")
    with st.expander("Raw data"):
        st.dataframe(df, hide_index=True, width="stretch")

    if st.button("Retrain model", icon=":material/refresh:"):
        with st.spinner("Retraining…"):
            risk_model.load_or_train(force=True)
        get_bundle.clear()
        flash("Model retrained")
        st.rerun()


# --------------------------------------------------------------------------- #
# Courses
# --------------------------------------------------------------------------- #
@st.dialog("Rename course")
def rename_dialog(old: str) -> None:
    state = get_state()
    new = st.text_input("Course name", value=old, max_chars=tracker.MAX_COURSE_NAME)
    st.caption("Sessions, events, materials and quizzes move to the new name.")
    cancel, save = st.columns(2)
    if cancel.button("Cancel", width="stretch"):
        st.rerun()
    if save.button("Save", type="primary", width="stretch"):
        ok, message = tracker.rename_course(state, old, new)
        if ok:
            persist()
            flash(message)
            st.rerun()
        st.error(message)


def page_courses() -> None:
    state = get_state()
    page_header("Courses", "Add the classes you're taking. Study sessions, deadlines and materials are all "
                           "organized by course.")

    with st.form("add_course", clear_on_submit=True, border=True):
        c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
        name = c1.text_input("Course name or code", placeholder="e.g. MA 241 or Organic Chemistry",
                             max_chars=tracker.MAX_COURSE_NAME)
        submitted = c2.form_submit_button("Add course", type="primary", icon=":material/add:", width="stretch")
    if submitted:
        ok, message = tracker.add_course(state, name)
        if ok:
            persist()
            flash(message)
            st.rerun()
        st.error(message)

    suggestions = [c for c in sorted(get_dataset()["course"].unique()) if c not in state["courses"]]
    if suggestions:
        nonce = st.session_state.get("pill_nonce", 0)
        picked = st.pills("Quick add (courses from the WolfHacks dataset)", suggestions, selection_mode="multi",
                          key=f"quick-{nonce}")
        if st.button("Add selected", icon=":material/playlist_add:", disabled=not picked):
            for course in picked:
                tracker.add_course(state, course)
            persist()
            st.session_state["pill_nonce"] = nonce + 1
            flash(f"Added {', '.join(picked)}")
            st.rerun()

    st.subheader(f"Your courses ({len(state['courses'])})")
    if not state["courses"]:
        st.caption("No courses yet — add one above.")
    for course in state["courses"]:
        usage = tracker.course_usage(state, course)
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 4, 1, 1], vertical_alignment="center")
            c1.markdown(f"**{course}**")
            c2.caption(f"{usage['hours']:.1f} h studied · {usage['sessions']} sessions · {usage['events']} events · "
                       f"{usage['materials']} materials")
            if c3.button("Rename", key=f"ren-{course}", icon=":material/edit:", width="stretch"):
                rename_dialog(course)
            if c4.button("Remove", key=f"rm-{course}", icon=":material/delete:", width="stretch"):
                attached = (f"This also deletes {usage['sessions']} sessions, {usage['events']} events, "
                            f"{usage['materials']} materials, {usage['quizzes']} quiz results and "
                            f"{usage['grades']} graded items for this course."
                            if any(usage.values()) else "It has no data attached.")

                def remove(course=course):
                    flash(tracker.remove_course(state, course))
                    persist()
                confirm_dialog(f"Remove **{course}**? {attached} This can't be undone.", "Remove", remove)

    st.caption("Courses outside the WolfHacks list work everywhere; the risk model simply treats them as a "
               "general course (course name barely affects its predictions).")


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
def _save_key() -> None:
    st.session_state["gemini_key"] = st.session_state["gemini_key_widget"].strip()


def _do_import(data: bytes) -> None:
    try:
        st.session_state.state = tracker.import_archive(data)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        flash(f"Import failed: {exc}")
        return
    persist()
    st.session_state["_suppress_achievements"] = True
    st.session_state["archive_nonce"] = st.session_state.get("archive_nonce", 0) + 1
    st.session_state.pop("export_bytes", None)
    imported = st.session_state.state
    flash(f"Imported {len(imported['courses'])} courses, {len(imported['sessions'])} sessions, "
          f"{len(imported['events'])} events and {len(imported['materials'])} materials")


def _do_reset() -> None:
    st.session_state.state = tracker.default_state()
    persist()
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    for key in ("_unlocked", "export_bytes"):
        st.session_state.pop(key, None)
    flash("All data erased")


def page_settings() -> None:
    state, today = get_state(), date.today()
    page_header("Settings", "AI features, moving your data between computers, and resetting the app.")

    with st.container(border=True):
        st.subheader("AI features")
        st.text_input("Gemini API key", type="password", key="gemini_key_widget",
                      value=st.session_state.get("gemini_key", ""), on_change=_save_key,
                      help="Get a free key at aistudio.google.com/apikey. Or put GEMINI_API_KEY in the .env file.")
        if gemini_key():
            st.success(f"Connected · model `{ai_helper.DEFAULT_MODEL}`", icon=":material/check_circle:")
        else:
            st.info("No key yet — summaries and flashcards use offline mode; quizzes and syllabus import are "
                    "off.", icon=":material/info:")

    with st.container(border=True):
        st.subheader("Export data")
        st.caption("Download everything (courses, sessions, calendar, quizzes and uploaded files) as one .zip "
                   "to back it up or move it to another computer.")
        if st.button("Prepare export", icon=":material/inventory_2:"):
            st.session_state["export_bytes"] = tracker.export_archive(state)
        if st.session_state.get("export_bytes"):
            st.download_button("Download archive", st.session_state["export_bytes"], type="primary",
                               icon=":material/download:", file_name=f"wolf-tracks-archive-{today:%Y%m%d}.zip",
                               mime="application/zip")

    with st.container(border=True):
        st.subheader("Import data")
        st.caption("Load an archive exported from Wolf Tracks — try `examples/dashboard_archive/example_student_archive.zip`.")
        archive = st.file_uploader("Archive (.zip)", type=["zip"],
                                   key=f"archive-{st.session_state.get('archive_nonce', 0)}")
        if st.button("Import archive", type="primary", icon=":material/upload:", disabled=archive is None):
            data = archive.getvalue()
            has_data = any(state[k] for k in ("courses", "sessions", "events", "materials"))
            if has_data:
                confirm_dialog("Importing **replaces** your current courses, sessions, calendar and materials. "
                               "Export first if you want a backup.", "Replace my data", lambda: _do_import(data))
            else:
                _do_import(data)
                st.rerun()

    with st.container(border=True):
        st.subheader(":red[Danger zone]")
        st.caption("Permanently delete all courses, sessions, events, materials and quiz results on this computer.")
        if st.button("Erase all data", icon=":material/delete_forever:"):
            confirm_dialog("Erase **all** your Wolf Tracks data? This can't be undone.", "Erase everything",
                           _do_reset)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    state = get_state()
    get_bundle()
    today = date.today()
    if message := st.session_state.pop("flash", None):
        st.toast(message)

    PAGE.update({
        "dashboard": st.Page(page_dashboard, title="Dashboard", icon=":material/dashboard:", default=True),
        "log": st.Page(page_log, title="Study log", icon=":material/timer:", url_path="study-log"),
        "calendar": st.Page(page_calendar, title="Calendar", icon=":material/calendar_month:", url_path="calendar"),
        "plan": st.Page(page_plan, title="Study plan", icon=":material/event_note:", url_path="study-plan"),
        "materials": st.Page(page_materials, title="Study materials", icon=":material/library_books:",
                             url_path="materials"),
        "risk": st.Page(page_risk, title="Risk check", icon=":material/monitor_heart:", url_path="risk"),
        "achievements": st.Page(page_achievements, title="Achievements", icon=":material/emoji_events:",
                                url_path="achievements"),
        "insights": st.Page(page_insights, title="Model insights", icon=":material/insights:", url_path="model"),
        "courses": st.Page(page_courses, title="Courses", icon=":material/school:", url_path="courses"),
        "settings": st.Page(page_settings, title="Settings", icon=":material/settings:", url_path="settings"),
    })
    navigation = st.navigation({
        "Overview": [PAGE["dashboard"]],
        "Study": [PAGE["log"], PAGE["calendar"], PAGE["plan"], PAGE["materials"]],
        "Insights": [PAGE["risk"], PAGE["achievements"], PAGE["insights"]],
        "Manage": [PAGE["courses"], PAGE["settings"]],
    })
    # Logo + name at the top left of the sidebar (just the paw when the sidebar is collapsed).
    st.logo(str(ASSETS / "wordmark.png"), icon_image=str(ASSETS / "logo.png"), size="large")
    st.html("<style>[data-testid='stSidebarLogo'], [data-testid='stHeaderLogo'] { height: 2.75rem; }</style>")
    sidebar_status(state, today)
    render_effects()  # confetti queued by a callback or before an st.rerun()
    navigation.run()
    render_effects()  # confetti queued during this run (no rerun happened)
    notify_new_achievements(st.session_state.state, today)


main()
