import sys
import os

# Ensure the py folder is in the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "py"))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from py.database import initialize_db
from py.login import LoginWindow


def main():
    initialize_db()
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyle("Fusion")

    win = LoginWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()