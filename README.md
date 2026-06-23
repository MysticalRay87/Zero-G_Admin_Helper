# Zero-G Admin Helper (v1.0-Alpha)

An immersive, high-tech sci-fi standalone desktop administration station designed to monitor a dedicated Empyrion Galactic Survival game server environment and handle live, in-game administration operations.
An immersive, high-tech sci-fi standalone desktop administration station designed to monitor a dedicated Empyrion Galactic Survival game server environment and handle live, in-game administration operations.

---

## 🏗️ Technical Stack & Framework Constraints

* **Framework:** PyQt6 (Strict usage of scoped enum namespaces like `Qt.AlignmentFlag` and `Qt.Orientation`).
* **Root Workspace Path:** `/mnt/Zero-G_Files/Zero-G_Admin_Helper`
* **Line Terminations:** All outbound server commands must use `\r\n` line terminations paired with a 500ms input buffer delay to match GTX Gaming hardware calibrations.

---

## 🌌 Aesthetic Identity & UI Guidelines

The interface moves completely away from traditional flat, corporate grey layouts to model an immersive starship cockpit HUD utilizing custom widget textures:
* **Deep Space Backgrounds:** Shadowy Marine Blue (`#001A33` / RGB: 0, 26, 51).
* **Neon Accent Tones:** Bright Cerulean Blue (`#1DACD6` / RGB: 29, 172, 214) and Vivid Cerulean (`#007BA7` / RGB: 0, 123, 167).
* **UI Integrity:** Strict reliance on QSS (Qt Style Sheets) border-image properties. This is mandated to prevent high-detail vector asset corner-brackets and custom neon glow textures from warping or stretching across variable monitor resolutions.
* **Fixed Dimensions:** The application orchestrator expects an initial canvas resolution layout of 1000x750 pixels, while specific configuration components like the AccountOnboardingWizard enforce a fixed structural window size of 512x512 pixels.

---

## 🛠️ Technical Stack & Core Framework

* **Primary Language:** Python.
* **GUI Framework:** PyQt6.
* **Namespace Rigor:** Strict usage of scoped enum namespaces within the GUI library (such as explicitly utilizing Qt.AlignmentFlag and Qt.Orientation).
* **Target Host & Integration environment:** Dedicated Empyrion: Galactic Survival game server hosted via GTXGaming.

## 🏗️ Architectural & File System Constraints

* **Feature-First Pattern:** All application functional logic, controllers, and sub-views are isolated cleanly within the /features/ subdirectory. Cross-dependency between distinct features is strictly prohibited.
* **Fixed Entry Points & Discovery:** Root paths are locked. Discovery relies explicitly on the fixed entry points ZAH.py (Master Lifecycle Orchestrator) and startup.py (Discovery Initialization Script).
* **State Separation Protocol:** Dynamic runtime data, persistent cache databases, configurations, and application telemetry (/data, /logs, __pycache__) are strictly excluded from Git tracking via .gitignore.

## 📡 Networking & Server Calibration Constraints

* **Asynchronous Thread Execution:** Multi-threaded architecture is mandatory. Dedicated asynchronous background threads handle heavy workloads—such as parsing raw stdout server console logs and broadcasting secure live in-game chat—to eliminate UI-thread latency and freeze-ups.
* **GTXGaming Hardware Calibration:** All outbound network command strings pushed to the server must handle explicit formatting calibrations:
* Must utilize Windows-style \r\n line terminations.
* Must include a mandatory 500ms input buffer delay between commands.
* **UI Integrity:** Strict reliance on QSS (Qt Style Sheets) border-image properties. This is mandated to prevent high-detail vector asset corner-brackets and custom neon glow textures from warping or stretching across variable monitor resolutions.
* **Fixed Dimensions:** The application orchestrator expects an initial canvas resolution layout of 1000x750 pixels, while specific configuration components like the AccountOnboardingWizard enforce a fixed structural window size of 512x512 pixels.

---

## 🛠️ Technical Stack & Core Framework

* **Primary Language:** Python.
* **GUI Framework:** PyQt6.
* **Namespace Rigor:** Strict usage of scoped enum namespaces within the GUI library (such as explicitly utilizing Qt.AlignmentFlag and Qt.Orientation).
* **Target Host & Integration environment:** Dedicated Empyrion: Galactic Survival game server hosted via GTXGaming.

## 🏗️ Architectural & File System Constraints

* **Feature-First Pattern:** All application functional logic, controllers, and sub-views are isolated cleanly within the /features/ subdirectory. Cross-dependency between distinct features is strictly prohibited.
* **Fixed Entry Points & Discovery:** Root paths are locked. Discovery relies explicitly on the fixed entry points ZAH.py (Master Lifecycle Orchestrator) and startup.py (Discovery Initialization Script).
* **State Separation Protocol:** Dynamic runtime data, persistent cache databases, configurations, and application telemetry (/data, /logs, __pycache__) are strictly excluded from Git tracking via .gitignore.

