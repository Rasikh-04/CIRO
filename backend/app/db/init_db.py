from app.db.session import engine, Base
from app.models import signal, crisis, dispatch, simulation, resource, operational_picture

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("All tables created.")