"""
Database Migration Utility: SQLite -> PostgreSQL
Migrates all students and attendance history from local SQLite ('attendance_tracker.db')
to your hosted production PostgreSQL database (Neon / Supabase).
"""

import os
import sys
import sqlite3
from pathlib import Path

# Load environment variable from .env if present
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip().strip("'").strip('"'))

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("Error: psycopg2 is required. Run: pip install psycopg2-binary")
    sys.exit(1)


def migrate():
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not db_url:
        print("\n=======================================================")
        print(" Error: No DATABASE_URL found!")
        print("=======================================================")
        print("Please set your PostgreSQL connection string in a local '.env' file:")
        print("DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require")
        print("\nOr run with environment variable:")
        print("python migrate_to_postgres.py")
        sys.exit(1)

    # Normalize PostgreSQL URL
    if db_url.startswith("postgres://"):
        db_url = "postgresql://" + db_url[len("postgres://"):]
    if "sslmode=" not in db_url and any(h in db_url for h in ("neon.tech", "supabase", "aws")):
        connector = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{connector}sslmode=require"

    sqlite_path = Path(__file__).resolve().parent / "attendance_tracker.db"
    if not sqlite_path.exists():
        print(f"Error: Local SQLite file not found at {sqlite_path}")
        sys.exit(1)

    print(f"\n1. Reading local SQLite database: {sqlite_path}")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    s_cur = sqlite_conn.cursor()

    students = s_cur.execute("SELECT id, roll_no, name, class_name, section, created_at FROM students ORDER BY id ASC").fetchall()
    attendance = s_cur.execute("SELECT id, student_id, attendance_date, status FROM attendance ORDER BY id ASC").fetchall()
    sqlite_conn.close()

    print(f"   Found {len(students)} students and {len(attendance)} attendance records.")

    print(f"\n2. Connecting to hosted PostgreSQL database...")
    pg_conn = psycopg2.connect(db_url)
    pg_cur = pg_conn.cursor()

    # Ensure schema exists
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            roll_no VARCHAR(100) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            class_name VARCHAR(100) DEFAULT '',
            section VARCHAR(50) DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            attendance_date VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL CHECK(status IN ('Present', 'Absent', 'Leave')),
            UNIQUE(student_id, attendance_date)
        );
    """)

    # Migrate students
    print(f"\n3. Migrating {len(students)} students to PostgreSQL...")
    migrated_students = 0
    for s in students:
        pg_cur.execute("""
            INSERT INTO students (id, roll_no, name, class_name, section, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (roll_no) DO UPDATE SET
                name = EXCLUDED.name,
                class_name = EXCLUDED.class_name,
                section = EXCLUDED.section;
        """, (s["id"], s["roll_no"], s["name"], s["class_name"] or "", s["section"] or "", s["created_at"]))
        migrated_students += 1

    # Reset student sequence
    pg_cur.execute("SELECT setval(pg_get_serial_sequence('students', 'id'), coalesce(max(id), 1)) FROM students;")

    # Migrate attendance
    print(f"4. Migrating {len(attendance)} attendance records to PostgreSQL...")
    migrated_att = 0
    for a in attendance:
        pg_cur.execute("""
            INSERT INTO attendance (id, student_id, attendance_date, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (student_id, attendance_date) DO UPDATE SET
                status = EXCLUDED.status;
        """, (a["id"], a["student_id"], a["attendance_date"], a["status"]))
        migrated_att += 1

    # Reset attendance sequence
    pg_cur.execute("SELECT setval(pg_get_serial_sequence('attendance', 'id'), coalesce(max(id), 1)) FROM attendance;")

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()

    print("\n=======================================================")
    print(f" Migration Complete! Successfully migrated:")
    print(f" - {migrated_students} Students")
    print(f" - {migrated_att} Attendance Logs")
    print("=======================================================")
    print("Refresh your live Vercel application to see all your data!\n")


if __name__ == "__main__":
    migrate()
