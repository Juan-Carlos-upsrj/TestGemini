import csv
from typing import List, Dict, Any
from datetime import date, datetime, timedelta
from . import data_manager

DEFAULT_ATTENDANCE_THRESHOLD = 80.0
PRESENT_STATUSES = ["presente", "justificado"]

def create_new_group(group_name: str, prefix: str = "") -> Dict[str, Any]:
    print(f"LOG: Attempting to create new group: {group_name}")
    full_name = f"{prefix}{group_name}" if prefix else group_name
    if full_name in data_manager.list_groups():
        raise ValueError(f"El grupo '{full_name}' ya existe.")
    default_config = {
        "name": full_name,
        "creation_date": date.today().isoformat(),
        "attendance_threshold": DEFAULT_ATTENDANCE_THRESHOLD,
        "students": [],
        "grading_periods": [
            {"id": "p_1", "name": "Parcial 1", "start_date": "", "end_date": "", "assignments": []},
            {"id": "p_2", "name": "Parcial 2", "start_date": "", "end_date": "", "assignments": []},
            {"id": "p_3", "name": "Parcial 3", "start_date": "", "end_date": "", "assignments": []}
        ],
        "schedule": {
            "Lunes": {"active": False, "start": "10:00", "end": "12:00"},
            "Martes": {"active": False, "start": "10:00", "end": "12:00"},
            "Miércoles": {"active": False, "start": "10:00", "end": "12:00"},
            "Jueves": {"active": False, "start": "10:00", "end": "12:00"},
            "Viernes": {"active": False, "start": "10:00", "end": "12:00"},
            "Sábado": {"active": False, "start": "10:00", "end": "12:00"},
            "Domingo": {"active": False, "start": "10:00", "end": "12:00"}
        }
    }
    data_manager.save_group_config(full_name, default_config)
    data_manager.save_attendance(full_name, [])
    return default_config

def get_group_list() -> List[str]:
    return data_manager.list_groups()

def delete_group(group_name: str):
    data_manager.delete_group_data(group_name)

def _calculate_student_attendance(student_id: str, attendance_records: List[Dict[str, str]]) -> float:
    student_records = [rec for rec in attendance_records if rec.get('student_id') == student_id]
    total_classes = len(student_records)
    if total_classes == 0:
        return 100.0
    attended_classes = sum(1 for rec in student_records if rec.get('status', '').lower() in PRESENT_STATUSES)
    return (attended_classes / total_classes) * 100

def get_all_groups_summary() -> List[Dict[str, Any]]:
    summaries = []
    for name in get_group_list():
        config = data_manager.load_group_config(name)
        attendance = data_manager.load_attendance(name)
        students = config.get("students", [])
        student_count = len(students)
        threshold = config.get("attendance_threshold", DEFAULT_ATTENDANCE_THRESHOLD)
        at_risk_count = 0
        if student_count > 0:
            for student in students:
                percentage = _calculate_student_attendance(student.get("id"), attendance)
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
    config = data_manager.load_group_config(group_name)
    if not config: return {}
    attendance = data_manager.load_attendance(group_name)
    students = config.get("students", [])
    threshold = config.get("attendance_threshold", DEFAULT_ATTENDANCE_THRESHOLD)
    for student in students:
        student_id = student.get("id")
        percentage = _calculate_student_attendance(student_id, attendance)
        student["attendance_percentage"] = round(percentage, 2)
        student["is_at_risk"] = percentage < threshold
    return config

def add_student_to_group(group_name: str, student_name: str, config: Dict = None) -> Dict[str, Any]:
    """Adds a single student. Can accept an existing config to avoid re-reading the file."""
    print(f"LOG: Adding student '{student_name}' to group '{group_name}'")

    # If no config is passed, load it. Otherwise, use the provided one.
    config_was_passed = config is not None
    if not config_was_passed:
        config = data_manager.load_group_config(group_name)

    if not config: raise ValueError(f"Group '{group_name}' not found.")

    students = config.get("students", [])
    # Simple ID generation based on current student count + 1
    new_id = f"s_{len(students) + 1}"
    new_student = {"id": new_id, "name": student_name}
    students.append(new_student)
    config["students"] = students

    # Only save if we loaded the config inside this function
    if not config_was_passed:
        data_manager.save_group_config(group_name, config)

    return new_student

def add_multiple_students(group_name: str, names: List[str]) -> Dict[str, int]:
    """Adds a list of students to a group, skipping duplicates."""
    print(f"LOG: Adding multiple students to group '{group_name}'")
    config = data_manager.load_group_config(group_name)
    if not config: raise ValueError(f"Group '{group_name}' not found.")

    students = config.get("students", [])
    existing_names = {s['name'].lower().strip() for s in students}
    added_count, skipped_count = 0, 0

    for name in names:
        clean_name = name.strip()
        if clean_name and clean_name.lower() not in existing_names:
            # Pass the already-loaded config to avoid repeated file I/O
            add_student_to_group(group_name, clean_name, config=config)
            existing_names.add(clean_name.lower())
            added_count += 1
        else:
            skipped_count += 1

    # Save the config once after all students have been added
    data_manager.save_group_config(group_name, config)
    return {"added": added_count, "skipped": skipped_count}

