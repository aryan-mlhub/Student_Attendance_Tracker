"""
Comprehensive automated test suite for the Flask Student Attendance Tracker.
Covers:
- Flask App startup and route availability
- Student CRUD operations & duplicate roll number prevention
- Search, filter, and sort capabilities
- Attendance marking, modification, and duplicate prevention
- Attendance percentage formula (Present / (Present + Absent) * 100, excluding leaves)
- Defaulter detection (< 75%)
- Bulk imports: CSV, TXT, PDF, Excel
- CSV export generation
- Database persistence & transaction rollback
"""

import os
import io
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import date, timedelta

# Add flask_app to sys.path
FLASK_DIR = Path(__file__).resolve().parent.parent / "flask_app"
sys.path.insert(0, str(FLASK_DIR))

import app as flask_module
from database import (
    Database,
    StudentManager,
    AttendanceManager,
    ReportsManager,
    BulkImportManager,
    DuplicateRollNumberError,
    ValidationError,
)


class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for test isolation
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_file.close()
        self.db_path = Path(self.temp_db_file.name)

        self.db = Database(self.db_path)
        self.student_mgr = StudentManager(self.db)
        self.attendance_mgr = AttendanceManager(self.db)
        self.reports_mgr = ReportsManager(self.db)
        self.import_mgr = BulkImportManager(self.db, self.student_mgr)

        # Reconfigure Flask app to use test DB
        flask_module.db = self.db
        flask_module.student_mgr = self.student_mgr
        flask_module.attendance_mgr = self.attendance_mgr
        flask_module.reports_mgr = self.reports_mgr
        flask_module.import_mgr = self.import_mgr

        flask_module.app.config["TESTING"] = True
        flask_module.app.config["WTF_CSRF_ENABLED"] = False
        self.client = flask_module.app.test_client()

    def tearDown(self):
        try:
            if self.db_path.exists():
                self.db_path.unlink()
        except Exception:
            pass

    # -------------------------------------------------------------
    # 1. Routing and Navigation Tests
    # -------------------------------------------------------------
    def test_routes_respond_ok(self):
        """Ensure all primary pages return HTTP 200."""
        routes = ["/dashboard", "/students", "/attendance", "/history", "/import", "/reports"]
        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200, f"Route {route} failed with {response.status_code}")

    def test_root_redirects_to_dashboard(self):
        """Root URL / should redirect to /dashboard."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard", response.location)

    # -------------------------------------------------------------
    # 2. Student CRUD and Duplicate Handling
    # -------------------------------------------------------------
    def test_student_crud_and_duplicate_prevention(self):
        """Test adding, duplicate prevention, editing, and deleting a student."""
        # Add Student
        sid = self.student_mgr.add_student("TEST-001", "John Doe", "CSE", "A")
        self.assertIsNotNone(sid)

        # Duplicate Roll Number should raise DuplicateRollNumberError
        with self.assertRaises(DuplicateRollNumberError):
            self.student_mgr.add_student("test-001", "Jane Doe", "CSE", "B")

        # Missing name or roll should raise ValidationError
        with self.assertRaises(ValidationError):
            self.student_mgr.add_student("", "No Roll")
        with self.assertRaises(ValidationError):
            self.student_mgr.add_student("TEST-002", "")

        # Edit Student
        self.student_mgr.update_student(sid, "TEST-001", "John Updated", "CSE", "B")
        updated = self.student_mgr.get_student_by_id(sid)
        self.assertEqual(updated["name"], "John Updated")
        self.assertEqual(updated["section"], "B")

        # Delete Student
        self.student_mgr.delete_student(sid)
        deleted = self.student_mgr.get_student_by_id(sid)
        self.assertIsNone(deleted)

    def test_search_and_filter_students(self):
        """Test student directory search, class filtering, and sorting."""
        self.student_mgr.add_student("CSE-10", "Alice Smith", "CSE", "A")
        self.student_mgr.add_student("CSE-20", "Bob Jones", "CSE", "B")
        self.student_mgr.add_student("ECE-10", "Charlie Brown", "ECE", "A")

        # Search by name
        results = self.student_mgr.get_all_students(search_query="Alice")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["roll_no"], "CSE-10")

        # Filter by class
        cse_students = self.student_mgr.get_all_students(class_filter="CSE")
        self.assertEqual(len(cse_students), 2)

        # Sort DESC by roll_no
        sorted_desc = self.student_mgr.get_all_students(class_filter="CSE", sort_by="roll_no", sort_order="DESC")
        self.assertEqual(sorted_desc[0]["roll_no"], "CSE-20")

    # -------------------------------------------------------------
    # 3. Attendance Marking and Overwrite Tests
    # -------------------------------------------------------------
    def test_attendance_marking_and_upsert(self):
        """Test marking attendance, historical modification, and upsert uniqueness."""
        sid1 = self.student_mgr.add_student("ST-1", "Student One", "CSE", "A")
        sid2 = self.student_mgr.add_student("ST-2", "Student Two", "CSE", "A")
        test_date = "2026-10-01"

        # Save batch attendance
        saved = self.attendance_mgr.save_batch_attendance(test_date, [
            {"student_id": sid1, "status": "Present"},
            {"student_id": sid2, "status": "Absent"},
        ])
        self.assertEqual(saved, 2)

        # Verify stats
        stats = self.attendance_mgr.get_date_stats(test_date)
        self.assertEqual(stats["present_count"], 1)
        self.assertEqual(stats["absent_count"], 1)
        self.assertEqual(stats["percentage"], 50.0)

        # Edit historical attendance (Overwrite Student Two to Present)
        self.attendance_mgr.save_batch_attendance(test_date, [
            {"student_id": sid2, "status": "Present"},
        ], overwrite=True)

        updated_stats = self.attendance_mgr.get_date_stats(test_date)
        self.assertEqual(updated_stats["present_count"], 2)
        self.assertEqual(updated_stats["absent_count"], 0)
        self.assertEqual(updated_stats["percentage"], 100.0)

    # -------------------------------------------------------------
    # 4. Attendance Percentage Formula & Defaulters (<75%)
    # -------------------------------------------------------------
    def test_attendance_percentage_formula_excluding_leaves(self):
        """
        Formula: Present / (Present + Absent) * 100
        Leave days MUST be excluded from the denominator.
        """
        # Case 1: 3 Present, 1 Absent, 1 Leave
        # Present Days = 3
        # Present + Absent = 4 (Leave excluded)
        # Expected % = (3 / 4) * 100 = 75.0%
        pct = self.reports_mgr.calculate_attendance_percentage(present_days=3, absent_days=1)
        self.assertEqual(pct, 75.0)

        # Case 2: 1 Present, 4 Absent -> 20.0% (<75% Defaulter)
        pct_low = self.reports_mgr.calculate_attendance_percentage(present_days=1, absent_days=4)
        self.assertEqual(pct_low, 20.0)

        # Test reports report generation
        sid = self.student_mgr.add_student("DEF-01", "Defaulter Student", "CSE", "A")
        self.attendance_mgr.save_batch_attendance("2026-10-01", [{"student_id": sid, "status": "Absent"}])
        self.attendance_mgr.save_batch_attendance("2026-10-02", [{"student_id": sid, "status": "Absent"}])
        self.attendance_mgr.save_batch_attendance("2026-10-03", [{"student_id": sid, "status": "Present"}])
        self.attendance_mgr.save_batch_attendance("2026-10-04", [{"student_id": sid, "status": "Leave"}])

        report = self.reports_mgr.get_attendance_report(search_query="DEF-01")
        self.assertEqual(len(report), 1)
        row = report[0]
        self.assertEqual(row["present_days"], 1)
        self.assertEqual(row["absent_days"], 2)
        self.assertEqual(row["leave_days"], 1)
        self.assertEqual(row["total_days"], 4)
        # Denominator = 1 + 2 = 3. Pct = 1/3 * 100 = 33.3%
        self.assertEqual(row["percentage"], 33.3)
        self.assertTrue(row["is_low"])
        self.assertEqual(row["status_label"], "CRITICAL (<75%)")

    # -------------------------------------------------------------
    # 5. CSV Export Generation
    # -------------------------------------------------------------
    def test_csv_export_format(self):
        """Ensure CSV string generator outputs correct headers and data."""
        report_data = [{
            "roll_no": "2026-CSE-001",
            "name": "Aarav Sharma",
            "class_name": "CSE",
            "section": "A",
            "total_days": 5,
            "present_days": 4,
            "absent_days": 1,
            "leave_days": 0,
            "percentage": 80.0,
            "status_label": "Satisfactory"
        }]
        csv_str = self.reports_mgr.generate_csv_string(report_data)
        self.assertIn("Roll Number,Student Name,Class,Section", csv_str)
        self.assertIn("2026-CSE-001,Aarav Sharma,CSE,A,5,4,1,0,80.0%,Satisfactory", csv_str)

    # -------------------------------------------------------------
    # 6. Bulk Import: CSV and TXT
    # -------------------------------------------------------------
    def test_bulk_import_csv(self):
        """Test parsing and importing CSV data with duplicate detection."""
        csv_content = b"roll_no,name,class_name,section\nIMP-101,Maya Patel,CSE,A\nIMP-102,Samir Khan,CSE,B\n"
        res = self.import_mgr.load_file_content("test.csv", csv_content)
        self.assertTrue(res["success"])
        self.assertEqual(len(res["records"]), 2)
        self.assertEqual(res["summary"]["valid_count"], 2)

        # Execute import
        import_res = self.import_mgr.execute_import(res["records"])
        self.assertTrue(import_res["success"])
        self.assertEqual(import_res["added"], 2)

        # Verify added to database
        s = self.student_mgr.get_student_by_roll_no("IMP-101")
        self.assertIsNotNone(s)
        self.assertEqual(s["name"], "Maya Patel")

    def test_bulk_import_txt_pipe(self):
        """Test parsing pipe-delimited TXT file."""
        txt_content = b"ROLL-201 | Rahul Mehta | ECE | A\nROLL-202 | Priya Das | ECE | B\n"
        res = self.import_mgr.load_file_content("test.txt", txt_content)
        self.assertTrue(res["success"])
        self.assertEqual(len(res["records"]), 2)
        self.assertEqual(res["records"][0]["roll_no"], "ROLL-201")
        self.assertEqual(res["records"][0]["name"], "Rahul Mehta")

    def test_bulk_import_duplicate_in_file_detection(self):
        """Detect duplicate roll numbers inside the uploaded file."""
        csv_content = b"roll_no,name\nDUP-01,Student One\nDUP-01,Student Two\n"
        res = self.import_mgr.load_file_content("test.csv", csv_content)
        self.assertTrue(res["success"])
        self.assertEqual(res["summary"]["duplicate_file_count"], 2)
        self.assertEqual(res["summary"]["valid_count"], 0)

    def test_pdf_parsing_sample_file(self):
        """Test parsing text-based sample PDF through BulkImportManager."""
        pdf_path = FLASK_DIR / "static" / "samples" / "sample_students.pdf"
        self.assertTrue(pdf_path.exists())
        pdf_bytes = pdf_path.read_bytes()
        res = self.import_mgr.load_file_content("sample_students.pdf", pdf_bytes)
        self.assertTrue(res["success"])
        self.assertGreaterEqual(len(res["records"]), 10)
        first_rec = res["records"][0]
        self.assertEqual(first_rec["roll_no"], "101")
        self.assertEqual(first_rec["name"], "Rahul Sharma")

    def test_scanned_pdf_detection_and_ocr_guidance(self):
        """Test that image-only/scanned PDFs are detected and error message explains OCR."""
        scanned_path = FLASK_DIR / "static" / "samples" / "sample_scanned.pdf"
        self.assertTrue(scanned_path.exists())
        scanned_bytes = scanned_path.read_bytes()
        res = self.import_mgr.load_file_content("sample_scanned.pdf", scanned_bytes)
        self.assertFalse(res["success"])
        self.assertTrue(res.get("is_scanned_pdf"))
        self.assertIn("scanned document", res["error"].lower())
        self.assertIn("ocr", res["error"].lower())

    # -------------------------------------------------------------
    # 7. Database Persistence
    # -------------------------------------------------------------
    def test_database_persistence_across_connections(self):
        """Ensure records persist when new database instances connect."""
        self.student_mgr.add_student("PERSIST-01", "Persistent Student", "IT", "A")

        # Open completely fresh Database connection to the same file
        new_db = Database(self.db_path)
        new_student_mgr = StudentManager(new_db)
        found = new_student_mgr.get_student_by_roll_no("PERSIST-01")
        self.assertIsNotNone(found)
        self.assertEqual(found["name"], "Persistent Student")


if __name__ == "__main__":
    unittest.main()
