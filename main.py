import json
import sqlite3
from datetime import date, datetime
from html import escape
from pathlib import Path

from flask import Flask, redirect, request


app = Flask(__name__)
DB_FILE = Path(__file__).with_name("workouts.db")
WORKOUT_TYPES = ["Push", "Pull", "Legs", "Arms", "Back", "Cardio", "Other"]
EXERCISES = {
    "Push": [
        "Bench Press",
        "Incline Bench Press",
        "Decline Bench Press",
        "Dumbbell Bench Press",
        "Chest Fly",
        "Cable Fly",
        "Push-Up",
        "Shoulder Press",
        "Dumbbell Shoulder Press",
        "Arnold Press",
        "Lateral Raise",
        "Front Raise",
        "Upright Row",
        "Tricep Pushdown",
        "Overhead Tricep Extension",
        "Skull Crusher",
        "Dips",
    ],
    "Pull": [
        "Pull-Up",
        "Chin-Up",
        "Lat Pulldown",
        "Wide Grip Lat Pulldown",
        "Close Grip Lat Pulldown",
        "Barbell Row",
        "Dumbbell Row",
        "T-Bar Row",
        "Seated Cable Row",
        "Chest Supported Row",
        "Face Pull",
        "Rear Delt Fly",
        "Barbell Curl",
        "Dumbbell Curl",
        "Hammer Curl",
        "Preacher Curl",
        "Cable Curl",
    ],
    "Legs": [
        "Back Squat",
        "Front Squat",
        "Goblet Squat",
        "Leg Press",
        "Hack Squat",
        "Walking Lunge",
        "Bulgarian Split Squat",
        "Romanian Deadlift",
        "Stiff Leg Deadlift",
        "Leg Extension",
        "Leg Curl",
        "Seated Leg Curl",
        "Hip Thrust",
        "Glute Bridge",
        "Standing Calf Raise",
        "Seated Calf Raise",
    ],
    "Arms": [
        "Barbell Curl",
        "Dumbbell Curl",
        "Hammer Curl",
        "Preacher Curl",
        "Cable Curl",
        "Concentration Curl",
        "Tricep Pushdown",
        "Rope Pushdown",
        "Overhead Tricep Extension",
        "Skull Crusher",
        "Close Grip Bench Press",
        "Dips",
    ],
    "Back": [
        "Deadlift",
        "Rack Pull",
        "Pull-Up",
        "Chin-Up",
        "Lat Pulldown",
        "Barbell Row",
        "Dumbbell Row",
        "T-Bar Row",
        "Seated Cable Row",
        "Face Pull",
        "Straight Arm Pulldown",
        "Back Extension",
    ],
    "Cardio": [
        "Walking",
        "Incline Walk",
        "Jogging",
        "Running",
        "Treadmill",
        "Cycling",
        "Stationary Bike",
        "Elliptical",
        "Stair Climber",
        "Rowing Machine",
        "Swimming",
        "Jump Rope",
        "HIIT",
        "Badminton",
        "Football",
        "Basketball",
    ],
    "Other": [
        "Stretching",
        "Yoga",
        "Pilates",
        "Mobility Work",
        "Core Workout",
        "Plank",
        "Crunch",
        "Russian Twist",
        "Mountain Climber",
        "Custom Exercise",
    ],
}


def format_display_date(date_text):
    try:
        parsed_date = datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        return date_text

    day = parsed_date.day
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    return parsed_date.strftime(f"%A, %B {day}{suffix} %Y")


