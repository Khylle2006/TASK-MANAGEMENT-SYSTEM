from datetime import date

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView

from py.database import get_connection

TODAY = date.today().isoformat()

PRIORITY_BG = {"High": "#FDECEA", "Medium": "#FFF8E1", "Low": "#E8F5E9"}
PRIORITY_FG = {"High": "#D93025", "Medium": "#F9A825", "Low": "#2E7D32"}

STATUS_FG = {"Done": "#2E7D32", "Overdue": "#D93025", "Upcoming": "#888888", "Today": "#1565C0"}


class PriorityViewPage(QObject):
    """
    Controller for the pagePriorityView page inside user_dashboard.ui.
    Uses comboBox_2 (priority filter) and tableWidget to display tasks.
    """

    def __init__(self, username: str, page_widget, parent=None):
        super().__init__(parent)
        self.username = username
        self.page     = page_widget

        win = parent  # the QMainWindow

        self.combo = win.comboBox_2    # QComboBox  High / Medium / Low
        self.table = win.tableWidget   # QTableWidget

        # ── Table setup ───────────────────────────────────────────────────
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Priority", "Task", "Description", "Due Date", "Status"])
        self.table.setEditTriggers(self.table.NoEditTriggers)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # ── Filter change ─────────────────────────────────────────────────
        self.combo.currentTextChanged.connect(self.load)

    # ── Load / refresh ────────────────────────────────────────────────────

    def load(self):
        priority = self.combo.currentText()   # "High" / "Medium" / "Low"

        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            """SELECT id, priority, title, description, due_date, is_done
               FROM tasks
               WHERE username=? AND priority=? AND is_draft=0
               ORDER BY due_date ASC""",
            (self.username, priority)
        )
        tasks = [dict(r) for r in cur.fetchall()]
        conn.close()

        self.table.setRowCount(len(tasks))

        for i, t in enumerate(tasks):
            status = self._status(t)

            pri = t["priority"] or "Medium"
            pri_item = QTableWidgetItem(pri)
            pri_item.setForeground(QColor(PRIORITY_FG.get(pri, "#888")))
            pri_item.setBackground(QColor(PRIORITY_BG.get(pri, "#FFF")))
            pri_item.setTextAlignment(Qt.AlignCenter)

            title_item = QTableWidgetItem(t["title"])
            title_item.setData(Qt.UserRole, t["id"])

            description = QTableWidgetItem(t["description"])

            due_item = QTableWidgetItem(t["due_date"] or "—")
            due_item.setForeground(QColor("#888888"))

            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(STATUS_FG.get(status, "#888")))
            status_item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(i, 0, pri_item)
            self.table.setItem(i, 1, title_item)
            self.table.setItem(i, 2, description)
            self.table.setItem(i, 3, due_item)
            self.table.setItem(i, 4, status_item)

        self.table.resizeRowsToContents()

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _status(task) -> str:
        if task["is_done"]:
            return "Done"
        due = task["due_date"]
        if not due:
            return "Upcoming"
        if due < TODAY:
            return "Overdue"
        if due == TODAY:
            return "Today"
        return "Upcoming"