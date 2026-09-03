import os
import sys
import shutil
import datetime
import json
from typing import Dict, List, Tuple

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QLineEdit, QFileDialog, QProgressBar,
        QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
        QTabWidget, QTextEdit, QDialog, QFormLayout, QDialogButtonBox
    )
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QFont, QIcon, QPalette, QColor
except ImportError:
    print("PySide6 not installed. Run: pip install PySide6")
    sys.exit(1)

# ============================================================
# CONFIG
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "organizer_log.json")
UNDO_FILE = os.path.join(BASE_DIR, "undo_data.json")
CATEGORIES_FILE = os.path.join(BASE_DIR, "custom_categories.json")

DEFAULT_CATEGORIES = {
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images",
    ".bmp": "Images", ".svg": "Images", ".webp": "Images", ".ico": "Images",
    ".pdf": "Documents", ".doc": "Documents", ".docx": "Documents", ".txt": "Documents",
    ".rtf": "Documents", ".odt": "Documents", ".xls": "Documents", ".xlsx": "Documents",
    ".ppt": "Documents", ".pptx": "Documents", ".csv": "Documents",
    ".mp3": "Music", ".wav": "Music", ".flac": "Music", ".aac": "Music",
    ".ogg": "Music", ".wma": "Music",
    ".mp4": "Videos", ".mkv": "Videos", ".avi": "Videos", ".mov": "Videos",
    ".wmv": "Videos", ".flv": "Videos",
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives", ".tar": "Archives", ".gz": "Archives",
    ".exe": "Programs", ".msi": "Programs", ".apk": "Programs",
    ".py": "Code", ".js": "Code", ".html": "Code", ".css": "Code",
    ".json": "Code", ".xml": "Code", ".cpp": "Code", ".java": "Code",
}

CATEGORIES = DEFAULT_CATEGORIES.copy()
FOLDER_TO_ORGANIZE = os.path.expanduser("~/Downloads")


def load_custom_categories():
    global CATEGORIES
    if os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, "r") as f:
            CATEGORIES.update(json.load(f))


def save_custom_categories():
    custom = {ext: folder for ext, folder in CATEGORIES.items()
              if ext not in DEFAULT_CATEGORIES or DEFAULT_CATEGORIES.get(ext) != folder}
    with open(CATEGORIES_FILE, "w") as f:
        json.dump(custom, f, indent=2)


def log_action(action, details):
    log = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            log = json.load(f)
    log.append({
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details
    })
    if len(log) > 500:
        log = log[-500:]
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def get_preview(folder_path: str) -> List[Tuple[str, str]]:
    """Get list of files and their target folders."""
    if not os.path.exists(folder_path):
        return []
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    result = []
    for filename in files:
        ext = os.path.splitext(filename)[1].lower()
        category = CATEGORIES.get(ext, "Other")
        result.append((filename, category))
    return sorted(result, key=lambda x: x[1])


# ============================================================
# WORKER THREAD
# ============================================================
class OrganizeWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(int, int)
    error = Signal(str)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        if not os.path.exists(self.folder_path):
            self.error.emit("Folder not found.")
            return

        files = [f for f in os.listdir(self.folder_path) if os.path.isfile(os.path.join(self.folder_path, f))]
        total = len(files)
        moved = 0
        skipped = 0
        undo_data = []

        for i, filename in enumerate(files):
            file_path = os.path.join(self.folder_path, filename)
            ext = os.path.splitext(filename)[1].lower()
            category = CATEGORIES.get(ext, "Other")
            category_path = os.path.join(self.folder_path, category)

            if not os.path.exists(category_path):
                os.makedirs(category_path)

            destination = os.path.join(category_path, filename)

            if os.path.exists(destination):
                skipped += 1
                self.progress.emit(i + 1, total, f"Skipped: {filename}")
                continue

            try:
                shutil.move(file_path, destination)
                undo_data.append({"from": destination, "to": file_path})
                moved += 1
                self.progress.emit(i + 1, total, f"Moved: {filename} -> {category}/")
            except Exception as e:
                skipped += 1
                self.progress.emit(i + 1, total, f"Error: {filename}")

        with open(UNDO_FILE, "w") as f:
            json.dump(undo_data, f, indent=2)

        log_action("organize", f"Moved {moved} files, skipped {skipped}")
        self.finished.emit(moved, skipped)


