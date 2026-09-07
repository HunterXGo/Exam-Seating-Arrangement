# ExamFlow — AI-Based Examination Seating

A full-stack examination seating application powered by Google OR-Tools CP-SAT. It assigns every student to a valid physical seat while enforcing capacity, unavailable-seat, and accessibility constraints, and minimizing department and nearby-roll-number adjacency.

## Run locally

1. Start the API:
   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
2. In another terminal start the web app:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
3. Open `http://localhost:5173`.

## Test the optimizer

```bash
cd backend
pytest -q
```

The API documentation is available at `http://localhost:8000/docs`. SQLite is the default persistence layer; set `DATABASE_URL` to a PostgreSQL connection string to migrate later.

## Load 100 sample students, classrooms, and subjects

With the backend virtual environment active, run:

```bash
cd backend
python sample_data.py
```

This adds (without deleting existing data): 100 Year-2 students across CSE, ECE, ME, and CIV; two 5×10 engineering halls; and four subject exams—Data Structures, Digital Electronics, Thermodynamics, and Structural Analysis. Each subject exam contains only the 25 students from its branch.

### Roll-number strategy

The solver preserves original roll numbers and extracts digit groups for proximity optimization (for example, `CSE-A-23001` becomes `23001`). IDs with no digits are excluded from roll-distance penalties, never rejected.
