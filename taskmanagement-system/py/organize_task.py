from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QWidget, QListWidgetItem, QMessageBox, QHBoxLayout, 
                            QVBoxLayout, QLabel, QPushButton, QSpacerItem, 
                            QSizePolicy, QListWidget, QLineEdit, QComboBox, 
                            QFrame, QScrollArea, QDialog, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QDialogButtonBox)
from py.database import get_connection


PRIORITY_BG = {"High": "#FDECEA", "Medium": "#FFF8E1", "Low": "#E8F5E9"}
PRIORITY_FG = {"High": "#D93025", "Medium": "#F9A825", "Low": "#2E7D32"}


# ── List Tasks Dialog ──────────────────────────────────────────────────────────

class ListTasksDialog(QDialog):
    """Dialog that shows all tasks belonging to a specific list"""

    def __init__(self, username, list_name, parent=None):
        super().__init__(parent)
        self.username = username
        self.list_name = list_name

        self.setWindowTitle(f"📁 {list_name}")
        self.setMinimumSize(650, 450)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
        """)

        self._build_ui()
        self._load_tasks()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # ── Header ──────────────────────────────────────────────────────
        header = QLabel(f"📁 {self.list_name}")
        header.setStyleSheet("font-size: 22px; font-weight: 700; color: #333333;")
        layout.addWidget(header)

        self.subtitleLabel = QLabel("Loading tasks...")
        self.subtitleLabel.setStyleSheet("font-size: 13px; color: #888888;")
        layout.addWidget(self.subtitleLabel)

        # ── Table ────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Task", "Priority", "Due Date", "Status"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E5E5E5;
                border-radius: 8px;
                background-color: #FFFFFF;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                font-weight: 600;
                font-size: 12px;
                color: #555555;
                border: none;
                padding: 8px;
                border-bottom: 1px solid #E0E0E0;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #333333;
            }
        """)
        layout.addWidget(self.table)

        # ── Close Button ─────────────────────────────────────────────────
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(40)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 24px;
            }
            QPushButton:hover { background-color: #444444; }
        """)
        close_btn.clicked.connect(self.accept)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def _load_tasks(self):
        """Query tasks that belong to this list and populate the table"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT t.id, t.title, t.priority, t.due_date, t.is_done
                FROM tasks t
                INNER JOIN lists l ON t.list_id = l.id
                WHERE t.username = ? AND l.name = ? AND t.is_draft = 0
                ORDER BY t.is_done ASC, t.due_date ASC
            """, (self.username, self.list_name))

            tasks = cursor.fetchall()
            conn.close()

            total = len(tasks)
            done = sum(1 for t in tasks if t[4] == 1)
            self.subtitleLabel.setText(
                f"{total} task{'s' if total != 1 else ''} — {done} completed, {total - done} pending"
            )

            self.table.setRowCount(total)

            for row, (task_id, title, priority, due_date, is_done) in enumerate(tasks):
                # Title
                title_item = QTableWidgetItem(title)
                title_item.setData(Qt.UserRole, task_id)
                if is_done:
                    font = title_item.font()
                    font.setStrikeOut(True)
                    title_item.setFont(font)
                    title_item.setForeground(QColor("#AAAAAA"))
                self.table.setItem(row, 0, title_item)

                # Priority
                pri = priority or "Medium"
                pri_item = QTableWidgetItem(pri)
                pri_item.setForeground(QColor(PRIORITY_FG.get(pri, "#888")))
                pri_item.setBackground(QColor(PRIORITY_BG.get(pri, "#FFF")))
                pri_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 1, pri_item)

                # Due Date
                due_item = QTableWidgetItem(due_date or "—")
                due_item.setForeground(QColor("#888888"))
                due_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 2, due_item)

                # Status
                status_text = "✅ Done" if is_done else "🔲 Pending"
                status_item = QTableWidgetItem(status_text)
                status_item.setTextAlignment(Qt.AlignCenter)
                if is_done:
                    status_item.setForeground(QColor("#2E7D32"))
                else:
                    status_item.setForeground(QColor("#F9A825"))
                self.table.setItem(row, 3, status_item)

            self.table.resizeRowsToContents()

            if total == 0:
                self.subtitleLabel.setText("No tasks in this list yet.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load tasks: {str(e)}")


# ── Organize Page ──────────────────────────────────────────────────────────────

class OrganizePage(QWidget):
    list_selected = pyqtSignal(str)
    list_created = pyqtSignal(str)
    list_deleted = pyqtSignal(str)
    
    def __init__(self, username, container, main_window):
        super().__init__(container)
        self.username = username
        self.main_window = main_window
        self.container = container
        
        if container.layout():
            old_layout = container.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(layout)
        
        self.setup_ui(layout)
        self.refresh()
    
    def setup_ui(self, parent_layout):
        content_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        self.headerTitle = QLabel("📋 My Lists")
        self.headerTitle.setStyleSheet("font-size: 28px; font-weight: 700; color: #333333;")
        main_layout.addWidget(self.headerTitle)
        
        self.headerSubtitle = QLabel("Organize your tasks by creating custom lists")
        self.headerSubtitle.setStyleSheet("font-size: 13px; color: #666666;")
        main_layout.addWidget(self.headerSubtitle)
        
        # Add List Frame
        addListFrame = QFrame()
        addListFrame.setStyleSheet("""
            QFrame {
                background-color: #F8F8F8;
                border: 1px solid #E5E5E5;
                border-radius: 12px;
            }
        """)
        addListLayout = QVBoxLayout()
        addListLayout.setSpacing(12)
        addListLayout.setContentsMargins(20, 20, 20, 20)
        
        sectionLabel = QLabel("CREATE NEW LIST")
        sectionLabel.setStyleSheet("font-size: 11px; font-weight: 600; color: #666666;")
        addListLayout.addWidget(sectionLabel)
        
        self.listNameInput = QLineEdit()
        self.listNameInput.setPlaceholderText("List name (e.g., Work, Personal, Shopping)")
        self.listNameInput.setMinimumHeight(40)
        self.listNameInput.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
            }
        """)
        addListLayout.addWidget(self.listNameInput)
        
        self.sectionCombo = QComboBox()
        self.sectionCombo.addItems(["WORK", "PERSONAL", "SHOPPING", "URGENT", "OTHER"])
        self.sectionCombo.setMinimumHeight(40)
        self.sectionCombo.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 8px;
                padding: 8px 15px;
                font-size: 14px;
            }
        """)
        addListLayout.addWidget(self.sectionCombo)
        
        self.btnAddList = QPushButton("+ Add List")
        self.btnAddList.setMinimumHeight(45)
        self.btnAddList.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 10px;
            }
            QPushButton:hover { background-color: #444444; }
        """)
        self.btnAddList.clicked.connect(self._add_list)
        addListLayout.addWidget(self.btnAddList)
        
        addListFrame.setLayout(addListLayout)
        main_layout.addWidget(addListFrame)
        
        # Lists Container
        listsContainer = QFrame()
        listsContainer.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 12px;
            }
        """)
        listsLayout = QVBoxLayout()
        listsLayout.setSpacing(0)
        listsLayout.setContentsMargins(0, 0, 0, 0)
        
        listsTitle = QLabel("Your Lists")
        listsTitle.setStyleSheet("""
            font-size: 16px; 
            font-weight: 700; 
            color: #333333; 
            padding: 15px 20px; 
            border-bottom: 1px solid #E5E5E5;
        """)
        listsLayout.addWidget(listsTitle)

        # hint label
        hintLabel = QLabel("💡 Click a list to view its tasks")
        hintLabel.setStyleSheet("font-size: 11px; color: #AAAAAA; padding: 6px 20px 0px 20px;")
        listsLayout.addWidget(hintLabel)
        
        self.listsList = QListWidget()
        self.listsList.setMinimumHeight(300)
        self.listsList.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #FFFFFF;
            }
            QListWidget::item {
                padding: 0px;
                border-bottom: 1px solid #F0F0F0;
            }
            QListWidget::item:hover {
                background-color: #FAFAFA;
            }
        """)
        listsLayout.addWidget(self.listsList)
        
        listsContainer.setLayout(listsLayout)
        main_layout.addWidget(listsContainer)
        
        content_widget.setLayout(main_layout)
        parent_layout.addWidget(content_widget)
    
    def _add_list(self):
        list_name = self.listNameInput.text().strip()
        section = self.sectionCombo.currentText()
        
        if not list_name:
            QMessageBox.warning(self.main_window, "Warning", "Please enter a list name!")
            return
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO lists (username, name, section)
                VALUES (?, ?, ?)
            """, (self.username, list_name, section))
            conn.commit()
            conn.close()
            
            QMessageBox.information(self.main_window, "Success", f"List '{list_name}' created successfully!")
            self.listNameInput.clear()
            self.refresh()
            self.list_created.emit(list_name)
            
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                QMessageBox.warning(self.main_window, "Error", f"List '{list_name}' already exists!")
            else:
                QMessageBox.critical(self.main_window, "Error", f"Failed to create list: {str(e)}")
    
    def refresh(self):
        self.listsList.clear()
        
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
            
            if not lists:
                empty_item = QListWidgetItem()
                empty_widget = QLabel("📭 No lists yet.\n\nCreate your first list above!")
                empty_widget.setAlignment(Qt.AlignCenter)
                empty_widget.setStyleSheet("color: #999999; padding: 60px 20px; font-size: 14px;")
                empty_item.setSizeHint(empty_widget.sizeHint())
                self.listsList.addItem(empty_item)
                self.listsList.setItemWidget(empty_item, empty_widget)
                return
            
            for list_data in lists:
                list_id, list_name, section = list_data
                
                item = QListWidgetItem()
                item.setData(Qt.UserRole, list_id)
                item.setData(Qt.UserRole + 1, list_name)
                
                item_widget = QWidget()
                item_widget.setCursor(Qt.PointingHandCursor)
                # ── clicking anywhere on the row opens the dialog ──
                item_widget.mousePressEvent = lambda event, name=list_name: self._open_list_dialog(name)

                layout = QHBoxLayout()
                layout.setContentsMargins(20, 15, 20, 15)
                
                name_label = QLabel(f"📁 {list_name}")
                name_label.setStyleSheet("font-size: 15px; font-weight: 600; color: #333333;")
                name_label.setAttribute(Qt.WA_TransparentForMouseEvents)  # pass clicks to parent widget
                
                section_label = QLabel(section)
                section_label.setFixedHeight(28)
                section_label.setStyleSheet(f"""
                    font-size: 12px;
                    color: #666666;
                    background-color: {self._get_section_color(section)};
                    padding: 4px 12px;
                    border-radius: 14px;
                """)
                section_label.setAttribute(Qt.WA_TransparentForMouseEvents)
                
                delete_btn = QPushButton("Delete")
                delete_btn.setFixedSize(70, 32)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FFFFFF;
                        color: #F44336;
                        border: 1px solid #FFCDD2;
                        border-radius: 6px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #FFEBEE;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, name=list_name: self._delete_list(name))
                
                spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
                
                layout.addWidget(name_label, 1)
                layout.addWidget(section_label)
                layout.addItem(spacer)
                layout.addWidget(delete_btn)
                
                item_widget.setLayout(layout)
                item_widget.adjustSize()
                
                self.listsList.addItem(item)
                self.listsList.setItemWidget(item, item_widget)
                item.setSizeHint(item_widget.sizeHint())
                
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Failed to load lists: {str(e)}")

    def _open_list_dialog(self, list_name):
        """Open dialog showing tasks in the selected list"""
        dialog = ListTasksDialog(self.username, list_name, parent=self.main_window)
        dialog.exec_()
        # also emit signal for any other listeners
        self.list_selected.emit(list_name)
    
    def _get_section_color(self, section):
        colors = {
            "WORK": "#E3F2FD",
            "PERSONAL": "#E8F5E9",
            "SHOPPING": "#FFF3E0",
            "URGENT": "#FDECEA",
            "OTHER": "#F5F5F5"
        }
        return colors.get(section, "#F5F5F5")
    
    def _delete_list(self, list_name):
        reply = QMessageBox.question(
            self.main_window,
            "Confirm Delete",
            f"Delete '{list_name}'? Tasks in this list will NOT be deleted.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM lists WHERE username = ? AND name = ?", (self.username, list_name))
                conn.commit()
                conn.close()
                
                QMessageBox.information(self.main_window, "Success", f"List '{list_name}' deleted!")
                self.refresh()
                self.list_deleted.emit(list_name)
            except Exception as e:
                QMessageBox.critical(self.main_window, "Error", str(e))