import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Adjust the path to import from the ui module
from gestor_academico.ui.main_window import MainWindow
from gestor_academico.core import data_manager

def main():
    """The main entry point for the application."""
    # Ensure the data directory exists before launching the UI
    data_manager.ensure_data_directory_exists()

    app = QApplication(sys.argv)

    # Load the stylesheet
    # This makes the path relative to this script file
    script_dir = Path(__file__).parent
    style_path = script_dir / "assets" / "styles.qss"

    try:
        with open(style_path, "r", encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Warning: Stylesheet not found at {style_path}. The UI will not be styled.")
    except Exception as e:
        print(f"An error occurred while loading the stylesheet: {e}")

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the Qt event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    # You can add some dummy data here for easy testing if the data dir is empty
    if not data_manager.list_groups():
        print("No groups found, creating dummy data for demonstration...")
        from gestor_academico.core import logic
        try:
            calc_group = "Grupo de Cálculo"
            logic.create_new_group(calc_group)
            logic.add_student_to_group(calc_group, "Sofia Rodriguez")
            logic.add_student_to_group(calc_group, "Mateo Vargas")
            logic.add_student_to_group(calc_group, "Isabella Perez")
            logic.add_student_to_group(calc_group, "Alejandro Gomez")
            logic.add_student_to_group(calc_group, "Camila Torres")

            logic.create_new_group("Lab. de Física", prefix="IAEV-")
            logic.create_new_group("Taller de Redacción")
        except ValueError as e:
            print(f"Dummy data might already exist: {e}")

    main()
