import sys
from PyQt5 import uic
from PyQt5.QtWidgets import (QDialog, QMainWindow, QApplication, QMessageBox, QPushButton,
                              QLineEdit)
from PyQt5.QtCore import Qt
from py.database import get_connection, initialize_db
from datetime import datetime


class Register(QDialog):
    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/signup.ui", self)
        self.user_data = user_data
        self.btnSave.clicked.connect(self.save)
        self.btnCancel.clicked.connect(self.reject)

        if user_data:
            self.dlgTitle.setText("Register User")
            self.txtUsername.setText(user_data["username"])
            self.txtFirstName.setText(user_data["first_name"])
            self.txtLastName.setText(user_data["last_name"])
            self.txtEmail.setText(user_data["email"])
            self.txtPassword.setText(user_data["password"])
            self.txtConfirmPassword.setText(user_data["password"])

    def save(self):
        username = self.txtUsername.text().strip()
        first_name = self.txtFirstName.text().strip()
        last_name = self.txtLastName.text().strip()
        email = self.txtEmail.text().strip()
        password = self.txtPassword.text()
        confirm_password = self.txtConfirmPassword.text()
        
        # Validate required fields
        if not username or not first_name or not last_name or not email:
            self.errorLabel.setText("Username, First Name, Last Name and Email are required.")
            return
        
        # Validate password match
        if password != confirm_password:
            self.errorLabel.setText("Passwords do not match!")
            return
        
        # Validate password length
        if len(password) < 6:
            self.errorLabel.setText("Password must be at least 6 characters!")
            return
        
        # Validate email format (basic)
        if '@' not in email or '.' not in email:
            self.errorLabel.setText("Please enter a valid email address!")
            return

        conn = get_connection()
        if conn is None:
            self.errorLabel.setText("Database connection failed!")
            return
            
        cursor = conn.cursor()
        
        try:
            if self.user_data:
                # Update existing user
                cursor.execute("""
                    UPDATE users 
                    SET first_name=?, last_name=?, email=?, password=?
                    WHERE username=?
                """, (first_name, last_name, email, password, username))
                conn.commit()
                QMessageBox.information(self, "Success", "User updated successfully!")
            else:
                # Check if username already exists
                cursor.execute("SELECT username FROM users WHERE username=?", (username,))
                if cursor.fetchone():
                    self.errorLabel.setText("Username already exists!")
                    return
                
                # Check if email already exists
                cursor.execute("SELECT email FROM users WHERE email=?", (email,))
                if cursor.fetchone():
                    self.errorLabel.setText("Email already registered!")
                    return
                
                # Insert new user
                cursor.execute("""
                    INSERT INTO users (username, first_name, last_name, email, password, role, created_at)
                    VALUES (?, ?, ?, ?, ?, 'user', ?)
                """, (username, first_name, last_name, email, password, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()

                QMessageBox.information(self, "User Created",
                    f"  User created successfully!\n\n"
                    f"  Login Credentials:\n"
                    f"     Username : {username}\n"
                    f"     Password : {password}\n\n"
                    f"Please keep these credentials safe.")
                self.accept()
                
        except Exception as e:
            self.errorLabel.setText(f"Error: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/login.ui", self)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.btnLogin.clicked.connect(self.handle_login)
        self.btnSignup.clicked.connect(self.open_register_window)
        self.txtPassword.returnPressed.connect(self.handle_login)
        self._pwd_visible = False
        self._add_eye_button()

    def _add_eye_button(self):
        """Overlay a visible eye button inside the password field."""
        self.eyeBtn = QPushButton("👁", self.txtPassword)
        self.eyeBtn.setFixedSize(28, 28)
        self.eyeBtn.setCursor(Qt.PointingHandCursor)
        self.eyeBtn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #8a9bb0;
                font-size: 16px;
                padding: 0;
            }
            QPushButton:hover { color: #ffffff; }
        """)
        self.eyeBtn.clicked.connect(self._toggle_password)

        # Add right padding to the field so text doesn't overlap the button
        self.txtPassword.setStyleSheet(
            self.txtPassword.styleSheet() + "padding-right: 34px;"
        )

        # Position the eye button — will be repositioned on resize
        self._reposition_eye()

    def _reposition_eye(self):
        fw = self.txtPassword.width()
        fh = self.txtPassword.height()
        bw = self.eyeBtn.width()
        bh = self.eyeBtn.height()
        self.eyeBtn.move(fw - bw - 6, (fh - bh) // 2)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_eye()

    def showEvent(self, event):
        super().showEvent(event)
        self._reposition_eye()

    def _toggle_password(self):
        self._pwd_visible = not self._pwd_visible
        if self._pwd_visible:
            self.txtPassword.setEchoMode(QLineEdit.Normal)
            self.eyeBtn.setText("⌣")
        else:
            self.txtPassword.setEchoMode(QLineEdit.Password)
            self.eyeBtn.setText("👁")

    def handle_login(self):
        username = self.txtUsername.text().strip()
        password = self.txtPassword.text().strip()
        role = self.cmbRole.currentText().lower()
        
        if not username or not password:
            self.errorLabel.setText("Please fill in all fields.")
            return
        
        conn = get_connection()
        if conn is None:
            self.errorLabel.setText("Database connection failed!")
            return
        
        cursor = conn.cursor()
        
        try:
            # Try login with credentials
            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=? AND role=?",
                (username, password, role)
            )
            user = cursor.fetchone()
            
            if user:  # ✅ FIXED: Check if user exists (not user_data)
                self.errorLabel.setText("")
                print("✅ Login successful")
                
                # Convert to dictionary properly
                if hasattr(user, 'keys'):  # If using sqlite3.Row
                    user_data = dict(user)
                else:  # If using tuple
                    # Create dict manually based on your table structure
                    # Assuming columns: username, first_name, last_name, email, password, role, created_at
                    user_data = {
                        'username': user[0],
                        'first_name': user[1],
                        'last_name': user[2],
                        'email': user[3],
                        'password': user[4],
                        'role': user[5],
                    }
                    # Add created_at if it exists
                    if len(user) > 6:
                        user_data['created_at'] = user[6]
                
                self.open_dashboard(role, user_data)
            else:
                # Check if username exists to give better error
                cursor.execute("SELECT username FROM users WHERE username=?", (username,))
                if cursor.fetchone():
                    self.errorLabel.setText("Invalid password or role. Please try again.")
                    print("❌ Wrong password or role")
                else:
                    self.errorLabel.setText("User not found. Please register first.")
                    print("❌ User not found")
                self.txtPassword.clear()
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            import traceback
            traceback.print_exc()
            self.errorLabel.setText(f"Login error: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def open_register_window(self):
        dlg = Register(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", 
                "Registration successful! You can now login with your credentials.")
            
    def open_dashboard(self, role, user_data):
        if role == "admin":
            from py.admin_dashboard import AdminDashboard
            self.dashboard = AdminDashboard(user_data)
        else:
            from py.user_dashboard import UserDashboard
            self.dashboard = UserDashboard(user_data)
        self.dashboard.show()
        self.close()

if __name__ == "__main__":
    initialize_db()
    app = QApplication(sys.argv)
    win = LoginWindow()
    win.show()
    sys.exit(app.exec_())