## 📡 Networking & Server Calibration Constraints

* **Asynchronous Thread Execution:** Multi-threaded architecture is mandatory. Dedicated asynchronous background threads handle heavy workloads—such as parsing raw stdout server console logs and broadcasting secure live in-game chat—to eliminate UI-thread latency and freeze-ups.
* **GTXGaming Hardware Calibration:** All outbound network command strings pushed to the server must handle explicit formatting calibrations:
* Must utilize Windows-style \r\n line terminations.
* Must include a mandatory 500ms input buffer delay between commands.

## 📦 System Architecture & Directory Patterns

* **This repository enforces strict **Feature-First Pattern** boundaries and **State Separation Protocols**. All code tracking is restricted by these root namespaces:**

/mnt/Zero-G_Files/Zero-G_Admin_Helper/
│
├── ZAH.py                              # Master Lifecycle Orchestrator / Root Entry Point [cite: 46, 81]
├── startup.py                          # Discovery Initialization Entry Script [cite: 46, 81]
│
├── assets/                             # Immutable Visual & UI Infrastructure
│   └── backgrounds/
│       ├── account_creation_wizard.png # Screen 2 Canvas Background Artwork [cite: 358]
│       └── [loader_splash_assets].png
│
├── data/                               # Dynamic Runtime Registries (Git Track-Excluded) [cite: 45, 83]
│   ├── users.json                      # Master Account & Administrator Profiles [cite: 126, 404]
│   └── server_config.json              # Ingested Production IP/Port Targets [cite: 226, 878]
│
├── features/                           # Encapsulated Business Logic & Views [cite: 23, 45, 82]
│   │
│   ├── auth/                           # Authentication, Access, & Session Profiles
│   │   ├── login.py                    # Screen 1B Pop-up Modal (Symmetrically Flipped Controls) [cite: 322]
│   │   ├── onboarding.py               # Screen 2 Account Onboarding Wizard Class [cite: 100, 347]
│   │   └── persistence.py              # Session Management, Token Tracking & Data Serialization [cite: 322, 738, 739]
│   │
│   ├── loading/                        # Active Event Pumping & Timeline Splashes
│   │   └── loading_screen.py           # Screen 1A ApplicationLoader (Canvas & Animation Engine) [cite: 286, 458]
│   │
│   └── network/                        # Diagnostic Verification & Remote Communication Layers
│       └── connection.py               # NetworkWizardOverlay & is_network_ready() Validation [cite: 170, 301, 783]
│
├── logs/                               # Transient Output Runtime Telemetry (Git-Excluded) [cite: 45, 83]
│   └── zah_runtime.log
│
└── styles/                             # Immersive Space-Themed Styling Sheets
    └── ZAH.css                         # Layout Rules (Deep Space Navy #001A33 & Cerulean Neon) [cite: 67, 185]
* **This repository enforces strict **Feature-First Pattern** boundaries and **State Separation Protocols**. All code tracking is restricted by these root namespaces:**

/mnt/Zero-G_Files/Zero-G_Admin_Helper/
│
├── ZAH.py                              # Master Lifecycle Orchestrator / Root Entry Point [cite: 46, 81]
├── startup.py                          # Discovery Initialization Entry Script [cite: 46, 81]
│
├── assets/                             # Immutable Visual & UI Infrastructure
│   └── backgrounds/
│       ├── account_creation_wizard.png # Screen 2 Canvas Background Artwork [cite: 358]
│       └── [loader_splash_assets].png
│
├── data/                               # Dynamic Runtime Registries (Git Track-Excluded) [cite: 45, 83]
│   ├── users.json                      # Master Account & Administrator Profiles [cite: 126, 404]
│   └── server_config.json              # Ingested Production IP/Port Targets [cite: 226, 878]
│
├── features/                           # Encapsulated Business Logic & Views [cite: 23, 45, 82]
│   │
│   ├── auth/                           # Authentication, Access, & Session Profiles
│   │   ├── login.py                    # Screen 1B Pop-up Modal (Symmetrically Flipped Controls) [cite: 322]
│   │   ├── onboarding.py               # Screen 2 Account Onboarding Wizard Class [cite: 100, 347]
│   │   └── persistence.py              # Session Management, Token Tracking & Data Serialization [cite: 322, 738, 739]
│   │
│   ├── loading/                        # Active Event Pumping & Timeline Splashes
│   │   └── loading_screen.py           # Screen 1A ApplicationLoader (Canvas & Animation Engine) [cite: 286, 458]
│   │
│   └── network/                        # Diagnostic Verification & Remote Communication Layers
│       └── connection.py               # NetworkWizardOverlay & is_network_ready() Validation [cite: 170, 301, 783]
│
├── logs/                               # Transient Output Runtime Telemetry (Git-Excluded) [cite: 45, 83]
│   └── zah_runtime.log
│
└── styles/                             # Immersive Space-Themed Styling Sheets
    └── ZAH.css                         # Layout Rules (Deep Space Navy #001A33 & Cerulean Neon) [cite: 67, 185]