def connect_database():
    connection = sqlite3.connect(DB_FILE)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def setup_database():
    with connect_database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS workout_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_date TEXT NOT NULL,
                workout_type TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS workout_exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                exercise TEXT NOT NULL,
                sets TEXT NOT NULL,
                reps TEXT NOT NULL,
                weight TEXT NOT NULL,
                duration TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (session_id)
                    REFERENCES workout_sessions (id)
                    ON DELETE CASCADE
            )
            """
        )
        add_duration_column_if_needed(connection)
        migrate_old_workouts(connection)


def add_duration_column_if_needed(connection):
    columns = connection.execute(
        "PRAGMA table_info(workout_exercises)"
    ).fetchall()
    column_names = [column[1] for column in columns]

    if "duration" not in column_names:
        connection.execute(
            "ALTER TABLE workout_exercises ADD COLUMN duration TEXT NOT NULL DEFAULT ''"
        )


def migrate_old_workouts(connection):
    old_table_exists = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'workouts'
        """
    ).fetchone()
    session_count = connection.execute(
        "SELECT COUNT(*) FROM workout_sessions"
    ).fetchone()[0]

    if not old_table_exists or session_count:
        return

    old_workouts = connection.execute(
        """
        SELECT workout_date, exercise, sets, reps, weight
        FROM workouts
        ORDER BY workout_date, id
        """
    ).fetchall()

    session_ids = {}
    for workout_date, exercise, sets, reps, weight in old_workouts:
        if workout_date not in session_ids:
            cursor = connection.execute(
                """
                INSERT INTO workout_sessions (workout_date, workout_type)
                VALUES (?, ?)
                """,
                (workout_date, "Other"),
            )
            session_ids[workout_date] = cursor.lastrowid

        connection.execute(
            """
            INSERT INTO workout_exercises
                (session_id, exercise, sets, reps, weight, duration)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (session_ids[workout_date], exercise, sets, reps, weight, ""),
        )


def create_session(workout_date, workout_type):
    with connect_database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO workout_sessions (workout_date, workout_type)
            VALUES (?, ?)
            """,
            (workout_date, workout_type),
        )
        return cursor.lastrowid


def delete_session(session_id):
    with connect_database() as connection:
        connection.execute(
            """
            DELETE FROM workout_sessions
            WHERE id = ?
            """,
            (session_id,),
        )


def add_exercise(session_id, exercise, sets="", reps="", weight="", duration=""):
    with connect_database() as connection:
        connection.execute(
            """
            INSERT INTO workout_exercises
                (session_id, exercise, sets, reps, weight, duration)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (session_id, exercise, sets, reps, weight, duration),
        )


def delete_exercise(exercise_id):
    with connect_database() as connection:
        connection.execute(
            """
            DELETE FROM workout_exercises
            WHERE id = ?
            """,
            (exercise_id,),
        )


def get_sessions():
    with connect_database() as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT
                workout_sessions.id,
                workout_sessions.workout_date,
                workout_sessions.workout_type,
                COUNT(workout_exercises.id) AS exercise_count
            FROM workout_sessions
            LEFT JOIN workout_exercises
                ON workout_exercises.session_id = workout_sessions.id
            GROUP BY workout_sessions.id
            ORDER BY workout_sessions.workout_date DESC, workout_sessions.id DESC
            """
        ).fetchall()


def get_session(session_id):
    with connect_database() as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT id, workout_date, workout_type
            FROM workout_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()


def get_session_exercises(session_id):
    with connect_database() as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT id, exercise, sets, reps, weight, duration
            FROM workout_exercises
            WHERE session_id = ?
            ORDER BY id
            """,
            (session_id,),
        ).fetchall()


def get_recent_exercise_names(workout_type):
    with connect_database() as connection:
        rows = connection.execute(
            """
            SELECT
                workout_exercises.exercise,
                MAX(workout_sessions.workout_date) AS latest_date,
                MAX(workout_exercises.id) AS latest_id
            FROM workout_exercises
            JOIN workout_sessions
                ON workout_sessions.id = workout_exercises.session_id
            WHERE workout_sessions.workout_type = ?
            GROUP BY workout_exercises.exercise
            ORDER BY latest_date DESC, latest_id DESC
            """,
            (workout_type,),
        ).fetchall()

    return [row[0] for row in rows]


def get_all_exercise_names():
    names = []
    for exercise_type, exercises in EXERCISES.items():
        names.extend(exercises)

    with connect_database() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT exercise
            FROM workout_exercises
            """
        ).fetchall()

    names.extend(row[0] for row in rows)
    unique_names = []
    seen_names = set()

    for exercise_name in sorted(names, key=str.lower):
        normalized_name = exercise_name.lower()

        if normalized_name not in seen_names:
            unique_names.append(exercise_name)
            seen_names.add(normalized_name)

    return unique_names


