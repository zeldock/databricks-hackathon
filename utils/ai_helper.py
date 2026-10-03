"""Document parsing and Gemini (google-genai) helpers for the Resource Hub.

Supported uploads: PDF, PPTX, DOCX, TXT and Markdown. When no Gemini API key is
configured, summaries and flashcards fall back to a simple offline extractive
approach so the hub still works during demos; quizzes require Gemini.
"""

from __future__ import annotations

import io
import json
import os
import re
import time
from collections import Counter
from datetime import date
from pathlib import Path

from pydantic import BaseModel

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
# Used when the main model stays overloaded (503) or rate-limited (429) after retries.
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-flash-lite-latest")
RETRIES = 3
SUPPORTED_TYPES = ["pdf", "pptx", "docx", "txt", "md"]
MIME_TYPES = {
    ".pdf": "application/pdf",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
}
MAX_CHARS = 150_000  # keep prompts well within the model's context window

SYSTEM_PROMPT = (
    "You are a friendly, rigorous study assistant for university students. "
    "Base everything strictly on the provided study material; do not invent facts that are not in it."
)


class Flashcard(BaseModel):
    front: str
    back: str


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    answer_index: int
    explanation: str


class SyllabusEvent(BaseModel):
    title: str
    date: str
    type: str


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
def extract_text(filename: str, data: bytes) -> str:
    """Extract plain text from an uploaded study file."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
    if ext == ".pptx":
        from pptx import Presentation

        slides = []
        for i, slide in enumerate(Presentation(io.BytesIO(data)).slides, start=1):
            texts = [shape.text_frame.text for shape in slide.shapes if shape.has_text_frame]
            if slide.has_notes_slide:
                texts.append(slide.notes_slide.notes_text_frame.text)
            slides.append(f"--- Slide {i} ---\n" + "\n".join(t for t in texts if t.strip()))
        return "\n\n".join(slides).strip()
    if ext == ".docx":
        import docx

        document = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs if p.text.strip()).strip()
    if ext in (".txt", ".md"):
        return data.decode("utf-8", errors="ignore").strip()
    raise ValueError(f"Unsupported file type: {ext}")


def mime_type(filename: str) -> str:
    return MIME_TYPES.get(Path(filename).suffix.lower(), "application/octet-stream")


# --------------------------------------------------------------------------- #
# Gemini
# --------------------------------------------------------------------------- #
def resolve_api_key(explicit: str | None = None) -> str | None:
    """Use an explicitly provided key, else GEMINI_API_KEY / GOOGLE_API_KEY from the environment."""
    return explicit or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def get_client(api_key: str | None):
    """Create a google-genai client, or return None when no key is available."""
    if not api_key:
        return None
    from google import genai

    return genai.Client(api_key=api_key)


def _contents(instruction: str, text: str, data: bytes | None, mime: str | None) -> list:
    """Build request contents: extracted text when available, else the raw PDF (e.g. scanned docs)."""
    if text.strip():
        return [f"{instruction}\n\nSTUDY MATERIAL:\n\"\"\"\n{text[:MAX_CHARS]}\n\"\"\""]
    if data and mime == "application/pdf":
        from google.genai import types

        return [types.Part.from_bytes(data=data, mime_type=mime), instruction]
    raise ValueError("No readable text was found in this document.")


def _is_transient(exc: Exception) -> bool:
    """503 overloaded / 500 server errors and 429 rate limits are worth retrying."""
    from google.genai import errors

    return isinstance(exc, errors.ServerError) or (isinstance(exc, errors.ClientError) and exc.code == 429)


def _generate(client, contents: list, model: str, schema=None, temperature: float = 0.3):
    """Call Gemini, retrying transient errors with backoff and then falling back to the lighter model."""
    from google.genai import types

    options = {
        "system_instruction": SYSTEM_PROMPT,
        "temperature": temperature,
        "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True),
    }
    if schema is not None:
        options.update(response_mime_type="application/json", response_schema=schema)
    config = types.GenerateContentConfig(**options)

    models = [model] + ([FALLBACK_MODEL] if FALLBACK_MODEL != model else [])
    last_error: Exception | None = None
    for current in models:
        for attempt in range(RETRIES):
            try:
                return client.models.generate_content(model=current, contents=contents, config=config)
            except Exception as exc:
                if not _is_transient(exc):
                    raise
                last_error = exc
                time.sleep(1.5 * 2 ** attempt)
    raise RuntimeError(f"Gemini is busy right now — please try again in a minute. ({last_error})")


def _parse_list(response, item_model: type[BaseModel]) -> list[dict]:
    parsed = getattr(response, "parsed", None)
    if parsed:
        return [p.model_dump() if isinstance(p, BaseModel) else dict(p) for p in parsed]
    raw = json.loads(response.text)
    return [item_model.model_validate(item).model_dump() for item in raw]


def summarize(client, text: str, *, data: bytes | None = None, mime: str | None = None,
              model: str = DEFAULT_MODEL) -> str:
    """Markdown summary: overview, key concepts, and likely exam topics."""
    instruction = (
        "Summarize this study material for exam review. Use Markdown with these sections:\n"
        "### Overview (2-3 sentences)\n### Key Concepts (bullets, bold each term, one-line explanation)\n"
        "### Formulas & Definitions (only if present)\n### Likely Exam Topics (3-5 bullets)"
    )
    return _generate(client, _contents(instruction, text, data, mime), model).text


def generate_flashcards(client, text: str, n: int = 10, *, data: bytes | None = None,
                        mime: str | None = None, model: str = DEFAULT_MODEL) -> list[dict]:
    instruction = (
        f"Create exactly {n} flashcards covering the most important ideas. "
        "The front is a concise question or term; the back is a short, precise answer (max 2 sentences)."
    )
    response = _generate(client, _contents(instruction, text, data, mime), model,
                         schema=list[Flashcard], temperature=0.4)
    return _parse_list(response, Flashcard)[:n]


def generate_quiz(client, text: str, n: int = 5, *, data: bytes | None = None,
                  mime: str | None = None, model: str = DEFAULT_MODEL) -> list[dict]:
    instruction = (
        f"Write exactly {n} multiple-choice practice questions that test understanding, not just recall. "
        "Each question has exactly 4 options, one correct answer (answer_index is 0-based), "
        "plausible distractors, and a one-sentence explanation of why the answer is correct."
    )
    response = _generate(client, _contents(instruction, text, data, mime), model,
                         schema=list[QuizQuestion], temperature=0.5)
    questions = []
    for q in _parse_list(response, QuizQuestion):
        if len(q["options"]) >= 2 and 0 <= q["answer_index"] < len(q["options"]):
            questions.append(q)
    return questions[:n]


class PlanDay(BaseModel):
    date: str
    focus: str
    tasks: list[str]


def generate_plan_details(client, course: str, test_title: str, test_date: date, days: list[dict],
                          material_text: str, model: str = DEFAULT_MODEL) -> list[dict]:
    """Course-specific focus and tasks for each day of an existing study plan schedule."""
    schedule = "\n".join(
        f"- {d['date']}: {d['minutes']} minutes, phase: {d.get('phase', d['focus'])}"
        + (f", topics: {', '.join(d['topics'])}" if d.get("topics") else "") for d in days)
    instruction = (
        f"A student in {course} has “{test_title}” on {test_date.isoformat()}. Their study schedule is fixed:\n"
        f"{schedule}\n\n"
        "For EACH date above, return a short focus (the topic to study, taken from the course material) and 2–4 "
        "concrete tasks that fit the minutes and phase. Early days rebuild understanding, middle days use active "
        "practice (problems, flashcards, practice quizzes), the second-to-last day is a timed practice test, and "
        "the last day is light review and sleep. When a day lists topics, its focus and tasks must cover exactly "
        "those topics, naming the specific ideas, formulas or examples from the material to work on. Otherwise "
        "cover the material's main topics across the days. Use the exact dates given."
    )
    response = _generate(client, _contents(instruction, material_text, None, None), model,
                         schema=list[PlanDay], temperature=0.4)
    return _parse_list(response, PlanDay)


class TestTopic(BaseModel):
    name: str
    summary: str
    importance: str
    source: str


def extract_test_topics(client, course: str, test_title: str, materials: list[tuple[str, str]], note: str = "",
                        max_topics: int = 10, model: str = DEFAULT_MODEL) -> list[dict]:
    """The main topics a test covers, from the files the student says are on it."""
    per_file = max(4000, MAX_CHARS // max(1, len(materials)))
    corpus = "\n\n".join(f"=== FILE: {name} ===\n{text[:per_file]}" for name, text in materials)
    instruction = (
        f"These files are what will be on “{test_title}” in {course}."
        + (f" The student also noted: {note}." if note.strip() else "")
        + f" List the {max_topics} or fewer most important topics to study, in the order they should be learned "
        "(foundations first). For each give: name (2–6 words), summary (one sentence on what to know), importance "
        "(high, medium or low — rank them: high for the student's noted topics and the few core ideas everything "
        "else builds on, at most about a third of the list; medium for standard topics; low for minor details) and source (the file name it comes from)."
    )
    response = _generate(client, _contents(instruction, corpus or note, None, None), model,
                         schema=list[TestTopic], temperature=0.2)
    return _parse_list(response, TestTopic)


def extract_syllabus_events(client, text: str, course: str, year: int, *, data: bytes | None = None,
                            mime: str | None = None, model: str = DEFAULT_MODEL) -> list[dict]:
    """Pull dated exams, deadlines, quizzes and milestones out of a course syllabus."""
    instruction = (
        f"Extract every dated exam, assignment deadline, quiz, and project milestone from this syllabus for "
        f"{course}. Give each a short title, its date as YYYY-MM-DD (assume the year is {year} when it is not "
        "stated), and a type that is exactly one of: Exam, Deadline, Quiz, Milestone. "
        "Skip anything without a specific calendar date."
    )
    response = _generate(client, _contents(instruction, text, data, mime), model,
                         schema=list[SyllabusEvent], temperature=0.1)
    events = []
    for item in _parse_list(response, SyllabusEvent):
        try:
            when = date.fromisoformat(item["date"])
        except ValueError:
            continue
        kind = item["type"] if item["type"] in ("Exam", "Deadline", "Quiz", "Milestone") else "Milestone"
        events.append({"title": item["title"], "date": when, "type": kind})
    return sorted(events, key=lambda e: e["date"])


# --------------------------------------------------------------------------- #
# Offline fallbacks (no API key)
# --------------------------------------------------------------------------- #
_STOPWORDS = set(
    "a an the and or but if then else of to in on for with by from as at is are was were be been being "
    "this that these those it its into than so such can could would should will may might must do does did "
    "not no yes we you they he she i our your their his her them us which who whom what when where why how "
    "also more most other some any each all both few many much very just only over under between about".split()
)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n{2,}", re.sub(r"[ \t]+", " ", text))
    return list(dict.fromkeys(p.strip() for p in parts if 40 <= len(p.strip()) <= 400))  # dedupe, keep order


def _word_scores(text: str) -> Counter:
    words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text.lower())
    return Counter(w for w in words if w not in _STOPWORDS)


def offline_summary(text: str, n_sentences: int = 7) -> str:
    """Extractive summary: the highest-scoring sentences, kept in original order."""
    sentences = _sentences(text)
    if not sentences:
        return "_Not enough text to summarize._"
    freq = _word_scores(text)
    scored = sorted(
        range(len(sentences)),
        key=lambda i: -sum(freq[w] for w in re.findall(r"[a-z\-]{3,}", sentences[i].lower()))
        / (len(sentences[i].split()) ** 0.5),
    )[:n_sentences]
    top_terms = ", ".join(f"**{w}**" for w, _ in freq.most_common(8))
    bullets = "\n".join(f"- {sentences[i]}" for i in sorted(scored))
    return f"### Key Points (offline summary)\n{bullets}\n\n### Frequent Terms\n{top_terms}"


def offline_flashcards(text: str, n: int = 10) -> list[dict]:
    """Fill-in-the-blank cards: hide a high-frequency term in its most informative sentences."""
    freq = _word_scores(text)
    key_terms = [w for w, _ in freq.most_common(40) if len(w) > 4]
    cards, used = [], set()
    for sentence in _sentences(text):
        for term in key_terms:
            if term in used:
                continue
            pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            if pattern.search(sentence):
                cards.append({"front": pattern.sub("_____", sentence, count=1), "back": term})
                used.add(term)
                break
        if len(cards) >= n:
            break
    return cards
