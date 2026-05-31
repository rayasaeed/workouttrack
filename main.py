import sqlite3
from datetime import date
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


DB_FILE = "workouts.db"
HOST = "localhost"
PORT = 8000
WORKOUT_TYPES = ["Push", "Pull", "Legs", "Arms", "Back", "Cardio", "Other"]


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
                FOREIGN KEY (session_id)
                    REFERENCES workout_sessions (id)
                    ON DELETE CASCADE
            )
            """
        )
        migrate_old_workouts(connection)


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
                (session_id, exercise, sets, reps, weight)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_ids[workout_date], exercise, sets, reps, weight),
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


def add_exercise(session_id, exercise, sets, reps, weight):
    with connect_database() as connection:
        connection.execute(
            """
            INSERT INTO workout_exercises
                (session_id, exercise, sets, reps, weight)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, exercise, sets, reps, weight),
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
            SELECT id, exercise, sets, reps, weight
            FROM workout_exercises
            WHERE session_id = ?
            ORDER BY id
            """,
            (session_id,),
        ).fetchall()


def get_exercise_names(workout_type=""):
    with connect_database() as connection:
        rows = connection.execute(
            """
            SELECT
                workout_exercises.exercise,
                MAX(
                    CASE
                        WHEN workout_sessions.workout_type = ? THEN 1
                        ELSE 0
                    END
                ) AS type_match
            FROM workout_exercises
            JOIN workout_sessions
                ON workout_sessions.id = workout_exercises.session_id
            GROUP BY workout_exercises.exercise
            ORDER BY type_match DESC, workout_exercises.exercise
            """,
            (workout_type,),
        ).fetchall()

    return [row[0] for row in rows]


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
    for exercise_name in get_exercise_names(workout_type):
        options += f'<option value="{escape(exercise_name)}"></option>'
    return options


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

    for exercise in exercises:
        rows += f"""
            <tr>
                <td>{exercise["id"]}</td>
                <td>{escape(exercise["exercise"])}</td>
                <td>{escape(exercise["sets"])}</td>
                <td>{escape(exercise["reps"])}</td>
                <td>{escape(exercise["weight"])}</td>
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
        rows = """
            <tr>
                <td colspan="6" class="empty">No exercises in this session yet.</td>
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
            <button type="submit">Add</button>
        </form>
        <table>
            <thead>
                <tr>
                    <th>id</th>
                    <th>exercise</th>
                    <th>sets</th>
                    <th>reps</th>
                    <th>weight</th>
                    <th>delete</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
"""
    return render_layout(content, message)


def get_id_from_query(path):
    query = parse_qs(urlparse(path).query)
    value = query.get("id", [""])[0]
    if value.isdigit():
        return int(value)
    return None


def redirect_to(handler, path):
    handler.send_response(303)
    handler.send_header("Location", path)
    handler.end_headers()


class WorkoutHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path).path

        if parsed_path == "/":
            self.send_html(render_home_page())
            return

        if parsed_path == "/sessions":
            self.send_html(render_sessions_page())
            return

        if parsed_path == "/session":
            session_id = get_id_from_query(self.path)
            if session_id:
                self.send_html(render_session_page(session_id))
            else:
                self.send_html(render_sessions_page("Session not found."))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed_path = urlparse(self.path).path

        if parsed_path == "/sessions/create":
            form = self.read_form()
            workout_date = form.get("workout_date", [""])[0].strip()
            workout_type = form.get("workout_type", [""])[0].strip()

            if workout_date and workout_type in WORKOUT_TYPES:
                session_id = create_session(workout_date, workout_type)
                redirect_to(self, f"/session?id={session_id}")
            else:
                self.send_html(render_home_page("Please choose a date and type."))
            return

        if parsed_path == "/sessions/delete":
            form = self.read_form()
            session_id = form.get("id", [""])[0].strip()

            if session_id.isdigit():
                delete_session(int(session_id))
                self.send_html(render_sessions_page("Session deleted."))
            else:
                self.send_html(render_sessions_page("Could not delete session."))
            return

        if parsed_path == "/exercises/add":
            form = self.read_form()
            session_id = form.get("session_id", [""])[0].strip()
            exercise = form.get("exercise", [""])[0].strip()
            sets = form.get("sets", [""])[0].strip()
            reps = form.get("reps", [""])[0].strip()
            weight = form.get("weight", [""])[0].strip()

            if session_id.isdigit() and exercise and sets and reps and weight:
                add_exercise(int(session_id), exercise, sets, reps, weight)
                self.send_html(render_session_page(int(session_id), "Exercise saved."))
            else:
                self.send_html(render_sessions_page("Please fill out every field."))
            return

        if parsed_path == "/exercises/delete":
            form = self.read_form()
            exercise_id = form.get("id", [""])[0].strip()
            session_id = form.get("session_id", [""])[0].strip()

            if exercise_id.isdigit() and session_id.isdigit():
                delete_exercise(int(exercise_id))
                self.send_html(render_session_page(int(session_id), "Exercise deleted."))
            else:
                self.send_html(render_sessions_page("Could not delete exercise."))
            return

        self.send_response(404)
        self.end_headers()

    def read_form(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        return parse_qs(body)

    def send_html(self, html):
        content = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main():
    setup_database()
    server = HTTPServer((HOST, PORT), WorkoutHandler)
    print(f"Open http://{HOST}:{PORT} in Chrome or Safari")
    server.serve_forever()


if __name__ == "__main__":
    main()
