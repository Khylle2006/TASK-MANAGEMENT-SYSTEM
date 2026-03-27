from datetime import date, datetime, timedelta
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QHeaderView, QButtonGroup, QComboBox

from py.database import get_connection

TODAY = date.today().isoformat()

PRIORITY_BG = {"High": "#FDECEA", "Medium": "#FFF8E1", "Low": "#E8F5E9"}
PRIORITY_FG = {"High": "#D93025", "Medium": "#F9A825", "Low": "#2E7D32"}


def _style_table(table, headers):
    """Style table with given headers"""
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setEditTriggers(table.NoEditTriggers)
    table.setSelectionBehavior(table.SelectRows)
    table.verticalHeader().setVisible(False)
    table.setShowGrid(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


def _fill_row(table, row, task, show_completed_date=False):
    """Fill a table row with task data"""
    title = QTableWidgetItem(task["title"])
    title.setData(Qt.UserRole, task["id"])

    pri = task["priority"] or "Medium"
    pri_item = QTableWidgetItem(pri)
    pri_item.setForeground(QColor(PRIORITY_FG.get(pri, "#888")))
    pri_item.setBackground(QColor(PRIORITY_BG.get(pri, "#FFF")))
    pri_item.setTextAlignment(Qt.AlignCenter)

    if show_completed_date:
        # For completed tasks, show completion date
        done_date = task.get("done_at", "—")
        if done_date and done_date != "—":
            done_date = done_date[:10]  # Take only date part
        due_item = QTableWidgetItem(done_date)
        due_item.setForeground(QColor("#888888"))
        table.setItem(row, 0, title)
        table.setItem(row, 1, pri_item)
        table.setItem(row, 2, due_item)
    else:
        # For active tasks, show due date
        due = QTableWidgetItem(task["due_date"] or "—")
        due.setForeground(QColor("#888888"))
        table.setItem(row, 0, title)
        table.setItem(row, 1, pri_item)
        table.setItem(row, 2, due)


class OverallTaskPage:
    """Overall Task page with combo box to switch between task types"""
    
    def __init__(self, username, container_widget, parent=None):
        """
        Initialize the Overall Task page
        :param username: Current user's username
        :param container_widget: The QWidget container from UI
        :param parent: Parent window (UserDashboard)
        """
        self.username = username
        self.container = container_widget
        self.parent = parent
        
        # Find UI elements
        self._find_ui_elements()
        
        # Setup combo box
        self._setup_combo_box()
        
        # Setup table
        self._setup_table()
        
        # Load initial data
        self.load()
    
    def _find_ui_elements(self):
        """Find all UI elements in the container widget"""
        # Combo box for task type selection
        self.cmbTaskType = self.container.findChild(QComboBox, "cmbTaskType")
        
        # Table for displaying tasks
        self.tblTasks = self.container.findChild(QWidget, "tblTasks")
        
        # Labels for counts (if they exist)
        self.lblTodayCount = self.container.findChild(QWidget, "lblTodayCount")
        self.lblOverdueCount = self.container.findChild(QWidget, "lblOverdueCount")
        self.lblUpcomingCount = self.container.findChild(QWidget, "lblUpcomingCount")
        self.lblCompletedCount = self.container.findChild(QWidget, "lblCompletedCount")
        
        # If labels not found, try alternative names
        if self.lblTodayCount is None:
            self.lblTodayCount = self.container.findChild(QWidget, "lblDueToday")
        if self.lblOverdueCount is None:
            self.lblOverdueCount = self.container.findChild(QWidget, "lblOverDue")
        if self.lblUpcomingCount is None:
            self.lblUpcomingCount = self.container.findChild(QWidget, "lblUpcoming")
        if self.lblCompletedCount is None:
            self.lblCompletedCount = self.container.findChild(QWidget, "lblCompleted")
    
    def _setup_combo_box(self):
        """Setup combo box with task types"""
        if self.cmbTaskType:
            # Add task types
            self.cmbTaskType.addItem("📅 Today Tasks", "today")
            self.cmbTaskType.addItem("⚠️ Overdue", "overdue")
            self.cmbTaskType.addItem("📌 Upcoming", "upcoming")
            self.cmbTaskType.addItem("✅ Completed", "completed")
            
            # Connect signal
            self.cmbTaskType.currentIndexChanged.connect(self.on_task_type_changed)
    
    def _setup_table(self):
        """Setup table headers and properties"""
        if self.tblTasks:
            # Set headers based on selected type
            self._update_table_headers()
            
            # Connect double-click to toggle done
            self.tblTasks.doubleClicked.connect(self._on_table_double_click)
    
    def _update_table_headers(self):
        """Update table headers based on current selection"""
        if not self.tblTasks:
            return
        
        current_type = self.cmbTaskType.currentData() if self.cmbTaskType else "today"
        
        if current_type == "completed":
            _style_table(self.tblTasks, ["Task", "Priority", "Completed On"])
        else:
            _style_table(self.tblTasks, ["Task", "Priority", "Due Date"])
    
    def on_task_type_changed(self):
        """Handle combo box selection change"""
        self._update_table_headers()
        self.load_current_view()
    
    def load(self):
        """Load all data (counts and current view)"""
        self._load_counts()
        self.load_current_view()
    
    def load_current_view(self):
        """Load tasks based on current combo box selection"""
        if not self.cmbTaskType or not self.tblTasks:
            return
        
        current_type = self.cmbTaskType.currentData()
        
        if current_type == "today":
            self._load_today_tasks()
        elif current_type == "overdue":
            self._load_overdue_tasks()
        elif current_type == "upcoming":
            self._load_upcoming_tasks()
        elif current_type == "completed":
            self._load_completed_tasks()
    
    # ─── Database Helpers ───────────────────────────────────────────────
    
    def _query(self, sql, params=()):
        """Execute query and return results as list of dicts"""
        conn = get_connection()
        if conn is None:
            return []
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    
    def _scalar(self, sql, params=()):
        """Execute query and return single value"""
        conn = get_connection()
        if conn is None:
            return 0
        cur = conn.cursor()
        cur.execute(sql, params)
        val = cur.fetchone()[0]
        conn.close()
        return val
    
    # ─── Counts Loading ─────────────────────────────────────────────────
    
    def _load_counts(self):
        """Load and update count labels"""
        # Today's tasks count
        today_count = self._scalar(
            "SELECT COUNT(*) FROM tasks WHERE username=? AND due_date=? AND is_done=0 AND is_draft=0",
            (self.username, TODAY))
        
        # Overdue tasks count
        overdue_count = self._scalar(
            "SELECT COUNT(*) FROM tasks WHERE username=? AND due_date<? AND is_done=0 AND is_draft=0",
            (self.username, TODAY))
        
        # Upcoming tasks count (next 7 days)
        next7 = (date.today() + timedelta(days=7)).isoformat()
        upcoming_count = self._scalar(
            "SELECT COUNT(*) FROM tasks WHERE username=? AND due_date>? AND due_date<=? AND is_done=0 AND is_draft=0",
            (self.username, TODAY, next7))
        
        # Completed tasks count
        completed_count = self._scalar(
            "SELECT COUNT(*) FROM tasks WHERE username=? AND is_done=1",
            (self.username,))
        
        # Update labels if they exist
        if self.lblTodayCount:
            self.lblTodayCount.setText(str(today_count))
        if self.lblOverdueCount:
            self.lblOverdueCount.setText(str(overdue_count))
        if self.lblUpcomingCount:
            self.lblUpcomingCount.setText(str(upcoming_count))
        if self.lblCompletedCount:
            self.lblCompletedCount.setText(str(completed_count))
    
    # ─── Task Loading Methods ──────────────────────────────────────────
    
    def _populate_table(self, tasks, show_completed_date=False):
        """Populate table with tasks"""
        if not self.tblTasks:
            return
        
        self.tblTasks.setRowCount(len(tasks))
        
        for i, task in enumerate(tasks):
            _fill_row(self.tblTasks, i, task, show_completed_date)
        
        self.tblTasks.resizeRowsToContents()
    
    def _load_today_tasks(self):
        """Load today's tasks"""
        tasks = self._query(
            "SELECT id, title, priority, due_date FROM tasks "
            "WHERE username=? AND due_date=? AND is_done=0 AND is_draft=0 "
            "ORDER BY priority",
            (self.username, TODAY))
        self._populate_table(tasks, show_completed_date=False)
    
    def _load_overdue_tasks(self):
        """Load overdue tasks"""
        tasks = self._query(
            "SELECT id, title, priority, due_date FROM tasks "
            "WHERE username=? AND due_date<? AND is_done=0 AND is_draft=0 "
            "ORDER BY due_date",
            (self.username, TODAY))
        self._populate_table(tasks, show_completed_date=False)
    
    def _load_upcoming_tasks(self):
        """Load upcoming tasks (next 7 days)"""
        next7 = (date.today() + timedelta(days=7)).isoformat()
        tasks = self._query(
            "SELECT id, title, priority, due_date FROM tasks "
            "WHERE username=? AND due_date>? AND due_date<=? AND is_done=0 AND is_draft=0 "
            "ORDER BY due_date",
            (self.username, TODAY, next7))
        self._populate_table(tasks, show_completed_date=False)
    
    def _load_completed_tasks(self):
        """Load completed tasks"""
        tasks = self._query(
            "SELECT id, title, priority, done_at FROM tasks "
            "WHERE username=? AND is_done=1 "
            "ORDER BY done_at DESC LIMIT 50",
            (self.username,))
        self._populate_table(tasks, show_completed_date=True)
    
    # ─── Task Actions ───────────────────────────────────────────────────
    
    def _on_table_double_click(self):
        """Handle double-click on table based on current view"""
        if not self.tblTasks or not self.cmbTaskType:
            return
        
        current_type = self.cmbTaskType.currentData()
        
        if current_type == "completed":
            # Restore completed task
            self._restore_task()
        else:
            # Toggle done for active tasks
            self._toggle_done()
    
    def _toggle_done(self):
        """Toggle task completion status on double-click"""
        current_row = self.tblTasks.currentRow()
        if current_row < 0:
            return
        
        task_id = self.tblTasks.item(current_row, 0).data(Qt.UserRole)
        if task_id is None:
            return
        
        conn = get_connection()
        if conn is None:
            return
        
        cur = conn.cursor()
        cur.execute("SELECT is_done FROM tasks WHERE id=?", (task_id,))
        row = cur.fetchone()
        
        if row:
            new_val = 0 if row[0] else 1
            done_at = datetime.now().isoformat() if new_val else None
            cur.execute(
                "UPDATE tasks SET is_done=?, done_at=? WHERE id=?",
                (new_val, done_at, task_id)
            )
            conn.commit()
        
        conn.close()
        
        # Refresh all data
        self.load()
        
        # Also refresh dashboard if parent exists
        if self.parent and hasattr(self.parent, '_refresh_dashboard'):
            self.parent._refresh_dashboard()
    
    def _restore_task(self):
        """Restore a completed task (un-complete it)"""
        current_row = self.tblTasks.currentRow()
        if current_row < 0:
            return
        
        task_id = self.tblTasks.item(current_row, 0).data(Qt.UserRole)
        if task_id is None:
            return
        
        conn = get_connection()
        if conn is None:
            return
        
        cur = conn.cursor()
        cur.execute(
            "UPDATE tasks SET is_done=0, done_at=NULL WHERE id=?",
            (task_id,)
        )
        conn.commit()
        conn.close()
        
        # Refresh all data
        self.load()
        
        # Also refresh dashboard if parent exists
        if self.parent and hasattr(self.parent, '_refresh_dashboard'):
            self.parent._refresh_dashboard()