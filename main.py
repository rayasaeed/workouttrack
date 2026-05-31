import json
from datetime import date
from pathlib import Path


DATA_FILE = Path("workouts.json")


def load_workouts():
    if not DATA_FILE.exists():
        return []

    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_workouts(workouts):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(workouts, file, indent=2)


def ask_required(prompt):
    while True:
        answer = input(prompt).strip()

        if answer:
            return answer

        print("Please enter a value.")


def add_workout(workouts):
    print("\nAdd Workout")
    exercise = ask_required("Exercise name: ")
    sets = ask_required("Number of sets: ")
    reps = ask_required("Number of reps: ")
    weight = ask_required("Weight used: ")

    workout = {
        "date": date.today().isoformat(),
        "exercise": exercise,
        "sets": sets,
        "reps": reps,
        "weight": weight,
    }

    workouts.append(workout)
    save_workouts(workouts)
    print("Workout saved.")


def list_workouts(workouts):
    if not workouts:
        print("No workouts yet.")
        return

    workouts_by_date = {}

    for workout in workouts:
        workout_date = workout["date"]
        workouts_by_date.setdefault(workout_date, []).append(workout)

    for workout_date, daily_workouts in workouts_by_date.items():
        print(f"\n{workout_date}")

        for index, workout in enumerate(daily_workouts, start=1):
            print(
                f"  {index}. {workout['exercise']}: "
                f"{workout['sets']} sets x {workout['reps']} reps "
                f"@ {workout['weight']}"
            )


def show_menu():
    print("\nWorkout Tracker")
    print("1. Add workout")
    print("2. List workouts")
    print("Type q to quit")


def main():
    workouts = load_workouts()

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_workout(workouts)
        elif choice == "2":
            list_workouts(workouts)
        elif choice.lower() == "q":
            print("Goodbye.")
            break
        else:
            print("Please choose 1, 2, or q.")


if __name__ == "__main__":
    main()
