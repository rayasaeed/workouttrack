import sqlite3
from datetime import date


DB_FILE = "workouts.db"


def connect_database():
    return sqlite3.connect(DB_FILE)


def setup_database():
    with connect_database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_date TEXT NOT NULL,
                exercise TEXT NOT NULL,
                sets TEXT NOT NULL,
                reps TEXT NOT NULL,
                weight TEXT NOT NULL
            )
            """
        )


def ask_required(prompt):
    while True:
        answer = input(prompt).strip()

        if answer:
            return answer

        print("Please enter a value.")


def add_one_workout(exercise):
    sets = ask_required("Number of sets: ")
    reps = ask_required("Number of reps: ")
    weight = ask_required("Weight used: ")

    with connect_database() as connection:
        connection.execute(
            """
            INSERT INTO workouts (workout_date, exercise, sets, reps, weight)
            VALUES (?, ?, ?, ?, ?)
            """,
            (date.today().isoformat(), exercise, sets, reps, weight),
        )

    print("Workout saved.")


def add_workouts():
    print("\nAdd Workout")
    print("Type q as the exercise name to stop adding workouts.")

    while True:
        exercise = ask_required("Exercise name: ")

        if exercise.lower() == "q":
            break

        add_one_workout(exercise)


def get_workouts():
    with connect_database() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, workout_date, exercise, sets, reps, weight
            FROM workouts
            ORDER BY workout_date, id
            """
        ).fetchall()

    return rows


def print_table(headers, rows):
    column_widths = []

    for index, header in enumerate(headers):
        widest_cell = max(len(str(row[index])) for row in rows)
        column_widths.append(max(len(header), widest_cell))

    header_line = " | ".join(
        header.ljust(column_widths[index])
        for index, header in enumerate(headers)
    )
    separator_line = "-+-".join("-" * width for width in column_widths)

    print(header_line)
    print(separator_line)

    for row in rows:
        print(
            " | ".join(
                str(value).ljust(column_widths[index])
                for index, value in enumerate(row)
            )
        )


def list_workouts():
    workouts = get_workouts()

    if not workouts:
        print("No workouts yet.")
        return

    headers = ["id", "date", "exercise", "sets", "reps", "weight"]
    rows = [
        (
            workout["id"],
            workout["workout_date"],
            workout["exercise"],
            workout["sets"],
            workout["reps"],
            workout["weight"],
        )
        for workout in workouts
    ]

    print()
    print_table(headers, rows)


def show_menu():
    print("\nWorkout Tracker")
    print("1. Add workout")
    print("2. List workouts")
    print("Type q to quit")


def main():
    setup_database()

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_workouts()
        elif choice == "2":
            list_workouts()
        elif choice.lower() == "q":
            print("Goodbye.")
            break
        else:
            print("Please choose 1, 2, or q.")


if __name__ == "__main__":
    main()
