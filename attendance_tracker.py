print("===== Student Attendance Tracker =====")

name = input("Enter student name: ")
roll_no = input("Enter roll number: ")

total_classes = 0
present = 0
absent = 0

while True:
    print("\n1. Mark Present")
    print("2. Mark Absent")
    print("3. View Attendance")
    print("4. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        present = present + 1
        total_classes = total_classes + 1
        print("Attendance marked as Present.")

    elif choice == "2":
        absent = absent + 1
        total_classes = total_classes + 1
        print("Attendance marked as Absent.")

    elif choice == "3":
        if total_classes == 0:
            print("No attendance has been recorded.")
        else:
            percentage = (present / total_classes) * 100

            print("\n----- Attendance Report -----")
            print("Student Name:", name)
            print("Roll Number:", roll_no)
            print("Total Classes:", total_classes)
            print("Present:", present)
            print("Absent:", absent)
            print("Attendance Percentage:", round(percentage, 2), "%")

            if percentage < 75:
                print("Status: Defaulter")
            else:
                print("Status: Regular")

    elif choice == "4":
        print("Thank you for using Student Attendance Tracker.")
        break

    else:
        print("Invalid choice. Please try again.")