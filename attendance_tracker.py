print("===== Student Attendance Tracker =====")

name = input("Enter student name: ")
roll_no = input("Enter roll number: ")

present = 0
absent = 0
total_classes = 0

while True:
    print("\n===== Attendance Menu =====")
    print("1. Mark Present")
    print("2. Mark Absent")
    print("3. View Attendance")
    print("4. Check 75% Eligibility")
    print("5. Exit")

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
        print("\n----- Attendance Report -----")
        print("Student Name:", name)
        print("Roll Number:", roll_no)
        print("Total Classes:", total_classes)
        print("Present:", present)
        print("Absent:", absent)

        if total_classes > 0:
            percentage = (present / total_classes) * 100

            print("Attendance Percentage:", round(percentage, 2), "%")

            if percentage < 75:
                print("Status: Defaulter")
                print("Warning: Attendance is below 75%.")
            elif percentage < 85:
                print("Status: Regular")
                print("Warning: Maintain your attendance.")
            else:
                print("Status: Regular")
                print("Attendance is good.")
        else:
            print("No attendance has been recorded.")

    elif choice == "4":
        if total_classes == 0:
            print("No attendance has been recorded.")
        else:
            percentage = (present / total_classes) * 100

            print("\n----- 75% Eligibility -----")
            print("Current Attendance:", round(percentage, 2), "%")

            if percentage >= 75:
                print("You are eligible with 75% attendance.")
            else:
                required = (0.75 * total_classes - present) / 0.25
                required = int(required)

                if required > 0:
                    print("You need to attend approximately",
                          required, "more classes to reach 75%.")

    elif choice == "5":
        print("\nThank you for using Student Attendance Tracker.")
        break

    else:
        print("Invalid choice. Please enter a number from 1 to 5.")