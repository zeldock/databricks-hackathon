# Example files

Ready-made files for trying every part of StudyPulse without entering your own data.
Everything here is **fictional** — "Example State University", its instructors and the example.edu addresses
don't exist.

```
examples/
├── dashboard_archive/
│   └── example_student_archive.zip      A complete example student
├── student_csvs/
│   ├── heldout_students.csv             160 students the model never trained on (with true outcomes)
│   └── new_class_unlabeled.csv          25 students without outcomes, like a real class
├── syllabi/
│   ├── MA141_Calculus_I_Syllabus.pdf
│   ├── CSC113_Intro_to_Programming_Syllabus.pdf
│   ├── ENG101_Academic_Writing_Syllabus.pdf
│   └── PSY200_Intro_to_Psychology_Syllabus.pdf
├── course_materials/
│   ├── MA141_Calculus_I/                 2 lecture decks (.pptx), notes (.docx), Test 2 review (.pdf)
│   ├── CSC113_Intro_to_Programming/      2 lecture decks, notes, Lab 6 exercises
│   ├── ENG101_Academic_Writing/          2 lecture decks, notes, research essay rubric
│   └── PSY200_Intro_to_Psychology/       2 lecture decks, notes, Exam 1 study guide
├── make_examples.py                      Regenerates everything in this folder
├── course_content.py                     The text of the fictional courses
└── course_files.py                       Turns that text into PDF / PowerPoint / Word files
```

## How to use them

| I want to… | Do this |
|---|---|
| See a fully filled-in dashboard | **Settings → Import data**, upload `dashboard_archive/example_student_archive.zip`, click **Import archive** |
| Set up a new class from its syllabus | Add the course (e.g. `MA 141`) on **Courses**, then **Calendar → Import dates from a syllabus (AI)** and upload the PDF from `syllabi/`. Review the dates it finds and click **Add selected to calendar** |
| Plan for a test | Add an exam to the calendar (or import a syllabus), open **Study plan**, upload the lecture decks from `course_materials/<course>/` under *What's on this test?* and click **Generate study plan** |
| Try AI summaries, flashcards and quizzes | **Study materials → Upload files**, choose the course and upload any file from `course_materials/<course>/` |
| Fill in the grade calculator | Open a syllabus — the **Grading** table lists each component and its weight. Enter them in **Risk check → My activity → Your grades** |
| Test the model on unseen students | **Risk check → Upload a CSV**, upload `student_csvs/heldout_students.csv` |
| Score a class with no known outcomes | **Risk check → Upload a CSV**, upload `student_csvs/new_class_unlabeled.csv` |

Syllabus import and practice quizzes need a Gemini API key (see the main README). Summaries and flashcards
also work offline.

### A quick end-to-end demo with MA 141
1. **Courses** → add `MA 141`.
2. **Calendar** → *Import dates from a syllabus (AI)* → upload `syllabi/MA141_Calculus_I_Syllabus.pdf` → it finds
   all 18 homework sets, quizzes, tests, project milestones and the final exam → **Add selected to calendar**.
3. **Study materials** → upload the two lecture decks and the notes from `course_materials/MA141_Calculus_I/` →
   generate a summary, flashcards and a practice quiz.
4. **Study log** → start a timer for MA 141.
5. **Risk check** → enter the grading components from the syllabus with a few scores to see your expected grade.

## The fictional courses

| Course | Instructor | Major work |
|---|---|---|
| **MA 141 — Calculus I** (4 cr) | Dr. Jordan Rivera | 8 homework sets, 4 quizzes, 2 tests, modeling project (proposal → draft → final), cumulative final |
| **CSC 113 — Intro to Programming in Python** (3 cr) | Prof. Alex Chen | 9 weekly labs, 2 projects, final project (proposal → prototype → final), midterm, final |
| **ENG 101 — Academic Writing and Research** (3 cr) | Dr. Morgan Ellis | 6 reading responses, rhetorical analysis essay, annotated bibliography, research essay, presentation, portfolio |
| **PSY 200 — Introduction to Psychology** (3 cr) | Dr. Taylor Brooks | 7 online quizzes, 2 exams, article analysis, group poster, cumulative final |

Each syllabus has the usual sections: course information, description, learning outcomes, required materials,
grading breakdown and scale, a week-by-week schedule, a full list of dated deadlines, and course policies.

**Dates are relative to when the files were generated.** The 10-week session starts on the Monday after
`make_examples.py` runs, so every deadline is in the future (anything that would land on Thanksgiving break is
moved earlier). To refresh the dates later, run:

```
python examples/make_examples.py
```