def add_students_from_csv(group_name: str, file_path: str) -> Dict[str, int]:
    print(f"LOG: Importing students from '{file_path}' to group '{group_name}'")
    config = data_manager.load_group_config(group_name)
    if not config: raise ValueError(f"Group '{group_name}' not found.")

    students = config.get("students", [])
    existing_names = {s['name'].lower() for s in students}
    added_count, skipped_count = 0, 0

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        try:
            header = [h.lower() for h in next(reader)]
        except StopIteration:
            raise ValueError("CSV file is empty.")

        name_col_idx = -1
        possible_headers = ['name', 'student name', 'nombre', 'estudiante']
        for p_header in possible_headers:
            if p_header in header:
                name_col_idx = header.index(p_header)
                break

        if name_col_idx == -1: raise ValueError("CSV header must contain 'Name' or 'Nombre'.")

        for row in reader:
            if not row or not row[name_col_idx].strip(): continue
            student_name = row[name_col_idx].strip()
            if student_name.lower() not in existing_names:
                add_student_to_group(group_name, student_name)
                existing_names.add(student_name.lower())
                added_count += 1
            else:
                skipped_count += 1
    return {"added": added_count, "skipped": skipped_count}

def remove_student_from_group(group_name: str, student_id: str):
    config = data_manager.load_group_config(group_name)
    students = config.get("students", [])
    students_after_removal = [s for s in students if s.get("id") != student_id]
    if len(students) == len(students_after_removal): raise ValueError("Student not found.")
    config["students"] = students_after_removal
    data_manager.save_group_config(group_name, config)

def update_student_in_group(group_name: str, student_id: str, new_name: str):
    config = data_manager.load_group_config(group_name)
    student_found = False
    for student in config.get("students", []):
        if student.get("id") == student_id:
            student["name"] = new_name
            student_found = True
            break
    if not student_found: raise ValueError("Student not found.")
    data_manager.save_group_config(group_name, config)

def get_students_for_group(group_name: str) -> List[Dict[str, Any]]:
    """Returns the list of students for a given group."""
    config = data_manager.load_group_config(group_name)
    return config.get("students", [])

def get_attendance_for_date(group_name: str, target_date: str) -> Dict[str, Dict[str, str]]:
    all_attendance = data_manager.load_attendance(group_name)
    date_attendance = {}
    for record in all_attendance:
        if record.get('date') == target_date:
            student_id = record.get('student_id')
            if student_id:
                date_attendance[student_id] = {"status": record.get("status", ""), "notes": record.get("notes", "")}
    return date_attendance

def save_attendance_for_date(group_name: str, target_date: str, new_records: List[Dict[str, str]]):
    print(f"LOG: Saving attendance for group '{group_name}' on date '{target_date}'")
    all_attendance = data_manager.load_attendance(group_name)
    other_dates_attendance = [rec for rec in all_attendance if rec.get('date') != target_date]
    updated_date_records = [{"date": target_date, **rec} for rec in new_records]
    final_attendance = other_dates_attendance + updated_date_records
    data_manager.save_attendance(group_name, final_attendance)

def update_group_settings(group_name: str, new_settings: Dict[str, Any]):
    print(f"LOG: Updating settings for group '{group_name}'")
    config = data_manager.load_group_config(group_name)
    config.update(new_settings)
    data_manager.save_group_config(group_name, config)

def generate_class_dates(group_name: str, start_date_str: str, end_date_str: str) -> List[str]:
    config = data_manager.load_group_config(group_name)
    schedule = config.get("schedule", {})
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError: return []
    day_mapping = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}
    active_days = set()
    for day, info in schedule.items():
        # Defensive check for backward compatibility with old data format
        if isinstance(info, dict) and info.get("active"):
            if day in day_mapping:
                active_days.add(day_mapping[day])

    class_dates = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() in active_days:
            class_dates.append(current_date.isoformat())
        current_date += timedelta(days=1)
    return class_dates

def get_grading_periods(group_name: str) -> List[Dict[str, Any]]:
    config = data_manager.load_group_config(group_name)
    return config.get("grading_periods", [])

def add_assignment(group_name: str, period_id: str, name: str, weight: float) -> Dict[str, Any]:
    print(f"LOG: Adding assignment '{name}' to period '{period_id}' in group '{group_name}'")
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
    if not period_found: raise ValueError("Grading period not found.")
    data_manager.save_group_config(group_name, config)
    return new_assignment

def save_grades_for_assignment(group_name: str, period_id: str, assignment_id: str, grades: Dict[str, float]):
    print(f"LOG: Saving grades for assignment '{assignment_id}' in group '{group_name}'")
    config = data_manager.load_group_config(group_name)
    assignment_found = False
    for period in config.get("grading_periods", []):
        if period.get("id") == period_id:
            for assignment in period.get("assignments", []):
                if assignment.get("id") == assignment_id:
                    assignment["grades"].update(grades)
                    assignment_found = True
                    break
        if assignment_found: break
    if not assignment_found: raise ValueError("Assignment not found.")
    data_manager.save_group_config(group_name, config)
