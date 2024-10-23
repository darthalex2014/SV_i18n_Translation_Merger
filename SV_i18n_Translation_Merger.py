import sys
import os
import re
import traceback
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QFileDialog,
    QLabel,
    QVBoxLayout,
    QLineEdit,
    QTextEdit,
    QProgressBar,
)
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class TranslationWorker(QThread):
    progress_updated = pyqtSignal(int)
    log_message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, new_mod_file, old_mod_file, old_translation_file, output_path):
        super().__init__()
        self.new_mod_file = new_mod_file
        self.old_mod_file = old_mod_file
        self.old_translation_file = old_translation_file
        self.output_path = output_path

    def run(self):
        try:
            # Read files as text
            with open(self.new_mod_file, "r", encoding="utf-8") as f_new_mod, open(
                self.old_mod_file, "r", encoding="utf-8"
            ) as f_old_mod, open(
                self.old_translation_file, "r", encoding="utf-8"
            ) as f_old_translation:
                new_mod_lines = f_new_mod.readlines()
                old_mod_lines = f_old_mod.readlines()
                old_translation_lines = f_old_translation.readlines()

            # Create a dictionary for translation from the old translation file
            translation_dict = {}
            for translation_line in old_translation_lines:
                translation_match = re.search(r'"(.*?)": "(.*?(?<!\\))"', translation_line)
                if translation_match:
                    key = translation_match.group(1)
                    translation = translation_match.group(2)
                    translation_dict[key] = translation

            # Replace i18n in the new mod file
            new_mod_copy = new_mod_lines.copy()
            total_lines = len(new_mod_copy)
            processed_lines = 0

            for i, line in enumerate(new_mod_copy):
                match = re.search(r'"(.*?)": "(.*?(?<!\\))"', line)
                if match:
                    key = match.group(1)
                    current_i18n = match.group(2)

                    # Find the corresponding line in the old mod file
                    for old_mod_line in old_mod_lines:
                        old_mod_match = re.search(r'"(.*?)": "(.*?(?<!\\))"', old_mod_line)
                        if old_mod_match and old_mod_match.group(1) == key:
                            old_i18n = old_mod_match.group(2)
                            # If keys and i18n match, replace with the translation
                            if current_i18n == old_i18n and key in translation_dict:
                                new_line = line.replace(current_i18n, translation_dict[key])
                                new_mod_copy[i] = new_line
                                break  # Exit the loop after replacement

                processed_lines += 1
                self.progress_updated.emit(int((processed_lines / total_lines) * 100))

            # Save the new file
            with open(self.output_path, "w", encoding="utf-8") as f_out:
                f_out.writelines(new_mod_copy)

            self.log_message.emit(f"File saved: {self.output_path}")

        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_message = f"Error:\n"
            error_message += f"{exc_type.__name__}: {exc_value}\n"
            error_message += "".join(traceback.format_tb(exc_traceback, limit=10))
            self.log_message.emit(error_message)

        finally:
            self.finished.emit()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("SV i18n Translation Merger by Alex(GoD)")
        self.setGeometry(100, 100, 400, 400)

        # Dark Theme
        self.setDarkTheme()

        # Main layout
        main_layout = QVBoxLayout()

        # --- File Selection Frame ---
        files_frame = QVBoxLayout()
        main_layout.addLayout(files_frame)

        # File Selection Labels and Inputs
        self.file_new_mod_entry = self.createFileSelectionInput(files_frame, "NEW MOD:", "background-color: #4CAF50; color: white;")
        self.file_old_mod_entry = self.createFileSelectionInput(files_frame, "OLD MOD:", "background-color: #008CBA; color: white;")
        self.file_old_translation_entry = self.createFileSelectionInput(files_frame, "OLD TRANSLATION:", "background-color: #f44336; color: white;")

        # Translate Button
        process_button = QPushButton("Translate", self)
        process_button.setStyleSheet("background-color: #555555; color: white;")
        process_button.clicked.connect(self.processFiles)
        main_layout.addWidget(process_button)

        # Log Output
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)
        main_layout.addWidget(self.log_text_edit)

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        main_layout.addWidget(self.progress_bar)

        self.setLayout(main_layout)
        self.show()

    def createFileSelectionInput(self, layout, label_text, button_style):
        label = QLabel(label_text, self)
        layout.addWidget(label)
        entry = QLineEdit(self)
        entry.setStyleSheet("background-color: #333333; color: white;")
        layout.addWidget(entry)
        button = QPushButton("Browse", self)
        button.setStyleSheet(button_style)
        button.clicked.connect(lambda: self.browseFile(entry))
        layout.addWidget(button)
        return entry

    def setDarkTheme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setPalette(palette)

    def browseFile(self, entry):
        initialdir = os.path.dirname(sys.executable)
        filename = QFileDialog.getOpenFileName(
            self, "Select File", initialdir, "JSON Files (*.json);;All Files (*)"
        )[0]
        if filename:
            entry.setText(filename)

    def processFiles(self):
        new_mod_file = self.file_new_mod_entry.text()
        old_mod_file = self.file_old_mod_entry.text()
        old_translation_file = self.file_old_translation_entry.text()
        output_path = QFileDialog.getSaveFileName(self, "Save File", "", "*.json")[0]

        if not all([new_mod_file, old_mod_file, old_translation_file, output_path]):
            self.log("Error: Select all three files and specify the save path")
            return

        # Create and start the processing thread
        self.worker_thread = TranslationWorker(
            new_mod_file, old_mod_file, old_translation_file, output_path
        )
        self.worker_thread.progress_updated.connect(self.updateProgressBar)
        self.worker_thread.log_message.connect(self.log)
        self.worker_thread.finished.connect(self.onProcessingFinished)
        self.worker_thread.start()

    def updateProgressBar(self, progress):
        self.progress_bar.setValue(progress)

    def log(self, message):
        self.log_text_edit.append(message)

    def onProcessingFinished(self):
        self.log("Processing complete.")
        self.worker_thread = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())