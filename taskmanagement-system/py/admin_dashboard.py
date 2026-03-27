from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QButtonGroup, QTableWidgetItem, QVBoxLayout, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from py.database import get_connection
from py.confirm_dialog import confirm


class AdminDashboard(QMainWindow):
    def __init__(self, user):
        super().__init__()
        uic.loadUi("ui/admin_dashboard.ui", self)
        self.user = user
        self.lblUser.setText(f"{user['username'].title()}")

        self.navGroup = QButtonGroup(self)
        self.navGroup.setExclusive(True)
        for btn in [self.btnNavDash, self.btnNavUsers]:
            self.navGroup.addButton(btn)

        self.btnNavDash.clicked.connect(lambda: self.switch_page(0))
        self.btnNavUsers.clicked.connect(lambda: self.switch_page(1))
        
        self.btnLogout.clicked.connect(self.logout)

        # Initialize sub-pages
        self.load_sub_pages()  # ✅ FIXED: Call this!
        
        # Load initial data
        self.load_dashboard_stats()
        self.load_recent_users()

        self.showMaximized()

    def load_sub_pages(self):
        from py.manage_users import ManageUsers

        self.usersWidget = ManageUsers()
        self.usersWidget.on_data_changed = self.refresh_all  # This needs to be defined
        self._inject(self.pageUsers, self.usersWidget)

    def _inject(self, page, widget):
        if page.layout() is None:
            layout = QVBoxLayout(page)
            layout.setContentsMargins(0, 0, 0, 0)
        page.layout().addWidget(widget)

    def switch_page(self, index):
        self.stackedWidget.setCurrentIndex(index)
        refresh_map = {
            0: self.refresh_dashboard,
            1: self.usersWidget.load_users if hasattr(self, 'usersWidget') else None,
        }
        if index in refresh_map and refresh_map[index]:
            refresh_map[index]()

    def refresh_all(self):
        """Refresh all data when changes are made"""
        self.refresh_dashboard()
        if hasattr(self, 'usersWidget'):
            self.usersWidget.load_users()

    def refresh_dashboard(self):
        self.load_dashboard_stats()
        self.load_recent_users()

    def load_dashboard_stats(self):
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            self.valEmp.setText(str(count))
        except Exception as e:
            print(f"Error loading stats: {e}")
            self.valEmp.setText("0")
        finally:
            conn.close()

    def load_recent_users(self):
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # ✅ FIXED: Get separate columns instead of concatenating
            cursor.execute("""
                SELECT username, first_name, last_name, email, created_at 
                FROM users 
                ORDER BY id DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()
        except Exception as e:
            print(f"Error loading recent users: {e}")
            rows = []
        finally:
            conn.close()

        tbl = self.tblRecentUsers
        tbl.setRowCount(0)
        tbl.setColumnCount(5)
        tbl.setHorizontalHeaderLabels([
            "Username", "First Name", "Last Name", "Email", "Created At"
        ])
        
        # Configure table appearance
        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setStretchLastSection(False)
        tbl.setAlternatingRowColors(True)
        tbl.setStyleSheet("""
            QTableWidget {
                background: #253447;
                alternate-background-color: #1e2a3a;
                border: none;
                border-radius: 8px;
                gridline-color: #2a3d55;
                color: #c8d6e5;
            }
            QTableWidget::item {
                padding: 6px 4px;
                color: #c8d6e5;
            }
            QTableWidget::item:selected {
                background: #4a9eff30;
                color: #ffffff;
            }
            QHeaderView::section {
                background: #1e2a3a;
                color: #8a9bb0;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #2a3d55;
            }
        """)

        bg_even = QColor("#253447")
        bg_odd = QColor("#1e2a3a")
        c_white = QColor("#c8d6e5")

        # Populate table
        for row_data in rows:
            row = tbl.rowCount()
            tbl.insertRow(row)
            bg = bg_even if row % 2 == 0 else bg_odd

            for col, val in enumerate(row_data):
                text = str(val) if val is not None else ""
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(c_white)
                item.setBackground(bg)
                tbl.setItem(row, col, item)

    def logout(self):
        if not confirm(self, "Logout", "Are you sure you want to logout?",
                confirm_text="Logout", confirm_color="#e74c3c", icon=""):
            return
        from py.login import LoginWindow
        self.login = LoginWindow()
        self.login.show()
        self.close()