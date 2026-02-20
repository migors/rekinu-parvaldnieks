"""FastAPI application entry point."""

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import sys
import logging

# Allow HTTP for local OAuth2 development (only in non-production)
if os.environ.get("ENVIRONMENT", "development") != "production":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from .database import engine, get_db
from .models import Base
from . import crud, schemas, auth
from .auth import get_current_user, authenticate_user, create_access_token, Token, LoginRequest
from .routers import clients, invoices, services

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Invoice Manager", version="1.0.0")

@app.on_event("startup")
def startup_event():
    from .database import SessionLocal
    from . import models, auth
    from sqlalchemy import text
    
    # Auto-migrate DB schema for existing databases (SQLite doesn't do this via create_all)
    try:
        with engine.begin() as conn:
            # Check clients table
            res = conn.execute(text("PRAGMA table_info(clients)")).fetchall()
            columns = [row[1] for row in res]
            if "postal_code" not in columns and len(columns) > 0:
                conn.execute(text('ALTER TABLE clients ADD COLUMN postal_code VARCHAR(20) DEFAULT ""'))
            if "email" not in columns and len(columns) > 0:
                conn.execute(text('ALTER TABLE clients ADD COLUMN email VARCHAR(255) DEFAULT ""'))
                
            # Check services table
            res = conn.execute(text("PRAGMA table_info(services)")).fetchall()
            columns = [row[1] for row in res]
            if "vat_rate" not in columns and len(columns) > 0:
                conn.execute(text('ALTER TABLE services ADD COLUMN vat_rate FLOAT DEFAULT 21.0'))
        print("Database schemas verified and migrated.")
    except Exception as e:
        print(f"Error migrating DB schema: {e}")

    db = SessionLocal()
    try:
        # Check if any user exists
        user_count = db.query(models.User).count()
        if user_count == 0:
            print("Creating default admin user...")
            hashed_pw = auth.get_password_hash("admin123")
            admin = models.User(
                username="admin",
                password_hash=hashed_pw,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("Default admin created: admin / admin123")
    except Exception as e:
        print(f"Error creating default user: {e}")
    finally:
        db.close()

# Mount static files — resolve correct path for both dev and frozen EXE
if getattr(sys, 'frozen', False):
    _base_dir = os.path.join(sys._MEIPASS, "app")
else:
    _base_dir = os.path.dirname(os.path.abspath(__file__))
_static_dir = os.path.join(_base_dir, "static")
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# Include routers
app.include_router(clients.router)
app.include_router(invoices.router)
app.include_router(services.router)


# ── Auth endpoints (public) ───────────────────────────────────────────

@app.post("/api/auth/login", response_model=auth.Token)
def login(data: auth.LoginRequest, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Nepareizs lietotājvārds vai parole")
    
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.put("/api/auth/profile")
def update_profile(
    data: schemas.UserProfileUpdate, 
    db: Session = Depends(get_db), 
    current_username: str = Depends(auth.get_current_user)
):
    """Update current user's username and/or password."""
    user = crud.update_user_profile(db, current_username, data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "Profils atjaunināts", "username": user.username}


@app.get("/api/auth/me")
def auth_me(user: str = Depends(get_current_user)):
    return {"username": user}


# ── Settings endpoints (protected) ───────────────────────────────────

@app.get("/api/settings", response_model=schemas.SettingsRead)
def read_settings(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return crud.get_settings(db)


@app.get("/api/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return crud.get_stats(db)


@app.put("/api/settings", response_model=schemas.SettingsRead)
def save_settings(data: schemas.SettingsUpdate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return crud.update_settings(db, data)


class TestEmailRequest(BaseModel):
    to_email: str


@app.post("/api/settings/test-email")
async def test_email(payload: TestEmailRequest, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Send a test email using current SMTP settings."""
    settings = crud.get_settings(db)
    from .utils import send_test_email
    try:
        await send_test_email(settings, payload.to_email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")
    return {"message": f"Test email sent to {payload.to_email}"}



@app.get("/api/backup/export")
def export_backup(user: str = Depends(get_current_user)):
    """Export the database file as a download."""
    from .database import DATA_DIR
    db_path = os.path.join(DATA_DIR, "invoices.db")
    if not os.path.exists(db_path):
        return JSONResponse(status_code=404, content={"detail": "Database file not found"})
    
    return FileResponse(
        path=db_path,
        filename="invoices_backup.db",
        media_type='application/x-sqlite3'
    )


# ── Google Drive OAuth2 ──────────────────────────────────────────────

@app.get("/api/gdrive/auth")
def gdrive_auth(request: Request, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Redirect user to Google consent screen."""
    from .gdrive import get_auth_url
    settings = crud.get_settings(db)
    client_id = settings.get("gdrive_client_id", "").strip()
    client_secret = settings.get("gdrive_client_secret", "").strip()
    if not client_id or not client_secret:
        return JSONResponse(status_code=400, content={"detail": "Client ID and Client Secret are required in settings"})
    # Force localhost to match Google Console registration recommendations
    redirect_uri = "http://localhost:8000/api/gdrive/callback"
    auth_url = get_auth_url(client_id, client_secret, redirect_uri)
    return RedirectResponse(auth_url)


@app.get("/api/gdrive/callback")
def gdrive_callback(code: str, request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth2 callback — exchange code for refresh token."""
    from .gdrive import exchange_code
    settings = crud.get_settings(db)
    client_id = settings.get("gdrive_client_id", "").strip()
    client_secret = settings.get("gdrive_client_secret", "").strip()
    redirect_uri = "http://localhost:8000/api/gdrive/callback"
    try:
        refresh_token = exchange_code(code, client_id, client_secret, redirect_uri)
        if refresh_token:
            crud.set_setting(db, "gdrive_refresh_token", refresh_token)
            # Redirect back to the app with success
            return RedirectResponse("/?gdrive=ok")
        else:
            return RedirectResponse("/?gdrive=fail")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"GDrive OAuth2 callback error: {e}")
        # Also print to make sure it shows in terminal
        print(f"!!! GDrive OAuth2 callback error: {e}")
        return RedirectResponse("/?gdrive=fail")



# ── Pages ─────────────────────────────────────────────────────────────

@app.get("/login")
def login_page():
    return FileResponse(os.path.join(_static_dir, "login.html"))


@app.get("/")
def root():
    return FileResponse(
        os.path.join(_static_dir, "index.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )
