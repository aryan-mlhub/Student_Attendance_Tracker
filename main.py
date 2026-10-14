"""
Student Attendance Tracker
Full-Stack Web Application (HTML + Tailwind CSS -> Flask -> SQLite)

Primary entry point for running the Attendance Tracker web application.
"""

from app import app, main
from database import (
    Database,
    StudentManager,
    AttendanceManager,
    BulkImportManager,
    PDFParser,
    ReportsManager,
    ImportValidationStatus,
    DuplicateRollNumberError,
    ValidationError,
    VALID_STATUSES,
    ATTENDANCE_DEFICIT_THRESHOLD,
)

if __name__ == "__main__":
    main()
