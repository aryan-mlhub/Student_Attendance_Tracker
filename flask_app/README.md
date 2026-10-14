# Student Attendance Tracker (Flask Edition)

A complete, functional, responsive Student Attendance Tracker web application built for college Python subject project evaluation.

Developed using **Python 3**, **Flask**, **SQLite**, and **Tailwind CSS**, this edition features full student management, attendance recording with overwrite protection, multi-format bulk imports (CSV, TXT, text-based PDF via `pypdf`, and Excel via `openpyxl`), analytics reporting with university deficit rules (< 75%), and CSV report export.

---

## 1. Mandatory Technology Stack

### Frontend
- **HTML5 & Jinja2 Templates:** Modular layouts with template inheritance (`base.html`).
- **Tailwind CSS:** Responsive styling using utility classes, featuring a deep navy/slate sidebar, light neutral page backgrounds, and emerald/rose/amber status indicators.
- **Accessible UI:** Native HTML5 `<dialog>` elements for accessible confirmation dialogs.
- **Vanilla JavaScript:** Client-side helpers for bulk attendance toggling, toast dismissals, and mobile menu interaction.

### Backend
- **Python 3.10+:** 100% of the business logic, attendance computations, parsing, and data validation runs in Python.
- **Flask Framework:** RESTful routing, session management, CSRF protection, and error handling.
- **SQLite 3:** Relational database with enabled foreign key constraints (`PRAGMA foreign_keys = ON;`), transactions, and uniqueness rules.
- **pypdf (v6.20+):** Text extraction from PDF rosters.
- **openpyxl:** Parsing Excel spreadsheets (`.xlsx`).

---

## 2. Key Features

### A. Dashboard
- Total number of registered students.
- Date selector with quick **Today** and **Yesterday** buttons.
- Real-time counts: **Present**, **Absent**, **On Leave**, and **Unmarked**.
- Attendance percentage calculation for the selected date.
- Color-coded progress bar visualizing attendance distribution.
- **Attendance Deficit Warning Banner:** Highlights students below the mandatory 75% college requirement.
- Recent attendance sessions table with direct links to edit historical sheets.

### B. Student Management
- **Add & Edit Students:** Capture Roll Number, Full Name, Class/Department, and Section.
- **Duplicate Prevention:** Case-insensitive validation preventing duplicate roll numbers across the institution.
- **Search & Filter:** Instant search by roll number or name, filter by class/branch and section.
- **Dynamic Sorting:** Sort columns by Roll Number, Full Name, Class, or Enrollment Date.
- **Individual Student Profile:** View attendance performance, percentage, and full chronological attendance history.
- **Safe Deletion:** Accessible confirmation dialog before deleting records (cascades to attendance).

### C. Attendance Management
- Select any attendance date.
- Mark **Present**, **Absent**, or **Leave** with radio pill toggles.
- **Bulk Actions:** One-click buttons to "Mark All Present", "Mark All Absent", or "Mark All Leave".
- **Duplicate Prevention:** SQLite compound unique constraint on `(student_id, attendance_date)` with atomic `UPSERT` operations.
- **Historical Overwrite Confirmation:** Warning modal and notification before modifying past attendance records.

### D. Bulk Import Pipeline
- Support for **CSV**, **TXT** (comma, pipe, tab, or key-value format), **PDF** (text-based), and **Excel (.xlsx)**.
- **Validation Engine:** Automatically detects missing fields, duplicate roll numbers within the file, and conflicts with existing database records.
- **Interactive Preview Table:** View all parsed rows with color-coded status badges before committing.
- **Duplicate Resolution Options:** Choose between "Skip existing records" or "Update existing records with new data".
- **Scanned PDF Detection:** Accurately alerts when a PDF contains no selectable text (scanned image) and explains OCR requirements.
- **Sample Downloads:** Built-in download links for sample CSV, TXT, and PDF files.

### E. Reports & Defaulter Tracking
- **Date-Range Filtering:** Filter attendance between Start Date and End Date.
- **Defaulters Toggle:** Isolate students below the 75% attendance threshold with one click.
- **College Attendance Formula:**
  $$\text{Attendance Percentage} = \frac{\text{Present Days}}{\text{Present Days} + \text{Absent Days}} \times 100$$
  *(Approved leave days are excluded from the denominator).*
- **CSV Report Export:** Generates RFC 4180-compliant CSV files for administration.

---

## 3. Project Directory Structure

