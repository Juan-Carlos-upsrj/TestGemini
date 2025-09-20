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
            "Lunes": {"active": False, "start": "10:00", "end": "12:00"},
            "Martes": {"active": False, "start": "10:00", "end": "12:00"},
            "Miércoles": {"active": False, "start": "10:00", "end": "12:00"},
            "Jueves": {"active": False, "start": "10:00", "end": "12:00"},
            "Viernes": {"active": False, "start": "10:00", "end": "12:00"},
            "Sábado": {"active": False, "start": "10:00", "end": "12:00"},
            "Domingo": {"active": False, "start": "10:00", "end": "12:00"}
        },
        "grading_periods": [
            {"id": "p_1", "name": "Parcial 1", "assignments": []},
            {"id": "p_2", "name": "Parcial 2", "assignments": []},
            {"id": "p_3", "name": "Parcial 3", "assignments": []}
        ]
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
    Calculates the attendance percentage for a single student from long-format data.
    """
    student_records = [rec for rec in attendance_records if rec.get('student_id') == student_id]
    total_classes = len(student_records)

    if total_classes == 0:
        return 100.0  # No classes yet, so perfect attendance

    attended_classes = sum(1 for rec in student_records if rec.get('status', '').lower() in PRESENT_STATUSES)
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

# --- Student & Attendance Specific Logic ---

def add_student_to_group(group_name: str, student_name: str) -> Dict[str, Any]:
    """Adds a new student to a group."""
    config = data_manager.load_group_config(group_name)
    if not config:
        raise ValueError(f"Group '{group_name}' not found.")

    students = config.get("students", [])

    # Simple ID generation for now
    new_id = f"s_{len(students) + 1}"

    new_student = {"id": new_id, "name": student_name}
    students.append(new_student)

    config["students"] = students
    data_manager.save_group_config(group_name, config)
    return new_student

def get_students_for_group(group_name: str) -> List[Dict[str, Any]]:
    """Returns the list of students for a given group."""
    config = data_manager.load_group_config(group_name)
    return config.get("students", [])

def get_attendance_for_date(group_name: str, target_date: str) -> Dict[str, Dict[str, str]]:
    """
    Gets attendance for a specific date, returning a dict for easy lookup.
    Format: {student_id: {'status': 'presente', 'notes': '...'}, ...}
    """
    all_attendance = data_manager.load_attendance(group_name)
    date_attendance = {}

    for record in all_attendance:
        if record.get('date') == target_date:
            student_id = record.get('student_id')
            if student_id:
                date_attendance[student_id] = {
                    "status": record.get("status", ""),
                    "notes": record.get("notes", "")
                }
    return date_attendance

def save_attendance_for_date(group_name: str, target_date: str, new_records: List[Dict[str, str]]):
    """
    Saves attendance for a specific date.
    It reads all data, removes old records for the target date, appends the new ones, and saves.
    `new_records` is a list of dicts: [{'student_id': 's_1', 'status': 'presente', 'notes': ''}, ...]
    """
    all_attendance = data_manager.load_attendance(group_name)

    # Filter out any old records for the target date
    other_dates_attendance = [rec for rec in all_attendance if rec.get('date') != target_date]

    # Create new records with the date included
    updated_date_records = []
    for record in new_records:
        updated_date_records.append({
            "date": target_date,
            "student_id": record["student_id"],
            "status": record["status"],
            "notes": record.get("notes", "")
        })

    # Combine and save
    final_attendance = other_dates_attendance + updated_date_records
    data_manager.save_attendance(group_name, final_attendance)

def remove_student_from_group(group_name: str, student_id: str):
    """Removes a student from a group's student list."""
    config = data_manager.load_group_config(group_name)
    if not config:
        raise ValueError(f"Group '{group_name}' not found.")

    students = config.get("students", [])
    students_after_removal = [s for s in students if s.get("id") != student_id]

    if len(students) == len(students_after_removal):
        raise ValueError(f"Student with id '{student_id}' not found in group '{group_name}'.")

    config["students"] = students_after_removal
    data_manager.save_group_config(group_name, config)

def update_student_in_group(group_name: str, student_id: str, new_name: str):
    """Updates a student's information in a group."""
    config = data_manager.load_group_config(group_name)
    if not config:
        raise ValueError(f"Group '{group_name}' not found.")

    students = config.get("students", [])
    student_found = False
    for student in students:
        if student.get("id") == student_id:
            student["name"] = new_name
            student_found = True
            break

    if not student_found:
        raise ValueError(f"Student with id '{student_id}' not found in group '{group_name}'.")

    config["students"] = students
    data_manager.save_group_config(group_name, config)

