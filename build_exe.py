"""
Build script — creates InvoiceManager.exe using PyInstaller.
Run: python build_exe.py
"""

import subprocess
import sys
import os


def install_deps():
    """Install build-time dependencies."""
    deps = ['pyinstaller', 'pystray', 'Pillow']
    for dep in deps:
        print(f"  Installing {dep}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep, '-q'])


def build():
    """Run PyInstaller to create the EXE."""
    project_dir = os.path.dirname(os.path.abspath(__file__))

    # Paths to bundle
    app_dir = os.path.join(project_dir, 'app')
    static_dir = os.path.join(app_dir, 'static')
    templates_dir = os.path.join(app_dir, 'templates')

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--clean',
        '--name', 'InvoiceManager',

        # Single-folder mode (faster startup than --onefile)
        '--onedir',

        # Console mode — launcher manages console visibility itself
        '--console',

        # Bundle data files
        f'--add-data={static_dir};app/static',
        f'--add-data={templates_dir};app/templates',

        # Hidden imports that PyInstaller may miss
        '--hidden-import=uvicorn.logging',
        '--hidden-import=uvicorn.loops',
        '--hidden-import=uvicorn.loops.auto',
        '--hidden-import=uvicorn.protocols',
        '--hidden-import=uvicorn.protocols.http',
        '--hidden-import=uvicorn.protocols.http.auto',
        '--hidden-import=uvicorn.protocols.websockets',
        '--hidden-import=uvicorn.protocols.websockets.auto',
        '--hidden-import=uvicorn.lifespan',
        '--hidden-import=uvicorn.lifespan.on',
        '--hidden-import=uvicorn.lifespan.off',
        '--hidden-import=sqlalchemy.sql.default_comparator',
        '--hidden-import=sqlalchemy.sql.default_comparator',
        '--hidden-import=reportlab',
        '--hidden-import=reportlab.graphics.barcode',
        '--hidden-import=reportlab.rl_config',
        '--hidden-import=html5lib',
        '--hidden-import=cssselect2',
        '--hidden-import=pypdf',
        '--hidden-import=arabic_reshaper',
        '--hidden-import=bidi.algorithm',
        '--hidden-import=pystray',
        '--hidden-import=pystray._win32',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageDraw',
        '--hidden-import=email.mime.multipart',
        '--hidden-import=email.mime.text',
        '--hidden-import=email.mime.base',
        '--hidden-import=google.auth',
        '--hidden-import=google.auth.transport',
        '--hidden-import=google.auth.transport.requests',
        '--hidden-import=google.oauth2',
        '--hidden-import=google.oauth2.credentials',
        '--hidden-import=googleapiclient',
        '--hidden-import=googleapiclient.discovery',
        '--hidden-import=google_auth_oauthlib',
        '--hidden-import=google_auth_oauthlib.flow',
        '--hidden-import=passlib.handlers.bcrypt',
        '--hidden-import=bcrypt',
        '--hidden-import=jose',

        # Collect submodules for packages that lazy-load
        '--collect-submodules=uvicorn',
        '--collect-submodules=uvicorn',
        '--collect-submodules=reportlab',
        '--collect-submodules=google',
        '--collect-submodules=googleapiclient',
        '--collect-submodules=google_auth_oauthlib',

        # Collect data for packages that need data files
        # Collect data for packages that need data files
        '--collect-data=reportlab',
        '--collect-data=certifi',

        # Output directory
        f'--distpath={os.path.join(project_dir, "dist")}',
        f'--workpath={os.path.join(project_dir, "build")}',

        # Entry point
        os.path.join(project_dir, 'launcher.py'),
    ]

    print("\n  Running PyInstaller...\n")
    subprocess.check_call(cmd)


def main():
    print("=" * 60)
    print("  Invoice Manager — EXE Build")
    print("=" * 60)

    print("\n[1/2] Installing build dependencies...")
    install_deps()

    print("\n[2/2] Building EXE...")
    build()

    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'InvoiceManager')
    print("\n" + "=" * 60)
    print("  BUILD COMPLETE!")
    print(f"  EXE location: {dist_dir}\\InvoiceManager.exe")
    print("=" * 60)
    print("\nPirmajā palaišanā tiks izveidots admin lietotājs:")
    print("  Lietotājs: admin")
    print("  Parole:    admin123")
    print("  (Mainiet paroli pēc pirmās pieslēgšanās!)")


if __name__ == "__main__":
    main()
