"""Script to create default admin user in the AppData database."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force database to use AppData path (simulate frozen EXE)
sys.frozen = True

from app.database import engine, Base
from app import models
from app.auth import get_password_hash
from sqlalchemy.orm import Session

# Create all tables
Base.metadata.create_all(bind=engine)

with Session(engine) as db:
    count = db.query(models.User).count()
    print(f"Users in database: {count}")
    if count == 0:
        user = models.User(
            username='admin',
            hashed_password=get_password_hash('admin123')
        )
        db.add(user)
        db.commit()
        print("Created admin user: admin / admin123")
    else:
        users = db.query(models.User).all()
        print(f"Existing users: {[u.username for u in users]}")
