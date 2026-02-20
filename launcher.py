"""
Invoice Manager — Windows Desktop Launcher
Starts the FastAPI server, opens the browser, and provides a system tray icon.
"""

import os
import sys
import time
import socket
import signal
import threading
import webbrowser
import subprocess
import logging
import ctypes
import ctypes.wintypes

# ── Singleton (prevent multiple instances) ───────────────────────────

_MUTEX_NAME = "InvoiceManagerMutex_DEV_8001"
_mutex = None

def _acquire_mutex() -> bool:
    """Try to acquire a named mutex. Returns False if another instance is already running."""
    global _mutex
    _mutex = ctypes.windll.kernel32.CreateMutexW(None, True, _MUTEX_NAME)
    last_error = ctypes.windll.kernel32.GetLastError()
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        return False
    return True


# ── Logging is set up inside main() to avoid running in PyWebView child processes ──
logger = logging.getLogger(__name__)
log_dir = ''  # Will be set in main()

# ── Console helpers ──────────────────────────────────────────────────

def _show_console():
    """Allocate a console for status messages."""
    try:
        ctypes.windll.kernel32.AllocConsole()
        # Redirect stdout/stderr to the new console
        sys.stdout = open('CONOUT$', 'w', encoding='utf-8')
        sys.stderr = open('CONOUT$', 'w', encoding='utf-8')
        # Set console title
        ctypes.windll.kernel32.SetConsoleTitleW("Invoice Manager")
    except Exception:
        pass

# Ensure stdout and stderr are never None (prevents PyInstaller child process crashes)
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')


def _hide_console():
    """Hide the console window (minimize to tray)."""
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except Exception:
        pass


# ── Default admin user creation ──────────────────────────────────────

def ensure_default_user():
    """Create a default admin user if no users exist (first launch)."""
    try:
        from app.database import SessionLocal, engine, Base
        from app.models import User
        from app.auth import get_password_hash

        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            count = db.query(User).count()
            if count == 0:
                hashed = get_password_hash("admin123")
                user = User(username="admin", password_hash=hashed, email="admin@localhost")
                db.add(user)
                db.commit()
                print("  [OK] Izveidots noklusētais lietotājs: admin / admin123")
                logger.info("Created default admin user (admin / admin123)")
            else:
                print(f"  [OK] Datubāzē ir {count} lietotāj(i)")
        finally:
            db.close()
    except Exception as e:
        print(f"  [!] Kļūda veidojot lietotāju: {e}")
        logger.error(f"Could not create default user: {e}")


# ── Port helpers ─────────────────────────────────────────────────────

