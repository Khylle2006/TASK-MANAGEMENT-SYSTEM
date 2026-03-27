from PyQt5 import uic
from PyQt5.QtWidgets import (QWidget, QDialog, QTableWidgetItem,
                              QMessageBox, QHBoxLayout, QPushButton,
                              QVBoxLayout, QLabel, QLineEdit,
                              QTableWidget, QHeaderView, QApplication)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
from py.database import get_connection
from py.confirm_dialog import confirm


# ── Add / Edit Employee Dialog ────────────────────────────────────────────────

# ── Credentials Dialog ────────────────────────────────────────────────────────
class CredentialsDialog(QDialog):
    """Shows username & created date for a user with copy buttons."""
    def __init__(self, email, username, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Credentials")
        self.setFixedSize(480, 280)
        self.setStyleSheet("background:#1a2535; color:#c8d6e5;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        # Title
        title = QLabel("🔑  Login Credentials")
        title.setStyleSheet("font-size:16px;font-weight:bold;color:#ffffff;")
        layout.addWidget(title)

        sub = QLabel(f"Viewing info for: {username}")
        sub.setStyleSheet("color:#8a9bb0;font-size:12px;")
        layout.addWidget(sub)

        # Fetch from DB — use clear variable names
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, created_at FROM users WHERE username=?",
            (username,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            db_username = row[0]
            db_created  = str(row[1])[:10] if row[1] else "—"  # show date only

            def field_row(label, value):
                box = QVBoxLayout()
                box.setSpacing(4)

                lbl = QLabel(label)
                lbl.setStyleSheet("color:#8a9bb0;font-size:11px;font-weight:600;")

                val_row = QHBoxLayout()

                val_edit = QLineEdit(value)
                val_edit.setReadOnly(True)
                val_edit.setMinimumWidth(280)
                val_edit.setFixedHeight(38)
                val_edit.setStyleSheet("""
                    QLineEdit {
                        background:#253447; border:1px solid #3a4f66;
                        border-radius:6px; padding:8px 14px;
                        color:#ffffff; font-size:14px;
                        selection-background-color:#4a9eff;
                    }
                """)

                copy_btn = QPushButton("Copy")
                copy_btn.setFixedHeight(36)
                copy_btn.setFixedWidth(60)
                copy_btn.setStyleSheet("""
                    QPushButton{background:#2a3d55;color:#c8d6e5;border:none;
                    border-radius:6px;font-size:12px;font-weight:bold;}
                    QPushButton:hover{background:#4a9eff;color:#fff;}
                """)
                copy_btn.clicked.connect(lambda _, v=value, b=copy_btn: (
                    QApplication.clipboard().setText(v),
                    b.setText("✔"),
                    b.setStyleSheet("QPushButton{background:#2ecc71;color:#fff;"
                                    "border:none;border-radius:6px;font-size:12px;font-weight:bold;}")
                ))

                val_row.addWidget(val_edit, 1)
                val_row.addWidget(copy_btn)
                box.addWidget(lbl)
                box.addLayout(val_row)
                return box

            layout.addLayout(field_row("Username", db_username))
            layout.addLayout(field_row("Created Date", db_created))

        else:
            no_creds = QLabel("⚠  No account found for this user.")
            no_creds.setStyleSheet("color:#f39c12;font-size:13px;")
            no_creds.setWordWrap(True)
            layout.addWidget(no_creds)

        layout.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(38)
        btn_close.setStyleSheet("""
            QPushButton{background:#2a3d55;color:#c8d6e5;border:none;
            border-radius:6px;padding:9px;font-size:13px;}
            QPushButton:hover{background:#4a9eff;color:#fff;}
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


# ── Manage Employees Widget ───────────────────────────────────────────────────
class ManageUsers(QWidget):
    on_data_changed = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.load_users()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("👥 Manage Users")
        title.setStyleSheet("font-size:20px;font-weight:bold;color:#fff;")
        hdr.addWidget(title)
        hdr.addStretch()

        self.txtSearch = QLineEdit()
        self.txtSearch.setPlaceholderText("🔍 Search Users...")
        self.txtSearch.setFixedWidth(250)
        self.txtSearch.setStyleSheet("""
            QLineEdit {
                background: #253447;
                border: 1px solid #3a4f66;
                border-radius: 6px;
                padding: 8px 12px;
                color: #fff;
            }
            QLineEdit:focus {
                border: 1px solid #4a9eff;
            }
        """)
        self.txtSearch.textChanged.connect(self.filter_table)
        hdr.addWidget(self.txtSearch)

        # FIXED: Set correct column count (5 data columns + 1 actions = 6 total)
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # 5 data columns + 1 actions column
        self.table.setHorizontalHeaderLabels([
            "Username", "First Name", "Last Name", "Email", "Created At", "Actions"
        ])

        # Configure column resizing
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Username
        hh.setSectionResizeMode(1, QHeaderView.Stretch)           # First Name
        hh.setSectionResizeMode(2, QHeaderView.Stretch)           # Last Name
        hh.setSectionResizeMode(3, QHeaderView.Stretch)           # Email
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Created At
        hh.setSectionResizeMode(5, QHeaderView.Fixed)             # Actions
        self.table.setColumnWidth(5, 100)  # Fixed width for actions column

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.verticalHeader().setVisible(False)  # Hide row numbers
        self.table.setStyleSheet("""
            QTableWidget {
                background: #253447;
                border: none;
                border-radius: 8px;
                color: #c8d6e5;
                alternate-background-color: #1e2a3a;
                gridline-color: #2a3d55;
            }
            QTableWidget::item {
                padding: 8px 4px;
            }
            QTableWidget::item:selected {
                background: #4a9eff30;
                color: #ffffff;
            }
        """)
        hh.setStyleSheet("""
            QHeaderView::section {
                background: #1e2a3a;
                color: #8a9bb0;
                padding: 10px;
                border: none;
                border-bottom: 1px solid #2a3d55;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)

    def load_users(self, search=""):
        conn = get_connection()
        cursor = conn.cursor()
        
        # FIXED: Query to get all users
        query = """
            SELECT username, first_name, last_name,
                   email, created_at
            FROM users
            WHERE role != 'admin'
        """
        
        try:
            if search:
                # FIXED: Correct parameter handling
                query += " AND (username LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR email LIKE ?)"
                search_pattern = f"%{search}%"
                cursor.execute(query + " ORDER BY username",
                               (search_pattern, search_pattern, search_pattern, search_pattern))
            else:
                cursor.execute(query + " ORDER BY username")
            
            rows = cursor.fetchall()
        except Exception as e:
            print(f"Error loading users: {e}")
            rows = []
        finally:
            conn.close()

        self.table.setRowCount(0)
        
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Add data to columns (col 0-4)
            username = row_data[0]
            first_name = row_data[1] or ""
            last_name = row_data[2] or ""
            email = row_data[3] or ""
            created_at = row_data[4] or ""
            
            # Format created_at to show only date if needed
            if created_at and ' ' in str(created_at):
                created_at = str(created_at).split()[0]
            
            # Create and style items
            username_item = QTableWidgetItem(username)
            username_item.setTextAlignment(Qt.AlignCenter)
            username_item.setForeground(QColor("#4a9eff"))
            font = username_item.font()
            font.setBold(True)
            username_item.setFont(font)
            
            first_item = QTableWidgetItem(first_name)
            first_item.setTextAlignment(Qt.AlignCenter)
            
            last_item = QTableWidgetItem(last_name)
            last_item.setTextAlignment(Qt.AlignCenter)
            
            email_item = QTableWidgetItem(email)
            email_item.setTextAlignment(Qt.AlignCenter)
            
            created_item = QTableWidgetItem(str(created_at))
            created_item.setTextAlignment(Qt.AlignCenter)
            
            self.table.setItem(row, 0, username_item)
            self.table.setItem(row, 1, first_item)
            self.table.setItem(row, 2, last_item)
            self.table.setItem(row, 3, email_item)
            self.table.setItem(row, 4, created_item)

            # Actions cell (col 5)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(8)

            def _icon_btn(icon, hover_color, tooltip):
                btn = QPushButton(icon)
                btn.setFixedSize(32, 32)
                btn.setToolTip(tooltip)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        border: none;
                        font-size: 18px;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        background: {hover_color};
                    }}
                """)
                return btn

            # Credentials button
            btn_creds = _icon_btn("🔑", "#f39c12", "View credentials")
            btn_creds.clicked.connect(lambda checked, e=email, u=username: 
                                      self.show_credentials(e, u))

            # Delete button
            btn_del = _icon_btn("🗑️", "#ff6b6b", "Delete user")
            btn_del.clicked.connect(lambda checked, u=username: 
                                    self.delete_employee(u))

            actions_layout.addStretch()
            actions_layout.addWidget(btn_creds)
            actions_layout.addWidget(btn_del)
            actions_layout.addStretch()
            
            # FIXED: Set cell widget at column 5 (Actions column)
            self.table.setCellWidget(row, 5, actions_widget)

    def filter_table(self, text):
        self.load_users(text)

    def show_credentials(self, email, username):
        from py.admin_dashboard import CredentialsDialog
        dlg = CredentialsDialog(email, username, parent=self)
        dlg.exec_()

    def delete_employee(self, username):
        if not confirm(self, "Delete Employee",
                f"Are you sure you want to delete employee {username}?\n\nThis will also remove their data.",
                confirm_text="Delete", confirm_color="#e74c3c", icon="🗑"):
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Delete in correct order (child tables first)
            cursor.execute("DELETE FROM tasks WHERE username=?", (username,))
            cursor.execute("DELETE FROM tags WHERE username=?", (username,))
            cursor.execute("DELETE FROM lists WHERE username=?", (username,))
            cursor.execute("DELETE FROM users WHERE username=?", (username,))
            conn.commit()
            self.load_users()
            if callable(self.on_data_changed):
                self.on_data_changed()
        except Exception as e:
            conn.rollback()
            print(f"Error deleting user: {e}")
        finally:
            conn.close()

    def _notify(self):
        if callable(self.on_data_changed):
            self.on_data_changed()

    def filter_table(self, text):
        self.load_users(text)

    def _notify(self):
        if callable(self.on_data_changed):
            self.on_data_changed()

    def show_credentials(self, email, username):
        dlg = CredentialsDialog(email, username, parent=self)
        dlg.exec_()

    def delete_employee(self, username):
        if not confirm(self, "Delete Employee",
                f"Are you sure you want to delete users {username}?\n\nThis will also remove their data.",
                confirm_text="Delete", confirm_color="#e74c3c", icon="🗑"):
            return
        if True:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE username=?", (username,))
            cursor.execute("DELETE FROM users      WHERE username=?", (username,))
            cursor.execute("DELETE FROM lists         WHERE username=?", (username,))
            cursor.execute("DELETE FROM tags       WHERE username=?", (username,))
            conn.commit()
            conn.close()
            self.load_users()
            self._notify()