const STORAGE_KEY = "workoutTrackerData";
const WORKOUT_TYPES = ["Push", "Pull", "Legs", "Arms", "Back", "Cardio", "Other"];
const EXERCISES = {
    Push: [
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
    Pull: [
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
    Legs: [
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
    Arms: [
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
    Back: [
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
    Cardio: [
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
    Other: [
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
};

const state = loadData();
let activeSessionId = null;

const createSessionPanel = document.querySelector("#create-session-panel");
const sessionsPanel = document.querySelector("#sessions-panel");
const sessionPanel = document.querySelector("#session-panel");
const sessionForm = document.querySelector("#session-form");
const sessionDate = document.querySelector("#session-date");
const sessionsList = document.querySelector("#sessions-list");
const activeSessionTitle = document.querySelector("#active-session-title");
const exerciseForm = document.querySelector("#exercise-form");
const exerciseName = document.querySelector("#exercise-name");
const exerciseOptions = document.querySelector("#exercise-options");
const strengthFields = document.querySelector("#strength-fields");
const cardioFields = document.querySelector("#cardio-fields");
const exerciseSets = document.querySelector("#exercise-sets");
const exerciseReps = document.querySelector("#exercise-reps");
const exerciseWeight = document.querySelector("#exercise-weight");
const exerciseDuration = document.querySelector("#exercise-duration");
const exerciseList = document.querySelector("#exercise-list");
const latestPerformance = document.querySelector("#latest-performance");
const message = document.querySelector("#message");

sessionDate.value = new Date().toISOString().slice(0, 10);

document.querySelector("#create-session-view").addEventListener("click", showCreateSession);
document.querySelector("#sessions-view").addEventListener("click", showSessions);
document.querySelector("#back-to-sessions").addEventListener("click", showSessions);
sessionForm.addEventListener("submit", createSession);
exerciseForm.addEventListener("submit", addExercise);
exerciseName.addEventListener("input", updateLatestPerformance);
exerciseName.addEventListener("change", updateLatestPerformance);

showCreateSession();

function loadData() {
    const saved = localStorage.getItem(STORAGE_KEY);

    if (!saved) {
        return { nextSessionId: 1, nextExerciseId: 1, sessions: [] };
    }

    return JSON.parse(saved);
}

function saveData() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function showMessage(text) {
    message.textContent = text;
    message.hidden = false;
}

function clearMessage() {
    message.hidden = true;
    message.textContent = "";
}

function showCreateSession() {
    clearMessage();
    createSessionPanel.hidden = false;
    sessionsPanel.hidden = true;
    sessionPanel.hidden = true;
}

function showSessions() {
    clearMessage();
    createSessionPanel.hidden = true;
    sessionsPanel.hidden = false;
    sessionPanel.hidden = true;
    renderSessions();
}

function showSession(sessionId) {
    clearMessage();
    activeSessionId = sessionId;
    createSessionPanel.hidden = true;
    sessionsPanel.hidden = true;
    sessionPanel.hidden = false;
    renderSession();
}

function createSession(event) {
    event.preventDefault();
    const formData = new FormData(sessionForm);
    const session = {
        id: state.nextSessionId,
        date: formData.get("workout_date"),
        type: formData.get("workout_type"),
        exercises: [],
    };

    state.nextSessionId += 1;
    state.sessions.push(session);
    saveData();
    sessionForm.reset();
    sessionDate.value = new Date().toISOString().slice(0, 10);
    showSession(session.id);
    showMessage("Session created.");
}

function addExercise(event) {
    event.preventDefault();
    const session = getActiveSession();
    const name = exerciseName.value.trim();

    if (!session || !name) {
        return;
    }

    const exercise = {
        id: state.nextExerciseId,
        name,
        sets: "",
        reps: "",
        weight: "",
        duration: "",
    };

    if (session.type === "Cardio") {
        exercise.duration = exerciseDuration.value.trim();

        if (!exercise.duration) {
            showMessage("Please enter a duration.");
            return;
        }
    } else {
        exercise.sets = exerciseSets.value.trim();
        exercise.reps = exerciseReps.value.trim();
        exercise.weight = exerciseWeight.value.trim();

        if (!exercise.sets || !exercise.reps || !exercise.weight) {
            showMessage("Please fill out every field.");
            return;
        }
    }

    state.nextExerciseId += 1;
    session.exercises.push(exercise);
    saveData();
    exerciseForm.reset();
    latestPerformance.hidden = true;
    renderSession();
    showMessage("Exercise saved.");
}

function deleteSession(sessionId) {
    state.sessions = state.sessions.filter((session) => session.id !== sessionId);
    saveData();
    renderSessions();
    showMessage("Session deleted.");
}

function deleteExercise(exerciseId) {
    const session = getActiveSession();

    if (!session) {
        return;
    }

    session.exercises = session.exercises.filter((exercise) => exercise.id !== exerciseId);
    saveData();
    renderSession();
    showMessage("Exercise deleted.");
}

function renderSessions() {
    const sessions = [...state.sessions].sort((a, b) => {
        if (a.date === b.date) {
            return b.id - a.id;
        }

        return b.date.localeCompare(a.date);
    });

    if (!sessions.length) {
        sessionsList.innerHTML = "<p class='empty'>No sessions yet.</p>";
        return;
    }

    sessionsList.innerHTML = `
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
                ${sessions.map((session) => `
                    <tr>
                        <td>${session.id}</td>
                        <td>${escapeHtml(session.date)}</td>
                        <td>${escapeHtml(session.type)}</td>
                        <td>${session.exercises.length}</td>
                        <td><button class="secondary" data-open="${session.id}" type="button">Open</button></td>
                        <td><button class="danger" data-delete-session="${session.id}" type="button">Delete</button></td>
                    </tr>
                `).join("")}
            </tbody>
        </table>
    `;

    sessionsList.querySelectorAll("[data-open]").forEach((button) => {
        button.addEventListener("click", () => showSession(Number(button.dataset.open)));
    });
    sessionsList.querySelectorAll("[data-delete-session]").forEach((button) => {
        button.addEventListener("click", () => deleteSession(Number(button.dataset.deleteSession)));
    });
}

function renderSession() {
    const session = getActiveSession();

    if (!session) {
        showSessions();
        return;
    }

    const isCardio = session.type === "Cardio";
    activeSessionTitle.textContent = `${session.date} - ${session.type}`;
    strengthFields.hidden = isCardio;
    cardioFields.hidden = !isCardio;
    exerciseSets.required = !isCardio;
    exerciseReps.required = !isCardio;
    exerciseWeight.required = !isCardio;
    exerciseDuration.required = isCardio;
    renderExerciseOptions(session.type);
    renderExerciseTable(session);
}

function renderExerciseTable(session) {
    if (!session.exercises.length) {
        exerciseList.innerHTML = "<p class='empty'>No exercises in this session yet.</p>";
        return;
    }

    if (session.type === "Cardio") {
        exerciseList.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>id</th>
                        <th>exercise</th>
                        <th>duration</th>
                        <th>delete</th>
                    </tr>
                </thead>
                <tbody>
                    ${session.exercises.map((exercise) => `
                        <tr>
                            <td>${exercise.id}</td>
                            <td>${escapeHtml(exercise.name)}</td>
                            <td>${escapeHtml(exercise.duration)} min</td>
                            <td><button class="danger" data-delete-exercise="${exercise.id}" type="button">Delete</button></td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;
    } else {
        exerciseList.innerHTML = `
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
                    ${session.exercises.map((exercise) => `
                        <tr>
                            <td>${exercise.id}</td>
                            <td>${escapeHtml(exercise.name)}</td>
                            <td>${escapeHtml(exercise.sets)}</td>
                            <td>${escapeHtml(exercise.reps)}</td>
                            <td>${escapeHtml(exercise.weight)} kg</td>
                            <td><button class="danger" data-delete-exercise="${exercise.id}" type="button">Delete</button></td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;
    }

    exerciseList.querySelectorAll("[data-delete-exercise]").forEach((button) => {
        button.addEventListener("click", () => deleteExercise(Number(button.dataset.deleteExercise)));
    });
}

function renderExerciseOptions(workoutType) {
    const recentNames = getRecentExerciseNames(workoutType);
    const allNames = getAllExerciseNames();
    const options = [];

    recentNames.forEach((name) => {
        options.push(`<option value="${escapeHtml(name)}" label="Recent ${escapeHtml(workoutType)}"></option>`);
    });
    allNames.forEach((name) => {
        options.push(`<option value="${escapeHtml(name)}" label="All exercises"></option>`);
    });

    exerciseOptions.innerHTML = options.join("");
}

function getRecentExerciseNames(workoutType) {
    const seen = new Set();
    const rows = [];

    state.sessions.forEach((session) => {
        if (session.type !== workoutType) {
            return;
        }

        session.exercises.forEach((exercise) => {
            rows.push({ name: exercise.name, date: session.date, id: exercise.id });
        });
    });

    rows.sort((a, b) => {
        if (a.date === b.date) {
            return b.id - a.id;
        }

        return b.date.localeCompare(a.date);
    });

    return rows
        .filter((row) => {
            const key = row.name.toLowerCase();

            if (seen.has(key)) {
                return false;
            }

            seen.add(key);
            return true;
        })
        .map((row) => row.name);
}

function getAllExerciseNames() {
    const names = Object.values(EXERCISES).flat();
    state.sessions.forEach((session) => {
        session.exercises.forEach((exercise) => names.push(exercise.name));
    });

    const seen = new Set();
    return names
        .sort((a, b) => a.localeCompare(b))
        .filter((name) => {
            const key = name.toLowerCase();

            if (seen.has(key)) {
                return false;
            }

            seen.add(key);
            return true;
        });
}

function updateLatestPerformance() {
    const name = exerciseName.value.trim().toLowerCase();
    const performances = getRecentPerformances(name);

    if (!performances.length) {
        latestPerformance.hidden = true;
        latestPerformance.innerHTML = "";
        return;
    }

    latestPerformance.hidden = false;
    latestPerformance.innerHTML = `
        <strong>Most recent:</strong><br>
        ${performances.map((performance) => (
            `${formatDisplayDate(performance.date)} (${escapeHtml(performance.type)}) - ${escapeHtml(performance.summary)}`
        )).join("<br>")}
    `;
}

function getRecentPerformances(exerciseNameLower) {
    const rows = [];

    state.sessions.forEach((session) => {
        session.exercises.forEach((exercise) => {
            if (exercise.name.toLowerCase() !== exerciseNameLower) {
                return;
            }

            const summary = session.type === "Cardio"
                ? `${exercise.duration} min`
                : `${exercise.sets} sets x ${exercise.reps} reps @ ${exercise.weight} kg`;
            rows.push({
                date: session.date,
                id: exercise.id,
                type: session.type,
                summary,
            });
        });
    });

    return rows
        .sort((a, b) => {
            if (a.date === b.date) {
                return b.id - a.id;
            }

            return b.date.localeCompare(a.date);
        })
        .slice(0, 3);
}

function getActiveSession() {
    return state.sessions.find((session) => session.id === activeSessionId);
}

function formatDisplayDate(dateText) {
    const parsedDate = new Date(`${dateText}T00:00:00`);
    const day = parsedDate.getDate();
    const suffix = getDaySuffix(day);

    return parsedDate.toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
    }) + ` ${day}${suffix} ${parsedDate.getFullYear()}`;
}

function getDaySuffix(day) {
    if (day % 100 >= 10 && day % 100 <= 20) {
        return "th";
    }

    return { 1: "st", 2: "nd", 3: "rd" }[day % 10] || "th";
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
