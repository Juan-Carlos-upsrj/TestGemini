import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any

DATA_DIR = Path.home() / "Documents" / "GestorAsistencia"
GROUPS_DIR = DATA_DIR / "groups"

def ensure_data_directory_exists():
    """Ensures the main application data directory and groups subdirectory exist."""
    GROUPS_DIR.mkdir(parents=True, exist_ok=True)

def list_groups() -> List[str]:
    """Lists all available group directories by name."""
    ensure_data_directory_exists()
    if not GROUPS_DIR.exists():
        return []
    return [d.name for d in GROUPS_DIR.iterdir() if d.is_dir()]

def get_group_config_path(group_name: str) -> Path:
    """Returns the path to a group's configuration file."""
    return GROUPS_DIR / group_name / "config.json"

def get_group_attendance_path(group_name: str) -> Path:
    """Returns the path to a group's attendance file."""
    return GROUPS_DIR / group_name / "attendance.csv"

def save_group_config(group_name: str, config_data: Dict[str, Any]):
    """Saves a group's configuration to its JSON file."""
    ensure_data_directory_exists()
    group_dir = GROUPS_DIR / group_name
    group_dir.mkdir(exist_ok=True)
    config_path = get_group_config_path(group_name)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

def load_group_config(group_name: str) -> Dict[str, Any]:
    """Loads a group's configuration from its JSON file."""
    config_path = get_group_config_path(group_name)
    if not config_path.exists():
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_attendance(group_name: str, attendance_data: List[Dict[str, Any]]):
    """Saves a group's attendance data to a CSV file in long format."""
    ensure_data_directory_exists()
    path = get_group_attendance_path(group_name)
    headers = ['date', 'student_id', 'status', 'notes']

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        if attendance_data:
            writer.writerows(attendance_data)

def load_attendance(group_name: str) -> List[Dict[str, Any]]:
    """Loads a group's attendance data from its CSV file."""
    path = get_group_attendance_path(group_name)
    if not path.exists():
        return []

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def delete_group_data(group_name: str):
    """Deletes a group's entire directory."""
    import shutil
    group_dir = GROUPS_DIR / group_name
    if group_dir.exists() and group_dir.is_dir():
        shutil.rmtree(group_dir)
