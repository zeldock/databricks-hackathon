<p align="center"><img src="assets/wordmark.png" alt="Wolf Tracks" width="420"></p>

# Wolf Tracks — AI-Powered Student Dashboard (WolfHacks 2026)

# AI Statement: We directed AI tools to create the majority of our code

Wolf Tracks brings a student's courses, deadlines, study time and study materials into one place. It uses AI to
turn notes into summaries, flashcards and practice quizzes, and a **decision-tree model** to warn students who
may be at risk of finishing a course with a D or F, with an explanation and concrete next steps.

---

## New UI (React + FastAPI)

The front end is a fluid, green-and-black, wolf-themed React app built around the Wolf Tracks paw logo. It talks to
a FastAPI service (`api.py`) that wraps the same Python logic as before (`utils/`), so the risk model, grade
calculator, study planner and Gemini features are unchanged. The design lives in Figma:
[Wolf Tracks – UI Redesign](https://www.figma.com/design/BMPmgHj0N4HEnX2we7HVdJ) (design system + 8 screens).

**Run it (two terminals):**
```
# 1. API  (after: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt)
uvicorn api:app --port 8000

# 2. Web  (needs Node 20+)
cd web && npm install && npm run dev        # http://localhost:5173
```
Or build once and let the API serve everything on one port: `cd web && npm run build`, then `uvicorn api:app --port 8000`
and open http://localhost:8000.

The older Streamlit app (`streamlit run app.py`) still works and uses the same data file.

---

## How to run the Streamlit version (step by step)

You only need to do steps 1–4 once. After that, skip to step 5 each time.

**1. Install Python.** Download Python 3.11 or newer from [python.org](https://www.python.org/downloads/).
On Windows, tick **"Add python.exe to PATH"** on the first installer screen.

**2. Open a terminal in this folder.**
- Windows: open the project folder in File Explorer, click the address bar, type `cmd`, press Enter.
- Mac: right-click the folder in Finder → **New Terminal at Folder**.

**3. Create a private Python environment and install the app's packages** (takes 1–3 minutes):

| Windows | Mac / Linux |
|---|---|
| `python -m venv .venv` | `python3 -m venv .venv` |
| `.venv\Scripts\activate` | `source .venv/bin/activate` |
| `pip install -r requirements.txt` | `pip install -r requirements.txt` |

You'll see `(.venv)` at the start of the terminal line when the environment is active.

**4. (Optional) Turn on the AI features.** Get a free Gemini API key at
[aistudio.google.com/apikey](https://aistudio.google.com/apikey). Copy the file `.env.example`, rename the copy
to `.env`, and paste your key after `GEMINI_API_KEY=`. You can also paste the key later in the app under
**Settings**. Without a key the app still works; summaries and flashcards use a simpler offline mode.

**5. Start the app:**

```
.venv\Scripts\activate          (Mac/Linux: source .venv/bin/activate)
streamlit run app.py
```

Your browser opens at **http://localhost:8501**. If it doesn't, open that address yourself.
The first launch takes a few extra seconds while the model trains.

**6. Stop the app** by pressing **Ctrl + C** in the terminal.

---

## Your first five minutes

The app starts **empty** — it's your dashboard. The **Getting started** checklist on the Dashboard walks you through:

1. **Courses** — add the classes you're taking (type any name, or quick-add one from the WolfHacks list).
2. **Calendar** — add exams and deadlines (or let AI read them from your syllabus).
3. **Study log** — press **Start timer** when you study; it fills in your green activity grid.
   **Study plan** turns any upcoming exam into a day-by-day plan.
4. **Study materials** — upload notes or slides and generate summaries, flashcards and quizzes.

Then open **Risk check → My activity**, enter your graded work (assignments, quizzes, midterm — weight and
score from your syllabus), and you'll get your **expected final grade**, what you need on the rest of the course
for an A/B/C, and a check of whether you're heading for a **D or F**.

---

## Starting with the example files

Want to see everything working without entering data yourself? The `examples/` folder has ready-made files,
sorted into folders (full list in [`examples/README.md`](examples/README.md)):

| Folder | What's inside |
|---|---|
| `examples/dashboard_archive/` | A complete example student to import |
| `examples/student_csvs/` | Student records for testing the risk model |
| `examples/syllabi/` | Syllabus PDFs for four fictional classes — **MA 141 Calculus I**, CSC 113 Intro to Programming, ENG 101 Academic Writing, PSY 200 Intro to Psychology — with homework, quizzes, tests, projects and finals dated after today |
| `examples/course_materials/` | Lecture slides (.pptx), notes (.docx) and practice sheets (.pdf) for each fictional class |

### A full example student (recommended first)
1. Start the app and go to **Settings** (bottom of the left menu).
2. Under **Import data**, click **Upload** (or drag the file in) and choose
   `examples/dashboard_archive/example_student_archive.zip`.
3. Click **Import archive**.
4. Go to the **Dashboard** — you now have 4 courses, ~5 months of study sessions, upcoming deadlines,
   quiz results, unlocked badges, and two uploaded notes with summaries and flashcards.
5. Open **Risk check** and switch the course between BIO 181 (B), CH 101 (D), CSC 216 (F) and EC 201 (A) to see
   the grade calculator and the D/F check in each situation.

Importing **replaces** whatever is in the app (you'll be asked to confirm). To go back to an empty app, use
**Settings → Danger zone → Erase all data**.

### Set up a class from a syllabus (MA 141 Calculus I)
1. Go to **Courses** and add `MA 141`.
2. Go to **Calendar**, open **Import dates from a syllabus (AI)**, choose MA 141 and upload
   `examples/syllabi/MA141_Calculus_I_Syllabus.pdf`. Click **Find dates**.
3. The AI lists every homework set, quiz, test, project milestone and the final exam with its date. Untick
   anything you don't want and click **Add selected to calendar**.
4. Go to **Study materials**, choose MA 141 and upload the slides and notes from
   `examples/course_materials/MA141_Calculus_I/`. Generate a summary, flashcards and a practice quiz.
5. In **Risk check → My activity**, enter the grading components from the syllabus (Homework 15%, Quizzes 10%,
   Test 1 15%…) to start tracking your expected grade.

Repeat with the other three syllabi to fill your calendar for a whole semester. (Syllabus import needs a
Gemini API key.)

### Test the model on students it has never seen
1. Go to **Risk check** and choose **Upload a CSV** at the top.
2. Upload `examples/student_csvs/heldout_students.csv` — the 160 students (20%) held out from training.
3. You'll see how many are at risk, the model's accuracy / recall / ROC AUC against their **true** outcomes,
   charts, and a ranked table. Pick any student at the bottom to see why the model flagged them and what it
   suggests.

### Score a new class with no answers
Upload `examples/student_csvs/new_class_unlabeled.csv` the same way. It has no `at_risk` column, so the app predicts
risk for each student and suggests support, the way it would for a real class mid-semester.
Click **Download scored CSV** to save the results.

### Move your own data to another computer
**Settings → Export data → Prepare export → Download archive** saves everything (courses, sessions, calendar,
quizzes and uploaded files) as one `.zip`. Import it on the other computer the same way as the example.

To rebuild the example files: `python examples/make_examples.py`.

---

## What's in the app

| Menu | Page | What it does |
|---|---|---|
| Overview | **Dashboard** | Getting-started checklist, weekly/total hours, streaks, GitHub-style activity grid, weekly chart, upcoming deadlines, risk snapshot |
| Study | **Study log** | Live timer (survives refreshes), add past sessions, 30-day chart, history with multi-select delete |
| | **Calendar** | Month and week views of exams, deadlines, quizzes and milestones — click any event to mark it complete; week view also lists each day's study sessions; AI syllabus import |
| | **Study plan** | Pick an upcoming exam or quiz, then **upload the slides / notes / study guide it covers right on the page** (or pick ones you already uploaded, and type topics your instructor mentioned). Wolf Tracks finds the topics (Gemini, or slide titles and headings offline), ranks them by priority and builds a day-by-day plan: learn each topic, practice the weak and important ones, a timed rehearsal, then light review and rest. A **Next up** box tells you exactly which topic to study now; rate each topic Shaky / OK / Confident and re-plan around your weak ones. Add sessions to the calendar, start a timer, or download |
| | **Study materials** | Upload PDF / PPTX / DOCX / TXT / MD → AI summary, flip-card flashcards, scored practice quizzes |
| Insights | **Risk check** | **Grade calculator** (current average, expected final grade, score needed for each letter) plus D/F risk from the decision tree, cross-checked against each other; works from your activity, an uploaded CSV, a dataset student, or a what-if profile. Every value can be dragged **or typed** |
| | **Achievements** | 12 badges (streaks, hours, quiz scores, flashcards, deadlines…) with progress |
| | **Model insights** | Held-out accuracy, precision, recall, F1, ROC AUC vs. baseline; confusion matrix; feature importance; the tree; dataset explorer |
| Manage | **Courses** | Add, rename and remove courses (removing asks for confirmation and lists what will be deleted) |
| | **Settings** | Gemini key, export/import archives, erase all data |

### How the app feeds the model
In **Risk check → My activity**, these are shown under **From your activity** and fill themselves in; you only enter the few things under **About you** (class year, credit and work hours, attendance, sleep).

| Model feature | Where it comes from in the app |
|---|---|
| `avg_weekly_study_hours`, `study_sessions_logged` | Study log |
| `late_night_study_pct` | Share of study minutes in sessions starting 12–4 a.m. |
| `avg_days_started_before_exam` | First session for a course in the 14 days before each exam |
| `on_time_submission_rate`, `missed_deadlines` | Past calendar deadlines ticked done or not |
| `materials_uploaded`, `practice_quizzes_taken`, `avg_practice_quiz_score`, `flashcards_reviewed` | Study materials |
| `midterm_score` | Your Midterm item in the Risk check grade table |
| credit hours, work hours, attendance, sleep, class year | Entered once in **Risk check → My activity → Save my profile** |

---

## The model

`data/synthetic_students.csv` (the WolfHacks dataset) is used **only to train and test the model** — it is never
shown as your activity.

- **Split:** stratified 80% train / 20% held-out test (`utils/model.py → held_out_split`).
- **Pipeline:** median imputation with missing-value indicators (a blank quiz score means "no quizzes taken"),
  one-hot encoding for course and class year, then a `DecisionTreeClassifier`.
- **Tuning:** 5-fold cross-validated grid search over depth, leaf size, criterion and class weighting, optimizing
  **F1 on the at-risk class** (catching struggling students matters more than raw accuracy).
- **Held-out results:** ~82% accuracy (baseline 72.5%), 73% recall, ROC AUC 0.90.
- **What it learned:** midterm score matters most, followed by on-time submission rate, late-night study share,
  and how early exam prep starts.
- **From prediction to advice:** each suggestion compares the student to the median of on-track students,
  weighted by how much the tree relies on that feature.
- **Expected grade & D vs. F:** the dataset labels D and F together (final score below 70) and has no final
  scores, so the model can only estimate *D-or-F risk*. The expected letter grade — and whether it's a D (60–69)
  or an F (below 60) — comes from the student's real weighted grades (`utils/grades.py`), and the app shows
  whether the grades and the model agree. When they disagree (e.g. good habits but failing scores) the student
  is told which one needs attention.

Run `python -m utils.model` to retrain and print the metrics. The trained model is cached in
`models/risk_tree.joblib` and rebuilt automatically when the data or scikit-learn version changes.

---

## Project structure
```
api.py                     FastAPI service used by the React app
utils/pet.py               Wolf mood, tokens, shop catalog, slot machine and roulette logic
web/                       React + Vite + TypeScript front end (src/pages = one file per page, src/components/Wolf.tsx = the wolf)
app.py                     Original Streamlit UI (all pages, navigation, dialogs)
utils/model.py             Data loading, held-out split, training, joblib persistence, prediction + explanations
utils/tracker.py           Courses, sessions, streaks, achievements, calendar, archives, grid/calendar HTML
utils/ai_helper.py         PDF/PPTX/DOCX parsing; Gemini summaries, flashcards, quizzes, syllabus extraction
utils/grades.py            Grade calculator: weighted average, expected grade, score needed, D/F cross-check
data/synthetic_students.csv  WolfHacks training dataset (800 students)
examples/                  Example archive, student CSVs, fake-course syllabi and course materials (see examples/README.md)
```

## Keeping your API key out of GitHub
Your key lives only in `.env`, which `.gitignore` excludes (along with `.env.*`, `.streamlit/secrets.toml`, your
personal data in `data/user_state.json` and `data/uploads/`, and `.venv/`). Only `.env.example`, which has no key,
is committed. Optional settings for `.env`: `GEMINI_MODEL` (default `gemini-flash-latest`).

## Troubleshooting
| Problem | Fix |
|---|---|
| `python` is not recognized | Reinstall Python with **Add to PATH** ticked, then open a new terminal |
| `streamlit` is not recognized | Activate the environment first (step 5) |
| "Gemini is busy right now" | Google's servers are overloaded; wait a minute and try again |
| Port 8501 already in use | Another copy is running — close it, or run `streamlit run app.py --server.port 8502` |
