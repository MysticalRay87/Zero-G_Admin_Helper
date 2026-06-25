import os
import json
from PyQt6.QtWidgets import QDialog, QLineEdit, QPushButton, QLabel, QCheckBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen

# Imported features
from features.auth.persistence import USERS_FILE
file_path = USERS_FILE

class LoginWindow(QDialog):
    """Screen 1B: Standalone Pop-up Modal Login Window - Symmetrically Flipped Controls"""

    login_successful = pyqtSignal()  # Signal to notify successful login to the orchestrator
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.onboarding_requested = False # State flag to track onboarding request
        print("[DEBUG] Initializing standard, stable pop-up LoginWindow...")
        
        self.setFixedSize(512, 512)
        self.setWindowTitle("Security Access Verification")

        # -------------------------------------------------------------------
        # PHYSICAL ASSET PATH RESOLUTION
        # -------------------------------------------------------------------
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../"))
        bg_image_path = os.path.join(project_root, "assets/backgrounds/login_screen.png")
        
        self.bg_pixmap = QPixmap(os.path.normpath(bg_image_path))
        if self.bg_pixmap.isNull():
            print(f"[ERROR] Asset loader failed to find login template file at: {bg_image_path}")

        # -------------------------------------------------------------------
        # ABSOLUTE COMPONENT POSITION MATRIX MAPPING
        # -------------------------------------------------------------------
        self.title_label = QLabel("SECURE SYSTEM ACCESS", self)
        self.title_label.setGeometry(20, 135, 472, 30)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("QLabel { color: #00ffff; font-family: 'Courier New'; font-weight: bold; font-size: 15px; background: transparent; border: none; letter-spacing: 2px; }")
        
        input_style = "QLineEdit { background-color: transparent; color: #00ffff; font-family: 'Courier New'; font-size: 13px; padding-left: 10px; border: none; }"
        
        self.username_input = QLineEdit(self)
        self.username_input.setGeometry(132, 185, 250, 38)
        self.username_input.setPlaceholderText("ENTER ADMIN ID...")
        self.username_input.setStyleSheet(input_style)
        
        self.password_input = QLineEdit(self)
        self.password_input.setGeometry(132, 262, 250, 38)
        self.password_input.setPlaceholderText("ENTER PASSKEY...")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(input_style)
        
        self.remember_me_check = QCheckBox("", self)
        self.remember_me_check.setGeometry(133, 316, 17, 16)
        self.remember_me_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remember_me_check.setStyleSheet("QCheckBox { background: transparent; border: none; } QCheckBox::indicator { width: 17px; height: 16px; background-color: transparent; }")
        self.remember_me_check.clicked.connect(self.update)
        
        self.error_label = QLabel("", self)
        self.error_label.setGeometry(56, 345, 400, 20)
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("QLabel { color: #ff3333; font-family: 'Courier New'; font-size: 11px; font-weight: bold; background: transparent; border: none; }")
        
        self.auth_btn = QPushButton("", self)
        self.auth_btn.setGeometry(117, 371, 127, 40)
        self.auth_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auth_btn.setStyleSheet("QPushButton { background-color: transparent; border: none; } QPushButton:hover { background-color: rgba(29, 172, 214, 0.25); border: 1px solid #22f222; } QPushButton:pressed { background-color: rgba(29, 172, 214, 0.05); }")
        self.auth_btn.clicked.connect(self.verify_login)

        self.cancel_btn = QPushButton("", self)
        self.cancel_btn.setGeometry(268, 371, 127, 40)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("QPushButton { background-color: transparent; border: none; } QPushButton:hover { background-color: rgba(255, 51, 51, 0.2); border: 1px solid #ff3333; } QPushButton:pressed { background-color: rgba(255, 51, 51, 0.03); }")
        self.cancel_btn.clicked.connect(self.process_cancel_dismissal)

        # Onboarding trigger button
        self.onboarding_btn = QPushButton("Set Up New Account", self)
        self.onboarding_btn.setGeometry(132, 420, 250, 30) # Adjusted geometry
        self.onboarding_btn.setStyleSheet("QPushButton { color: #00ffff; background: transparent; border: 1px solid #00ffff; }")
        self.onboarding_btn.clicked.connect(self.initiate_onboarding)

    def initiate_onboarding(self):
        print("[STATUS] Onboarding trigger detected. Handoff to wizard phase...")
        try:
            from features.auth.onboarding import AccountOnboardingWizard
            self.wizard = AccountOnboardingWizard(self)
            self.wizard.exec()
        except Exception as e:
            print(f"[ERROR] Failed to launch onboarding: {e}")
            

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.bg_pixmap.isNull():
            painter.drawPixmap(self.rect(), self.bg_pixmap)
        else:
            painter.fillRect(self.rect(), QColor(6, 19, 32))
            
        if self.remember_me_check.isChecked():
            cross_pen = QPen(QColor("#00ffff"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(cross_pen)
            bx = 133 + 3
            by = 316 + 3
            bw = 17 - 6
            bh = 16 - 3
            painter.drawLine(bx, by, bx + bw, by + bh)
            painter.drawLine(bx, by + bh, bx + bw, by)

    def verify_login(self):
        # 1. Capture user inputs
        entered_id = self.username_input.text().strip()
        entered_key = self.password_input.text().strip()
    
        # 2. Locate registry file using the persistence utility
        file_path = USERS_FILE
        
        # 3. Handle missing registry
        if not os.path.exists(file_path):
            self.error_label.setText("CRITICAL: REGISTRY NOT FOUND")
            return
            
        # 4. Load and iterate through user profiles
        with open(file_path, 'r') as f:
            try:
                users = json.load(f)
            except json.JSONDecodeError:
                users = []
        
        # 5. Authenticate
        auth_success = False
        for user in users:
            # Fixed: Matching capitalized keys from persistence.py
            if user.get("Username") == entered_id and user.get("Password") == entered_key:
                auth_success = True
                break
        
        # 6. Execute handoff or error
        if auth_success:
            print("[AUTH] Credentials verified successfully.")
            
            # --- PATCH: Update Persistence & Timestamp ---
            from features.auth.persistence import save_persistence_state, update_last_login
            save_persistence_state(entered_id, self.remember_me_check.isChecked())
            update_last_login(entered_id)
            
            self.login_successful.emit() # Signal orchestrator
            self.accept()
        else:
            print("[WARNING] Authentication Rejected: Signature Mismatch.")
            self.error_label.setText("ACCESS DENIED: SIGNATURE INVALID")

    def process_cancel_dismissal(self):
        print("[STATUS] Authentication canceled. Exiting application framework cleanly...")
        self.reject()