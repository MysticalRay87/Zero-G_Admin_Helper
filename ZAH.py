import os
import sys
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import QEventLoop, QCoreApplication

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
    # The ApplicationLoader now internalizes the LoginWindow gate at 30%.
    if ApplicationLoader is not None:
        print("[DEBUG] Instantiating Screen 1: Application Splash Loader Canvas...")
        loader = ApplicationLoader()
        loader.start_boot_sequence()
        # Block until finished. Loader handles login internally.
        loader_result = loader.exec()
        
        # NAVIGATION HUB: Inspect intent from the LoginWindow instance held by loader
        # (Assuming loader stores a reference to the login window or state)
        # For now, we route based on the result of the loader chain
        if loader_result == QDialog.DialogCode.Accepted:
            print("[SUCCESS] All initialization gates clear. Spinning up master core cockpit dashboard view...")
        
        # If the user requested onboarding during the loader phase:
        elif hasattr(loader, 'onboarding_requested') and loader.onboarding_requested:
            if AccountOnboardingWizard is not None:
                print("[DEBUG] Instantiating Screen 2: Account Onboarding Wizard Canvas...")
                wizard = AccountOnboardingWizard(parent=None)
                QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
                wizard.exec()
            else:
                print("[ERROR] Wizard missing.")
                sys.exit(1)
        else:
            print("[STATUS] User exited or auth failed. Shutting down.")
            sys.exit(0)
            
        loader.deleteLater()
    
# PHASE 0: Network Check (The first gate)
    from features.network.connection import is_network_ready, NetworkWizardOverlay
    
    if not is_network_ready():
        print("[STATUS] Network unreachable. Launching Network Wizard...")
        network_wizard = NetworkWizardOverlay()
        if network_wizard.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0) # Exit if wizard canceled
    else:
        print("[SUCCESS] Network verified.")
    
    # PHASE 3: Launch Primary System Administration Dashboard Frame
    if loader.onboarding_requested and AccountOnboardingWizard:
        wizard = AccountOnboardingWizard()
        wizard.exec()
    else:
        print("[STATUS] All initialization gates clear. Spinning up master core cockpit dashboard view...")
        if loader.result() == QDialog.DialogCode.Accepted:
            print("[SUCCESS] Loading sequence complete. Launching Main Cockpit.")
            
            # Instantiate and show the main dashboard
            main_cockpit = MainCockpit()
            main_cockpit.show()
            
            # Keep the application alive
            sys.exit(app.exec())

if __name__ == "__main__":
    main()