---

## 🔄 Automated Lifecycle & Sequential Flows

[ Boot: ZAH.py ] ──> UI Thread Draws 1000x750 Canvas
                           │
                           ▼
                 [ Increment to 30% ]
                           │
             Gated Check: "Keep Me Logged In"?
               ├── Yes ──► Bypass Login
               └── No  ──► [ HALT Progress ] ──► Open Login Screen
                                                       │
                                            Verified Account Login/Creation
                                                       │
                           ┌───────────────────────────┘
                           ▼
                 [ Progress Resumes ]
                           │
                           ▼
                 [ Increment to 60% ]
                           │
             Gated Check: Server Config Profiles?
               ├── Yes ──► Bypass Network Wizard
               └── No  ──► [ HALT Progress ] ──► Open Network Connection Wizard
                                                       │
                                            Config Created + Validated Ping
                                                       │
                           ┌───────────────────────────┘
                           ▼
                 [ Progress Resumes ]
                           │
                           ▼
                 [ Milestone 100% ] ──► Hand off to Main Workspace

### 1. Boot Diagnostics & Key Milestone Logic Recap
At 30% Progress: The loader's timing loop pauses and checks if there are accounts with "keep me logged in", if there are login screen is bypassed if no then the Login Screen Overlay is activated, Progress bar is kept frozen until successful user login or account creation has been verified.

At 60% Progress: The progression bar halts a second time to check if a server configuration profile available, conditionally intercepting the initialization of the Network Connection Wizard. If there are available network configurations then network wizard is bypassed. If there are no configuration profiles available then the network wizard opens for network login data. Progress bar is kept frozen until successful configuration profile is found/created. 

Ping is run to verify network configuration. If unable to verify then network wizard is re-initialized with ping error and request to re-enter network login info.

At 100% Progress: Upon successfully navigating both state gates, the orchestrator closes the loading phase and hands control off over to the main_window cockpit dashboard interface. 
[ Boot: ZAH.py ] ──> UI Thread Draws 1000x750 Canvas
                           │
                           ▼
                 [ Increment to 30% ]
                           │
             Gated Check: "Keep Me Logged In"?
               ├── Yes ──► Bypass Login
               └── No  ──► [ HALT Progress ] ──► Open Login Screen
                                                       │
                                            Verified Account Login/Creation
                                                       │
                           ┌───────────────────────────┘
                           ▼
                 [ Progress Resumes ]
                           │
                           ▼
                 [ Increment to 60% ]
                           │
             Gated Check: Server Config Profiles?
               ├── Yes ──► Bypass Network Wizard ────────────────────────────────────────► [Network Ping] ◃───┒
               └── No  ──► [ HALT Progress ] ──► Open Network Connection Wizard                   |           |
                                                       │                                          |           |
                                                Config Created                                    |           |
                                                       │                                          |           |
                                                       |                                          |           |
                                                       ▼                                          |           |
                           ┌───────────────────[Validated Ping]<──────────────────────────────────┘           |
                           |                           |                                                      |
                           ▼                           ▼                                                      |
                         (Yes)                       (NO)                                                     |
                           ▼                         └────► Re-launch Network Connection Wizard ──────────────┘
                 [ Progress Resumes ]
                           │
                           ▼
                 [ Milestone 100% ] ──► Hand off to Main Workspace

### 1. Boot Diagnostics & Key Milestone Logic Recap
At 30% Progress: The loader's timing loop pauses and checks if there are accounts with "keep me logged in", if there are login screen is bypassed if no then the Login Screen Overlay is activated, Progress bar is kept frozen until successful user login or account creation has been verified.

At 60% Progress: The progression bar halts a second time to check if a server configuration profile available, conditionally intercepting the initialization of the Network Connection Wizard. If there are available network configurations then network wizard is bypassed. If there are no configuration profiles available then the network wizard opens for network login data. Progress bar is kept frozen until successful configuration profile is found/created. 

Ping is run to verify network configuration. If unable to verify then network wizard is re-initialized with ping error and request to re-enter network login info.

At 100% Progress: Upon successfully navigating both state gates, the orchestrator closes the loading phase and hands control off over to the main_window cockpit dashboard interface. 
---

## 📡 Remote Server Connection Variables
* **Target Host:** Dedicated Empyrion Server hosted via GTX Gaming
* **Active Destination IP:** `66.23.236.138`
* **Active Routing Port:** `30004` (Dedicated text-based Telnet console log stream)
* **Authentication Token:** `******`
* **Authentication Token:** `******`
