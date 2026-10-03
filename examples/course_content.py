"""Content for the fictional example courses (syllabi, lecture slides, notes and practice sheets).

Everything here is invented for demos: "Example State University", the instructors and the example.edu
addresses are not real. Deliverables are given as (week, weekday, title, type) and turned into real dates
by make_examples.py, always starting after the day the script runs.

Weekday numbers: 0 = Monday ... 6 = Sunday. Weeks are 1-based within a 10-week session.
"""

UNIVERSITY = "Example State University"
TERM_NAME = "Fall 2026 · Second Session (10 weeks)"

COMMON_POLICIES = [
    ("Academic integrity",
     "All work you submit must be your own. You may discuss ideas with classmates, but written work, code and "
     "solutions must be produced individually unless an assignment says otherwise. Using AI tools to generate "
     "submitted work is not allowed unless the assignment explicitly permits it; when it is permitted, you must "
     "say how you used it. Suspected violations are reported to the Office of Student Conduct."),
    ("Accessibility",
     "Students who need accommodations should contact Disability Resources as early as possible and share their "
     "accommodation letter with the instructor. All course materials are available in accessible formats on request."),
    ("Attendance",
     "Regular attendance is expected and strongly linked to success in this course. If you must miss class, review "
     "the posted slides and notes and contact a classmate or the instructor. Absences for illness, religious "
     "observance or university-sanctioned events are excused with notice."),
    ("Communication",
     "Course announcements are posted on the course website. Email the instructor from your university account and "
     "include the course code in the subject line; expect a reply within one business day."),
    ("Wellness",
     "Your health matters more than any deadline. If you are struggling, reach out early — the Counseling Center, "
     "Academic Success Center and your academic advisor are all free resources."),
]

SUPPORT = [
    "Academic Success Center — free tutoring and study-skills coaching, drop-in or by appointment",
    "Writing Center — one-on-one help at any stage of a writing project",
    "Counseling Center — confidential support for stress, anxiety and other concerns",
    "Library Research Help — chat, email or in-person help finding and citing sources",
]

GRADE_SCALE = "A 90–100 · B 80–89 · C 70–79 · D 60–69 · F below 60"

