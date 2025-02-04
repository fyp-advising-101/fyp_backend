from flask import Flask, json, request, jsonify
from flask_cors import CORS
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.models.base import Base
from shared.models.jobScheduler import JobScheduler
from shared.models.scrapeTarget import ScrapeTarget
from shared.database import engine, SessionLocal
from sqlalchemy.sql import text
import json
import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# Create tables if not created
Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3002)