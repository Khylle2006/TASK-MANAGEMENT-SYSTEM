from datetime import date, datetime

from PyQt5.QtCore import QObject, pyqtSignal, QDate
from PyQt5.QtWidgets import QMessageBox

from py.database import get_connection


class AddTaskPage(QObject):
    """
    Controller for the pageAddTask page that already exists in user_dashboard.ui.
    Pass in the QWidget page and the parent QMainWindow.

    Emits task_saved when a task is successfully created so the dashboard
    can refresh and navigate back to the home page.
    """

    task_saved = pyqtSignal()

    def __init__(self, username: str, container, main_window):
        super().__init__(container)  # container is the page widget
        self.username = username
        self.main_window = main_window
        self.container = container

        # ── Grab widgets from the main window (where the UI was loaded) ───
        # The widgets are children of main_window, not container
        self.titleField = main_window.inputField      # QLineEdit
        self.descField = main_window.descField        # QTextEdit  
        self.priorityCombo = main_window.comboBox     # QComboBox
        self.dueDate = main_window.dateEdit           # QDateEdit
        self.btnCreate = main_window.btnCreateTask    # QPushButton
        self.btnCancel = main_window.btnCancel        # QPushButton
        
        # ── New list widgets ───────────────────────────────────────────────
        self.listCombo = main_window.listCombo        # QComboBox for lists
        self.btnRefreshLists = main_window.btnRefreshLists  # Refresh button

        # Set date minimum to today
        self.dueDate.setMinimumDate(QDate.currentDate())
        self.dueDate.setDate(QDate.currentDate())

        # ── Load lists into combo box ──────────────────────────────────────
        self._load_lists()

        # ── Connect buttons ───────────────────────────────────────────────
        self.btnCreate.clicked.connect(self._create_task)
        self.btnCancel.clicked.connect(self._cancel)
        self.btnRefreshLists.clicked.connect(self._load_lists)

    # ── List Methods ───────────────────────────────────────────────────────

    def _load_lists(self):
        """Load user's lists into the combo box"""
        self.listCombo.clear()
        self.listCombo.addItem("-- No List --", None)  # Add None option for no list
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, section
                FROM lists
                WHERE username = ?
                ORDER BY name
            """, (self.username,))
            
            lists = cursor.fetchall()
            conn.close()
            
            for list_id, list_name, section in lists:
                # Add each list with icon and section info
                self.listCombo.addItem(f"📁 {list_name} ({section})", list_id)
                
        except Exception as e:
            print(f"Error loading lists: {e}")

    # ── Actions ───────────────────────────────────────────────────────────

    def _create_task(self):
        """Save task to database and clear form for next entry"""
        title = self.titleField.text().strip()
        desc = self.descField.toPlainText().strip()
        priority = self.priorityCombo.currentText()
        due_date = self.dueDate.date().toString("yyyy-MM-dd")
        list_id = self.listCombo.currentData()  # Get the list ID (None if no list)
        
        # Validation
        if not title:
            QMessageBox.warning(self.main_window, "Warning", "Task title cannot be empty!")
            return
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Insert task with list_id
            cursor.execute("""
                INSERT INTO tasks (username, title, description, priority, due_date, list_id, is_done, is_draft, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?)
            """, (self.username, title, desc, priority, due_date, list_id, datetime.now().isoformat()))
            
            conn.commit()
            task_id = cursor.lastrowid
            conn.close()
            
            QMessageBox.information(self.main_window, "Success", f"Task '{title}' created successfully!")
            self._clear_form()
            self.task_saved.emit()
            
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Failed to create task: {str(e)}")

    def _cancel(self):
        """Clear form and navigate home"""
        self._clear_form()
        self.task_saved.emit()   # just navigate home without saving

    def _clear_form(self):
        """Clear all input fields"""
        self.titleField.clear()
        self.descField.clear()
        self.priorityCombo.setCurrentIndex(1)  # Medium (index 1)
        self.dueDate.setDate(QDate.currentDate())
        self.listCombo.setCurrentIndex(0)  # Reset to "-- No List --"
        self.titleField.setFocus()  # Set focus back to title field for next task

    def refresh_lists(self):
        """Public method to refresh lists (can be called from dashboard)"""
        self._load_lists()