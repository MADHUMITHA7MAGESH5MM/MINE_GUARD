from src.database.database import engine
from src.database.models import Base

def init_database():
    print("Connecting to SQLite engine...")
    print("Creating database tables based on models.py...")
    
    # This single line reads your Incident class and translates it into SQL tables!
    Base.metadata.create_all(bind=engine)
    
    print("Database initialization complete! The safety_app.db file is ready.")

if __name__ == "__main__":
    init_database()