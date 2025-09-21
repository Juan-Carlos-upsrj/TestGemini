import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from gestor_academico.ui.main_window import MainWindow
from gestor_academico.core import data_manager, logic

def main():
    data_manager.ensure_data_directory_exists()
    app = QApplication(sys.argv)

    script_dir = Path(__file__).parent
    style_path = script_dir / "assets" / "styles.qss"
    try:
        with open(style_path, "r", encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Warning: Stylesheet not found.")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    if not data_manager.list_groups():
        print("No groups found, creating dummy data...")
        try:
            calc_group = "Grupo de Cálculo"
            logic.create_new_group(calc_group)
            logic.add_student_to_group(calc_group, "Sofia Rodriguez")
            logic.add_student_to_group(calc_group, "Mateo Vargas")
        except ValueError as e:
            print(f"Dummy data might already exist: {e}")
    main()