def find_free_port(preferred: int = 8001) -> int:
    """Return the preferred port if available, otherwise find a free one."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', preferred))
            return preferred
    except OSError:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            port = s.getsockname()[1]
            return port


def wait_for_server(port: int, timeout: float = 45.0) -> bool:
    """Block until the server is accepting connections on the given port."""
    deadline = time.time() + timeout
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            if attempt % 5 == 0:
                remaining = int(deadline - time.time())
                print(f"  ... gaida serveri ({remaining}s atlikušas)")
            time.sleep(0.5)
    return False


# ── System tray ──────────────────────────────────────────────────────

def run_tray(port: int, shutdown_event: threading.Event):
    """Show a system tray icon with Open / Quit actions."""
    try:
        import pystray
        from PIL import Image, ImageDraw, ImageFont

        # Create a simple icon: green circle on white bg
        img = Image.new('RGB', (64, 64), '#1a1a2e')
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([4, 4, 60, 60], radius=12, fill='#2ecc71')
        draw.text((16, 18), 'IM', fill='white')

        def on_open(icon, item):
            webbrowser.open(f"http://localhost:{port}")

        def on_quit(icon, item):
            shutdown_event.set()
            icon.stop()

        icon = pystray.Icon(
            "InvoiceManager",
            img,
            "Invoice Manager",
            menu=pystray.Menu(
                pystray.MenuItem("Atvērt pārlūku", on_open, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Aizvērt", on_quit),
            ),
        )
        # Hide the console once tray icon is ready
        _hide_console()
        icon.run()
    except ImportError:
        print("\n  [i] System tray nav pieejams. Nospiediet Ctrl+C lai aizvērtu.")
        logger.info("pystray not available — running without system tray")
        try:
            shutdown_event.wait()
        except KeyboardInterrupt:
            shutdown_event.set()
    except Exception as e:
        logger.error(f"System tray error: {e}")
        try:
            shutdown_event.wait()
        except KeyboardInterrupt:
            shutdown_event.set()


# ── Main entry point ─────────────────────────────────────────────────


def _open_app_window(url: str):
    """Open the app in a dedicated window using Edge/Chrome --app mode.
    This gives a native-looking window without needing pywebview or pythonnet.
    Falls back to default browser if no Chromium browser is found.
    Returns the Popen object if app mode succeeded, else None.
    """
    candidate_paths = [
        # Microsoft Edge (ships with every Windows 10+)
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        # Google Chrome
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    app_args = [
        f"--app={url}",
        "--new-window",
        "--window-size=1280,800",
        "--disable-extensions",
    ]
    for path in candidate_paths:
        if os.path.isfile(path):
            try:
                proc = subprocess.Popen([path] + app_args)
                logger.info(f"Opened app window using: {path}")
                return proc
            except Exception as e:
                logger.warning(f"Failed to launch {path}: {e}")

    # Fallback: open in default browser (no blocking process returned)
    logger.warning("No Chromium browser found — falling back to default browser")
    webbrowser.open(url)
    return None


def main():
    # Show console for startup feedback
    _show_console()

    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║       INVOICE MANAGER v1.0           ║")
    print("  ╚══════════════════════════════════════╝")
    print()

    port = find_free_port(8001)
    print(f"  [1/3] Startē serveri uz porta {port}...")
    logger.info(f"Starting Invoice Manager on port {port}")

    # Make sure the default admin user exists
    print("  [2/3] Pārbauda datubāzi...")
    ensure_default_user()

    # Start uvicorn in a thread
    shutdown_event = threading.Event()
    server_error = threading.Event()

    def run_server():
        try:
            import traceback
            import uvicorn
            from app.main import app as fastapi_app
            config = uvicorn.Config(
                fastapi_app,
                host="127.0.0.1",
                port=port,
                log_level="info",
                # Force logs to stderr so we can capture them
                # access_log=True,
                # use_colors=False
            )
            server = uvicorn.Server(config)
            run_server.uvicorn_server = server
            server.run()
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"Server error: {e}\n{tb}")
            print(f"\n  [!] Servera kļūda: {e}")
            print(f"  {tb}")
            server_error.set()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for the server to be ready, then open an app window
    print("  [3/3] Gaida servera gatāvību...")
    if wait_for_server(port):
        print(f"\n  ✓ Serveris gatavs!")
        print(f"  ✓ Iekšējā adrese: http://localhost:{port}")
        logger.info("Server is ready — opening app window")

        url = f"http://localhost:{port}"
        _open_app_window(url)

        # Always run the system tray so the user can quit the server cleanly.
        # The server stays alive until the user chooses "Aizvērt" from the tray.
        run_tray(port, shutdown_event)
    elif server_error.is_set():
        print("\n  [!] Serveris nevarēja startēt. Skatiet logu:")
        print(f"      {os.path.join(log_dir, 'app.log')}")
        input("\n  Nospiediet Enter lai aizvērtu...")
        return
    else:
        print("\n  [!] Serveris nestartēja 45 sekunžu laikā.")
        print(f"      Skatiet: {os.path.join(log_dir, 'app.log')}")
        logger.error("Server did not start in time")
        input("\n  Nospiediet Enter lai aizvērtu...")
        return

    # Graceful shutdown
    print("\n  Izslēdz serveri...")
    logger.info("Shutting down…")
    if hasattr(run_server, 'uvicorn_server'):
        run_server.uvicorn_server.should_exit = True

    # Give server time to clean up
    server_thread.join(timeout=5)
    logger.info("Goodbye!")


import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()

    # ── Logging setup (only in the main process, not PyWebView subprocesses) ──
    if getattr(sys, 'frozen', False):
        log_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'InvoiceManager', 'data')
    else:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(log_dir, 'app.log'),
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
    )

    # ── Mutex check (only in the main process) ──
    if not _acquire_mutex():
        print('  [!] Invoice Manager jau darbojas!')
        import webbrowser
        webbrowser.open('http://localhost:8001')
        sys.exit(0)

    main()
