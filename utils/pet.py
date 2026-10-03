"""The Wolf Tracks pet: mood from study habits, tokens, shop, and the post-session slot + roulette games.

Everything lives in ``state["pet"]`` (saved with the rest of the user's data)::

    {"name", "tokens", "earned" (lifetime tokens), "owned": [item ids], "equipped": {slot: id},
     "last_checkin", "checkin_streak", "study_days": {iso date: tokens earned from sessions that day},
     "tickets": {session_id: "slot" | "roulette"}, "history": [{"t", "amount", "reason"}]}

Games are decided on the server so the odds can't be tampered with from the browser.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from typing import Any

from . import tracker

# --------------------------------------------------------------------------- #
# Catalog
# --------------------------------------------------------------------------- #
SLOTS = ["hat", "eyewear", "neck", "scene"]
SLOT_LABELS = {"hat": "Hats", "eyewear": "Eyewear", "neck": "Neckwear", "scene": "Scenes"}


def _item(id_: str, slot: str, name: str, price: int, rarity: str, desc: str = "") -> dict[str, Any]:
    return {"id": id_, "slot": slot, "name": name, "price": price, "rarity": rarity, "desc": desc}


# Hats, eyewear and neckwear are hand-drawn images in web/public/wolf (hat-<id>.png ...); the Golden Halo is the one vector item.
CATALOG: list[dict[str, Any]] = [
    _item("cap_black", "hat", "Black Cap", 40, "common", "A classic bucket cap."),
    _item("cap_blue", "hat", "Blue Cap", 40, "common", "A classic bucket cap."),
    _item("cap_pink", "hat", "Pink Cap", 40, "common", "A classic bucket cap."),
    _item("cap_yellow", "hat", "Yellow Cap", 40, "common", "A classic bucket cap."),
    _item("party", "hat", "Party Hat", 45, "common", "Every study session is a celebration."),
    _item("propeller", "hat", "Propeller Cap", 70, "rare", "Ready for takeoff."),
    _item("gradcap", "hat", "Grad Cap", 90, "rare", "Future summa cum laude."),
    _item("fedora", "hat", "Fedora", 100, "rare", "Very distinguished."),
    _item("wizard", "hat", "Wizard Hat", 160, "epic", "Spells out good grades."),
    _item("halo", "hat", "Golden Halo", 200, "epic", "For a perfect streak."),
    _item("crown", "hat", "Alpha Crown", 250, "legendary", "Leader of the pack."),
    _item("glasses", "eyewear", "Round Glasses", 35, "common", "Looks smart, is smart."),
    _item("square", "eyewear", "Square Glasses", 40, "common", "Sharp and studious."),
    _item("shades", "eyewear", "Sunglasses", 60, "common", "Too cool for finals week."),
    _item("monocle", "eyewear", "Monocle", 90, "rare", "Fancy and refined."),
    _item("bandana_black", "neck", "Black Bandana", 30, "common", "Rep the Wolf Tracks."),
    _item("bandana_blue", "neck", "Blue Bandana", 30, "common", "Rep the Wolf Tracks."),
    _item("bandana_pink", "neck", "Pink Bandana", 30, "common", "Rep the Wolf Tracks."),
    _item("bandana_yellow", "neck", "Yellow Bandana", 30, "common", "Rep the Wolf Tracks."),
    _item("bowtie_black", "neck", "Black Bow Tie", 45, "common", "Bow ties are cool."),
    _item("bowtie_blue", "neck", "Blue Bow Tie", 45, "common", "Bow ties are cool."),
    _item("bowtie_pink", "neck", "Pink Bow Tie", 45, "common", "Bow ties are cool."),
    _item("bowtie_yellow", "neck", "Yellow Bow Tie", 45, "common", "Bow ties are cool."),
    _item("chain", "neck", "Silver Chain", 120, "rare", "Heavy hitter."),
    _item("scene_moon", "scene", "Moonlit Hill", 60, "common", "Howl at the moon."),
    _item("scene_forest", "scene", "Pine Forest", 90, "rare", "Home territory."),
    _item("scene_library", "scene", "Library", 120, "rare", "Quiet study zone."),
    _item("scene_aurora", "scene", "Aurora", 160, "epic", "Northern lights."),
    _item("scene_space", "scene", "Deep Space", 200, "epic", "Interstellar scholar."),
]
# Items removed from the shop (token price they sold for). Anyone who owned one is refunded and un-equipped.
RETIRED = {"beanie": 45, "tophat": 120, "starspecs": 90, "scarf": 70, "bandana": 30, "bowtie": 50, "backpack": 80, "cape": 120,
           "wings": 260, "fur_snow": 80, "fur_midnight": 80, "fur_ember": 100, "fur_emerald": 120, "fur_golden": 200}
UPGRADES: list[dict[str, Any]] = [
    _item("magnet", "upgrade", "Token Magnet", 150, "epic", "+25% tokens from every study session."),
    _item("lucky", "upgrade", "Lucky Paw", 200, "legendary", "Slot pairs pay double and the roulette favours big prizes."),
    _item("treat", "upgrade", "Daily Treat", 100, "rare", "+5 tokens on every daily check-in."),
]
CONSUMABLES: list[dict[str, Any]] = [
    _item("freeze", "consumable", "Streak Freeze", 60, "rare",
          "Automatically saves your streak if you miss a day. Hold up to 3."),
]
MAX_FREEZES = 3
ITEMS = {i["id"]: i for i in CATALOG + UPGRADES + CONSUMABLES}
DEFAULT_OWNED = ["scene_den"]
DEFAULT_EQUIPPED = {"hat": None, "eyewear": None, "neck": None, "scene": "scene_den"}
FREE_ITEMS = [
    _item("scene_den", "scene", "The Den", 0, "common", "Home sweet den."),
]
ITEMS.update({i["id"]: i for i in FREE_ITEMS})

LEVELS = [(0, "Pup"), (50, "Scout"), (150, "Tracker"), (300, "Hunter"), (500, "Pathfinder"), (800, "Packmate"),
          (1200, "Beta"), (1800, "Pack Leader"), (2600, "Alpha"), (3600, "Legend")]

PLAYS_PER_SESSION = 2  # bonus plays per finished session; spend them on any mini-game
SESSION_MIN_MINUTES = 5
SESSION_DAILY_CAP = 120  # tokens a day from sessions (games and check-ins are extra)
STREAK_BONUS = {3: 20, 7: 50, 14: 100, 30: 250}


# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #
def default_pet() -> dict[str, Any]:
    return {"name": "Wolfie", "tokens": 25, "earned": 25, "owned": list(DEFAULT_OWNED),
            "equipped": dict(DEFAULT_EQUIPPED), "last_checkin": None, "checkin_streak": 0,
            "study_days": {}, "tickets": {}, "crossy": None, "freezes": 0, "frozen": [], "last_freeze": None, "quests": None,
            "weekly": {}, "daily": {}, "rewarded_events": [], "history": [{"t": datetime.now().isoformat(timespec="seconds"),
                                                          "amount": 25, "reason": "Welcome gift"}]}


def ensure(state: dict[str, Any]) -> dict[str, Any]:
    """Fill in anything missing so older saves and archives keep working."""
    pet = state.get("pet")
    if not isinstance(pet, dict) or not pet:
        pet = state["pet"] = default_pet()
    base = default_pet()
    for key, value in base.items():
        pet.setdefault(key, value)
    if not isinstance(pet.get("weekly"), dict):
        pet["weekly"] = {}
    # Older saves stored the stage ("slot"/"roulette"); tickets are now a count of plays left.
    pet["tickets"] = {sid: (2 if v == "slot" else 1 if v == "roulette" else int(v))
                      for sid, v in pet["tickets"].items() if v}
    for slot, value in DEFAULT_EQUIPPED.items():
        pet["equipped"].setdefault(slot, value)
    for item in DEFAULT_OWNED:
        if item not in pet["owned"]:
            pet["owned"].append(item)
    _drop_retired(pet)
    return pet


def _drop_retired(pet: dict[str, Any]) -> None:
    """Remove shop items that no longer exist (and the Back / Fur slots), refunding what the player paid."""
    gone = [i for i in pet["owned"] if i not in ITEMS]
    for item in gone:
        pet["owned"].remove(item)
        if RETIRED.get(item):
            _log(pet, RETIRED[item], f"Refund: {item.replace('_', ' ')} left the shop")
    for slot in list(pet["equipped"]):
        if slot not in SLOTS or (pet["equipped"][slot] and pet["equipped"][slot] not in ITEMS):
            if slot in SLOTS:
                pet["equipped"][slot] = DEFAULT_EQUIPPED.get(slot)
            else:
                del pet["equipped"][slot]


def _log(pet: dict[str, Any], amount: int, reason: str) -> None:
    pet["tokens"] += amount
    if amount > 0:
        pet["earned"] += amount
    pet["history"].append({"t": datetime.now().isoformat(timespec="seconds"), "amount": amount, "reason": reason})
    pet["history"] = pet["history"][-60:]


def level_info(earned: int) -> dict[str, Any]:
    index = max(i for i, (need, _) in enumerate(LEVELS) if earned >= need)
    nxt = LEVELS[index + 1] if index + 1 < len(LEVELS) else None
    base = LEVELS[index][0]
    return {"level": index + 1, "title": LEVELS[index][1], "earned": earned, "next_at": nxt[0] if nxt else None,
            "progress": 1.0 if not nxt else (earned - base) / (nxt[0] - base)}


# --------------------------------------------------------------------------- #
# Mood
# --------------------------------------------------------------------------- #
def effective_daily(state: dict[str, Any]) -> dict[date, float]:
    """Study minutes per day, counting days saved by a Streak Freeze as studied."""
    daily = tracker.daily_minutes(state)
    for iso_day in ensure(state)["frozen"]:
        daily.setdefault(date.fromisoformat(iso_day), 0.001)
    return daily


def streak_risk(state: dict[str, Any], today: date, now: datetime | None = None) -> dict[str, Any]:
    """Is today's study the only thing keeping a streak alive? Includes a countdown to midnight."""
    pet = ensure(state)
    now = now or datetime.now()
    daily = effective_daily(state)
    current, _ = tracker.streaks(daily, today)
    studied_today = daily.get(today, 0) >= 1
    midnight = datetime.combine(today + timedelta(days=1), datetime.min.time())
    hours = max(0.0, (midnight - now).total_seconds() / 3600)
    return {"at_risk": current >= 1 and not studied_today, "streak": current, "hours_left": round(hours, 2),
            "ends_at": midnight.isoformat(timespec="seconds"), "freezes": pet["freezes"]}