```text
flask_app/
├── app.py                      # Core Flask application, routes, and error handlers
├── database.py                 # SQLite database, StudentManager, AttendanceManager, PDFParser, BulkImportManager, ReportsManager
├── requirements.txt            # Python dependencies (Flask, pypdf, openpyxl, gunicorn)
├── README.md                   # Complete documentation and deployment guide
├── .gitignore                  # Git ignore rules for virtualenvs, local databases, and temporary uploads
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Master layout with deep slate sidebar & accessible dialog modal
│   ├── dashboard.html          # Key metrics, date selector, progress bar, recent sessions
│   ├── students.html           # Student directory, search, filter, sort, pagination
│   ├── student_form.html       # Add/Edit student form with server-side validation
│   ├── student_detail.html     # Individual student attendance profile & history log
│   ├── attendance.html         # Daily attendance marking sheet with bulk actions & overwrite guard
│   ├── history.html            # Chronological attendance sessions archive
│   ├── bulk_import.html        # Multi-format upload, preview table, duplicate handling
│   ├── reports.html            # Attendance analytics, <75% defaulters filter, CSV export
│   ├── 404.html                # Friendly 404 page
│   └── 500.html                # Error page with transaction safety notes
└── static/
    ├── css/
    │   └── custom.css          # Custom fonts, scrollbars, dialog backdrop styling
    ├── js/
    │   └── main.js             # Client-side interactions (dialogs, bulk mark, toasts)
    ├── uploads/                # Temporary file uploads (auto-cleaned)
    └── samples/                # Sample test templates (CSV, TXT, PDF, Scanned PDF)
```

---

## 4. Local Installation and Setup

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14 installed
- pip package manager

### Step 1: Navigate to the `flask_app` Directory
```bash
cd flask_app
```

### Step 2: Create and Activate a Virtual Environment
- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Development Server
```bash
python app.py
```
Open your web browser and navigate to:
```text
http://127.0.0.1:5000/
```

*Note: On first launch, if the database is brand new, demo students across CSE and ECE with 5 days of realistic attendance records will automatically be seeded.*

---

## 5. Running Automated Tests

Run the unit and integration test suite:
```bash
# Run Flask app specific tests:
python -m unittest tests/test_flask_app.py

# Run all workspace tests (50 tests total):
python -m unittest discover -s tests -p "test_*.py"
```

---

## 6. GitHub Upload Instructions

To upload this project to your GitHub repository:

```bash
# Initialize git if not already initialized
git init

# Add all files (the provided .gitignore safely ignores .venv, *.db, and temporary uploads)
git add flask_app/ tests/

# Commit changes
git commit -m "Add full-stack Flask Student Attendance Tracker with Tailwind CSS"

# Add your GitHub repository remote
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPOSITORY_NAME>.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## 7. Online Deployment Guide

> **Important Deployment Note:** GitHub Pages only hosts static HTML/JS/CSS files and **cannot** execute Python Flask backend code. You must host this application on a Python-compatible web platform.

### Option A: Deploy on Render.com (Recommended Free/Low-Cost Python Host)
1. Push your project to GitHub.
2. Sign in to [Render](https://render.com/) and click **New > Web Service**.
3. Connect your GitHub repository.
4. Configure the service:
   - **Root Directory:** `flask_app`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -w 2 -b 0.0.0.0:$PORT app:app`
5. **Persistent Storage (Crucial for SQLite):**
   - Under the **Disks** tab, add a Persistent Disk (e.g. `/var/data`).
   - Under **Environment Variables**, add:
     - `ATTENDANCE_DB_PATH`: `/var/data/attendance_tracker.db`
     - `SECRET_KEY`: `<Generate a random 32-character string>`
6. Click **Create Web Service**. Render will build and deploy the live web application.

### Option B: Deploy on PythonAnywhere.com
1. Create a free account at [PythonAnywhere](https://www.pythonanywhere.com/).
2. Open a Bash console and clone your repository:
   ```bash
   git clone https://github.com/<YOUR_USERNAME>/<REPO_NAME>.git
   cd <REPO_NAME>/flask_app
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Go to the **Web** tab and click **Add a new web app**, selecting **Flask** and **Python 3**.
4. In the WSGI configuration file (`/var/www/<username>_pythonanywhere_com_wsgi.py`), set:
   ```python
   import sys
   path = '/home/<username>/<REPO_NAME>/flask_app'
   if path not in sys.path:
       sys.path.append(path)
   from app import app as application
   ```
5. Reload the web app and view it live at `https://<username>.pythonanywhere.com`.

---

## 8. College Project Evaluation Notes

- **Separation of Concerns:** Business logic, document parsing, and database transactions are encapsulated in `database.py`, keeping `app.py` dedicated to routing and presentation.
- **SQL Injection Prevention:** Every query uses parameterized inputs (`?` placeholders).
- **Data Integrity:** Cascading deletes prevent orphaned attendance records when a student is removed.
- **University Examination Compliance:** The 75% attendance threshold calculation faithfully adheres to college attendance ordinances.