COURSES = [
    # ------------------------------------------------------------------------------------------------- MA 141
    {
        "code": "MA 141",
        "title": "Calculus I",
        "slug": "MA141_Calculus_I",
        "credits": 4,
        "instructor": "Dr. Jordan Rivera",
        "email": "jrivera@example.edu",
        "office": "Mathematics Building 312",
        "office_hours": "Mondays and Wednesdays 2:00–3:30 PM, Fridays 9:00–10:00 AM, or by appointment",
        "meets": "Mon / Wed / Fri 10:40–11:30 AM (lecture) and Tue 1:30–2:20 PM (recitation), Science Hall 1102",
        "ta": "Priya Natarajan (pnatarajan@example.edu) — recitation and homework questions",
        "description": (
            "An introduction to differential calculus. Topics include limits and continuity, the derivative and "
            "its interpretations, differentiation rules, related rates, linear approximation, extreme values, the "
            "Mean Value Theorem, curve sketching, optimization and an introduction to antiderivatives. The course "
            "emphasizes both computation and understanding: you will explain why results are true, not just apply "
            "formulas."),
        "prereq": "MA 107 or a placement score qualifying for calculus.",
        "outcomes": [
            "Evaluate limits graphically, numerically and algebraically, and use them to determine continuity.",
            "Compute derivatives using the limit definition and the standard differentiation rules.",
            "Interpret the derivative as a rate of change and as the slope of a tangent line.",
            "Solve related-rates and optimization problems drawn from science, engineering and economics.",
            "Use the first and second derivative to analyze and sketch the graph of a function.",
            "Communicate mathematical reasoning clearly in writing.",
        ],
        "materials": [
            "Calculus: Early Transcendentals (OpenStax Calculus Volume 1, free online)",
            "A scientific calculator (graphing calculators are not allowed on tests)",
            "Access to the online homework system (link on the course website)",
        ],
        "grading": [
            ("Homework (8 sets, lowest dropped)", 15),
            ("Quizzes (4)", 10),
            ("Test 1", 15),
            ("Test 2", 15),
            ("Modeling project", 15),
            ("Final exam (cumulative)", 25),
            ("Recitation participation", 5),
        ],
        "topics": [
            "Functions review; the idea of a limit",
            "Limit laws, one-sided limits and continuity",
            "Squeeze Theorem, Intermediate Value Theorem, limits at infinity",
            "The derivative as a limit; Test 1",
            "Power, product and quotient rules; derivatives of trig functions",
            "Chain rule and implicit differentiation",
            "Related rates and linear approximation",
            "Extreme values and the Mean Value Theorem; Test 2",
            "Curve sketching, optimization and L'Hôpital's Rule",
            "Antiderivatives; review; final exam",
        ],
        "deliverables": [
            (1, 3, "Homework 1 (Functions and limits)", "Deadline"),
            (2, 2, "Quiz 1 (Limits)", "Quiz"),
            (2, 3, "Homework 2 (Limit laws and continuity)", "Deadline"),
            (3, 3, "Homework 3 (Squeeze Theorem and IVT)", "Deadline"),
            (3, 4, "Project proposal due", "Milestone"),
            (4, 3, "Homework 4 (Definition of the derivative)", "Deadline"),
            (4, 4, "Test 1 (Limits and continuity)", "Exam"),
            (5, 2, "Quiz 2 (Differentiation rules)", "Quiz"),
            (5, 3, "Homework 5 (Product and quotient rules)", "Deadline"),
            (6, 3, "Homework 6 (Chain rule and implicit differentiation)", "Deadline"),
            (6, 4, "Project draft due", "Milestone"),
            (7, 2, "Quiz 3 (Related rates)", "Quiz"),
            (7, 3, "Homework 7 (Related rates and linearization)", "Deadline"),
            (8, 3, "Homework 8 (Extrema and MVT)", "Deadline"),
            (8, 4, "Test 2 (Derivatives and applications)", "Exam"),
            (9, 2, "Quiz 4 (Optimization)", "Quiz"),
            (9, 4, "Final modeling project due", "Deadline"),
            (10, 2, "Final exam (cumulative)", "Exam"),
        ],
        "late_policy": (
            "Homework is accepted up to 48 hours late for 80% credit; your lowest homework score is dropped. Quizzes "
            "and tests cannot be made up without documentation, but your final exam score can replace your lowest "
            "test score if it is higher."),
        "project": (
            "Modeling project — “Calculus in the Real World.” In groups of three, choose a real situation (a rocket "
            "launch, a medicine dose, a business's profit) and model it with a function. Use derivatives to find "
            "rates of change and an optimal value, and explain what your answer means in context. Deliverables: a "
            "one-page proposal, a draft for feedback and a 4–6 page final report."),
        "slides": [
            {
                "file": "Lecture_03_Limits_and_Continuity.pptx",
                "title": "Limits and Continuity",
                "subtitle": "MA 141 · Lecture 3",
                "slides": [
                    ("What is a limit?", [
                        "lim x→a f(x) = L means f(x) gets arbitrarily close to L as x approaches a",
                        "The value f(a) itself does not matter — it may not even exist",
                        "Example: f(x) = (x² − 1)/(x − 1) is undefined at x = 1, but its limit there is 2",
                    ]),
                    ("One-sided limits", [
                        "Left-hand limit: x → a⁻;  right-hand limit: x → a⁺",
                        "The two-sided limit exists only if both one-sided limits exist and are equal",
                        "Piecewise functions and |x|/x are the classic examples where they differ",
                    ]),
                    ("Limit laws", [
                        "Limits of sums, differences, products and constant multiples split apart",
                        "Quotient law works when the limit of the denominator is not 0",
                        "0/0? Factor, rationalize or simplify first — then substitute",
                    ]),
                    ("The Squeeze Theorem", [
                        "If g(x) ≤ f(x) ≤ h(x) near a and g and h both approach L, then f does too",
                        "Classic result: lim x→0 sin(x)/x = 1",
                        "Also used for x² sin(1/x) → 0 as x → 0",
                    ]),
                    ("Continuity", [
                        "f is continuous at a if f(a) is defined, the limit exists, and they are equal",
                        "Types of discontinuity: removable, jump and infinite",
                        "Polynomials, rational functions (on their domains), sin and cos are continuous",
                    ]),
                    ("Intermediate Value Theorem", [
                        "If f is continuous on [a, b] and N is between f(a) and f(b), some c in (a, b) has f(c) = N",
                        "Use it to prove an equation has a root: show the sign of f changes",
                        "Example: x³ + x − 1 = 0 has a root between 0 and 1",
                    ]),
                    ("Check your understanding", [
                        "Find lim x→3 (x² − 9)/(x − 3)",
                        "Is f(x) = (x² − 4)/(x − 2) continuous at x = 2? What kind of discontinuity?",
                        "Show that cos x = x has a solution in [0, π/2]",
                    ]),
                ],
            },
            {
                "file": "Lecture_06_Derivative_Rules.pptx",
                "title": "Differentiation Rules",
                "subtitle": "MA 141 · Lecture 6",
                "slides": [
                    ("The derivative", [
                        "f′(x) = lim h→0 [f(x + h) − f(x)] / h",
                        "Slope of the tangent line and instantaneous rate of change",
                        "Differentiable ⇒ continuous (but not the other way around: |x| at 0)",
                    ]),
                    ("Basic rules", [
                        "Constant: d/dx[c] = 0;  power rule: d/dx[xⁿ] = n·xⁿ⁻¹",
                        "Sum and constant-multiple rules let you differentiate term by term",
                        "d/dx[eˣ] = eˣ and d/dx[ln x] = 1/x",
                    ]),
                    ("Product and quotient rules", [
                        "(fg)′ = f′g + fg′",
                        "(f/g)′ = (f′g − fg′) / g²",
                        "Example: d/dx[x² sin x] = 2x sin x + x² cos x",
                    ]),
                    ("Trigonometric derivatives", [
                        "d/dx[sin x] = cos x,  d/dx[cos x] = −sin x",
                        "d/dx[tan x] = sec² x,  d/dx[sec x] = sec x tan x",
                        "All follow from lim sin(h)/h = 1 and the quotient rule",
                    ]),
                    ("The chain rule", [
                        "d/dx[f(g(x))] = f′(g(x)) · g′(x) — outside derivative times inside derivative",
                        "Example: d/dx[(3x² + 1)⁵] = 5(3x² + 1)⁴ · 6x",
                        "Example: d/dx[sin(x³)] = cos(x³) · 3x²",
                    ]),
                    ("Implicit differentiation", [
                        "Differentiate both sides with respect to x, treating y as a function of x",
                        "Circle x² + y² = 25:  2x + 2y·y′ = 0  ⇒  y′ = −x/y",
                        "Slope of the tangent at (3, 4) is −3/4",
                    ]),
                    ("Practice", [
                        "Differentiate f(x) = x³ − 4x + 7",
                        "Differentiate g(x) = eˣ / (x² + 1)",
                        "Find dy/dx if xy + y² = 6",
                    ]),
                ],
            },
        ],
        "notes": {
            "file": "Notes_Applications_of_the_Derivative.docx",
            "title": "MA 141 — Notes: Applications of the Derivative",
            "sections": [
                ("Related rates", [
                    "Related-rates problems connect the rates of change of two or more quantities that are linked by "
                    "an equation. Differentiate the equation with respect to time t, then substitute the known values.",
                    "• Draw a picture and label the quantities that change.",
                    "• Write an equation relating them (Pythagorean theorem, area, volume, similar triangles).",
                    "• Differentiate with respect to t using the chain rule, then plug in numbers last.",
                    "Example: a 10 ft ladder slides down a wall. When the bottom is 6 ft from the wall and moving away "
                    "at 2 ft/s, x² + y² = 100 gives 2x·dx/dt + 2y·dy/dt = 0, so dy/dt = −(6·2)/8 = −1.5 ft/s.",
                ]),
                ("Extreme values", [
                    "A critical number of f is a value c where f′(c) = 0 or f′(c) does not exist.",
                    "Closed Interval Method: on [a, b], evaluate f at the critical numbers and at the endpoints; the "
                    "largest value is the absolute maximum and the smallest is the absolute minimum.",
                ]),
                ("The Mean Value Theorem", [
                    "If f is continuous on [a, b] and differentiable on (a, b), there is a c in (a, b) with "
                    "f′(c) = [f(b) − f(a)] / (b − a). Some instant matches the average rate of change.",
                    "Consequence: if f′(x) = 0 on an interval, f is constant there.",
                ]),
                ("First and second derivative tests", [
                    "• f′ > 0 ⇒ increasing; f′ < 0 ⇒ decreasing. A sign change of f′ at c gives a local extremum.",
                    "• f″ > 0 ⇒ concave up; f″ < 0 ⇒ concave down. A sign change of f″ is an inflection point.",
                    "• Second derivative test: if f′(c) = 0 and f″(c) > 0, f has a local minimum at c.",
                ]),
                ("Optimization", [
                    "1. Identify the quantity to maximize or minimize and write it as a function of one variable.",
                    "2. Use the constraint to eliminate extra variables and find the domain.",
                    "3. Find critical numbers and test them (Closed Interval Method or the first derivative test).",
                    "4. Answer the question in context, with units.",
                    "Example: the rectangle of perimeter 40 with the largest area is a 10 × 10 square.",
                ]),
                ("L'Hôpital's Rule", [
                    "For limits of the form 0/0 or ∞/∞: lim f(x)/g(x) = lim f′(x)/g′(x), if the right side exists.",
                    "Example: lim x→0 (1 − cos x)/x² = lim sin x/(2x) = 1/2.",
                ]),
            ],
        },
        "practice": {
            "file": "Practice_Test_2_Review.pdf",
            "title": "MA 141 — Test 2 Review Problems",
            "intro": "Work these without a calculator. Answers are at the end — try each problem before checking.",
            "items": [
                "Differentiate f(x) = (2x + 1)⁴ · cos x.",
                "Find the equation of the tangent line to y = √x at x = 9.",
                "A spherical balloon is inflated at 100 cm³/s. How fast is the radius increasing when r = 5 cm?",
                "Find the absolute extrema of f(x) = x³ − 3x² + 1 on [−1, 3].",
                "Verify the Mean Value Theorem for f(x) = x² on [1, 3] and find c.",
                "A farmer has 600 m of fence to enclose a rectangle along a river (no fence on the river side). "
                "What dimensions maximize the area?",
                "Evaluate lim x→0 (eˣ − 1 − x)/x².",
            ],
            "answers": [
                "8(2x + 1)³ cos x − (2x + 1)⁴ sin x",
                "y = (1/6)x + 3/2",
                "dr/dt = 1/π ≈ 0.318 cm/s",
                "Maximum 1 at x = 0 and x = 3; minimum −3 at x = −1 and x = 2",
                "c = 2",
                "150 m × 300 m (300 m side parallel to the river), area 45,000 m²",
                "1/2",
            ],
        },
    },
    # ------------------------------------------------------------------------------------------------- CSC 113
    {
        "code": "CSC 113",
        "title": "Introduction to Programming in Python",
        "slug": "CSC113_Intro_to_Programming",
        "credits": 3,
        "instructor": "Prof. Alex Chen",
        "email": "achen@example.edu",
        "office": "Engineering Building II, Room 2240",
        "office_hours": "Tuesdays 3:00–5:00 PM and Thursdays 10:00–11:00 AM; virtual hours Sunday 7:00–8:00 PM",
        "meets": "Tue / Thu 11:45 AM–1:00 PM (lecture), Fri 9:00–10:50 AM (lab), Engineering Building II 1011",
        "ta": "Marcus Lee and Sofia Alvarez — lab support and code reviews",
        "description": (
            "A first course in programming for students with no prior experience. You will learn to solve problems "
            "by writing clear, well-tested Python programs: variables and expressions, decisions, loops, functions, "
            "lists and dictionaries, files, exceptions and an introduction to classes. Weekly labs give hands-on "
            "practice, and three projects build toward a program of your own design."),
        "prereq": "None. Comfort with high-school algebra is helpful.",
        "outcomes": [
            "Break a problem into steps and express them as an algorithm.",
            "Write, run and debug Python programs that use conditionals, loops and functions.",
            "Choose appropriate data structures (lists, tuples, dictionaries, sets) for a task.",
            "Read and write files and handle errors with exceptions.",
            "Test programs systematically and write readable, documented code.",
        ],
        "materials": [
            "Think Python, 3rd edition, by Allen B. Downey (free online)",
            "A laptop with Python 3.12+ and VS Code installed (setup guide on the course website)",
            "A free GitHub account for submitting projects",
        ],
        "grading": [
            ("Weekly labs (9, lowest dropped)", 20),
            ("Project 1: Text adventure", 10),
            ("Project 2: Data analyzer", 10),
            ("Final project", 20),
            ("Midterm exam", 15),
            ("Final exam", 20),
            ("Participation", 5),
        ],
        "topics": [
            "What is programming? Variables, types and expressions",
            "Strings, input and output",
            "Booleans and conditional statements",
            "Loops: while and for; Project 1 due",
            "Functions, parameters and return values; midterm",
            "Lists, tuples and common list algorithms",
            "Dictionaries and sets; Project 2 due",
            "Files and exceptions",
            "Introduction to classes and objects; final project due",
            "Review and final exam",
        ],
        "deliverables": [
            (1, 1, "Lab 1 (Hello, Python)", "Deadline"),
            (2, 1, "Lab 2 (Strings and formatting)", "Deadline"),
            (3, 1, "Lab 3 (Decisions)", "Deadline"),
            (4, 1, "Lab 4 (Loops)", "Deadline"),
            (4, 4, "Project 1: Text adventure", "Deadline"),
            (5, 1, "Lab 5 (Functions)", "Deadline"),
            (5, 3, "Midterm exam", "Exam"),
            (6, 1, "Lab 6 (Lists)", "Deadline"),
            (6, 3, "Final project proposal", "Milestone"),
            (7, 1, "Lab 7 (Dictionaries)", "Deadline"),
            (7, 4, "Project 2: Data analyzer", "Deadline"),
            (8, 1, "Lab 8 (Files and exceptions)", "Deadline"),
            (8, 4, "Final project checkpoint (working prototype)", "Milestone"),
            (9, 1, "Lab 9 (Classes)", "Deadline"),
            (9, 4, "Final project due", "Deadline"),
            (10, 1, "Final exam", "Exam"),
        ],
        "late_policy": (
            "Labs and projects lose 10% per day late, up to 3 days. You have three “grace days” for the semester that "
            "waive the penalty — no explanation needed. Exams cannot be made up without documentation."),
        "project": (
            "Final project — design and build a Python program of your choice (a game, a budgeting tool, a data "
            "visualizer). It must use functions, at least one dictionary or class, file input/output and error "
            "handling. Deliverables: a proposal, a working prototype checkpoint and the final code with a README."),
        "slides": [
            {
                "file": "Lecture_03_Conditionals.pptx",
                "title": "Making Decisions",
                "subtitle": "CSC 113 · Lecture 3",
                "slides": [
                    ("Booleans", [
                        "A bool is either True or False",
                        "Comparison operators: ==, !=, <, <=, >, >=",
                        "Logical operators: and, or, not  (e.g. 0 <= score and score <= 100)",
                    ]),
                    ("if / elif / else", [
                        "if condition:  — runs the indented block only when the condition is True",
                        "elif checks another condition; else runs when nothing above matched",
                        "Only the first matching branch runs",
                    ]),
                    ("Example: letter grades", [
                        "if score >= 90: grade = 'A'",
                        "elif score >= 80: grade = 'B'",
                        "elif score >= 70: grade = 'C'  …  else: grade = 'F'",
                        "Order matters — test the highest cutoff first",
                    ]),
                    ("Common mistakes", [
                        "= assigns, == compares",
                        "Indentation defines the block — be consistent (4 spaces)",
                        "Comparing floats with == can fail: use abs(a - b) < 1e-9",
                    ]),
                    ("Try it", [
                        "Write a program that reads a year and prints whether it is a leap year",
                        "Rule: divisible by 4, except centuries, unless divisible by 400",
                        "Test with 1900, 2000, 2024 and 2026",
                    ]),
                ],
            },
            {
                "file": "Lecture_06_Lists.pptx",
                "title": "Working with Lists",
                "subtitle": "CSC 113 · Lecture 6",
                "slides": [
                    ("What is a list?", [
                        "An ordered, changeable collection: scores = [88, 92, 75]",
                        "Index from 0: scores[0] is 88; scores[-1] is the last item",
                        "len(scores) gives the number of items",
                    ]),
                    ("Changing lists", [
                        "append(x) adds to the end; insert(i, x) adds at position i",
                        "remove(x) deletes the first match; pop() removes and returns the last item",
                        "Lists are mutable — two names can refer to the same list",
                    ]),
                    ("Looping over lists", [
                        "for score in scores:  — visit every item",
                        "for i, score in enumerate(scores):  — get the index too",
                        "Accumulator pattern: total = 0, then total += score",
                    ]),
                    ("Slicing and useful functions", [
                        "scores[1:3] gives items 1 and 2; scores[::-1] reverses",
                        "sum(), min(), max(), sorted() and the in operator",
                        "List comprehension: [s * 1.1 for s in scores if s < 90]",
                    ]),
                    ("Practice", [
                        "Write average(nums) that returns the mean of a list (handle the empty list!)",
                        "Write count_above(nums, cutoff)",
                        "Remove duplicates from a list while keeping the original order",
                    ]),
                ],
            },
        ],
        "notes": {
            "file": "Notes_Functions_and_Testing.docx",
            "title": "CSC 113 — Notes: Functions and Testing",
            "sections": [
                ("Why functions?", [
                    "A function packages a piece of logic under a name so you can reuse it, test it on its own and "
                    "read your program at a higher level. Good functions do one thing and have a descriptive name.",
                ]),
                ("Defining and calling", [
                    "def area(width, height):\n    return width * height",
                    "• Parameters are the names in the definition; arguments are the values passed in a call.",
                    "• return sends a value back to the caller. A function with no return gives back None.",
                    "• Variables created inside a function are local — they disappear when it returns.",
                ]),
                ("Docstrings", [
                    "Put a short description on the first line of the function body in triple quotes. It explains "
                    "what the function does, what it expects and what it returns; help(area) will display it.",
                ]),
                ("Testing your functions", [
                    "Test normal cases, edge cases (empty input, zero, negative numbers) and invalid input.",
                    "assert area(3, 4) == 12 stops the program with an error if the result is wrong.",
                    "Write tests before or alongside the function — it forces you to decide what “correct” means.",
                ]),
                ("Debugging checklist", [
                    "• Read the whole error message, especially the last line and the line number.",
                    "• Print intermediate values or use the VS Code debugger to step through the code.",
                    "• Reproduce the bug with the smallest input you can, then fix one thing at a time.",
                ]),
            ],
        },
        "practice": {
            "file": "Lab_06_Lists_Exercises.pdf",
            "title": "CSC 113 — Lab 6: List Exercises",
            "intro": "Complete each function in lab6.py. Run the provided tests with: python -m pytest test_lab6.py",
            "items": [
                "average(nums): return the mean of a list of numbers, or 0 for an empty list.",
                "count_above(nums, cutoff): return how many values are strictly greater than cutoff.",
                "second_largest(nums): return the second-largest distinct value, or None if there isn't one.",
                "dedupe(items): return a new list with duplicates removed, keeping the original order.",
                "rotate(items, k): return the list rotated right by k positions (k may exceed the length).",
                "Challenge: running_totals(nums) returns the list of cumulative sums.",
            ],
            "answers": [
                "sum(nums) / len(nums) if nums else 0",
                "sum(1 for n in nums if n > cutoff)",
                "Sort the set of values; return the second-to-last if there are at least two",
                "Track seen values in a set and append unseen items to a result list",
                "k %= len(items); return items[-k:] + items[:-k] (handle the empty list)",
                "Keep a running total and append it after adding each number",
            ],
        },
    },
    # ------------------------------------------------------------------------------------------------- ENG 101
    {
        "code": "ENG 101",
        "title": "Academic Writing and Research",
        "slug": "ENG101_Academic_Writing",
        "credits": 3,
        "instructor": "Dr. Morgan Ellis",
        "email": "mellis@example.edu",
        "office": "Humanities Hall 207",
        "office_hours": "Mondays 1:00–3:00 PM and Thursdays 11:00 AM–12:00 PM, or by appointment",
        "meets": "Mon / Wed / Fri 9:35–10:25 AM, Humanities Hall 120",
        "ta": None,
        "description": (
            "A workshop course in reading, writing and research for academic audiences. You will analyze how texts "
            "persuade, develop arguable claims, find and evaluate sources, integrate evidence ethically and revise "
            "your work through peer feedback. The course culminates in a researched argument and a portfolio that "
            "reflects on your growth as a writer."),
        "prereq": "None.",
        "outcomes": [
            "Analyze the rhetorical situation of a text: audience, purpose, context and appeals.",
            "Write a focused, arguable thesis and support it with well-organized evidence.",
            "Locate, evaluate and responsibly integrate scholarly and popular sources.",
            "Cite sources correctly in MLA style.",
            "Revise drafts in response to peer and instructor feedback.",
        ],
        "materials": [
            "They Say / I Say, 5th edition, by Gerald Graff and Cathy Birkenstein",
            "Readings posted on the course website",
            "A notebook for in-class writing",
        ],
        "grading": [
            ("Reading responses (6)", 15),
            ("Essay 1: Rhetorical analysis", 15),
            ("Annotated bibliography", 10),
            ("Research essay", 25),
            ("Research presentation", 10),
            ("Final portfolio and reflection", 15),
            ("Participation and peer review", 10),
        ],
        "topics": [
            "The rhetorical situation; ethos, pathos and logos",
            "Reading critically and annotating",
            "From topic to thesis: making an arguable claim",
            "Paragraphs and evidence; Essay 1 due",
            "Finding and evaluating sources",
            "Integrating sources: quoting, paraphrasing and MLA citation",
            "Counterarguments and concessions",
            "Revision and peer review workshop",
            "Presenting research; research essay due",
            "Portfolio and reflection",
        ],
        "deliverables": [
            (2, 0, "Reading response 1", "Deadline"),
            (3, 0, "Reading response 2", "Deadline"),
            (3, 4, "Essay 1 draft (peer review)", "Milestone"),
            (4, 0, "Reading response 3", "Deadline"),
            (4, 4, "Essay 1: Rhetorical analysis (final)", "Deadline"),
            (5, 0, "Reading response 4", "Deadline"),
            (6, 0, "Reading response 5", "Deadline"),
            (6, 4, "Annotated bibliography", "Deadline"),
            (7, 0, "Reading response 6", "Deadline"),
            (8, 2, "Research essay draft (peer review)", "Milestone"),
            (9, 4, "Research essay (final)", "Deadline"),
            (10, 0, "Research presentations", "Deadline"),
            (10, 2, "Final portfolio and reflection", "Deadline"),
        ],
        "late_policy": (
            "Reading responses are not accepted late, but your lowest one is dropped. Essays lose one third of a letter "
            "grade per day late. If you need an extension, ask at least 24 hours before the deadline — reasonable "
            "requests are almost always granted."),
        "project": (
            "Research essay — a 2,000–2,500 word argument on a question you care about, supported by at least six "
            "credible sources (two scholarly). You will build it in stages: proposal conference, annotated "
            "bibliography, peer-reviewed draft, final essay and a five-minute presentation."),
        "slides": [
            {
                "file": "Lecture_03_Thesis_Statements.pptx",
                "title": "Writing a Strong Thesis",
                "subtitle": "ENG 101 · Week 3",
                "slides": [
                    ("What a thesis does", [
                        "States your main claim in one or two sentences",
                        "Tells the reader what you will argue — and why it matters",
                        "Usually appears at the end of the introduction",
                    ]),
                    ("Arguable, not obvious", [
                        "A thesis is a claim reasonable people could disagree with",
                        "Weak: “Social media is popular among teenagers.” (a fact)",
                        "Stronger: “Schools should teach social-media literacy because…”",
                    ]),
                    ("Specific and focused", [
                        "Narrow the topic to what you can support in the assigned length",
                        "Replace vague words (“good,” “bad,” “society”) with precise ones",
                        "Preview your reasons without listing every paragraph",
                    ]),
                    ("A useful template", [
                        "Although [counterargument], [claim] because [reason 1] and [reason 2].",
                        "Templates are a starting point — revise into your own voice",
                    ]),
                    ("Workshop", [
                        "Write a working thesis for Essay 1",
                        "Swap with a partner: Is it arguable? Specific? Supportable?",
                        "Revise once based on the feedback",
                    ]),
                ],
            },
            {
                "file": "Lecture_06_Using_Sources_MLA.pptx",
                "title": "Using Sources and MLA Citation",
                "subtitle": "ENG 101 · Week 6",
                "slides": [
                    ("Quote, paraphrase or summarize?", [
                        "Quote when the exact wording matters",
                        "Paraphrase to restate a specific idea in your own words and structure",
                        "Summarize to condense the main point of a longer passage",
                    ]),
                    ("The quotation sandwich", [
                        "Introduce the source (signal phrase): “As Smith argues, …”",
                        "Give the quotation or paraphrase with an in-text citation",
                        "Explain how it supports your point — never let a quote speak for itself",
                    ]),
                    ("MLA in-text citations", [
                        "Author's last name and page number: (Smith 42)",
                        "No page? Use just the author: (Smith)",
                        "Every in-text citation must match an entry in Works Cited",
                    ]),
                    ("Works Cited entries", [
                        "Author. Title. Container, Other contributors, Version, Number, Publisher, Date, Location.",
                        "Alphabetize by author's last name; use a hanging indent",
                        "Include DOIs or URLs for online sources",
                    ]),
                    ("Avoiding plagiarism", [
                        "Cite paraphrases and summaries, not just quotations",
                        "Keep source notes separate from your own ideas while researching",
                        "When in doubt, cite — or ask the Writing Center",
                    ]),
                ],
            },
        ],
        "notes": {
            "file": "Notes_Paragraphs_and_Revision.docx",
            "title": "ENG 101 — Notes: Paragraphs and Revision",
            "sections": [
                ("The PIE paragraph", [
                    "Point — a topic sentence that makes one claim supporting your thesis.",
                    "Illustration — evidence: a quotation, statistic, example or paraphrase, properly cited.",
                    "Explanation — your analysis of how the evidence proves the point. This is where your thinking "
                    "shows; aim for at least as much explanation as evidence.",
                ]),
                ("Transitions", [
                    "Transitions show the relationship between ideas: addition (furthermore), contrast (however), "
                    "cause (therefore), example (for instance). Use them to connect paragraphs, not only sentences.",
                ]),
                ("Global revision first", [
                    "• Does every paragraph support the thesis? Does the thesis still match what you argue?",
                    "• Is the order logical? Try a reverse outline — one sentence per paragraph.",
                    "• Have you answered the strongest counterargument?",
                ]),
                ("Then local editing", [
                    "• Cut filler (“In today's society,” “It is important to note that”).",
                    "• Prefer active voice and concrete verbs.",
                    "• Read aloud to catch errors; check every citation against the Works Cited.",
                ]),
            ],
        },
        "practice": {
            "file": "Research_Essay_Assignment_and_Rubric.pdf",
            "title": "ENG 101 — Research Essay: Assignment and Rubric",
            "intro": "Write a 2,000–2,500 word researched argument. Your essay will be evaluated on the criteria below.",
            "items": [
                "Thesis (20%) — clear, arguable and appropriately focused.",
                "Evidence (25%) — at least six credible sources, including two scholarly, used accurately.",
                "Analysis (25%) — explains how evidence supports claims; addresses counterarguments.",
                "Organization (15%) — logical structure, effective topic sentences and transitions.",
                "Style and mechanics (10%) — clear, concise prose with few errors.",
                "MLA formatting (5%) — correct in-text citations and Works Cited.",
            ],
            "answers": None,
        },
    },
    # ------------------------------------------------------------------------------------------------- PSY 200
    {
        "code": "PSY 200",
        "title": "Introduction to Psychology",
        "slug": "PSY200_Intro_to_Psychology",
        "credits": 3,
        "instructor": "Dr. Taylor Brooks",
        "email": "tbrooks@example.edu",
        "office": "Behavioral Sciences Building 418",
        "office_hours": "Wednesdays 1:00–3:00 PM and Fridays 11:00 AM–12:00 PM",
        "meets": "Tue / Thu 3:00–4:15 PM, Behavioral Sciences Auditorium",
        "ta": "Jamal Wright and Emily Novak — exam review sessions",
        "description": (
            "A survey of the scientific study of behavior and mental processes. Topics include research methods, the "
            "brain and nervous system, sensation and perception, learning, memory, cognition, development, social "
            "psychology and psychological disorders. Throughout the course you will learn to evaluate claims about "
            "human behavior using evidence."),
        "prereq": "None.",
        "outcomes": [
            "Describe the major perspectives and research methods in psychology.",
            "Explain how biological, psychological and social factors interact to shape behavior.",
            "Apply principles of learning and memory to improve your own study habits.",
            "Evaluate popular claims about psychology using scientific reasoning.",
        ],
        "materials": [
            "Psychology 2e (OpenStax, free online)",
            "Online quiz access through the course website",
        ],
        "grading": [
            ("Weekly online quizzes (8, lowest dropped)", 15),
            ("Exam 1", 15),
            ("Exam 2", 15),
            ("Article analysis paper", 10),
            ("Group myth-busting poster", 15),
            ("Final exam (cumulative)", 25),
            ("Participation", 5),
        ],
        "topics": [
            "Psychology as a science; history and perspectives",
            "Research methods and statistics",
            "Biological bases of behavior",
            "Sensation and perception; Exam 1",
            "Learning: classical and operant conditioning",
            "Memory and forgetting",
            "Thinking, language and intelligence; Exam 2",
            "Development across the lifespan",
            "Social psychology; posters due",
            "Psychological disorders and treatment; final exam",
        ],
        "deliverables": [
            (1, 6, "Online quiz 1", "Quiz"),
            (2, 6, "Online quiz 2", "Quiz"),
            (3, 4, "Poster group topic proposal", "Milestone"),
            (3, 6, "Online quiz 3", "Quiz"),
            (4, 3, "Exam 1 (Chapters 1–4)", "Exam"),
            (5, 6, "Online quiz 4", "Quiz"),
            (6, 4, "Article analysis paper", "Deadline"),
            (6, 6, "Online quiz 5", "Quiz"),
            (7, 3, "Exam 2 (Chapters 5–7)", "Exam"),
            (8, 6, "Online quiz 6", "Quiz"),
            (9, 1, "Group myth-busting poster", "Deadline"),
            (9, 6, "Online quiz 7", "Quiz"),
            (10, 3, "Final exam (cumulative)", "Exam"),
        ],
        "late_policy": (
            "Online quizzes close at 11:59 PM on Sunday and cannot be reopened, but your lowest quiz is dropped. The "
            "article analysis loses 10% per day late. Make-up exams require documentation and must be arranged within "
            "one week."),
        "project": (
            "Group myth-busting poster — in groups of four, pick a popular claim (“we only use 10% of our brains,” "
            "“learning styles”) and evaluate it with research evidence. Present your findings in a poster session. "
            "Deliverables: a topic proposal and the final poster."),
        "slides": [
            {
                "file": "Lecture_05_Learning.pptx",
                "title": "Learning: Conditioning",
                "subtitle": "PSY 200 · Lecture 5",
                "slides": [
                    ("What is learning?", [
                        "A relatively lasting change in behavior or knowledge that comes from experience",
                        "Associative learning links events: stimulus–stimulus or behavior–consequence",
                    ]),
                    ("Classical conditioning (Pavlov)", [
                        "Unconditioned stimulus (food) → unconditioned response (salivation)",
                        "A neutral stimulus (bell) paired with the US becomes a conditioned stimulus",
                        "CS alone now triggers a conditioned response",
                        "Extinction: CR fades when the CS appears without the US; spontaneous recovery can follow",
                    ]),
                    ("Operant conditioning (Skinner)", [
                        "Behavior is shaped by its consequences",
                        "Reinforcement increases behavior: positive (add something good) or negative (remove something bad)",
                        "Punishment decreases behavior",
                    ]),
                    ("Schedules of reinforcement", [
                        "Continuous reinforcement — fastest learning, fastest extinction",
                        "Fixed/variable ratio and fixed/variable interval schedules",
                        "Variable ratio (e.g. slot machines) produces high, persistent responding",
                    ]),
                    ("Observational learning", [
                        "Bandura's Bobo doll studies: children imitated modeled aggression",
                        "Learning can happen without direct reinforcement",
                    ]),
                ],
            },
            {
                "file": "Lecture_06_Memory.pptx",
                "title": "Memory",
                "subtitle": "PSY 200 · Lecture 6",
                "slides": [
                    ("Three processes", [
                        "Encoding — getting information in",
                        "Storage — keeping it over time",
                        "Retrieval — getting it back out when needed",
                    ]),
                    ("The Atkinson–Shiffrin model", [
                        "Sensory memory: brief, large capacity",
                        "Short-term (working) memory: about 7 ± 2 items for roughly 20 seconds without rehearsal",
                        "Long-term memory: effectively unlimited, lasting",
                    ]),
                    ("Encoding that works", [
                        "Deeper, meaning-based processing beats shallow repetition",
                        "Self-reference and elaboration connect new ideas to what you know",
                        "Chunking groups items to fit more into working memory",
                    ]),
                    ("Why we forget", [
                        "Ebbinghaus forgetting curve: most loss happens soon after learning",
                        "Interference: proactive (old blocks new) and retroactive (new blocks old)",
                        "Retrieval failure — the tip-of-the-tongue effect",
                    ]),
                    ("Study smarter", [
                        "Spacing effect: spread study sessions out instead of cramming",
                        "Testing effect: practice retrieval with quizzes and flashcards",
                        "Sleep consolidates memories — all-nighters backfire",
                    ]),
                ],
            },
        ],
        "notes": {
            "file": "Notes_Research_Methods.docx",
            "title": "PSY 200 — Notes: Research Methods",
            "sections": [
                ("The scientific method", [
                    "Psychologists form a testable hypothesis, collect data, analyze it and share results so others can "
                    "replicate them. A theory is a well-supported explanation that organizes many observations.",
                ]),
                ("Descriptive methods", [
                    "• Case studies examine one person or group in depth — rich but hard to generalize.",
                    "• Naturalistic observation records behavior in real settings without interfering.",
                    "• Surveys reach many people quickly; wording and sampling strongly affect results.",
                ]),
                ("Correlation", [
                    "A correlation coefficient (r, from −1 to +1) describes the direction and strength of a "
                    "relationship. Correlation does not prove causation — a third variable may explain both.",
                ]),
                ("Experiments", [
                    "Only experiments can show cause and effect. The researcher manipulates the independent variable "
                    "and measures the dependent variable. Random assignment to experimental and control groups "
                    "balances other differences between participants.",
                    "Double-blind procedures, where neither participants nor experimenters know who is in which group, "
                    "reduce placebo effects and experimenter bias.",
                ]),
                ("Ethics", [
                    "Research with people requires informed consent, protection from harm, confidentiality and a "
                    "debriefing. Institutional Review Boards (IRBs) review studies before they begin.",
                ]),
            ],
        },
        "practice": {
            "file": "Exam_1_Study_Guide.pdf",
            "title": "PSY 200 — Exam 1 Study Guide",
            "intro": "Exam 1 covers Chapters 1–4. Be able to define, give an example of and apply each concept.",
            "items": [
                "Compare the behavioral, cognitive, biological and sociocultural perspectives.",
                "Explain why correlation does not imply causation and give an example of a third variable.",
                "Identify the independent and dependent variables in a described experiment.",
                "Describe the parts of a neuron and how an action potential travels.",
                "Name the four lobes of the cerebral cortex and one function of each.",
                "Distinguish sensation from perception; explain top-down versus bottom-up processing.",
            ],
            "answers": None,
        },
    },
]
