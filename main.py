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


def add_workout(workouts):
    exercise = input("Exercise: ").strip()
    sets = input("Sets: ").strip()
    reps = input("Reps: ").strip()
    weight = input("Weight: ").strip()

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

    for index, workout in enumerate(workouts, start=1):
        print(
            f"{index}. {workout['date']} - "
            f"{workout['exercise']}: {workout['sets']} sets x "
            f"{workout['reps']} reps @ {workout['weight']}"
        )


def show_menu():
    print("\nWorkout Tracker")
    print("1. Add workout")
    print("2. List workouts")
    print("3. Quit")


def main():
    workouts = load_workouts()

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_workout(workouts)
        elif choice == "2":
            list_workouts(workouts)
        elif choice == "3":
            print("Goodbye.")
            break
        else:
            print("Please choose 1, 2, or 3.")


if __name__ == "__main__":
    main()
