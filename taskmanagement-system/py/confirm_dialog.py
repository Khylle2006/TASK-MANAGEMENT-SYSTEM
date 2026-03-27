from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


def confirm(parent, title, message, confirm_text="Confirm", confirm_color="#4a9eff", icon="❓"):
    """
    Show a styled confirmation dialog.
    Returns True if the user clicked the confirm button, False otherwise.
    """
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setFixedSize(400, 210)
    dlg.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
    dlg.setStyleSheet("""
        QDialog {
            background: #1e2a3a;
            border: 1px solid #3a4f66;
            border-radius: 12px;
        }
    """)

    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(32, 28, 32, 24)
    layout.setSpacing(16)

    # Icon + Title row
    title_row = QHBoxLayout()
    lbl_icon = QLabel(icon)
    lbl_icon.setStyleSheet("font-size:26px; background:transparent;")
    lbl_icon.setFixedWidth(36)
    lbl_title = QLabel(title)
    lbl_title.setStyleSheet("color:#ffffff; font-size:16px; font-weight:bold; background:transparent;")
    title_row.addWidget(lbl_icon)
    title_row.addWidget(lbl_title)
    title_row.addStretch()
    layout.addLayout(title_row)

    # Divider
    from PyQt5.QtWidgets import QFrame
    sep = QFrame(); sep.setFrameShape(QFrame.HLine)
    sep.setStyleSheet("background:#2a3d55; border:none; max-height:1px;")
    layout.addWidget(sep)

    # Message
    lbl_msg = QLabel(message)
    lbl_msg.setWordWrap(True)
    lbl_msg.setStyleSheet("color:#c8d6e5; font-size:13px; background:transparent;")
    lbl_msg.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    layout.addWidget(lbl_msg)

    layout.addStretch()

    # Buttons
    btn_row = QHBoxLayout()
    btn_row.setSpacing(10)

    btn_cancel = QPushButton("Cancel")
    btn_cancel.setFixedHeight(38)
    btn_cancel.setCursor(Qt.PointingHandCursor)
    btn_cancel.setStyleSheet("""
        QPushButton {
            background:#2a3d55; color:#c8d6e5;
            border:none; border-radius:7px;
            font-size:13px; font-weight:bold;
        }
        QPushButton:hover { background:#3a4f66; color:#fff; }
    """)
    btn_cancel.clicked.connect(dlg.reject)

    btn_ok = QPushButton(confirm_text)
    btn_ok.setFixedHeight(38)
    btn_ok.setCursor(Qt.PointingHandCursor)
    # Darken the confirm color on hover by mixing with black
    def _darken(hex_color, factor=0.8):
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
        return '#{:02x}{:02x}{:02x}'.format(int(r*factor), int(g*factor), int(b*factor))
    hover_color = _darken(confirm_color)

    btn_ok.setStyleSheet(f"""
        QPushButton {{
            background:{confirm_color}; color:#ffffff;
            border:none; border-radius:7px;
            font-size:13px; font-weight:bold;
        }}
        QPushButton:hover {{ background:{hover_color}; color:#ffffff; }}
        QPushButton:pressed {{ background:{hover_color}; color:#ffffff; }}
    """)
    btn_ok.clicked.connect(dlg.accept)

    btn_row.addWidget(btn_cancel)
    btn_row.addWidget(btn_ok)
    layout.addLayout(btn_row)

    return dlg.exec_() == QDialog.Accepted