def apply_freeze(state: dict[str, Any], today: date) -> dict[str, Any] | None:
    """If yesterday was missed and a Streak Freeze is held, spend it to keep the streak alive."""
    pet = ensure(state)
    if pet["freezes"] <= 0:
        return None
    daily = effective_daily(state)
    yesterday = today - timedelta(days=1)
    if daily.get(yesterday, 0) > 0:
        return None
    run, day = 0, yesterday - timedelta(days=1)
    while daily.get(day, 0) > 0:
        run += 1
        day -= timedelta(days=1)
    if run < 2:
        return None
    pet["freezes"] -= 1
    pet["frozen"] = (pet["frozen"] + [yesterday.isoformat()])[-30:]
    pet["last_freeze"] = {"date": today.isoformat(), "streak": run}
    _log(pet, 0, f"Streak Freeze saved your {run}-day streak")
    return pet["last_freeze"]


def mood(state: dict[str, Any], today: date) -> dict[str, Any]:
    daily = effective_daily(state)
    current, _ = tracker.streaks(daily, today)
    studied = sorted(d for d, m in daily.items() if m > 0)
    today_min = daily.get(today, 0.0)
    week_min = sum(m for d, m in daily.items() if today - timedelta(days=6) <= d <= today)
    days_since = (today - studied[-1]).days if studied else None

    score, reasons = 50, []
    if not studied:
        score = 35
        reasons.append("You haven't logged a session yet — your wolf is waiting.")
    else:
        if today_min > 0:
            score += 30 + (10 if today_min >= 60 else 0)
            reasons.append(f"You studied {today_min:.0f} min today.")
        elif days_since == 1:
            score -= 10
            reasons.append("No study yet today — a short session keeps your streak.")
        elif days_since is not None:
            score -= 25 if days_since == 2 else 45
            reasons.append(f"It's been {days_since} days since your last session.")
        risk = streak_risk(state, today)
        if risk["at_risk"] and current >= 3 and risk["hours_left"] < 6:
            score -= 12
            reasons.append(f"Your {current}-day streak ends in {risk['hours_left']:.0f}h — study to save it!")
        if week_min >= 300:
            score += 15
            reasons.append("Over 5 hours this week — amazing!")
        elif week_min >= 120:
            score += 8
            reasons.append("Solid week of studying.")
        if current >= 7:
            score += 20
            reasons.append(f"{current}-day streak!")
        elif current >= 3:
            score += 10
            reasons.append(f"{current}-day streak.")
    score = max(0, min(100, score))
    key = "ecstatic" if score >= 85 else "happy" if score >= 65 else "content" if score >= 45 else "worried" if score >= 25 else "sad"
    messages = {
        "ecstatic": "Your wolf is over the moon! 🌕",
        "happy": "Your wolf is happy. Keep it up!",
        "content": "Your wolf is doing alright — a session would make its day.",
        "worried": "Your wolf is worried about you. Study a little today?",
        "sad": "Your wolf misses you. Even 10 minutes helps!",
    }
    return {"key": key, "score": score, "message": messages[key], "reasons": reasons, "studied_today": today_min > 0,
            "streak": current}


