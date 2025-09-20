from typing import List, Dict, Any
from . import logic

def generate_grades_report(group_name: str) -> List[Dict[str, Any]]:
    """
    Calculates the final weighted grade for each student in a group.
    """
    group_details = logic.get_group_details(group_name)
    students = group_details.get("students", [])
    grading_periods = group_details.get("grading_periods", [])

    report_data = []

    for student in students:
        student_id = student["id"]
        total_grade = 0.0

        for period in grading_periods:
            for assignment in period.get("assignments", []):
                grade = float(assignment.get("grades", {}).get(student_id, 0.0))
                weight = float(assignment.get("weight", 0.0))

                # Calculate the weighted contribution of this assignment
                total_grade += (grade * weight) / 100.0

        report_data.append({
            "student_id": student_id,
            "student_name": student["name"],
            "final_grade": round(total_grade, 2)
        })

    return report_data

def generate_attendance_report(group_name: str) -> List[Dict[str, Any]]:
    """
    Generates a report of the final attendance percentage for each student.
    """
    group_details = logic.get_group_details(group_name)
    students = group_details.get("students", [])

    report_data = []

    for student in students:
        # The get_group_details function already calculates this for us
        report_data.append({
            "student_id": student["id"],
            "student_name": student["name"],
            "attendance_percentage": student.get("attendance_percentage", 0.0),
            "is_at_risk": student.get("is_at_risk", False)
        })

    return report_data