def update_group_settings(group_name: str, new_settings: Dict[str, Any]):
    """Updates the general settings of a group."""
    config = data_manager.load_group_config(group_name)
    if not config:
        raise ValueError(f"Group '{group_name}' not found.")

    # Update config with new values
    config.update(new_settings)

    # A special case: if the name changes, the directory name must change too.
    new_name = new_settings.get("name")
    if new_name and new_name != group_name:
        # This is a more complex operation involving renaming the directory.
        # For now, let's assume name change is handled separately or not at all.
        # To keep it simple, we'll just update the config file.
        # A more robust solution would involve a `rename_group` function in data_manager.
        config["name"] = new_name # Update the name inside the config

    data_manager.save_group_config(group_name, config)

def add_students_from_csv(group_name: str, file_path: str) -> Dict[str, int]:
    """
    Adds students to a group from a CSV file.
    The CSV should have a header, and one column should contain student names.
    Recognized header names are 'Name', 'Student Name', 'Nombre', 'Estudiante'.
    """
    config = data_manager.load_group_config(group_name)
    if not config:
        raise ValueError(f"Group '{group_name}' not found.")

    students = config.get("students", [])
    existing_names = {s['name'].lower() for s in students}

    added_count = 0
    skipped_count = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("CSV file is empty.")

        # Find the name column
        name_col_idx = -1
        possible_headers = ['name', 'student name', 'nombre', 'estudiante']
        for idx, h in enumerate(header):
            if h.lower() in possible_headers:
                name_col_idx = idx
                break

        if name_col_idx == -1:
            raise ValueError("CSV file must have a header with 'Name' or 'Nombre'.")

        for row in reader:
            if not row or not row[name_col_idx].strip():
                continue # Skip empty rows

            student_name = row[name_col_idx].strip()
            if student_name.lower() not in existing_names:
                # Re-using the single-add function is clean
                add_student_to_group(group_name, student_name)
                # We need to update our set of existing names for the next iteration
                existing_names.add(student_name.lower())
                added_count += 1
            else:
                skipped_count += 1

    return {"added": added_count, "skipped": skipped_count}

# --- Grading Logic ---

def generate_class_dates(group_name: str, start_date_str: str, end_date_str: str) -> List[str]:
    """
    Generates a list of class dates within a range, based on the group's schedule.
    """
    from datetime import datetime, timedelta

    config = data_manager.load_group_config(group_name)
    schedule = config.get("schedule", {})

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return [] # Invalid date format

    # Python's weekday(): Monday is 0 and Sunday is 6
    # Our schedule uses Spanish names.
    day_mapping = {
        "Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3,
        "Viernes": 4, "Sábado": 5, "Domingo": 6
    }

    active_days = set()
    for day_name, day_info in schedule.items():
        if day_info.get("active"):
            if day_name in day_mapping:
                active_days.add(day_mapping[day_name])

    class_dates = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() in active_days:
            class_dates.append(current_date.isoformat())
        current_date += timedelta(days=1)

    return class_dates

def get_grading_periods(group_name: str) -> List[Dict[str, Any]]:
    """Returns the list of grading periods for a given group."""
    config = data_manager.load_group_config(group_name)
    return config.get("grading_periods", [])

def add_assignment(group_name: str, period_id: str, name: str, weight: float) -> Dict[str, Any]:
    """Adds a new assignment to a specific grading period."""
    config = data_manager.load_group_config(group_name)
    periods = config.get("grading_periods", [])

    period_found = False
    for period in periods:
        if period.get("id") == period_id:
            assignments = period.get("assignments", [])
            new_id = f"a_{len(assignments) + 1}"
            new_assignment = {"id": new_id, "name": name, "weight": weight, "grades": {}}
            assignments.append(new_assignment)
            period_found = True
            break

    if not period_found:
        raise ValueError(f"Grading period with id '{period_id}' not found.")

    data_manager.save_group_config(group_name, config)
    return new_assignment

def save_grades_for_assignment(group_name: str, period_id: str, assignment_id: str, grades: Dict[str, float]):
    """Saves the grades for a specific assignment."""
    config = data_manager.load_group_config(group_name)
    periods = config.get("grading_periods", [])

    assignment_found = False
    for period in periods:
        if period.get("id") == period_id:
            for assignment in period.get("assignments", []):
                if assignment.get("id") == assignment_id:
                    # Merge new grades with existing ones
                    assignment["grades"].update(grades)
                    assignment_found = True
                    break
        if assignment_found:
            break

    if not assignment_found:
        raise ValueError(f"Assignment with id '{assignment_id}' not found in period '{period_id}'.")

    data_manager.save_group_config(group_name, config)