def get_recent_performances_by_exercise():
    with connect_database() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                workout_exercises.exercise,
                workout_exercises.sets,
                workout_exercises.reps,
                workout_exercises.weight,
                workout_exercises.duration,
                workout_sessions.workout_date,
                workout_sessions.workout_type
            FROM workout_exercises
            JOIN workout_sessions
                ON workout_sessions.id = workout_exercises.session_id
            ORDER BY
                LOWER(workout_exercises.exercise),
                workout_sessions.workout_date DESC,
                workout_exercises.id DESC
            """
        ).fetchall()

    recent_performances = {}
    for row in rows:
        key = row["exercise"].lower()
        exercise_history = recent_performances.setdefault(key, [])

        if len(exercise_history) < 3:
            if row["workout_type"] == "Cardio":
                summary = f"{row['duration']} min"
            else:
                summary = (
                    f"{row['sets']} sets x {row['reps']} reps "
                    f"@ {row['weight']} kg"
                )

            exercise_history.append({
                "date": format_display_date(row["workout_date"]),
                "type": row["workout_type"],
                "summary": summary,
            })

    return recent_performances


def render_layout(content, message=""):
    message_html = ""
    if message:
        message_html = f'<p class="message">{escape(message)}</p>'

    return f"""
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Workout Tracker</title>
    <style>
        body {{
            margin: 0;
            background: #f5f7fa;
            color: #1f2937;
            font-family: Arial, sans-serif;
        }}

        main {{
            max-width: 960px;
            margin: 0 auto;
            padding: 32px 20px;
        }}

        h1 {{
            margin: 0 0 24px;
            font-size: 32px;
        }}

        h2 {{
            margin: 0 0 16px;
            font-size: 22px;
        }}

        .actions {{
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
        }}

        .session-form,
        .exercise-form {{
            display: grid;
            gap: 12px;
            margin-bottom: 24px;
            align-items: end;
        }}

        .session-form {{
            grid-template-columns: repeat(2, minmax(160px, 1fr)) auto;
        }}

        .exercise-form {{
            grid-template-columns: repeat(4, minmax(120px, 1fr)) auto;
        }}

        .delete-form {{
            margin: 0;
        }}

        label {{
            display: grid;
            gap: 6px;
            font-size: 14px;
            font-weight: 700;
        }}

        input,
        select {{
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            font-size: 16px;
            padding: 10px;
        }}

        button,
        .button {{
            border: 0;
            border-radius: 6px;
            background: #2563eb;
            color: white;
            cursor: pointer;
            display: inline-block;
            font-size: 16px;
            font-weight: 700;
            padding: 11px 16px;
            text-decoration: none;
        }}

        .secondary {{
            background: #475569;
        }}

        .danger {{
            background: #dc2626;
            padding: 8px 12px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}

        th,
        td {{
            border: 1px solid #dbe3ef;
            padding: 12px;
            text-align: left;
        }}

        th {{
            background: #e9eef5;
        }}

        .message {{
            background: #dcfce7;
            border: 1px solid #86efac;
            border-radius: 6px;
            padding: 10px 12px;
        }}

        .empty {{
            color: #64748b;
            text-align: center;
        }}

        .progress {{
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 6px;
            color: #1e3a8a;
            display: none;
            font-size: 14px;
            margin: -12px 0 24px;
            padding: 10px 12px;
        }}

        @media (max-width: 760px) {{
            .actions,
            .session-form,
            .exercise-form {{
                display: grid;
                grid-template-columns: 1fr;
            }}

            table {{
                font-size: 14px;
            }}

            th,
            td {{
                padding: 8px;
            }}
        }}
    </style>
</head>
<body>
    <main>
        <h1>Workout Tracker</h1>
        {message_html}
        {content}
    </main>
</body>
</html>
"""


def render_type_options(selected_type=""):
    options = ""
    for workout_type in WORKOUT_TYPES:
        selected = " selected" if workout_type == selected_type else ""
        options += f'<option value="{workout_type}"{selected}>{workout_type}</option>'
    return options


def render_exercise_options(workout_type=""):
    options = ""
    for exercise_name in get_recent_exercise_names(workout_type):
        options += (
            f'<option value="{escape(exercise_name)}" '
            f'label="Recent {escape(workout_type)}"></option>'
        )

    for exercise_name in get_all_exercise_names():
        options += (
            f'<option value="{escape(exercise_name)}" '
            f'label="All exercises"></option>'
        )

    return options


def render_latest_performance_script():
    latest_performance = json.dumps(get_recent_performances_by_exercise())
    latest_performance = latest_performance.replace("<", "\\u003c")

    return f"""
        <script>
            const latestPerformance = {latest_performance};
            const exerciseInput = document.querySelector("[name='exercise']");
            const progressBox = document.querySelector("#latest-performance");

            function updateLatestPerformance() {{
                const exerciseName = exerciseInput.value.trim().toLowerCase();
                const performances = latestPerformance[exerciseName];

                if (!performances) {{
                    progressBox.style.display = "none";
                    progressBox.textContent = "";
                    return;
                }}

                progressBox.style.display = "block";
                progressBox.innerHTML = "<strong>Most recent:</strong><br>" +
                    performances.map((performance) =>
                        `${{performance.date}} (${{performance.type}}) - ` +
                        performance.summary
                    ).join("<br>");
            }}

            exerciseInput.addEventListener("input", updateLatestPerformance);
            exerciseInput.addEventListener("change", updateLatestPerformance);
        </script>
"""


def render_home_page(message=""):
    content = f"""
        <div class="actions">
            <a class="button secondary" href="/sessions">View sessions</a>
        </div>
        <h2>Create workout session</h2>
        <form class="session-form" method="post" action="/sessions/create">
            <label>
                Date
                <input type="date" name="workout_date" value="{date.today().isoformat()}" required>
            </label>
            <label>
                Type
                <select name="workout_type" required>
                    {render_type_options()}
                </select>
            </label>
            <button type="submit">Create</button>
        </form>
"""
    return render_layout(content, message)


def render_sessions_page(message=""):
    sessions = get_sessions()
    rows = ""

    for session in sessions:
        rows += f"""
            <tr>
                <td>{session["id"]}</td>
                <td>{escape(session["workout_date"])}</td>
                <td>{escape(session["workout_type"])}</td>
                <td>{session["exercise_count"]}</td>
                <td>
                    <a class="button secondary" href="/session?id={session["id"]}">Open</a>
                </td>
                <td>
                    <form class="delete-form" method="post" action="/sessions/delete">
                        <input type="hidden" name="id" value="{session["id"]}">
                        <button class="danger" type="submit">Delete</button>
                    </form>
                </td>
            </tr>
        """

    if not rows:
        rows = """
            <tr>
                <td colspan="6" class="empty">No sessions yet.</td>
            </tr>
        """

    content = f"""
        <div class="actions">
            <a class="button secondary" href="/">Create session</a>
        </div>
        <table>
            <thead>
                <tr>
                    <th>id</th>
                    <th>date</th>
                    <th>type</th>
                    <th>exercises</th>
                    <th>open</th>
                    <th>delete</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
"""
    return render_layout(content, message)


def render_session_page(session_id, message=""):
    session = get_session(session_id)
    if not session:
        return render_sessions_page("Session not found.")

    exercises = get_session_exercises(session_id)
    rows = ""
    is_cardio = session["workout_type"] == "Cardio"

    for exercise in exercises:
        if is_cardio:
            rows += f"""
                <tr>
                    <td>{exercise["id"]}</td>
                    <td>{escape(exercise["exercise"])}</td>
                    <td>{escape(exercise["duration"])} min</td>
                    <td>
                        <form class="delete-form" method="post" action="/exercises/delete">
                            <input type="hidden" name="id" value="{exercise["id"]}">
                            <input type="hidden" name="session_id" value="{session_id}">
                            <button class="danger" type="submit">Delete</button>
                        </form>
                    </td>
                </tr>
            """
        else:
            rows += f"""
                <tr>
                    <td>{exercise["id"]}</td>
                    <td>{escape(exercise["exercise"])}</td>
                    <td>{escape(exercise["sets"])}</td>
                    <td>{escape(exercise["reps"])}</td>
                    <td>{escape(exercise["weight"])} kg</td>
                    <td>
                        <form class="delete-form" method="post" action="/exercises/delete">
                            <input type="hidden" name="id" value="{exercise["id"]}">
                            <input type="hidden" name="session_id" value="{session_id}">
                            <button class="danger" type="submit">Delete</button>
                        </form>
                    </td>
                </tr>
            """

    if not rows:
        column_count = 4 if is_cardio else 6
        rows = """
            <tr>
                <td colspan="{column_count}" class="empty">No exercises in this session yet.</td>
            </tr>
        """.format(column_count=column_count)

    if is_cardio:
        exercise_fields = """
            <label>
                Duration
                <input name="duration" required>
            </label>
        """
        table_headers = """
            <tr>
                <th>id</th>
                <th>exercise</th>
                <th>duration</th>
                <th>delete</th>
            </tr>
        """
    else:
        exercise_fields = """
            <label>
                Sets
                <input name="sets" required>
            </label>
            <label>
                Reps
                <input name="reps" required>
            </label>
            <label>
                Weight
                <input name="weight" required>
            </label>
        """
        table_headers = """
            <tr>
                <th>id</th>
                <th>exercise</th>
                <th>sets</th>
                <th>reps</th>
                <th>weight</th>
                <th>delete</th>
            </tr>
        """

    content = f"""
        <div class="actions">
            <a class="button secondary" href="/sessions">View sessions</a>
            <a class="button secondary" href="/">Create session</a>
        </div>
        <h2>{escape(session["workout_date"])} - {escape(session["workout_type"])}</h2>
        <form class="exercise-form" method="post" action="/exercises/add">
            <input type="hidden" name="session_id" value="{session_id}">
            <label>
                Exercise
                <input name="exercise" list="exercise-options" required>
                <datalist id="exercise-options">
                    {render_exercise_options(session["workout_type"])}
                </datalist>
            </label>
            {exercise_fields}
            <button type="submit">Add</button>
        </form>
        <div id="latest-performance" class="progress"></div>
        <table>
            <thead>
                {table_headers}
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        {render_latest_performance_script()}
"""
    return render_layout(content, message)


@app.route("/")
def home():
    return render_home_page()


@app.route("/sessions")
def sessions():
    return render_sessions_page()


@app.route("/session")
def session_page():
    session_id = request.args.get("id", "")

    if session_id.isdigit():
        return render_session_page(int(session_id))

    return render_sessions_page("Session not found.")


@app.post("/sessions/create")
def create_session_route():
    workout_date = request.form.get("workout_date", "").strip()
    workout_type = request.form.get("workout_type", "").strip()

    if workout_date and workout_type in WORKOUT_TYPES:
        session_id = create_session(workout_date, workout_type)
        return redirect(f"/session?id={session_id}")

    return render_home_page("Please choose a date and type.")


@app.post("/sessions/delete")
def delete_session_route():
    session_id = request.form.get("id", "").strip()

    if session_id.isdigit():
        delete_session(int(session_id))
        return render_sessions_page("Session deleted.")

    return render_sessions_page("Could not delete session.")


@app.post("/exercises/add")
def add_exercise_route():
    session_id = request.form.get("session_id", "").strip()
    exercise = request.form.get("exercise", "").strip()
    sets = request.form.get("sets", "").strip()
    reps = request.form.get("reps", "").strip()
    weight = request.form.get("weight", "").strip()
    duration = request.form.get("duration", "").strip()

    if not session_id.isdigit() or not exercise:
        return render_sessions_page("Please fill out every field.")

    session = get_session(int(session_id))
    if not session:
        return render_sessions_page("Session not found.")

    if session["workout_type"] == "Cardio":
        if duration:
            add_exercise(int(session_id), exercise, duration=duration)
            return render_session_page(int(session_id), "Exercise saved.")

        return render_session_page(int(session_id), "Please enter a duration.")

    if sets and reps and weight:
        add_exercise(int(session_id), exercise, sets, reps, weight)
        return render_session_page(int(session_id), "Exercise saved.")

    return render_session_page(int(session_id), "Please fill out every field.")


@app.post("/exercises/delete")
def delete_exercise_route():
    exercise_id = request.form.get("id", "").strip()
    session_id = request.form.get("session_id", "").strip()

    if exercise_id.isdigit() and session_id.isdigit():
        delete_exercise(int(exercise_id))
        return render_session_page(int(session_id), "Exercise deleted.")

    return render_sessions_page("Could not delete exercise.")


def main():
    setup_database()
    print("Open http://localhost:8000 in Chrome or Safari")
    app.run(host="localhost", port=8000, debug=True, use_reloader=False)


setup_database()


if __name__ == "__main__":
    main()
