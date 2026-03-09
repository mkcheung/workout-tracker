"""
Run with:  .venv/bin/python generate_docs.py
Outputs:   workout_tracker_docs.pdf
"""

from fpdf import FPDF
from fpdf.enums import XPos, YPos

PRIMARY   = (37,  99, 235)   # blue-600
DARK      = (15,  23,  42)   # slate-900
MID       = (71,  85, 105)   # slate-500
LIGHT_BG  = (241, 245, 249)  # slate-100
CODE_BG   = (30,  41,  59)   # slate-800
CODE_FG   = (226, 232, 240)  # slate-200
WHITE     = (255, 255, 255)
ACCENT    = (16, 185, 129)   # emerald-500


class PDF(FPDF):

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=18)
        self.add_page()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _rgb(self, triple):
        return triple

    def hline(self, color=LIGHT_BG, thickness=0.5):
        self.set_draw_color(*color)
        self.set_line_width(thickness)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def spacer(self, h=4):
        self.ln(h)

    # ------------------------------------------------------------------
    # Text primitives
    # ------------------------------------------------------------------

    def h1(self, text):
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*PRIMARY)
        self.multi_cell(0, 9, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.hline(PRIMARY, 1)
        self.spacer(2)

    def h2(self, text):
        self.spacer(5)
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(*PRIMARY)
        self.set_fill_color(*LIGHT_BG)
        self.multi_cell(0, 8, f"  {text}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.spacer(2)

    def h3(self, text):
        self.spacer(3)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*DARK)
        self.multi_cell(0, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def h4(self, text):
        self.spacer(2)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*MID)
        self.multi_cell(0, 6, text.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def body(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK)
        self.multi_cell(0, 5.5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.spacer(1)

    def bullet(self, text, indent=6):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK)
        x = self.get_x() + indent
        self.set_x(x)
        self.multi_cell(0, 5.5, f"-  {text}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def code_inline(self, label, value="", indent=6):
        """Key: value line where value is rendered in monospace-style bold."""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK)
        self.set_x(self.l_margin + indent)
        self.cell(0, 5.5, "")   # reset x
        self.set_x(self.l_margin + indent)
        self.set_font("Courier", "B", 9)
        self.set_text_color(*PRIMARY)
        self.cell(self.get_string_width(label) + 2, 5.5, label)
        if value:
            self.set_font("Helvetica", "", 10)
            self.set_text_color(*DARK)
            self.multi_cell(0, 5.5, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            self.ln(5.5)

    def code_block(self, lines):
        """Render a dark-background code block."""
        self.spacer(2)
        padding = 4
        line_h = 5
        total_h = len(lines) * line_h + padding * 2
        x, y = self.l_margin, self.get_y()
        w = self.w - self.l_margin - self.r_margin
        self.set_fill_color(*CODE_BG)
        self.rect(x, y, w, total_h, "F")
        self.set_y(y + padding)
        self.set_font("Courier", "", 9)
        self.set_text_color(*CODE_FG)
        for line in lines:
            self.set_x(x + padding)
            self.cell(w - padding * 2, line_h, line)
            self.ln(line_h)
        self.set_y(y + total_h + 2)
        self.set_text_color(*DARK)
        self.spacer(2)

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    def table(self, headers, rows, col_widths=None):
        self.spacer(2)
        usable = self.w - self.l_margin - self.r_margin
        n = len(headers)
        if col_widths is None:
            col_widths = [usable / n] * n

        # Header
        self.set_fill_color(*PRIMARY)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 9)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, f" {h}", border=0, fill=True)
        self.ln(7)

        # Rows
        self.set_font("Helvetica", "", 9)
        for ri, row in enumerate(rows):
            fill = ri % 2 == 0
            self.set_fill_color(*LIGHT_BG if fill else WHITE)
            self.set_text_color(*DARK)
            # Calculate row height based on tallest cell
            max_lines = 1
            for ci, cell in enumerate(row):
                words = str(cell)
                approx = int(col_widths[ci] / 5.5)   # rough chars per line
                lines_needed = max(1, len(words) // max(approx, 1) + 1)
                max_lines = max(max_lines, lines_needed)
            row_h = max_lines * 5 + 2
            for ci, cell in enumerate(row):
                self.multi_cell(
                    col_widths[ci], row_h, f" {cell}",
                    border=0, fill=fill, max_line_height=5,
                    new_x=XPos.RIGHT, new_y=YPos.TOP,
                )
            self.ln(row_h)
        self.spacer(3)

    # ------------------------------------------------------------------
    # Cover page
    # ------------------------------------------------------------------

    def cover(self):
        self.set_fill_color(*PRIMARY)
        self.rect(0, 0, self.w, 80, "F")
        self.set_fill_color(*ACCENT)
        self.rect(0, 78, self.w, 4, "F")

        self.set_y(18)
        self.set_font("Helvetica", "B", 30)
        self.set_text_color(*WHITE)
        self.cell(0, 12, "Workout Tracker API", align="C")
        self.ln(14)
        self.set_font("Helvetica", "", 14)
        self.cell(0, 8, "Developer Reference & Architecture Guide", align="C")
        self.ln(10)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(200, 220, 255)
        self.cell(0, 6, "Django REST Framework  -  PostgreSQL  -  Token Auth", align="C")

        self.set_y(95)
        self.set_text_color(*DARK)
        self.set_font("Helvetica", "", 10)
        self.body(
            "This document describes every module, endpoint, serializer, and service function "
            "in the Workout Tracker backend. Use it as the single source of truth when "
            "returning to the project after time away."
        )

    # ------------------------------------------------------------------
    # Header / Footer
    # ------------------------------------------------------------------

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*MID)
        self.cell(0, 8, "Workout Tracker API -- Developer Reference", align="L")
        self.ln(0.5)
        self.hline(LIGHT_BG, 0.3)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*MID)
        self.hline(LIGHT_BG, 0.3)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