# --------------------------------------------------------------------------- #
# Earning tokens
# --------------------------------------------------------------------------- #
def checkin_preview(pet: dict[str, Any], today: date) -> dict[str, Any]:
    last = date.fromisoformat(pet["last_checkin"]) if pet["last_checkin"] else None
    available = last != today
    streak = pet["checkin_streak"] + 1 if last == today - timedelta(days=1) else 1
    amount = 5 + min(streak - 1, 6) + (5 if "treat" in pet["owned"] else 0)
    return {"available": available, "amount": amount, "streak": pet["checkin_streak"] if not available else streak,
            "next_streak": streak}


def checkin(state: dict[str, Any], today: date) -> dict[str, Any]:
    pet = ensure(state)
    preview = checkin_preview(pet, today)
    if not preview["available"]:
        raise ValueError("Your wolf already got its daily pat. Come back tomorrow!")
    pet["last_checkin"] = today.isoformat()
    pet["checkin_streak"] = preview["next_streak"]
    _log(pet, preview["amount"], "Daily check-in")
    return {"amount": preview["amount"], "streak": pet["checkin_streak"]}


def reward_session(state: dict[str, Any], session: dict[str, Any], today: date) -> dict[str, Any] | None:
    """Tokens for a freshly logged session (today's sessions of 5+ minutes). Also opens a slot-machine ticket."""
    pet = ensure(state)
    started = datetime.fromisoformat(session["start"]).date()
    if started != today or session["minutes"] < SESSION_MIN_MINUTES:
        return None
    first_today = today.isoformat() not in pet["study_days"]
    parts: list[dict[str, Any]] = [{"label": "Study session", "amount": 10}]
    minutes_tokens = min(30, int(session["minutes"] // 5) * 2)
    if minutes_tokens:
        parts.append({"label": f"{session['minutes']:.0f} minutes focused", "amount": minutes_tokens})
    if first_today:
        parts.append({"label": "First session today", "amount": 15})
        streak, _ = tracker.streaks(tracker.daily_minutes(state), today)
        if streak in STREAK_BONUS:
            parts.append({"label": f"{streak}-day streak bonus", "amount": STREAK_BONUS[streak]})
    if "magnet" in pet["owned"]:
        bump = round(sum(p["amount"] for p in parts) * 0.25)
        parts.append({"label": "Token Magnet +25%", "amount": bump})
    total = sum(p["amount"] for p in parts)
    room = max(0, SESSION_DAILY_CAP - pet["study_days"].get(today.isoformat(), 0))
    if total > room:
        parts.append({"label": "Daily session cap reached", "amount": room - total})
        total = room
    pet["study_days"][today.isoformat()] = pet["study_days"].get(today.isoformat(), 0) + total
    pet["study_days"] = dict(sorted(pet["study_days"].items())[-30:])
    if total:
        _log(pet, total, f"Studied {session['minutes']:.0f} min")
    pet["tickets"][session["id"]] = PLAYS_PER_SESSION
    return {"session_id": session["id"], "tokens": total, "parts": parts, "plays": PLAYS_PER_SESSION}


# --------------------------------------------------------------------------- #
# Shop
# --------------------------------------------------------------------------- #
def buy(state: dict[str, Any], item_id: str) -> dict[str, Any]:
    pet = ensure(state)
    item = ITEMS.get(item_id)
    if not item or item["price"] <= 0:
        raise ValueError("That item isn't for sale.")
    if item["slot"] == "consumable":
        if pet["freezes"] >= MAX_FREEZES:
            raise ValueError(f"You can hold up to {MAX_FREEZES} Streak Freezes.")
        if pet["tokens"] < item["price"]:
            raise ValueError(f"You need {item['price'] - pet['tokens']} more tokens.")
        pet["freezes"] += 1
        _log(pet, -item["price"], f"Bought {item['name']}")
        return item
    if item_id in pet["owned"]:
        raise ValueError("You already own that.")
    if pet["tokens"] < item["price"]:
        raise ValueError(f"You need {item['price'] - pet['tokens']} more tokens.")
    pet["owned"].append(item_id)
    _log(pet, -item["price"], f"Bought {item['name']}")
    if item["slot"] in SLOTS:
        pet["equipped"][item["slot"]] = item_id  # wear it straight away
    return item


def equip(state: dict[str, Any], slot: str, item_id: str | None) -> None:
    pet = ensure(state)
    if slot not in SLOTS:
        raise ValueError("Unknown slot.")
    if item_id is not None:
        if item_id not in pet["owned"] or ITEMS.get(item_id, {}).get("slot") != slot:
            raise ValueError("You don't own that item.")
    elif slot in ("fur", "scene"):
        raise ValueError("Pick a fur and a scene.")
    pet["equipped"][slot] = item_id


# --------------------------------------------------------------------------- #
# Games
# --------------------------------------------------------------------------- #
SLOT_SYMBOLS = [  # (symbol, weight, triple payout)
    ("🐺", 8, 60), ("🌙", 14, 30), ("⭐", 16, 40), ("🦴", 22, 20), ("🍖", 22, 20), ("💎", 6, 75),
]
ROULETTE = [  # (id, label, weight, color)
    ("t5", "+5", 30, "#1b261c"), ("t10", "+10", 25, "#178a2c"), ("t15", "+15", 18, "#1b261c"),
    ("t25", "+25", 12, "#2db32d"), ("double", "2× SLOT", 5, "#4cc9f0"), ("t50", "+50", 6, "#ffb020"),
    ("mystery", "MYSTERY", 2.5, "#c9a3ff"), ("t100", "+100", 1.5, "#ff5c6c"),
]
ROULETTE_LAYOUT = ["t5", "t10", "t15", "t25", "t5", "t10", "double", "t15", "t50", "t5", "t10", "mystery", "t25", "t15", "t100", "t10"]


def _ticket(pet: dict[str, Any], session_id: str) -> None:
    if pet["tickets"].get(session_id, 0) <= 0:
        raise ValueError("No bonus plays left for that session.")


def _spend(pet: dict[str, Any], session_id: str) -> int:
    left = pet["tickets"].get(session_id, 0) - 1
    if left <= 0:
        pet["tickets"].pop(session_id, None)
        return 0
    pet["tickets"][session_id] = left
    return left


def play_slot(state: dict[str, Any], session_id: str, rng: random.Random | None = None,
              mega: bool = False) -> dict[str, Any]:
    """``mega`` is the demo toggle: every spin is a top-prize triple (🐺 or 💎)."""
    pet = ensure(state)
    _ticket(pet, session_id)
    rng = rng or random.SystemRandom()
    symbols = [s for s, _, _ in SLOT_SYMBOLS]
    weights = [w for _, w, _ in SLOT_SYMBOLS]
    reels = [rng.choice(["🐺", "💎"])] * 3 if mega else rng.choices(symbols, weights=weights, k=3)
    if not mega and len(set(reels)) == 3 and rng.random() < 0.12:  # a little nudge toward near-wins keeps it fun
        reels[rng.randrange(3)] = reels[rng.randrange(3)]
    lucky = "lucky" in pet["owned"]
    counts = {s: reels.count(s) for s in set(reels)}
    best = max(counts.values())
    if best == 3:
        payout = dict((s, p) for s, _, p in SLOT_SYMBOLS)[reels[0]]
        payout = round(payout * (1.5 if lucky else 1))
        kind = "jackpot"
    elif best == 2:
        payout, kind = (12 if lucky else 6), "pair"
    else:
        payout, kind = 2, "none"
    _log(pet, payout, "Slot machine (mega mode)" if mega else "Slot machine")
    pet.setdefault("slot_wins", {})[session_id] = payout
    return {"reels": reels, "payout": payout, "kind": kind, "plays_left": _spend(pet, session_id), "tokens": pet["tokens"]}


def play_roulette(state: dict[str, Any], session_id: str, rng: random.Random | None = None,
                  mega: bool = False) -> dict[str, Any]:
    """``mega`` is the demo toggle: always the +100 segment (or the mystery prize)."""
    pet = ensure(state)
    _ticket(pet, session_id)
    slot_payout = pet.setdefault("slot_wins", {}).get(session_id, 0)
    rng = rng or random.SystemRandom()
    lucky = "lucky" in pet["owned"]
    ids = [r[0] for r in ROULETTE]
    weights = [r[2] * (1.6 if lucky and r[0] in ("t25", "t50", "t100", "double", "mystery") else 1) for r in ROULETTE]
    pick = rng.choice(["t100", "t100", "t100", "mystery"]) if mega else rng.choices(ids, weights=weights, k=1)[0]
    segment = rng.choice([i for i, s in enumerate(ROULETTE_LAYOUT) if s == pick])
    amount, prize, label = 0, None, ""
    if pick.startswith("t"):
        amount = int(pick[1:])
        label = f"+{amount} tokens"
    elif pick == "double":
        amount = max(5, int(slot_payout))
        label = f"Slot winnings doubled: +{amount} tokens"
    else:
        unowned = [i for i in CATALOG if i["id"] not in pet["owned"] and i["price"] <= 150]
        if unowned:
            prize = rng.choice(unowned)
            pet["owned"].append(prize["id"])
            label = f"Mystery prize: {prize['name']}!"
            _log(pet, 0, f"Won {prize['name']} on the roulette")
        else:
            amount, label = 40, "Mystery prize: +40 tokens"
    if amount:
        _log(pet, amount, "Roulette (mega mode)" if mega else "Roulette")
    return {"segment": segment, "id": pick, "amount": amount, "label": label, "prize": prize,
            "plays_left": _spend(pet, session_id), "tokens": pet["tokens"]}


# --------------------------------------------------------------------------- #
# Learning rewards: pay for studying actions, not just minutes on a timer
# --------------------------------------------------------------------------- #
QUIZ_PAYING_PER_DAY = 3
CARDS_TOKEN_EVERY = 5
CARDS_TOKEN_CAP = 20
EVENT_PAYING_PER_DAY = 4
EVENT_REWARD = {"Study": 8, "Deadline": 10, "Quiz": 10, "Milestone": 10, "Exam": 15}


def _daily(pet: dict[str, Any], today: date) -> dict[str, Any]:
    days = pet["daily"]
    entry = days.setdefault(today.isoformat(), {})
    for key in ("cards", "cards_paid", "quiz_paid", "event_paid", "deadlines"):
        entry.setdefault(key, 0)
    for old in sorted(days)[:-14]:
        del days[old]
    return entry


def reward_cards(state: dict[str, Any], count: int, today: date) -> int:
    """1 token per 5 flashcards reviewed, up to 20 tokens a day. Returns tokens earned now."""
    pet = ensure(state)
    daily = _daily(pet, today)
    daily["cards"] += max(0, count)
    due = min(CARDS_TOKEN_CAP, daily["cards"] // CARDS_TOKEN_EVERY) - daily["cards_paid"]
    if due > 0:
        daily["cards_paid"] += due
        _log(pet, due, "Flashcard review")
    return max(0, due)


def reward_quiz(state: dict[str, Any], score: float, today: date) -> dict[str, Any]:
    """Pay for quiz results: better scores pay more; the first 3 quizzes of the day pay."""
    pet = ensure(state)
    daily = _daily(pet, today)
    if daily["quiz_paid"] >= QUIZ_PAYING_PER_DAY:
        return {"tokens": 0, "label": "Daily quiz rewards reached — keep practicing anyway!"}
    daily["quiz_paid"] += 1
    tokens, label = (30, "Perfect score!") if score >= 100 else (20, "Great score") if score >= 80 else \
        (10, "Solid effort") if score >= 60 else (3, "Practice pays off")
    _log(pet, tokens, f"Quiz: {score:.0f}%")
    return {"tokens": tokens, "label": label}


def reward_event_done(state: dict[str, Any], event: dict[str, Any], today: date) -> int:
    """Tokens for ticking off a calendar item on time (once per item, ever)."""
    pet = ensure(state)
    daily = _daily(pet, today)
    if event["id"] in pet["rewarded_events"] or daily["event_paid"] >= EVENT_PAYING_PER_DAY:
        return 0
    if date.fromisoformat(event["date"]) < today - timedelta(days=0) and event["type"] != "Study":
        return 0  # late items don't pay; study tasks are always welcome
    tokens = EVENT_REWARD.get(event["type"], 10)
    pet["rewarded_events"] = (pet["rewarded_events"] + [event["id"]])[-300:]
    daily["event_paid"] += 1
    daily["deadlines"] += 1
    _log(pet, tokens, f"Completed {event['type'].lower()}: {event['title'][:30]}")
    return tokens


# --------------------------------------------------------------------------- #
# Daily quests, the daily chest and the weekly chest
# --------------------------------------------------------------------------- #
QUEST_POOLS: list[list[dict[str, Any]]] = [
    [{"id": "m20", "label": "Study for 20 minutes", "kind": "study_min", "target": 20, "reward": 15},
     {"id": "m45", "label": "Study for 45 minutes", "kind": "study_min", "target": 45, "reward": 30},
     {"id": "s2", "label": "Log 2 study sessions", "kind": "sessions", "target": 2, "reward": 20}],
    [{"id": "c10", "label": "Review 10 flashcards", "kind": "cards", "target": 10, "reward": 15},
     {"id": "c25", "label": "Review 25 flashcards", "kind": "cards", "target": 25, "reward": 30},
     {"id": "q1", "label": "Take a practice quiz", "kind": "quizzes", "target": 1, "reward": 20},
     {"id": "q80", "label": "Score 80%+ on a practice quiz", "kind": "quiz80", "target": 1, "reward": 35}],
    [{"id": "d1", "label": "Tick off a deadline or study task", "kind": "deadlines", "target": 1, "reward": 15},
     {"id": "u1", "label": "Upload a study material", "kind": "uploads", "target": 1, "reward": 15},
     {"id": "p1", "label": "Pet your wolf", "kind": "checkin", "target": 1, "reward": 10}],
]
WEEKLY_GOAL = 4  # days with a completed daily chest


def _progress(state: dict[str, Any], pet: dict[str, Any], today: date, kind: str) -> float:
    key = today.isoformat()
    if kind == "study_min":
        return tracker.daily_minutes(state).get(today, 0.0)
    if kind == "sessions":
        return sum(1 for x in state["sessions"] if x["start"].startswith(key))
    if kind == "cards":
        return _daily(pet, today)["cards"]
    if kind == "quizzes":
        return sum(1 for q in state["quizzes"] if q["taken_at"].startswith(key))
    if kind == "quiz80":
        return sum(1 for q in state["quizzes"] if q["taken_at"].startswith(key) and q["score"] >= 80)
    if kind == "deadlines":
        return _daily(pet, today)["deadlines"]
    if kind == "uploads":
        return sum(1 for m in state["materials"] if m["uploaded_at"].startswith(key))
    if kind == "checkin":
        return 1 if pet["last_checkin"] == key else 0
    return 0


def _week_start(today: date) -> str:
    return (today - timedelta(days=today.weekday())).isoformat()


def quests(state: dict[str, Any], today: date) -> dict[str, Any]:
    pet = ensure(state)
    key = today.isoformat()
    stored = pet.get("quests")
    if not stored or stored.get("date") != key:
        rng = random.Random(today.toordinal())
        stored = pet["quests"] = {"date": key, "ids": [rng.choice(pool)["id"] for pool in QUEST_POOLS],
                                  "claimed": [], "chest_opened": False}
    defs = {q["id"]: q for pool in QUEST_POOLS for q in pool}
    items = []
    for qid in stored["ids"]:
        q = defs[qid]
        done = _progress(state, pet, today, q["kind"])
        items.append({**q, "progress": min(done, q["target"]), "done": done >= q["target"], "claimed": qid in stored["claimed"]})
    week = pet["weekly"]
    if week.get("week") != _week_start(today):
        week = pet["weekly"] = {"week": _week_start(today), "days": [], "opened": False}
    return {"date": key, "items": items, "all_claimed": all(i["claimed"] for i in items),
            "chest_opened": stored["chest_opened"],
            "weekly": {"days": len(week["days"]), "goal": WEEKLY_GOAL, "claimable": len(week["days"]) >= WEEKLY_GOAL and not week["opened"],
                       "opened": week["opened"]}}


def claim_quest(state: dict[str, Any], quest_id: str, today: date) -> dict[str, Any]:
    pet = ensure(state)
    current = quests(state, today)
    item = next((i for i in current["items"] if i["id"] == quest_id), None)
    if not item:
        raise ValueError("That quest isn't active today.")
    if item["claimed"]:
        raise ValueError("Already claimed.")
    if not item["done"]:
        raise ValueError("Finish the quest first!")
    pet["quests"]["claimed"].append(quest_id)
    _log(pet, item["reward"], f"Quest: {item['label']}")
    return {"amount": item["reward"], "label": item["label"]}


def _bonus_item(pet: dict[str, Any], rng: random.Random, max_price: int) -> dict[str, Any] | None:
    pool = [i for i in CATALOG if i["id"] not in pet["owned"] and i["price"] <= max_price]
    if not pool:
        return None
    prize = rng.choice(pool)
    pet["owned"].append(prize["id"])
    return prize


def open_chest(state: dict[str, Any], today: date, rng: random.Random | None = None) -> dict[str, Any]:
    """Daily chest: unlocked when all three quests are claimed. Adds a day toward the weekly chest."""
    pet = ensure(state)
    rng = rng or random.SystemRandom()
    current = quests(state, today)
    if current["chest_opened"]:
        raise ValueError("You already opened today's chest.")
    if not current["all_claimed"]:
        raise ValueError("Claim all three quests to unlock the chest.")
    tokens = rng.choice([20, 25, 30, 35, 40, 50, 60])
    prize = _bonus_item(pet, rng, 120) if rng.random() < 0.15 else None
    pet["quests"]["chest_opened"] = True
    pet["weekly"]["days"].append(today.isoformat())
    _log(pet, tokens, "Daily chest")
    if prize:
        _log(pet, 0, f"Daily chest: {prize['name']}")
    return {"tokens": tokens, "prize": prize, "weekly_days": len(pet["weekly"]["days"])}


def open_weekly_chest(state: dict[str, Any], today: date, rng: random.Random | None = None) -> dict[str, Any]:
    pet = ensure(state)
    rng = rng or random.SystemRandom()
    current = quests(state, today)
    if not current["weekly"]["claimable"]:
        raise ValueError("Complete daily chests on 4 days this week to unlock the weekly chest.")
    tokens = rng.choice([100, 120, 150, 180, 200])
    prize = _bonus_item(pet, rng, 250) if rng.random() < 0.4 else None
    freeze = pet["freezes"] < MAX_FREEZES
    if freeze:
        pet["freezes"] += 1
    pet["weekly"]["opened"] = True
    _log(pet, tokens, "Weekly chest")
    return {"tokens": tokens, "prize": prize, "freeze": freeze}


# --------------------------------------------------------------------------- #
# Plinko
# --------------------------------------------------------------------------- #
PLINKO_ROWS = 12
PLINKO_PAYOUTS = [200, 80, 30, 20, 16, 12, 10, 12, 16, 20, 30, 80, 200]  # slot = number of right bounces (0..12)


def play_plinko(state: dict[str, Any], session_id: str, rng: random.Random | None = None,
                mega: bool = False) -> dict[str, Any]:
    """Drop a ball through 12 rows of pegs; each peg bounces it left (0) or right (1). ``mega`` forces an edge slot."""
    pet = ensure(state)
    _ticket(pet, session_id)
    rng = rng or random.SystemRandom()
    path = [rng.choice([0, 1])] * PLINKO_ROWS if mega else [rng.randint(0, 1) for _ in range(PLINKO_ROWS)]
    slot = sum(path)
    amount = PLINKO_PAYOUTS[slot]
    if "lucky" in pet["owned"]:
        amount = round(amount * 1.25)
    _log(pet, amount, "Plinko (mega mode)" if mega else "Plinko")
    return {"path": path, "slot": slot, "amount": amount, "payouts": PLINKO_PAYOUTS,
            "plays_left": _spend(pet, session_id), "tokens": pet["tokens"]}


# --------------------------------------------------------------------------- #
# Crossy Road: hop across lanes, cash out any time; a hidden car can end the run
# --------------------------------------------------------------------------- #
CROSSY_LANES = 10
CROSSY_CASH = [3, 6, 10, 15, 22, 32, 46, 66, 92, 120]  # cash value after n lanes crossed
CROSSY_HAZARD = 0.2
CROSSY_CRASH_PAYOUT = 2


def _crossy_view(pet: dict[str, Any], game: dict[str, Any]) -> dict[str, Any]:
    pos = game["pos"]
    return {"pos": pos, "lanes": CROSSY_LANES, "cash": CROSSY_CASH[pos - 1] if pos else 0, "cash_table": CROSSY_CASH,
            "plays_left": pet["tickets"].get(game["sid"], 0), "mega": game["mega"], "tokens": pet["tokens"]}


def crossy_start(state: dict[str, Any], session_id: str, rng: random.Random | None = None,
                 mega: bool = False) -> dict[str, Any]:
    """Begin a run (costs a bonus play). An unfinished run for the same session is resumed instead."""
    pet = ensure(state)
    game = pet.get("crossy")
    if game and game["sid"] == session_id:
        return _crossy_view(pet, game)
    _ticket(pet, session_id)
    rng = rng or random.SystemRandom()
    hazard = CROSSY_HAZARD * (0.85 if "lucky" in pet["owned"] else 1)
    game = pet["crossy"] = {"sid": session_id, "pos": 0, "mega": mega,
                            "hazards": [False] * CROSSY_LANES if mega else [rng.random() < hazard for _ in range(CROSSY_LANES)]}
    _spend(pet, session_id)
    return _crossy_view(pet, game)


def _crossy_end(pet: dict[str, Any], payout: int, why: str) -> None:
    game = pet["crossy"]
    pet["crossy"] = None
    _log(pet, payout, f"Crossy Road{' (mega mode)' if game['mega'] else ''}: {why}")


def crossy_hop(state: dict[str, Any], session_id: str) -> dict[str, Any]:
    pet = ensure(state)
    game = pet.get("crossy")
    if not game or game["sid"] != session_id:
        raise ValueError("Start a Crossy Road run first.")
    lane = game["pos"]
    if game["hazards"][lane]:
        _crossy_end(pet, CROSSY_CRASH_PAYOUT, "crashed")
        return {"crashed": True, "done": True, "pos": lane, "payout": CROSSY_CRASH_PAYOUT, "tokens": pet["tokens"],
                "plays_left": pet["tickets"].get(session_id, 0)}
    game["pos"] += 1
    if game["pos"] >= CROSSY_LANES:
        payout = CROSSY_CASH[-1]
        _crossy_end(pet, payout, "crossed every lane")
        return {"crashed": False, "done": True, "pos": CROSSY_LANES, "payout": payout, "tokens": pet["tokens"],
                "plays_left": pet["tickets"].get(session_id, 0)}
    return {"crashed": False, "done": False, "pos": game["pos"], "cash": CROSSY_CASH[game["pos"] - 1]}


def crossy_cashout(state: dict[str, Any], session_id: str) -> dict[str, Any]:
    pet = ensure(state)
    game = pet.get("crossy")
    if not game or game["sid"] != session_id:
        raise ValueError("No Crossy Road run in progress.")
    if game["pos"] == 0:
        raise ValueError("Hop at least once before cashing out.")
    payout = CROSSY_CASH[game["pos"] - 1]
    pos = game["pos"]
    _crossy_end(pet, payout, f"cashed out after {pos} lanes")
    return {"done": True, "pos": pos, "payout": payout, "tokens": pet["tokens"], "plays_left": pet["tickets"].get(session_id, 0)}


# --------------------------------------------------------------------------- #
# Payload
# --------------------------------------------------------------------------- #
def payload(state: dict[str, Any], today: date) -> dict[str, Any]:
    pet = ensure(state)
    apply_freeze(state, today)
    open_tickets = [{"session_id": sid, "plays_left": n} for sid, n in pet["tickets"].items()
                    if any(s["id"] == sid for s in state["sessions"]) or (pet.get("crossy") or {}).get("sid") == sid]
    pet["tickets"] = {t["session_id"]: t["plays_left"] for t in open_tickets}
    return {
        "name": pet["name"], "tokens": pet["tokens"], "owned": pet["owned"], "equipped": pet["equipped"],
        "mood": mood(state, today), "level": level_info(pet["earned"]), "checkin": checkin_preview(pet, today),
        "catalog": CATALOG + FREE_ITEMS, "upgrades": UPGRADES, "slots": SLOTS, "slot_labels": SLOT_LABELS,
        "history": list(reversed(pet["history"]))[:12], "tickets": open_tickets,
        "quests": quests(state, today), "streak_risk": streak_risk(state, today), "freezes": pet["freezes"],
        "freeze_notice": pet["last_freeze"] if pet.get("last_freeze") and pet["last_freeze"]["date"] == today.isoformat() else None,
        "consumables": CONSUMABLES,
        "crossy_active": (pet.get("crossy") or {}).get("sid"),
        "slot_symbols": [{"symbol": s, "triple": p} for s, _, p in SLOT_SYMBOLS],
        "plinko": {"rows": PLINKO_ROWS, "payouts": PLINKO_PAYOUTS},
        "roulette": [{"id": i, "label": label, "color": color} for i, label, _, color in ROULETTE],
        "roulette_layout": ROULETTE_LAYOUT,
    }