class UndoWorker(QThread):
    progress = Signal(str)
    finished = Signal(int, int)
    error = Signal(str)

    def run(self):
        if not os.path.exists(UNDO_FILE):
            self.error.emit("Nothing to undo.")
            return

        with open(UNDO_FILE, "r") as f:
            undo_data = json.load(f)

        if not undo_data:
            self.error.emit("Nothing to undo.")
            return

        undone = 0
        failed = 0

        for item in undo_data:
            try:
                if os.path.exists(item["from"]):
                    parent = os.path.dirname(item["to"])
                    if not os.path.exists(parent):
                        os.makedirs(parent)
                    shutil.move(item["from"], item["to"])
                    undone += 1
                    self.progress.emit(f"Undone: {os.path.basename(item['to'])}")
                else:
                    failed += 1
            except Exception as e:
                failed += 1

        os.remove(UNDO_FILE)
        log_action("undo", f"Undone {undone}, failed {failed}")
        self.finished.emit(undone, failed)


# ============================================================
# CATEGORY DIALOG
# ============================================================
class CategoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Categories")
        self.setFixedSize(400, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Extension", "Folder"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.refresh_table()
        layout.addWidget(self.table)

        # Add form
        form = QHBoxLayout()
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText(".ext")
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Folder name")
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_category)
        form.addWidget(self.ext_input)
        form.addWidget(self.folder_input)
        form.addWidget(add_btn)
        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_category)
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_categories)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(reset_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def refresh_table(self):
        self.table.setRowCount(len(CATEGORIES))
        for i, (ext, folder) in enumerate(sorted(CATEGORIES.items())):
            self.table.setItem(i, 0, QTableWidgetItem(ext))
            self.table.setItem(i, 1, QTableWidgetItem(folder))

    def add_category(self):
        ext = self.ext_input.text().strip().lower()
        folder = self.folder_input.text().strip()
        if ext and folder:
            if not ext.startswith("."):
                ext = "." + ext
            CATEGORIES[ext] = folder
            save_custom_categories()
            self.refresh_table()
            self.ext_input.clear()
            self.folder_input.clear()

    def remove_category(self):
        row = self.table.currentRow()
        if row >= 0:
            ext = self.table.item(row, 0).text()
            if ext not in DEFAULT_CATEGORIES:
                del CATEGORIES[ext]
                save_custom_categories()
                self.refresh_table()

    def reset_categories(self):
        global CATEGORIES
        CATEGORIES = DEFAULT_CATEGORIES.copy()
        if os.path.exists(CATEGORIES_FILE):
            os.remove(CATEGORIES_FILE)
        self.refresh_table()


# ============================================================
# MAIN WINDOW
# ============================================================
class FileOrganizerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        load_custom_categories()
        self.init_ui()
        self.apply_theme()
        self.refresh_preview()

    def init_ui(self):
        self.setWindowTitle("File Organizer")
        self.setFixedSize(600, 500)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(25, 20, 25, 20)

        # Title
        title = QLabel("FILE ORGANIZER")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Calibri", 20, QFont.Bold))
        layout.addWidget(title)

        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel(FOLDER_TO_ORGANIZE)
        self.folder_label.setFont(QFont("Calibri", 9))
        self.folder_label.setWordWrap(True)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_folder)
        browse_btn.setCursor(Qt.PointingHandCursor)
        folder_layout.addWidget(self.folder_label, 1)
        folder_layout.addWidget(browse_btn)
        layout.addLayout(folder_layout)

        # Tabs
        self.tabs = QTabWidget()
        
        # Preview tab
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(2)
        self.preview_table.setHorizontalHeaderLabels(["File", "Category"])
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setEditTriggers(QTableWidget.NoEditTriggers)
        preview_layout.addWidget(self.preview_table)
        self.preview_count = QLabel("")
        preview_layout.addWidget(self.preview_count)
        self.tabs.addTab(preview_widget, "Preview")
        
        # Log tab
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        self.tabs.addTab(log_widget, "Log")
        
        layout.addWidget(self.tabs)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Buttons
        btn_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Refresh Preview")
        self.preview_btn.clicked.connect(self.refresh_preview)
        self.preview_btn.setCursor(Qt.PointingHandCursor)
        
        self.organize_btn = QPushButton("Organize")
        self.organize_btn.clicked.connect(self.organize)
        self.organize_btn.setCursor(Qt.PointingHandCursor)
        
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.clicked.connect(self.undo)
        self.undo_btn.setCursor(Qt.PointingHandCursor)
        
        self.categories_btn = QPushButton("Categories")
        self.categories_btn.clicked.connect(self.manage_categories)
        self.categories_btn.setCursor(Qt.PointingHandCursor)
        
        btn_layout.addWidget(self.preview_btn)
        btn_layout.addWidget(self.organize_btn)
        btn_layout.addWidget(self.undo_btn)
        btn_layout.addWidget(self.categories_btn)
        layout.addLayout(btn_layout)

    def apply_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(26, 26, 46))
        palette.setColor(QPalette.WindowText, QColor(238, 238, 238))
        palette.setColor(QPalette.Base, QColor(30, 30, 50))
        palette.setColor(QPalette.Text, QColor(238, 238, 238))
        palette.setColor(QPalette.Button, QColor(233, 69, 96))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        self.setPalette(palette)

        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a2e; }
            QTabWidget::pane { background-color: #1e1e32; border: 1px solid #2a2a4a; border-radius: 6px; }
            QTabBar::tab { background-color: #2a2a4a; color: #888; padding: 8px 16px; margin-right: 2px; border-radius: 4px 4px 0 0; }
            QTabBar::tab:selected { background-color: #1e1e32; color: #e94560; }
            QTableWidget { background-color: #1e1e32; color: #ccc; border: 1px solid #2a2a4a; gridline-color: #2a2a4a; }
            QTableWidget::item { padding: 4px; }
            QHeaderView::section { background-color: #2a2a4a; color: #aaa; padding: 4px; border: none; }
            QTextEdit { background-color: #1e1e32; color: #ccc; border: 1px solid #2a2a4a; border-radius: 4px; }
            QProgressBar { background-color: #1e1e32; border: none; border-radius: 3px; height: 6px; }
            QProgressBar::chunk { background-color: #e94560; border-radius: 3px; }
        """)

        self.organize_btn.setStyleSheet("""
            QPushButton { background-color: #e94560; color: white; border: none; border-radius: 6px; padding: 8px 16px; }
            QPushButton:hover { background-color: #c73e54; }
            QPushButton:disabled { background-color: #555; }
        """)

        for btn in [self.preview_btn, self.undo_btn, self.categories_btn]:
            btn.setStyleSheet("""
                QPushButton { background-color: #3a3a5a; color: white; border: none; border-radius: 6px; padding: 8px 16px; }
                QPushButton:hover { background-color: #4a4a6a; }
            """)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            global FOLDER_TO_ORGANIZE
            FOLDER_TO_ORGANIZE = folder
            self.folder_label.setText(folder)
            self.refresh_preview()

    def refresh_preview(self):
        files = get_preview(FOLDER_TO_ORGANIZE)
        self.preview_table.setRowCount(len(files))
        for i, (filename, category) in enumerate(files):
            self.preview_table.setItem(i, 0, QTableWidgetItem(filename))
            self.preview_table.setItem(i, 1, QTableWidgetItem(category))
        self.preview_count.setText(f"{len(files)} files found")
        self.refresh_log()

    def refresh_log(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                log = json.load(f)
            lines = []
            for entry in log[-30:]:
                lines.append(f"[{entry['timestamp']}] {entry['action']}")
                if isinstance(entry['details'], list):
                    for d in entry['details'][:3]:
                        lines.append(f"    {d}")
            self.log_text.setText("\n".join(lines))

    def organize(self):
        reply = QMessageBox.question(self, "Confirm", "Organize files now?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Organizing...")

        self.worker = OrganizeWorker(FOLDER_TO_ORGANIZE)
        self.worker.progress.connect(self.on_organize_progress)
        self.worker.finished.connect(self.on_organize_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_organize_progress(self, current, total, msg):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(msg)

    def on_organize_finished(self, moved, skipped):
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Done! Moved: {moved}, Skipped: {skipped}")
        self.refresh_preview()

    def undo(self):
        if not os.path.exists(UNDO_FILE):
            QMessageBox.information(self, "Undo", "Nothing to undo.")
            return

        reply = QMessageBox.question(self, "Confirm", "Undo last organize?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Undoing...")

        self.worker = UndoWorker()
        self.worker.progress.connect(lambda msg: self.status_label.setText(msg))
        self.worker.finished.connect(lambda u, f: [
            self.set_ui_enabled(True),
            self.progress_bar.setVisible(False),
            self.status_label.setText(f"Undone: {u}, Failed: {f}"),
            self.refresh_preview()
        ])
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def manage_categories(self):
        dialog = CategoryDialog(self)
        dialog.exec()
        self.refresh_preview()

    def set_ui_enabled(self, enabled):
        for widget in [self.preview_btn, self.organize_btn, self.undo_btn, self.categories_btn]:
            widget.setEnabled(enabled)

    def on_error(self, msg):
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(msg)


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = FileOrganizerWindow()
    window.show()
    sys.exit(app.exec())