# ======================================================================
# CONTENT
# ======================================================================

def build(pdf: PDF):

    # ------------------------------------------------------------------
    # Cover
    # ------------------------------------------------------------------
    pdf.cover()

    # ------------------------------------------------------------------
    # 1. Purpose & overview
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.h1("1. Purpose & Overview")
    pdf.body(
        "Workout Tracker is a personal fitness logging API that lets authenticated users "
        "record workouts, track the exercises and sets they performed, and query rich "
        "analytics (progress charts, estimated 1-rep maxes, total training volume) over "
        "any date range."
    )
    pdf.body(
        "The backend is a Django REST Framework application backed by PostgreSQL. "
        "Every user's data is completely isolated -- a user can only see and modify their "
        "own workouts. Admin/staff accounts have broader access and can manage the shared "
        "exercise catalogue."
    )

    pdf.h2("Tech Stack")
    pdf.bullet("Python 3.14 / Django 5.2")
    pdf.bullet("Django REST Framework -- ViewSets, Serializers, Token Authentication")
    pdf.bullet("PostgreSQL (host configured via environment variables)")
    pdf.bullet("django-filter for query-param filtering on list endpoints")
    pdf.bullet("fpdf2 (used only for this documentation)")

    pdf.h2("Project Layout")
    pdf.code_block([
        "workout-tracker/",
        "  config/           Django project settings & root URL conf",
        "  accounts/         User registration, login, logout, profile",
        "  exercises/        Shared exercise catalogue (admin-managed)",
        "  workouts/         Workout, WorkoutExercise, WorkoutSet CRUD",
        "  insights/         Analytics endpoints & service functions",
        "  tests/            Shared test factories",
    ])

    pdf.h2("Authentication")
    pdf.body(
        "The API uses DRF Token Authentication. Every request to a protected endpoint "
        "must include the header:"
    )
    pdf.code_block(["Authorization: Token <token_key>"])
    pdf.body(
        "Tokens are created on registration or login and persist until the user explicitly "
        "logs out (DELETE via the logout endpoint)."
    )

    # ------------------------------------------------------------------
    # 2. Data model
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.h1("2. Data Model")

    pdf.h2("Entity Relationships")
    pdf.body(
        "The hierarchy is: User -> Workout -> WorkoutExercise -> WorkoutSet. "
        "Exercises live in a separate shared catalogue and are referenced by "
        "WorkoutExercise via a foreign key."
    )
    pdf.code_block([
        "User (django.contrib.auth)",
        "  +- Profile          (one-to-one; stores age, weight, height, max HR)",
        "  +- Workout          (performed_at, notes)",
        "       +- WorkoutExercise  (exercise FK, order)",
        "            +- WorkoutSet   (set_number, reps, weight [nullable])",
        "",
        "Exercise  (name, category, muscle_group, is_active)",
    ])

    pdf.h2("Model: Exercise")
    pdf.table(
        ["Field", "Type", "Notes"],
        [
            ["name",         "CharField(100)",      "Unique, indexed"],
            ["category",     "CharField(choices)",  "push | pull | strength | cardio, optional"],
            ["muscle_group", "CharField(choices)",  "chest | back | legs, optional"],
            ["is_active",    "BooleanField",        "Default True. Non-admins only see active exercises"],
            ["created_at",   "DateTimeField",       "Auto set on create"],
            ["updated_at",   "DateTimeField",       "Auto set on update"],
        ],
        [40, 55, 85]
    )

    pdf.h2("Model: Workout")
    pdf.table(
        ["Field", "Type", "Notes"],
        [
            ["user",         "ForeignKey(User)",   "CASCADE delete, indexed"],
            ["notes",        "TextField",           "Optional free-text notes"],
            ["performed_at", "DateTimeField",       "When the session happened, indexed"],
            ["created_at",   "DateTimeField",       "Auto"],
            ["updated_at",   "DateTimeField",       "Auto"],
        ],
        [40, 55, 85]
    )

    pdf.h2("Model: WorkoutExercise")
    pdf.table(
        ["Field", "Type", "Notes"],
        [
            ["workout",     "ForeignKey(Workout)",  "CASCADE delete"],
            ["exercise",    "ForeignKey(Exercise)", "CASCADE delete"],
            ["order",       "PositiveSmallInt",     "Display order within the workout (min 1)"],
            ["created_at",  "DateTimeField",        "Auto"],
        ],
        [40, 55, 85]
    )
    pdf.bullet("Unique constraint: (workout, order)")

    pdf.h2("Model: WorkoutSet")
    pdf.table(
        ["Field", "Type", "Notes"],
        [
            ["workout_exercise", "ForeignKey(WorkoutExercise)", "CASCADE delete"],
            ["set_number",       "PositiveSmallInt",            "Set order within the exercise (min 1)"],
            ["reps",             "PositiveSmallInt",            "Reps performed (min 1)"],
            ["weight",           "DecimalField(6,2)",           "Weight in lbs -- nullable (bodyweight sets)"],
            ["created_at",       "DateTimeField",               "Auto"],
        ],
        [44, 55, 81]
    )
    pdf.bullet("Unique constraint: (workout_exercise, set_number)")

    pdf.h2("Model: Profile")
    pdf.table(
        ["Field", "Type", "Notes"],
        [
            ["user",            "OneToOneField(User)", "CASCADE delete"],
            ["age",             "PositiveSmallInt",    "Optional"],
            ["weight_lbs",      "DecimalField(5,1)",   "Optional"],
            ["height_in",       "PositiveSmallInt",    "Optional"],
            ["max_heart_rate",  "PositiveSmallInt",    "Optional"],
        ],
        [44, 55, 81]
    )

    # ------------------------------------------------------------------
    # 3. Accounts app
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.h1("3. Accounts App")
    pdf.body(
        "Handles user registration, authentication, and profile management. "
        "Tokens are DRF's built-in authtoken tokens."
    )

    pdf.h2("Endpoints")
    pdf.table(
        ["Method", "URL", "Auth", "Description"],
        [
            ["POST",  "/api/auth/register/", "None",  "Create account, returns token"],
            ["POST",  "/api/auth/login/",    "None",  "Returns token for valid credentials"],
            ["POST",  "/api/auth/logout/",   "Token", "Deletes the caller's token"],
            ["GET",   "/api/me/",            "Token", "Returns current user + profile"],
            ["PATCH", "/api/me/",            "Token", "Updates email and/or profile fields"],
        ],
        [18, 58, 18, 86]
    )

    pdf.h2("Register -- POST /api/auth/register/")
    pdf.h4("Request body")
    pdf.table(
        ["Field", "Required", "Validation"],
        [
            ["username",   "Yes", "Unique"],
            ["email",      "Yes", "Valid email"],
            ["password",   "Yes", "Min 8 chars, passes Django password validators"],
            ["first_name", "Yes", ""],
            ["last_name",  "Yes", ""],
        ],
        [40, 22, 118]
    )
    pdf.h4("Response -- 201")
    pdf.code_block([
        '{',
        '  "token": "abc123...",',
        '  "user": { "id": 1, "email": "...", "first_name": "...",',
        '             "last_name": "...", "username": "..." }',
        '}',
    ])

    pdf.h2("Login -- POST /api/auth/login/")
    pdf.h4("Request body")
    pdf.bullet("username  (required)")
    pdf.bullet("password  (required, not trimmed)")
    pdf.h4("Response -- 200")
    pdf.code_block(['{ "token": "abc123..." }'])

    pdf.h2("Me -- GET /api/me/")
    pdf.h4("Response -- 200")
    pdf.code_block([
        '{',
        '  "id": 1, "username": "joe", "email": "joe@example.com",',
        '  "profile": { "age": 30, "weight_lbs": "185.0",',
        '               "height_in": 72, "max_heart_rate": 185 }',
        '}',
    ])

    pdf.h2("Me -- PATCH /api/me/")
    pdf.body("All fields optional. Only provided fields are updated.")
    pdf.code_block([
        '{',
        '  "email": "new@example.com",',
        '  "profile": { "weight_lbs": "190.0", "age": 31 }',
        '}',
    ])

    # ------------------------------------------------------------------
    # 4. Exercises app
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.h1("4. Exercises App")
    pdf.body(
        "Manages the shared exercise catalogue. Exercises are global (not user-specific). "
        "Anyone can read them; only admin/staff can create or modify them."
    )

    pdf.h2("Endpoints -- /api/exercises/")
    pdf.table(
        ["Method", "URL", "Auth", "Description"],
        [
            ["GET",    "/api/exercises/",     "None",        "List all active exercises (or all if admin)"],
            ["POST",   "/api/exercises/",     "Token+Admin", "Create an exercise"],
            ["GET",    "/api/exercises/{id}/","None",        "Retrieve one exercise"],
            ["PATCH",  "/api/exercises/{id}/","Token+Admin", "Partial update"],
            ["PUT",    "/api/exercises/{id}/","Token+Admin", "Full update"],
            ["DELETE", "/api/exercises/{id}/","Token+Admin", "Delete"],
        ],
        [18, 52, 28, 82]
    )

    pdf.h2("Query Parameters (GET list)")
    pdf.table(
        ["Param", "Example", "Description"],
        [
            ["search",   "?search=bench",          "Case-insensitive name search"],
            ["ordering", "?ordering=name",          "Sort by: name, category, muscle_group"],
            ["ordering", "?ordering=-name",         "Prefix - for descending"],
        ],
        [28, 58, 94]
    )

    pdf.h2("ExerciseSerializer fields")
    pdf.table(
        ["Field", "Read-only", "Notes"],
        [
            ["id",           "Yes", ""],
            ["name",         "No",  "Stripped of whitespace, cannot be blank"],
            ["category",     "No",  "push | pull | strength | cardio"],
            ["muscle_group", "No",  "chest | back | legs"],
            ["is_active",    "Yes", ""],
            ["created_at",   "Yes", ""],
            ["updated_at",   "Yes", ""],
        ],
        [40, 22, 118]
    )

    # ------------------------------------------------------------------
    # 5. Workouts app
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.h1("5. Workouts App")
    pdf.body(
        "Core CRUD for Workouts, WorkoutExercises, and WorkoutSets. "
        "All data is user-scoped -- queries automatically filter to the authenticated user."
    )

    pdf.h2("5.1 Workouts -- /api/workouts/")
    pdf.table(
        ["Method", "URL", "Description"],
        [
            ["GET",    "/api/workouts/",              "List user's workouts (newest first by default)"],
            ["POST",   "/api/workouts/",              "Create a workout"],
            ["GET",    "/api/workouts/{id}/",         "Retrieve workout with full exercise+set detail"],
            ["PATCH",  "/api/workouts/{id}/",         "Update notes or performed_at"],
            ["PUT",    "/api/workouts/{id}/",         "Full update"],
            ["DELETE", "/api/workouts/{id}/",         "Delete workout (cascades to exercises+sets)"],
            ["PUT",    "/api/workouts/{id}/set-exercises/", "Bulk replace all exercises and sets"],
        ],
        [18, 68, 94]
    )

    pdf.h3("Query Parameters (GET list)")
    pdf.table(
        ["Param", "Example", "Description"],
        [
            ["performed_at",        "?performed_at=2026-01-15",          "Exact date"],
            ["performed_at__gte",   "?performed_at__gte=2026-01-01",     "On or after date"],
            ["performed_at__lte",   "?performed_at__lte=2026-03-31",     "On or before date"],
            ["created_at__gte",     "?created_at__gte=2026-01-01",       "Created on/after"],
            ["created_at__lte",     "?created_at__lte=2026-12-31",       "Created on/before"],
            ["search",              "?search=leg day",                   "Search in notes"],
            ["ordering",            "?ordering=-performed_at",           "Sort field (prefix - for desc)"],
        ],
        [38, 66, 76]
    )

    pdf.h3("POST / PATCH request body")
    pdf.code_block([
        '{',
        '  "notes": "Heavy leg day",         // optional',
        '  "performed_at": "2026-01-15T10:00:00Z"  // optional, defaults to now()',
        '}',
    ])

    pdf.h3("GET single workout -- response shape")
    pdf.code_block([
        '{',
        '  "id": 42, "notes": "...", "performed_at": "2026-01-15T10:00:00Z",',
        '  "workout_exercises": [',
        '    {',
        '      "id": 7, "exercise": 3, "order": 1,',
        '      "workout_sets": [',
        '        { "id": 11, "set_number": 1, "reps": 5, "weight": "135.00" },',
        '        { "id": 12, "set_number": 2, "reps": 3, "weight": "185.00" }',
        '      ]',
        '    }',
        '  ]',
        '}',
    ])

    pdf.h2("5.2 set-exercises Action -- PUT /api/workouts/{id}/set-exercises/")
    pdf.body(
        "Atomically replaces ALL exercises and sets for a workout in one call. "
        "Existing WorkoutExercise records are deleted, then new ones are created "
        "in a single database transaction."
    )
    pdf.h4("Request body")
    pdf.code_block([
        '{',
        '  "workout_exercises": [',
        '    {',
        '      "exercise_id": 3,',
        '      "order": 1,',
        '      "sets": [',
        '        { "set_number": 1, "reps": 5, "weight": 135 },',
        '        { "set_number": 2, "reps": 3, "weight": 185 }',
        '      ]',
        '    }',
        '  ]',
        '}',
    ])
    pdf.body("Returns the newly created WorkoutExercise list (200).")

    pdf.h2("5.3 WorkoutExercises -- /api/workout-exercises/")
    pdf.table(
        ["Method", "URL", "Description"],
        [
            ["GET",    "/api/workout-exercises/",      "List exercises across all user workouts"],
            ["POST",   "/api/workout-exercises/",      "Add an exercise to a workout"],
            ["GET",    "/api/workout-exercises/{id}/", "Retrieve one"],
            ["PATCH",  "/api/workout-exercises/{id}/", "Partial update (e.g. reorder)"],
            ["DELETE", "/api/workout-exercises/{id}/", "Remove (cascades sets)"],
        ],
        [18, 68, 94]
    )
    pdf.body("Filter: ?workout=<id>  ?exercise=<id>   Ordering: order, created_at")

    pdf.h2("5.4 WorkoutSets -- /api/workout-sets/")
    pdf.table(
        ["Method", "URL", "Description"],
        [
            ["GET",    "/api/workout-sets/",      "List sets across all user workouts"],
            ["POST",   "/api/workout-sets/",      "Create a set"],
            ["GET",    "/api/workout-sets/{id}/", "Retrieve one"],
            ["PATCH",  "/api/workout-sets/{id}/", "Partial update"],
            ["DELETE", "/api/workout-sets/{id}/", "Delete"],
        ],
        [18, 68, 94]
    )
    pdf.body("Filter: ?workout_exercise=<id>   Ordering: set_number, created_at, updated_at")
    pdf.h4("Validation")
    pdf.bullet("set_number >= 1, unique per workout_exercise")
    pdf.bullet("reps >= 1")
    pdf.bullet("weight > 0 if provided (null is allowed for bodyweight sets)")

    # ------------------------------------------------------------------
    # 6. Insights app
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.h1("6. Insights App")
    pdf.body(
        "Three read-only analytics endpoints that crunch the workout data into "
        "time-series charts and exports. All heavy lifting lives in services.py; "
        "the views only handle query validation and queryset building."
    )

    pdf.h2("6.1 Architecture -- Views -> Serializers -> Services")
    pdf.body(
        "Each view validates incoming query params with a dedicated serializer, "
        "builds a prefetch-optimised queryset scoped to the current user, then "
        "delegates to a service function that iterates Python-side and returns "
        "a plain dict that DRF serializes to JSON."
    )
    pdf.code_block([
        "Request -> ViewSet.list()",
        "           +- QuerySerializer.is_valid()",
        "           +- Workout.objects.filter(user=...).prefetch_related(...)",
        "           +- calculate_*(user_workouts, ...) -> dict",
        "           +- Response(dict)",
    ])

    pdf.h2("6.2 Endpoints")
    pdf.table(
        ["Method", "URL", "Description"],
        [
            ["GET", "/api/insights/exercise-series/", "Daily time-series for top weight, est. 1RM, or tonnage"],
            ["GET", "/api/insights/weekly-volume/",   "Weekly tonnage aggregation for an exercise"],
            ["GET", "/api/insights/export-sets/",     "Paginated flat export of every set"],
        ],
        [18, 72, 90]
    )

    pdf.h2("6.3 exercise-series -- GET /api/insights/exercise-series/")
    pdf.body("Returns a daily data series for a chosen metric on a specific exercise.")

    pdf.h4("Query parameters (InsightsDateRangeQuerySerializer)")
    pdf.table(
        ["Param", "Required", "Values / Notes"],
        [
            ["exercise_id",    "Yes", "ID of the exercise to analyse"],
            ["metric",         "Yes", "top_set_weight | estimated_1rm | tonnage"],
            ["performed_from", "No",  "YYYY-MM-DD start date (inclusive)"],
            ["performed_to",   "No",  "YYYY-MM-DD end date (inclusive). Must be >= performed_from"],
        ],
        [38, 22, 120]
    )

    pdf.h4("Metrics explained")
    pdf.table(
        ["Metric", "Formula", "Per-day aggregation"],
        [
            ["top_set_weight", "Raw weight (lbs)",               "max(weight) across all sets"],
            ["estimated_1rm",  "weight x (1 + reps / 30)  [Epley]", "max(est_1rm) across all sets"],
            ["tonnage",        "weight x reps",              "sum of all sets"],
        ],
        [42, 66, 72]
    )
    pdf.body("Sets with null weight are silently skipped. Sets with 0 reps are skipped for estimated_1rm.")

    pdf.h4("Response shape (all three metrics)")
    pdf.code_block([
        '{',
        '  "exercise_id": 3,',
        '  "metric": "top_set_weight",   // or estimated_1rm / tonnage',
        '  "unit": "lbs",                // lbs_reps for tonnage',
        '  "points": [',
        '    { "date": "2026-01-06", "value": 185.0 },',
        '    { "date": "2026-01-08", "value": 190.0 }',
        '  ],',
        '  "summary": {',
        '    "start":  185.0,   // value of first data point',
        '    "latest": 225.0,   // value of last data point',
        '    "change": 40.0     // latest - start (can be negative)',
        '  }',
        '}',
    ])
    pdf.body("If no data points exist, summary values are null and points is an empty array.")

    pdf.h2("6.4 weekly-volume -- GET /api/insights/weekly-volume/")
    pdf.body(
        "Aggregates tonnage (weight x reps) per calendar week for an exercise, "
        "returning exactly the requested number of weeks."
    )

    pdf.h4("Query parameters (InsightsWeeklyVolumeSerializer)")
    pdf.table(
        ["Param", "Default", "Constraints", "Notes"],
        [
            ["exercise_id", "--",     "Required",  "ID of exercise"],
            ["weeks",       "12",    "1 - 52",    "How many weeks to return"],
            ["to",          "today", "YYYY-MM-DD","End date; weeks count backward from here"],
        ],
        [35, 22, 28, 95]
    )

    pdf.h4("Response shape")
    pdf.code_block([
        '{',
        '  "exercise_id": 3,',
        '  "unit": "lbs_reps",',
        '  "weeks": 12,',
        '  "points": [',
        '    { "week_start": "2025-12-15", "value": 4200.0 },',
        '    { "week_start": "2025-12-22", "value": 4550.5 },',
        '    ...',
        '  ]',
        '}',
    ])
    pdf.body("Week buckets with no data have value 0.0. Weeks are always Monday-anchored.")

    pdf.h2("6.5 export-sets -- GET /api/insights/export-sets/")
    pdf.body(
        "Flattens the entire workout -> exercise -> set hierarchy into a paginated "
        "list of rows, useful for spreadsheet exports or external analysis."
    )

    pdf.h4("Query parameters (InsightsExportSetsSerializer)")
    pdf.table(
        ["Param", "Default", "Constraints", "Notes"],
        [
            ["performed_from", "--",   "YYYY-MM-DD", "Optional start date filter"],
            ["performed_to",   "--",   "YYYY-MM-DD", "Optional end date filter. Must be >= from"],
            ["exercise_id",    "--",   "integer",    "Optional exercise filter (all if omitted)"],
            ["page",           "1",   "min 1",      "Page number"],
            ["page_size",      "200", "1 - 500",    "Max 1000 via pagination class"],
        ],
        [35, 18, 28, 99]
    )

    pdf.h4("Response shape")
    pdf.code_block([
        '{',
        '  "count": 840,',
        '  "next": "/api/insights/export-sets/?page=2",',
        '  "previous": null,',
        '  "results": [',
        '    {',
        '      "workout_id": 42,',
        '      "performed_at": "2026-01-06T10:00:00+00:00",',
        '      "exercise_id": 3,',
        '      "exercise_name": "Barbell Bench Press",',
        '      "workout_exercise_id": 7,',
        '      "order": 1,',
        '      "set_id": 11,',
        '      "set_number": 1,',
        '      "reps": 5,',
        '      "weight": 135.0    // null for bodyweight sets',
        '    }',
        '  ]',
        '}',
    ])

    # ------------------------------------------------------------------
    # 7. Service functions
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.h1("7. Insights Service Functions")
    pdf.body(
        "All business logic lives in insights/services.py. "
        "Functions receive pre-filtered, pre-fetched querysets from the view and return "
        "plain Python dicts. They never touch the database themselves -- only iterate "
        "the already-loaded related objects."
    )

    pdf.h2("calculate_daily_top_set_weight")
    pdf.code_block([
        "calculate_daily_top_set_weight(",
        "    user_workouts,       # prefetched Workout queryset",
        "    performed_from,      # date | None",
        "    performed_to,        # date | None",
        "    exercise_id,         # int",
        ") -> dict",
    ])
    pdf.body(
        "Groups all sets by date. For each date, finds the heaviest weight lifted "
        "in a single set. Sets with null weight are skipped."
    )

    pdf.h2("calculate_daily_1_rep_max")
    pdf.code_block([
        "calculate_daily_1_rep_max(",
        "    user_workouts, performed_from, performed_to, exercise_id",
        ") -> dict",
    ])
    pdf.body(
        "Applies the Epley formula to every set:  est_1rm = weight x (1 + reps/30). "
        "Per day, returns the highest estimated 1RM across all sets. "
        "Sets with null weight or 0 reps are skipped."
    )

    pdf.h2("calculate_daily_tonnage")
    pdf.code_block([
        "calculate_daily_tonnage(",
        "    user_workouts, performed_from, performed_to, exercise_id",
        ") -> dict",
    ])
    pdf.body(
        "Sums weight x reps for every set in a day. Null-weight sets are excluded. "
        "Returns one data point per day that had at least one valid set."
    )

    pdf.h2("calculate_weekly_volume")
    pdf.code_block([
        "calculate_weekly_volume(",
        "    user_workouts,   # Workout queryset",
        "    duration,        # int -- number of weeks",
        "    to,              # date -- last week's anchor",
        "    exercise_id,     # int",
        ") -> dict",
    ])
    pdf.body(
        "Builds an OrderedDict of week buckets (Monday-anchored, counting backward "
        "from 'to'). Accumulates tonnage into each bucket. Returns all buckets, "
        "including those with 0 volume."
    )

    pdf.h2("calculate_export_sets")
    pdf.code_block([
        "calculate_export_sets(",
        "    user_workouts, performed_from, performed_to, exercise_id",
        ") -> list[dict]",
    ])
    pdf.body(
        "Iterates workouts -> exercises -> sets and flattens into a list of row dicts. "
        "exercise_id=None returns all exercises. The list is then paginated by the view."
    )

    pdf.h2("Helper: week_buckets")
    pdf.code_block([
        "week_buckets(start, end, duration=None) -> list[dict]",
        "",
        "# start+end given: buckets from Monday(start) to Monday(end)",
        "# end+duration:    last 'duration' weeks ending at Monday(end)",
    ])
    pdf.body("Used by calculate_weekly_volume to pre-build the week scaffold.")

    # ------------------------------------------------------------------
    # 8. Query param serializers
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.h1("8. Query Param Serializers (Insights)")

    pdf.h2("InsightsDateRangeQuerySerializer")
    pdf.body("Validates query params for the exercise-series endpoint.")
    pdf.table(
        ["Field", "Type", "Required", "Validation"],
        [
            ["exercise_id",    "IntegerField", "Yes", ""],
            ["metric",         "ChoiceField",  "Yes", "top_set_weight | estimated_1rm | tonnage"],
            ["performed_from", "DateField",    "No",  "YYYY-MM-DD"],
            ["performed_to",   "DateField",    "No",  "YYYY-MM-DD, must be >= performed_from"],
        ],
        [40, 30, 22, 88]
    )

    pdf.h2("InsightsWeeklyVolumeSerializer")
    pdf.table(
        ["Field", "Type", "Required", "Default", "Validation"],
        [
            ["exercise_id", "IntegerField", "Yes", "--",     ""],
            ["weeks",       "IntegerField", "No",  "12",    "1 - 52"],
            ["to",          "DateField",    "No",  "today", "YYYY-MM-DD"],
        ],
        [35, 28, 20, 18, 79]
    )

    pdf.h2("InsightsExportSetsSerializer")
    pdf.table(
        ["Field", "Type", "Required", "Default", "Validation"],
        [
            ["performed_from", "DateField",    "No",  "--",   "YYYY-MM-DD"],
            ["performed_to",   "DateField",    "No",  "--",   "YYYY-MM-DD, >= performed_from"],
            ["exercise_id",    "IntegerField", "No",  "--",   ""],
            ["page",           "IntegerField", "No",  "1",   "min 1"],
            ["page_size",      "IntegerField", "No",  "200", "1 - 500"],
        ],
        [35, 28, 20, 18, 79]
    )

    # ------------------------------------------------------------------
    # 9. Seed data command
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.h1("9. Seed Demo Data")
    pdf.body(
        "A management command is included to quickly populate the database with "
        "realistic workout history so the Progress page charts have something "
        "interesting to display."
    )

    pdf.h2("Command: seed_demo")
    pdf.code_block([
        "# Basic usage -- creates demo@example.com / demo1234",
        "docker compose exec django python manage.py seed_demo",
        "",
        "# Custom credentials",
        "docker compose exec django python manage.py seed_demo \\",
        "    --email you@example.com --password mypass",
        "",
        "# Wipe existing demo data first, then re-seed",
        "docker compose exec django python manage.py seed_demo --flush",
        "",
        "# Generate 26 weeks of data",
        "docker compose exec django python manage.py seed_demo --weeks 26 --flush",
    ])

    pdf.h2("What it creates")
    pdf.table(
        ["Item", "Detail"],
        [
            ["Demo user",    "demo@example.com / demo1234 (or custom)"],
            ["Exercises",    "Barbell Bench Press, Back Squat, Deadlift, Overhead Press, Barbell Row"],
            ["Programme",    "3-day/week A/B split (Mon/Wed/Fri), alternating"],
            ["Duration",     "13 weeks by default (~39 sessions)"],
            ["Sets",         "4-5 sets per exercise: warm-up -> top set -> back-off"],
            ["Progression",  "Fixed weekly gain per exercise + +/-2.5 lb random noise"],
        ],
        [35, 145]
    )
    pdf.body(
        "All three metrics (top_set_weight, estimated_1rm, tonnage) will show "
        "clear upward trends with realistic variation."
    )

    # ------------------------------------------------------------------
    # 10. Running tests
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.h1("10. Tests")
    pdf.body(
        "Integration tests live in insights/tests/test_insights_api.py. "
        "They use DRF's APITestCase and a shared factory module at tests/factories.py."
    )

    pdf.h2("Test classes")
    pdf.table(
        ["Class", "Covers"],
        [
            ["InsightsAuthTests",   "All 3 endpoints return 401 without a token"],
            ["TopSetWeightTests",   "top_set_weight: picks heaviest set, skips null weight, date/user isolation, summary, validation"],
            ["Estimated1RMTests",   "estimated_1rm: Epley formula, best-per-day selection, null/zero-reps skipping"],
            ["DailyTonnageTests",   "tonnage: sums all sets, skips nulls, summary, empty response"],
            ["WeeklyVolumeTests",   "weekly-volume: 12 default weeks, custom weeks, volume bucket accuracy, user isolation"],
            ["ExportSetsTests",     "export-sets: row shape, null weight, exercise filter, date filter, pagination, user isolation"],
        ],
        [45, 135]
    )

    pdf.h2("Running tests")
    pdf.code_block([
        "# All insight tests",
        "docker compose exec django python manage.py test insights.tests.test_insights_api",
        "",
        "# Single class",
        "docker compose exec django python manage.py test \\",
        "    insights.tests.test_insights_api.TopSetWeightTests",
        "",
        "# All project tests",
        "docker compose exec django python manage.py test",
    ])

    pdf.h2("Test factories (tests/factories.py)")
    pdf.table(
        ["Function", "Description"],
        [
            ["create_user(**params)",    "Creates a regular test user (test@example.com / test@123)"],
            ["create_admin_user(**params)", "Creates a superuser"],
            ["create_workout(**params)", "Creates a Workout attached to a given user"],
            ["create_exercise(**params)","Creates an Exercise (default: push/chest)"],
        ],
        [55, 125]
    )

    # ------------------------------------------------------------------
    # 11. Quick-start
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.h1("11. Quick-start Cheat Sheet")

    pdf.h2("Get an auth token")
    pdf.code_block([
        "curl -X POST http://localhost:8000/api/auth/login/ \\",
        '  -H "Content-Type: application/json" \\',
        '  -d \'{"username": "demo@example.com", "password": "demo1234"}\'',
    ])

    pdf.h2("List exercises")
    pdf.code_block([
        "curl http://localhost:8000/api/exercises/",
    ])

    pdf.h2("Create a workout")
    pdf.code_block([
        "curl -X POST http://localhost:8000/api/workouts/ \\",
        '  -H "Authorization: Token <your_token>" \\',
        '  -H "Content-Type: application/json" \\',
        '  -d \'{"notes": "Monday push", "performed_at": "2026-03-09T09:00:00Z"}\'',
    ])

    pdf.h2("Bulk-set exercises and sets")
    pdf.code_block([
        "curl -X PUT http://localhost:8000/api/workouts/1/set-exercises/ \\",
        '  -H "Authorization: Token <your_token>" \\',
        '  -H "Content-Type: application/json" \\',
        '  -d \'{"workout_exercises": [',
        '    {"exercise_id": 1, "order": 1, "sets": [',
        '      {"set_number": 1, "reps": 5, "weight": 135},',
        '      {"set_number": 2, "reps": 3, "weight": 185}',
        '    ]}',
        '  ]}\'',
    ])

    pdf.h2("Get progress chart data")
    pdf.code_block([
        "curl 'http://localhost:8000/api/insights/exercise-series/",
        "  ?exercise_id=1&metric=top_set_weight",
        "  &performed_from=2026-01-01&performed_to=2026-03-31' \\",
        '  -H "Authorization: Token <your_token>"',
    ])

    pdf.h2("Export all sets to CSV (via export-sets)")
    pdf.code_block([
        "curl 'http://localhost:8000/api/insights/export-sets/?page_size=500' \\",
        '  -H "Authorization: Token <your_token>"',
    ])

    pdf.spacer(8)
    pdf.hline(ACCENT, 1)
    pdf.spacer(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*MID)
    pdf.cell(0, 6, "Generated from source -- keep this document alongside the repo.", align="C")


if __name__ == "__main__":
    pdf = PDF()
    build(pdf)
    out = "workout_tracker_docs.pdf"
    pdf.output(out)
    print(f"Done ->  {out}")
