# onboarding.py

import os
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QComboBox, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
from datetime import datetime
import re

from features.auth.persistence import save_account_data

class AccountOnboardingWizard(QDialog):
    """Screen 2: Account Onboarding Wizard interface class container"""
    registration_complete = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        print("[DEBUG] Initializing Account Onboarding Wizard Canvas...")

        # Force structural 512x512 square viewport bounds
        self.setFixedSize(512, 512)
        self.setWindowTitle("Account Onboarding Wizard")

        # Dynamic Project Root Asset Path Traversal
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../"))
        bg_path = os.path.join(
            project_root, "assets/backgrounds/account_creation_wizard_2.png"
        )

        print(f"[DEBUG PATH] Searching for artwork at {bg_path}")

        # Construct full-window background artwork canvas layer
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, 512, 512)

        # Ingest and force-fit background image asset edge-to-edge
        pixmap = QPixmap(bg_path)
        if not pixmap.isNull():
            self.background_label.setPixmap(pixmap)
            self.background_label.setScaledContents(True)
            print("[SUCCESS] Onboarding background asset painted successfully.")
        else:
            print(f"[WARNING] Background image asset is missing or unreadable at: {bg_path}")
    
        # ----------------------------------------------------------------
        # INTERFACE INPUT FIELDS & ABSOLUTE LAYER POSITIONING
        # ----------------------------------------------------------------

        print("[DEBUG] Overlaying absolute form entry inputs and selectors...")

        # 1. Username Field Overlay
        self.username_input = QLineEdit(self)
        self.username_input.setGeometry(150, 155, 220, 30)
        self.username_input.setPlaceholderText("Enter User Name")
        self.username_input.setObjectName("username_field")

        # 2. Password Field Overlay (With character overlay)
        self.password_input = QLineEdit(self)
        self.password_input.setGeometry(150, 215, 220, 30)
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("password_field")

        # 3. Confirm Password Field Overlay
        self.confirm_input = QLineEdit(self)
        self.confirm_input.setGeometry(150, 273, 220, 30)
        self.confirm_input.setPlaceholderText("Confirm Password")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setObjectName("confirm_field")

        # 4. Set SteamID Overlay
        self.steamID_input = QLineEdit(self)
        self.steamID_input.setGeometry(150, 333, 220, 30)
        self.steamID_input.setPlaceholderText("Enter SteamID")
        self.steamID_input.setObjectName("steamID_input")

        # 4. Administrative Role Selection Dropdown Tier
        self.role_selector = QComboBox(self)
        self.role_selector.setGeometry(150, 387, 280, 30)
        self.role_selector.addItems(["Primary Admin", "Secondary Admin"])
    
        print("[SUCCESS] Interactive fields anchored to layout coordinates.")

        # ------------------------------------------------------------------
        # INTERFACE PUSH BUTTONS & ABSOLUTE LAYER POSITIONING
        # ------------------------------------------------------------------
        print("[DEBUG] Injecting command buttons onto canvas axis...")

        # 1. Accept / Submit Form Button
        self.accept_button = QPushButton("ACCEPT", self)
        self.accept_button.setGeometry(271, 428, 157, 35)
        self.accept_button.setStyleSheet("QPushButton { background-color: transparent; border: none; } QPushButton:hover { background-color: rgba(29, 172, 214, 0.25); border: 1px solid #22f222; } QPushButton:pressed { background-color: rgba(29, 172, 214, 0.05); }")

        # 2. Reset Form Button
        self.cancel_button = QPushButton("CANCEL", self)
        self.cancel_button.setGeometry(85, 429, 155, 35)
        self.cancel_button.setStyleSheet("QPushButton { background-color: transparent; border: none; } QPushButton:hover { background-color: rgba(255, 51, 51, 0.2); border: 1px solid #ff3333; } QPushButton:pressed { background-color: rgba(255, 51, 51, 0.03); }")

        print("[SUCCESS] Control buttons locked to layout coordinates.")

        # -------------------------------------------------------------------
        # KEYBOARD NAVIGATION FOCUS CHAINS (TAB / ENTER ORDER)
        # -------------------------------------------------------------------
        print("[DEBUG] Hardcoding explicit keyboard focus sequences...")
        
        # Enforce strict, un-skippable focus policies on your input blocks
        self.username_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.password_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.confirm_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.role_selector.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.steamID_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # De-activate premature button interception when hitting Enter
        self.accept_button.setAutoDefault(False)
        self.accept_button.setDefault(False)
        self.cancel_button.setAutoDefault(False)

        # Link standard Tab-key navigation sequence pairs explicitly
        self.setTabOrder(self.username_input, self.password_input)
        self.setTabOrder(self.password_input, self.confirm_input)
        self.setTabOrder(self.confirm_input, self.steamID_input)
        self.setTabOrder(self.steamID_input, self.role_selector)
        self.setTabOrder(self.role_selector, self.accept_button)
        self.setTabOrder(self.accept_button, self.cancel_button)
        
        # Explicitly wire up individual sequential focus hops for the Enter key
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.confirm_input.setFocus)
        self.confirm_input.returnPressed.connect(self.steamID_input.setFocus)
        self.confirm_input.returnPressed.connect(self.role_selector.showPopup)
        self.role_selector.activated.connect(lambda: self.accept_button.setFocus())
        
        
        print("[SUCCESS] Focus chains synchronized and secured against bypass.")

        # -------------------------------------------------------------------
        # SIGNAL-SLOT EVEN BINDINGS
        # -------------------------------------------------------------------

        self.cancel_button.clicked.connect(self.handle_cancel)
        self.accept_button.clicked.connect(self.handle_accept)
        self.clear_ui_errors()
        print("[SUCCESS] Interactive Signals bound to operational Slots.")

    def handle_cancel(self):
        """Slot handler tied to CANCEL button overlay."""
        print("[STATUS] Cancel trigger detected. Aborting onboarding wizard operations...")
        self.reject()

    def handle_accept(self):
        """Slot handler that extracts form values and runs structural verification."""
        print("[STATUS] Accept trigger detected. Initiating credential validation matrix...")

        self.clear_ui_errors()

        # Extract real-time string captures from PyQt6 input widgets
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        steamID = self.steamID_input.text().strip()
        role = self.role_selector.currentText()

        # --- Validation Gateway Criteria ---
        
        # Initializes tracking flag - Assumes success until a rule breaks
        form_is_valid = True
        
        # Rule 1: Username Minimum Complexity Metrics (Presence and Character length boundary enforcement)
        if not username:
            print("[VALIDATION FAILURE] Username field is empty.")
            self.username_input.setPlaceholderText("Username is Empty")
            self.flash_widget_error(self.username_input)
            form_is_valid = False
        elif len(username) < 7:
            print(f"[VALIDATION FAILURE] Username fails to meet the minimum 7 character requirement.")
            self.username_input.clear()
            self.username_input.setPlaceholderText("Username must be 7+ characters")
            self.flash_widget_error(self.username_input)
            form_is_valid = False
        
        # Rule 2: Password Minimum Complexity Metrics (Enforces character length and Special Character requirement)
        password_pattern = r"^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>]).+$"
        if not password:
            print("[VALIDATION FAILURE] Password field is empty.")
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.password_input.setPlaceholderText("Password is Empty")
            self.flash_widget_error(self.password_input)
            form_is_valid = False
        elif len(password) < 8:
            print(f"[VALIDATION FAILURE] Password fails safety baseline. Length ({len(password)}) is under 8 characters or is missing special characters.")
            self.password_input.clear()
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.password_input.setPlaceholderText("Password must be 8+ Characters")
            self.flash_widget_error(self.password_input)
            form_is_valid = False    
        elif not re.match(password_pattern, password):
           print(f"[VALIDATION FAILURE] Password fails safety baseline. ({len(password)}) is missing required numbers, letters, or special characters.")
           self.password_input.clear()
           self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
           self.password_input.setPlaceholderText("Password is missing special Characters")
           self.flash_widget_error(self.password_input)
           form_is_valid = False
         
        # Rule 3: Cryptographic Symmetry (Passwords must match exactly)
        if not confirm:
           print("[VALIDATION FAILURE] Confirmation password field is empty.")
           self.confirm_input.setEchoMode(QLineEdit.EchoMode.Normal)
           self.confirm_input.setPlaceholderText("Confirmation is Empty")
           self.flash_widget_error(self.confirm_input)
           form_is_valid = False
        elif password != confirm:
            print("[VALIDATION FAILURE] Password symmetry broken. Password and verification do not match.")
            self.password_input.clear()
            self.confirm_input.clear()
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.confirm_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.password_input.setPlaceholderText("Password don't match")
            self.confirm_input.setPlaceholderText("Password don't match")
            self.flash_widget_error(self.password_input)
            self.flash_widget_error(self.confirm_input)
            form_is_valid = False
        
        # Rule 4: Steam ID Length Check
        steam_pattern = r"^\d{17}$"
        if not steamID:
            print("[VALIDATION FAILURE] Steam ID field is empty.")
            self.steamID_input.setPlaceholderText("Missing Steam ID")
            self.flash_widget_error(self.steamID_input)
            form_is_valid = False
        elif not re.match(steam_pattern, steamID):
            print(f"[VALIDATION FAILURE] Steam ID fails to meet the minimum 17 digit requirement.")
            self.steamID_input.clear()
            self.steamID_input.setPlaceholderText("Steam ID must be 17 digits")
            self.flash_widget_error(self.steamID_input)
            form_is_valid = False

        if not form_is_valid:
            print("[STATUS] Validation processing halted. Correct highlighted fields before proceeding.")
            return


        # --- VALIDATION SUCCESS ROUTINE ---
        print("\n==================================================================")
        print("[SUCCESS] CREDENTIAL VALIDATION MATRIX PASSED")
        print("==================================================================")
        print(f" -> Approved Operator Account: '{username}'")
        print(f" -> Assigned Security Clear Tier: [{role}]")
        print(" -> Proceeding to secure serialization pipeline...\n")

        # ---- ACCOUNT INPUT CAPTURE ----

        now = datetime.now().strftime("%m/%d/%Y at %H:%M")
        user_data = {
            "Username": username,
            "Password": password,
            "Account Type": role,
            "Keep me logged in status": False,
            "Steam ID": steamID,
            "Account Creation": now,
            "Account Status": "Active"
        }

        # --- DEBUGGING TRACE ---
        print("[DEBUG] Inspecting dictionary types before save:")
        for key, value in user_data.items():
            print(f"  Key: {key} | Type: {type(value)} | Value: {value}")
            if isinstance(value, set):
                print(f"  !!! FOUND OFFENDING SET AT KEY: {key}")
        # -----------------------
        save_account_data(user_data)
        print(f" -> Approved Operator Account '{username}' saved to database.")
        print(f" -> Assigned Security Clear Tier: [{role}]")

        """Native Dialog commitment trigger: Closes the UI canvas instantly
        and returns an execution flag of 1 (Accepted) back into ZAH.py"""
        self.accept()
        
    def clear_ui_errors(self): 
        """Resets all input widgets back to their nominal style state."""
        print("[DEBUG] Resetting UI widget styles...")
        widgets = [self.username_input, self.password_input, self.confirm_input, self.steamID_input]
        for widget in widgets:
            widget.setProperty("error", "false")
            # Only reset echo mode for password fields to avoid breaking non-password inputs
            if widget in [self.password_input, self.confirm_input]:
                widget.setEchoMode(QLineEdit.EchoMode.Password)
            widget.setStyleSheet("") 
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        
    def flash_widget_error(self, widget):
        """Injects the dynamic error property and forces an immediate engine repaint."""
        widget.setProperty("error", "true")
        widget.setStyleSheet("border: 2px solid #ff0000;")
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        # Force local widget focus to draw user attention
        widget.setFocus()

              # Future-proofing: This is where we will emit a signal to transition to the next dashboard    
