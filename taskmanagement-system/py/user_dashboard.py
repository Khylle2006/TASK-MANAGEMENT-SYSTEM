from datetime import date, datetime, timedelta

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QHeaderView, QButtonGroup

from py.database import get_connection

TODAY = date.today().isoformat()

PRIORITY_BG = {"High": "#FDECEA", "Medium": "#FFF8E1", "Low": "#E8F5E9"}
PRIORITY_FG = {"High": "#D93025", "Medium": "#F9A825", "Low": "#2E7D32"}


def _style_table(table, headers):
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setEditTriggers(table.NoEditTriggers)
    table.setSelectionBehavior(table.SelectRows)
    table.verticalHeader().setVisible(False)
    table.setShowGrid(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


def _fill_row(table, row, task):
    title = QTableWidgetItem(task["title"])
    title.setData(Qt.UserRole, task["id"])

    pri = task["priority"] or "Medium"
    pri_item = QTableWidgetItem(pri)
    pri_item.setForeground(QColor(PRIORITY_FG.get(pri, "#888")))
    pri_item.setBackground(QColor(PRIORITY_BG.get(pri, "#FFF")))
    pri_item.setTextAlignment(Qt.AlignCenter)

    due = QTableWidgetItem(task["due_date"] or "—")
    due.setForeground(QColor("#888888"))

    table.setItem(row, 0, title)
    table.setItem(row, 1, pri_item)
    table.setItem(row, 2, due)


class UserDashboard(QMainWindow):
    def __init__(self, user):
        super().__init__()
        uic.loadUi("ui/user_dashboard.ui", self)
        self.setMinimumSize(1000, 700)
        self.user = user
        self.username = user["username"]
        if hasattr(self, 'pageOrganize'):
            pass  # Hide organize page if it exists (it should, but just in case)

            
        # ── Sidebar nav ───────────────────────────────────────────────────
        self.navGroup = QButtonGroup(self)
        self.navGroup.setExclusive(True)
        for btn in [self.btnNavHome, self.btnAddTask_2, self.btnPriorityView, self.btnOverallTask, self.btnOrganizeTask]:
            btn.setCheckable(True)
            self.navGroup.addButton(btn)

        self.btnNavHome.clicked.connect(lambda: self._go(0))
        self.btnAddTask_2.clicked.connect(lambda: self._go(1))
        self.btnPriorityView.clicked.connect(lambda: self._go(2))
        self.btnOverallTask.clicked.connect(lambda: self._go(3))
        self.btnOrganizeTask.clicked.connect(lambda: self._go(4))
        self.btnLogout.clicked.connect(self._logout)

        # ── Dashboard header "Add Task" button → go to add task page ─────
        self.btnAddTask.clicked.connect(lambda: self._go(1))

        # ── Style tables ──────────────────────────────────────────────────
        _style_table(self.tblTodayTask, ["Task", "Priority", "Due"])
        _style_table(self.tblOverdue, ["Task", "Priority", "Due"])
        _style_table(self.tblUpcoming, ["Task", "Priority", "Due"])

        self.tblTodayTask.doubleClicked.connect(self._toggle_done)
        self.tblOverdue.doubleClicked.connect(self._toggle_done)
        self.tblUpcoming.doubleClicked.connect(self._toggle_done)

        # ── Sub-pages ─────────────────────────────────────────────────────
        from py.addtask import AddTaskPage
        self.addTaskPage = AddTaskPage(self.username, self.pageAddTask, self)
        self.addTaskPage.task_saved.connect(self._refresh_dashboard)

        from py.priorityview import PriorityViewPage
        self.priorityPage = PriorityViewPage(self.username, self.pagePriorityView, self)

        from py.overall_task import OverallTaskPage
        self.overallTaskPage = OverallTaskPage(self.username, self.pageOverallTask, self)

        from py.organize_task import OrganizePage
        self.organizeTask = OrganizePage(self.username, self.pageOrganization, self)

        # ── Boot ──────────────────────────────────────────────────────────
        self.btnNavHome.setChecked(True)
        self._refresh_dashboard()
        self.showMaximized()

    # ── Navigation ────────────────────────────────────────────────────────

    def _go(self, index):
        print(f"GO TO PAGE: {index}")  # ADD THIS LINE
        self.stackedWidget.setCurrentIndex(index)
        if index == 2:
            self.priorityPage.load()
        elif index == 3:
            self.overallTaskPage.load()
        elif index == 4:
            if hasattr(self, 'organizeTask'):
                print("REFRESHING ORGANIZE TASK")  # ADD THIS LINE
                self.organizeTask.refresh()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _query(self, sql, params=()):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def _scalar(self, sql, params=()):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        val = cur.fetchone()[0]
        conn.close()
        return val

    # ── Dashboard refresh ─────────────────────────────────────────────────

    def _refresh_dashboard(self):
        self._load_stats()
        self._load_today()
        self._load_overdue()
        self._load_upcoming()
        self._go(0)
        self.btnNavHome.setChecked(True)

    def _load_stats(self):
        self.lblDueToday.setText(str(self._scalar(
            "SELECT COUNT(*) FROM tasks WHERE username=? AND due_date=? AND is_done=0 AND is_draft=0",
            (self.username, TODAY))))
        self.lblCompleted.setText(str(self._scalar(
            "SELECT COUNT(*) FROM tasks WHERE username=? AND is_done=1",
            (self.username,))))
        self.lblOverDue.setText(str(self._scalar(
            "SELECT COUNT(*) FROM tasks WHERE username=? AND due_date<? AND is_done=0 AND is_draft=0",
            (self.username, TODAY))))

    def _populate(self, table, tasks):
        table.setRowCount(len(tasks))
        for i, t in enumerate(tasks):
            _fill_row(table, i, t)
        table.resizeRowsToContents()

    def _load_today(self):
        self._populate(self.tblTodayTask, self._query(
            "SELECT id,title,priority,due_date FROM tasks "
            "WHERE username=? AND due_date=? AND is_done=0 AND is_draft=0 ORDER BY priority",
            (self.username, TODAY)))

    def _load_overdue(self):
        tasks = self._query(
            "SELECT id,title,priority,due_date FROM tasks "
            "WHERE username=? AND due_date<? AND is_done=0 AND is_draft=0 ORDER BY due_date",
            (self.username, TODAY))
        self._populate(self.tblOverdue, tasks)
        n = len(tasks)
        self.overdueBadge.setText(f"{n} task{'s' if n != 1 else ''}")

    def _load_upcoming(self):
        next7 = (date.today() + timedelta(days=7)).isoformat()
        tasks = self._query(
            "SELECT id,title,priority,due_date FROM tasks "
            "WHERE username=? AND due_date>? AND due_date<=? AND is_done=0 AND is_draft=0 ORDER BY due_date",
            (self.username, TODAY, next7))
        self._populate(self.tblUpcoming, tasks)
        n = len(tasks)
        self.upcomingBadge.setText(f"{n} task{'s' if n != 1 else ''} · Next 7 days")

    # ── Toggle done on double-click ───────────────────────────────────────

    def _toggle_done(self, index):
        table = self.sender()
        task_id = table.item(index.row(), 0).data(Qt.UserRole)
        if task_id is None:
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT is_done FROM tasks WHERE id=?", (task_id,))
        row = cur.fetchone()
        if row:
            new_val = 0 if row[0] else 1
            done_at = datetime.now().isoformat() if new_val else None
            cur.execute("UPDATE tasks SET is_done=?, done_at=? WHERE id=?",
                        (new_val, done_at, task_id))
            conn.commit()
        conn.close()
        self._refresh_dashboard()

    # ── Logout ────────────────────────────────────────────────────────────

    def _logout(self):
        from py.login import LoginWindow
        self.login = LoginWindow()
        self.login.show()
        self.close()