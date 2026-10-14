# 🎓 Student Attendance Tracker

A responsive full-stack Python web application for college attendance management, faculty record-keeping, and academic reporting. Built with **HTML5, Tailwind CSS, Python 3, Flask, and SQLite**.

---

## 🏗️ Architecture & Technology Stack

```
Frontend: HTML5 + Tailwind CSS + Vanilla JS (Modals & Toast Notifications)
Backend:  Python 3 + Flask Framework
Database: SQLite (attendance_tracker.db) with Foreign Key Constraints & Cascades
Deploy:   Vercel Serverless (@vercel/python) / Render / Python WSGI
```

- **Backend**: Python 3 standard libraries + Flask (all business logic, validation, calculations, and database transactions executed in Python).
- **Frontend**: Responsive Jinja2 templates styled with Tailwind CSS; zero JavaScript frameworks (no React, Vue, or Angular).
- **Parsers**: Multi-format document parser supporting CSV, TXT, text-based PDF via `pypdf`, and Excel via `openpyxl`.
- **Database**: Atomic SQLite transactions with PRAGMA `foreign_keys = ON` ensuring complete referential integrity.

---

## ⚡ Quick Start

### 1. Clone & Navigate
```bash
git clone https://github.com/aryan-mlhub/Student_Attendance_Tracker.git
cd Student_Attendance_Tracker
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Application
```bash
python app.py
```
*(Or run `python main.py`)*

Open your browser and navigate to:
```
http://127.0.0.1:5000  (or http://127.0.0.1:5001 if port 5000 is occupied)
```

---

## 🌟 Key Features

### 1. 📊 Real-Time Dashboard
- **Key Metrics**: Total registered students, students present today, students absent today, and students on approved leave.
- **Attendance Rate**: Live daily percentage calculation with visual progress bar.
- **Attendance Deficit Alert Banner**: Prominently warns faculty if any student falls below the mandatory **75% attendance threshold**.
- **Date Switcher**: Fast navigation between Today, Yesterday, or any historical date.

### 2. 👥 Student Directory & Management
- **Full CRUD**: Add, edit, view, and delete students with cascading removal of attendance records.
- **Duplicate Prevention**: Enforces unique roll numbers (`COLLATE NOCASE`) with server-side error feedback.
- **Search & Filters**: Instant search by roll number or name, filterable by class and section.
- **Student Profile**: Individual student attendance history, overall attendance percentage, and status indicators.

### 3. 📅 Class Attendance Marking
- **Three Statuses Supported**: **Present (P)**, **Absent (A)**, and **Leave (L)**.
- **Fast Batch Actions**: **Mark All Present**, **Mark All Absent**, or reset selections with one click.
- **Overwrite Guard**: Built-in modal warning prevents accidental overwriting of previously submitted attendance.

### 4. 📥 Multi-Format Bulk Import
- **Supported Formats**:
  - `.csv`: Automatic header detection (`Roll No`, `Student Name`, `Class`, `Section`).
  - `.txt`: Key-value pipe formats (`Roll No: 101 | Name: Rahul | Class: CSE | Section: A`) and comma/tab-delimited records.
  - `.pdf`: Structured text extraction using `pypdf`, filtering headers/footers.
  - `.xlsx`: Native Excel import via `openpyxl`.
- **Scanned PDF Detection**: Identifies image-only scanned PDFs and provides actionable guidance.
- **Interactive Preview Table**: Review extracted data with validation badges before committing.
- **Duplicate Handling**: Choose between **Skip duplicates** or **Update existing student details**.
- **Transactional Safety**: Atomic database commit rolls back all changes if any error occurs.

### 5. 📈 Reports, Defaulter Analytics & CSV Export
- **Attendance Formula**:
  $$\text{Attendance \%} = \frac{\text{Present Days}}{\text{Present Days} + \text{Absent Days}} \times 100$$
  *(Approved leaves are excluded from the denominator so students are not penalized).*
- **Defaulter Filter**: One-click checkbox filter to view only students falling below **75% attendance**.
- **CSV Export**: One-click download of the complete attendance report with UTF-8 BOM encoding.

---

## 📂 Project Structure

```text
StudentAttendanceTracker/
├── app.py                      # Flask application entry point, routes & error handlers
├── main.py                     # Primary launcher script (aliases app.py)
├── database.py                 # SQLite database engine, StudentManager, AttendanceManager,
│                               # BulkImportManager, PDFParser & ReportsManager
├── requirements.txt            # Python dependencies (Flask, pypdf, openpyxl, gunicorn)
├── vercel.json                 # Vercel serverless deployment configuration
├── README.md                   # Project documentation
├── .gitignore                  # Git exclusions for databases and caches
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Master layout with responsive sidebar & modals
│   ├── dashboard.html          # Real-time metrics, date picker & session history
│   ├── students.html           # Student directory with search, filter & pagination
│   ├── student_form.html       # Add/Edit student form with server-side validation
│   ├── student_detail.html     # Individual student profile & date-wise attendance log
│   ├── attendance.html         # Daily attendance marking sheet with overwrite guard
│   ├── history.html            # Chronological attendance archive
│   ├── bulk_import.html        # Multi-format upload, preview table & error reporting
│   ├── reports.html            # Attendance analytics, <75% defaulters filter & CSV export
│   ├── 404.html                # Custom 404 error page
│   └── 500.html                # Custom 500 error page
│
├── static/                     # Static web assets
│   ├── css/
│   │   └── custom.css          # Custom scrollbars and modal backdrop styling
│   ├── js/
│   │   └── main.js             # Client-side interactions (dialog modals, toasts, bulk select)
│   ├── samples/                # Downloadable sample roster templates (CSV, TXT, PDF)
│   └── uploads/                # Temporary upload processing directory
│
└── tests/                      # Automated unit and integration test suite
    ├── test_flask_app.py       # Full-stack Flask route, workflow & error tests
    ├── test_database.py        # SQLite schema, transactions & foreign key cascades
    ├── test_attendance.py      # Attendance saving, date statistics & formula tests
    ├── test_parsers.py         # CSV, TXT, text PDF & scanned PDF parser tests
    ├── test_bulk_import.py     # 100+ student batch import, validation & duplicate tests
    ├── test_reports.py         # Attendance percentage & <75% defaulter detection tests
    └── test_e2e_workflow.py    # Complete end-to-end user lifecycle integration test
```

---

## 🧪 Automated Testing

Run the complete test suite:
```bash
python -m unittest discover -s tests -p "test_*.py"
```
All 38 unit and integration tests validate:
- Database creation, foreign key enforcement, and atomic rollbacks.
- Multi-format file parsing (CSV, TXT, PDF, Excel).
- Attendance calculation formulas (Present / (Present + Absent) * 100).
- Defaulter detection (< 75% threshold).
- All Flask HTTP routes, forms, CSRF tokens, and CSV exports.

---

## ☁️ Deployment to Vercel

The application is pre-configured for Vercel deployment with [vercel.json](file:///c:/Users/ADMIN/OneDrive/Desktop/StudentAttendanceTracker/vercel.json):

```bash
npm install -g vercel
vercel
```

During setup, select default settings. Vercel automatically detects `@vercel/python` and serves `app.py`.
