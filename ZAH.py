# ZAH.py

import os
import sys
import json
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import QEventLoop, QCoreApplication

# Internal imports for registry modules
from features.network.connection import is_network_ready
from features.dashboard.main_cockpit import MainCockpit

# -------------------------------------------------------------------
# MULTI-TIER PACKAGE NAMESPACE RESOLUTION
# -------------------------------------------------------------------

# Load Screen 1 (The Application Loader Component)
try:
    from features.loading.loading_screen import ApplicationLoader
    print("[SUCCESS] Package Namespace: ApplicationLoader Loaded")
except ImportError as e:
    print(f"[WARNING] Could not load Application Loader: {e}")
    ApplicationLoader = None

# Load Screen 2 'The Onboarding Wizard'
try:
    from features.auth.onboarding import AccountOnboardingWizard
    print("[SUCCESS] Package Namespace: AccountOnboardingWizard Loaded")
except ImportError as e:
    print(f"[WARNING] Could not load Onboarding Wizard: {e}")
    AccountOnboardingWizard = None

# LOAD LOGIN WINDOW: Must be imported before use in main()
try:
    from features.auth.login import LoginWindow
    print("[SUCCESS] Package Namespace: LoginWindow Loaded")
except ImportError as e:
    print(f"[ERROR] Could not load LoginWindow: {e}")
    LoginWindow = None

def main():
    print("[DEBUG] Initializing Master Operational Registry Engine (PyQt6 Mode)...")

    # Initialize the core global window event loop using PyQt6
    app = QApplication(sys.argv)

    # Dynamic Project Root Asset Traversal for the CSS Stylesheet
    root_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(root_dir, "assets/ZAH.css")

    # Ingest the centralized stylesheet via an immutable read stream
    if os.path.exists(css_path):
        try:
            with open(css_path, "r", encoding="utf-8") as stream:
                css_rules = stream.read()
                app.setStyleSheet(css_rules)
            print("[SUCCESS] Central layout stylesheet applied: ZAH.css, Cyan-Theme")
        except Exception as e:
            print(f"[ERROR] Failed to read central stylesheet: {e}")
    else:
        print(f"[WARNING] Local asset missing at: {css_path}. Using default system styles.")

    # -------------------------------------------------------------------
    # SEQUENTIAL BOOT LIFECYCLE MANAGEMENT LOOP
    # -------------------------------------------------------------------

    # PHASE 1. Initial Environment Synchronization
    if ApplicationLoader is not None:
        print("[DEBUG] Instantiating Screen 1: Application Splash Loader Canvas...")
        loader = ApplicationLoader()
        loader.start_boot_sequence()
        # Block until finished. Loader handles login/onboarding internal gating.
        loader_result = loader.exec()

        # Clean up loader instance
        loader.deleteLater()
    else:
        print("[ERROR] ApplicationLoader not found. Halting.")
        sys.exit(1)

    # PHASE 2: Network Verification Gate
    from features.network.connection import NetworkWizardOverlay

    if not is_network_ready():
        print("[STATUS] Network unreachable. Launching Network Wizard...")
        network_wizard = NetworkWizardOverlay()
        if network_wizard.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)  # Exit if user cancels network setup
    else:
        print("[SUCCESS] Network verified.")

    # PHASE 3: Dashboard Handoff
    # Logic: Only proceed to MainCockpit if the previous gates (Loader/Network) 
    # concluded with an 'Accepted' signal.
    if loader_result == QDialog.DialogCode.Accepted:
        print("[SUCCESS] Loading sequence complete. Launching Main Cockpit.")
        # --- LOAD CONFIGURATION ---
        config_path = os.path.join(root_dir, "data/server_config.json")
        try:
            with open(config_path, "r") as f:
                app_config = json.load(f)
            print("[DEBUG] Configuration loaded successfully.")
        except Exception as e:
            print(f"[CRITICAL] Failed to load server_config.json: {e}")
            sys.exit(1)
        # -------------------------------

        # Pass the loaded config to MainCockpit
        print("[DEBUG] Passing configuration to MainCockpit...")
        main_cockpit = MainCockpit(app_config) 
        main_cockpit.show()

        # Hand off control to the Main Dashboard event loop
        sys.exit(app.exec())
    else:
        print("[STATUS] Initialization halted. Shutting down.")
        sys.exit(0)

if __name__ == "__main__":
    main()