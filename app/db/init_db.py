from app.db.session import engine
from app.db.base_class import Base

# Import all models so Base.metadata knows them
from app.models.user import User

def init_db():
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")