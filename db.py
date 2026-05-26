

import os
from sqlalchemy import create_engine # used to create a connection to the database and execute SQL queries.
from sqlalchemy.orm import sessionmaker # used to perform database operations like: querying, inserting, updating, and deleting records.
from sqlalchemy.orm import declarative_base # Used to create database models (tables) using Python classes

#-----------------------------------------------------------------------------------#

# -----This string tells SQLAlchemy how to connect to MySQL------ #

DATABASE_URL = os.environ["DATABASE_URL"]

#-----------------------------------------------------------------------------------#

# ----- Create Engine ------ #
'''
Engine responsibilities:
- Opens database connections
- Sends SQL queries
'''
engine = create_engine(
    DATABASE_URL,
    echo=True  # Optional: shows SQL queries in terminal
)

#-----------------------------------------------------------------------------------#

# Create Session
# It creates a blueprint for creating sessions later.
SessionLocal = sessionmaker(
    autocommit=False, # Changes are NOT automatically saved. You must call session.commit() to save changes.
    autoflush=False, # Changes are NOT automatically sent to the database. You must call session.flush() to send changes.
    bind=engine # All sessions created by SessionLocal will use this database connection.
)

#-----------------------------------------------------------------------------------#

# Base class for models
'''
Creates a base class for all models. 
Models will inherit from this class to define database tables.
'''
Base = declarative_base() 

#-----------------------------------------------------------------------------------#

# Used to provide database session to API routes.
# It creates a new database session for each request and ensures that the session is
#  properly closed after the request is processed.
# Dependency function for FastAPI

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#-----------------------------------------------------------------------------------#

# Creates a new database session.
# Now you can run queries using db.

db = SessionLocal()

#-----------------------------------------------------------------------------------#

'''
Client Request
      ↓
FastAPI
      ↓
get_db()
      ↓
DB connection created
      ↓
db variable receives connection
      ↓
Your API runs
      ↓
Response sent
      ↓
DB connection closed
'''