"""Generate every example file in this folder.

    python examples/make_examples.py

Outputs (see examples/README.md for how to use each one)
-------
dashboard_archive/example_student_archive.zip   A full StudyPulse dashboard: ~5 months of study sessions,
                                                calendar events, quizzes, grades and two uploaded notes.
student_csvs/heldout_students.csv               The exact 20% held-out split the model never trained on.
student_csvs/new_class_unlabeled.csv            25 held-out students with the at_risk column removed.
syllabi/*.pdf                                   Syllabi for four fictional courses (MA 141 Calculus I,
                                                CSC 113, ENG 101, PSY 200) with deadlines after today.
course_materials/<course>/                      Lecture slides (.pptx), notes (.docx) and a practice sheet
                                                (.pdf) for each fictional course.
"""

from __future__ import annotations

import io
import json
import sys
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils import ai_helper, tracker  # noqa: E402
from utils import model as risk_model  # noqa: E402

import course_files  # noqa: E402  (lives next to this script)

OUT = Path(__file__).resolve().parent

SAMPLE_NOTES = {
    "BIO 181": ("bio181_cellular_respiration_notes.md", """# BIO 181 — Lecture 7: Cellular Respiration

Glycolysis occurs in the cytoplasm and converts one glucose molecule into two pyruvate, netting 2 ATP and 2 NADH.
Pyruvate oxidation takes place in the mitochondrial matrix, producing acetyl-CoA and releasing carbon dioxide.
The Krebs cycle (citric acid cycle) completes the oxidation of glucose and generates NADH, FADH2 and ATP.
Oxidative phosphorylation uses the electron transport chain on the inner mitochondrial membrane.
The electron transport chain pumps protons, and the resulting proton gradient drives ATP synthase.
Oxygen is the final electron acceptor and combines with electrons and protons to form water.
Aerobic respiration yields roughly 30 to 32 ATP per glucose molecule.
Without oxygen, cells rely on fermentation to regenerate NAD+ so that glycolysis can continue.
Lactic acid fermentation occurs in muscle cells, while alcohol fermentation occurs in yeast.
"""),
    "CH 101": ("ch101_stoichiometry_notes.md", """# CH 101 — Stoichiometry Review

A mole contains Avogadro's number of particles, about 6.022 x 10^23.
Molar mass converts between grams and moles and is found by summing atomic masses from the periodic table.
Balanced chemical equations give the mole ratios used in stoichiometry calculations.
The limiting reactant is the reactant that is completely consumed first and determines the theoretical yield.
Percent yield equals the actual yield divided by the theoretical yield, multiplied by one hundred.
Molarity is moles of solute per liter of solution and is used for solution stoichiometry.
Empirical formulas show the simplest whole-number ratio of atoms in a compound.
"""),
}


def build_archive(courses: list[str], today: date) -> bytes:
    state = tracker.default_state(courses[:4])
    tracker.seed_demo_data(state, today, courses)
    state["profile"] = {"class_year": "Sophomore", "credit_hours": 15, "work_hours_per_week": 8,
                        "attendance_rate": 0.9, "avg_sleep_hours": 7.0, "midterm_score": 74}

    # Graded work so far — one course in each grade range so the grade calculator has something to show.
    sample_scores = {courses[0]: (88, 79, 91), courses[1]: (72, 61, 70), courses[2]: (64, 52, 58),
                     courses[3]: (93, 86, 95)}
    for course, (homework, midterm, quizzes) in sample_scores.items():
        state["grades"][course] = [
            {"item": "Homework 1–5", "type": "Assignment", "weight": 20.0, "score": float(homework)},
            {"item": "Midterm exam", "type": "Midterm", "weight": 25.0, "score": float(midterm)},
            {"item": "Weekly quizzes", "type": "Quiz", "weight": 10.0, "score": float(quizzes)},
            {"item": "Final project", "type": "Project", "weight": 15.0, "score": None},
            {"item": "Final exam", "type": "Final exam", "weight": 30.0, "score": None},
        ]

    files: dict[str, bytes] = {}
    for i, (course, (name, text)) in enumerate(SAMPLE_NOTES.items()):
        material_id = tracker.new_id()
        stored = f"{material_id}_{name}"
        files[stored] = text.encode("utf-8")
        files[stored + ".txt"] = text.encode("utf-8")
        state["materials"].append({
            "id": material_id, "name": name, "course": course,
            "path": f"data/uploads/{stored}", "text_path": f"data/uploads/{stored}.txt",
            "chars": len(text), "size": len(text.encode("utf-8")), "error": None,
            "uploaded_at": (datetime.now() - timedelta(days=10 - i)).isoformat(timespec="seconds"),
            "summary": ai_helper.offline_summary(text), "summary_source": "offline",
            "flashcards": ai_helper.offline_flashcards(text, 6), "quiz": [],
        })

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(tracker.ARCHIVE_STATE_NAME, json.dumps(state, indent=2, default=str))
        for name, data in files.items():
            zf.writestr(f"uploads/{name}", data)
    return buf.getvalue()


def main() -> None:
    today = date.today()
    # Clear files from the old flat layout so only the organized folders remain.
    for old in ("example_student_archive.zip", "heldout_students.csv", "new_class_unlabeled.csv"):
        (OUT / old).unlink(missing_ok=True)

    raw = pd.read_csv(risk_model.DATA_PATH)  # keep the original "83%" formatting in exported CSVs
    clean = risk_model.load_data()
    clean[risk_model.TARGET] = clean[risk_model.TARGET].astype(int)
    _, test = risk_model.held_out_split(clean)
    heldout = raw[raw["student_id"].isin(test["student_id"])]
    csv_dir = OUT / "student_csvs"
    csv_dir.mkdir(exist_ok=True)
    heldout.to_csv(csv_dir / "heldout_students.csv", index=False)
    heldout.head(25).drop(columns=[risk_model.TARGET]).to_csv(csv_dir / "new_class_unlabeled.csv", index=False)

    archive_dir = OUT / "dashboard_archive"
    archive_dir.mkdir(exist_ok=True)
    courses = sorted(clean["course"].unique())
    (archive_dir / "example_student_archive.zip").write_bytes(build_archive(courses, today))

    written = course_files.write_all(OUT, today)
    print(f"Wrote {len(heldout)} held-out rows, 25 unlabeled rows, the dashboard archive and "
          f"{len(written)} course files:")
    for path in written:
        print("  ", path.relative_to(OUT).as_posix())


if __name__ == "__main__":
    main()
