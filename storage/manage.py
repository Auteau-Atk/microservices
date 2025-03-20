from sqlalchemy import create_engine
from models import Base
from db import engine

def create_tables():
    Base.metadata.create_all(engine)
    print("All tables created successfully.")

def drop_tables():
    Base.metadata.drop_all(engine)
    print("All tables dropped successfully.")

if __name__ == "__main__":
    # For ease of use
    import argparse

    parser = argparse.ArgumentParser(description="Manage database tables.")
    parser.add_argument("--create", action="store_true", help="Create all tables")
    parser.add_argument("--drop", action="store_true", help="Drop all tables")
    args = parser.parse_args()

    if args.create:
        create_tables()
    elif args.drop:
        drop_tables()
    else:
        print("Please specify --create or --drop.")