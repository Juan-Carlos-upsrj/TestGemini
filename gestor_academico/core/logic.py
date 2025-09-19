from typing import List, Dict, Any
from datetime import date
from . import data_manager

# --- Constants ---
DEFAULT_ATTENDANCE_THRESHOLD = 80.0  # Default minimum attendance percentage
PRESENT_STATUSES = ["presente", "justificado"] # Statuses that count as attended

# --- Group Management ---

def create_new_group(group_name: str, prefix: str = "") -> Dict[str, Any]:
    """
    Creates a new group with a default configuration.
    """
    full_name = f"{prefix}{group_name}" if prefix else group_name

    if full_name in data_manager.list_groups():
        raise ValueError(f"El grupo '{full_name}' ya existe, mi Capitán!")

    default_config = {
        "name": full_name,
        "creation_date": date.today().isoformat(),
        "attendance_threshold": DEFAULT_ATTENDANCE_THRESHOLD,
        "students": [],
        "grading_periods": {
            "Parcial 1": {"start": "", "end": ""},
            "Parcial 2": {"start": "", "end": ""},
            "Parcial 3": {"start": "", "end": ""},
        },
        "schedule": {
            "lunes": "", "martes": "", "miércoles": "", "jueves": "", "viernes": ""
        }
    }

    data_manager.save_group_config(full_name, default_config)
    # Create empty attendance file
    data_manager.save_attendance(full_name, [])

    return default_config

def get_group_list() -> List[str]:
    """Returns a list of all group names."""
    return data_manager.list_groups()

def delete_group(group_name: str):
    """Deletes a group and all its associated data."""
    data_manager.delete_group_data(group_name)

# --- Data Calculation & Summaries ---

def _calculate_student_attendance(student_id: str, attendance_records: List[Dict[str, str]]) -> float:
    """
    Calculates the attendance percentage for a single student.
    """
    total_classes = 0
    attended_classes = 0

    for record in attendance_records:
        if student_id in record:
            total_classes += 1
            if record[student_id].lower() in PRESENT_STATUSES:
                attended_classes += 1

    if total_classes == 0:
        return 100.0  # No classes yet, so perfect attendance

    return (attended_classes / total_classes) * 100

def get_all_groups_summary() -> List[Dict[str, Any]]:
    """
    Gathers a summary for each group, including the at-risk percentage.
    This is for the main screen view.
    """
    summaries = []
    group_names = get_group_list()

    for name in group_names:
        config = data_manager.load_group_config(name)
        attendance = data_manager.load_attendance(name)

        students = config.get("students", [])
        student_count = len(students)
        threshold = config.get("attendance_threshold", DEFAULT_ATTENDANCE_THRESHOLD)

        at_risk_count = 0
        if student_count > 0 and attendance:
            for student in students:
                student_id = student.get("id")
                if student_id:
                    percentage = _calculate_student_attendance(student_id, attendance)
                    if percentage < threshold:
                        at_risk_count += 1

        risk_percentage = (at_risk_count / student_count) * 100 if student_count > 0 else 0

        summaries.append({
            "name": name,
            "student_count": student_count,
            "at_risk_percentage": round(risk_percentage, 2)
        })

    return summaries

def get_group_details(group_name: str) -> Dict[str, Any]:
    """
    Gets the full details for a single group, including calculated fields for students.
    """
    config = data_manager.load_group_config(group_name)
    if not config:
        return {} # Or raise error

    attendance = data_manager.load_attendance(group_name)
    students = config.get("students", [])
    threshold = config.get("attendance_threshold", DEFAULT_ATTENDANCE_THRESHOLD)

    for student in students:
        student_id = student.get("id")
        if student_id:
            percentage = _calculate_student_attendance(student_id, attendance)
            student["attendance_percentage"] = round(percentage, 2)
            student["is_at_risk"] = percentage < threshold
        else:
            student["attendance_percentage"] = 100.0
            student["is_at_risk"] = False

    return config
