import os, sys
import pytest
from flask import json
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from crud.app import app as flask_app
from shared.database import engine, SessionLocal
from shared.models.base import Base
from shared.models.job import Job
from shared.models.scrape_target import ScrapeTarget

# Ensure app context is active for tests
@pytest.fixture(scope='session', autouse=True)
def app_context(app):
    with app.app_context():
        yield

@pytest.fixture(scope='session')
def app():
    """
    Creates a Flask application configured for testing.
    """
    # Create the database and the database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield flask_app
    # Teardown: Drop all tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope='session')
def client(app):
    """
    Provides a test client for the Flask application.
    """
    return app.test_client()

# ---------------------------
# Tests for JobScheduler APIs
# ---------------------------

def test_create_job(client):
    """Test creating a new JobScheduler entry."""
    payload = {
        "task_name": "Test Job",
        "scheduled_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending",
        "error_message": None
    }
    response = client.post('/jobs', json=payload)
    data = response.get_json()
    assert response.status_code == 201
    assert "job_id" in data
    assert data["message"] == "Job added successfully"


def test_get_job(client):
    """Test retrieving a single JobScheduler entry."""
    # First create a job
    payload = {
        "task_name": "Get Job Test",
        "scheduled_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending",
        "error_message": None
    }
    post_resp = client.post('/jobs', json=payload)
    job_id = post_resp.get_json()["job_id"]

    # Retrieve the created job
    get_resp = client.get(f'/jobs/{job_id}')
    data = get_resp.get_json()
    assert get_resp.status_code == 200
    assert data["id"] == job_id
    assert data["task_name"] == payload["task_name"]


def test_get_all_jobs(client):
    """Test retrieving all JobScheduler entries."""
    # Create two jobs
    for i in range(2):
        payload = {
            "task_name": f"Job {i}",
            "scheduled_date": (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending",
            "error_message": None
        }
        client.post('/jobs', json=payload)

    resp = client.get('/jobs')
    data = resp.get_json()
    assert resp.status_code == 200
    # Expecting at least 2 jobs (there could be more if previous tests haven't been cleaned up)
    assert isinstance(data, list)
    assert len(data) >= 2


def test_update_job(client):
    """Test updating a JobScheduler entry."""
    # Create a job to update
    payload = {
        "task_name": "Job to Update",
        "scheduled_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending",
        "error_message": None
    }
    post_resp = client.post('/jobs', json=payload)
    job_id = post_resp.get_json()["job_id"]

    # Prepare update payload
    update_payload = {
        "task_name": "Updated Job Name",
        "status": "completed"
    }
    put_resp = client.put(f'/jobs/{job_id}', json=update_payload)
    data = put_resp.get_json()
    assert put_resp.status_code == 200
    assert data["message"] == "Job updated successfully"

    # Verify update
    get_resp = client.get(f'/jobs/{job_id}')
    job_data = get_resp.get_json()
    assert job_data["task_name"] == "Updated Job Name"
    assert job_data["status"] == "completed"


def test_delete_job(client):
    """Test deleting a JobScheduler entry."""
    # Create a job to delete
    payload = {
        "task_name": "Job to Delete",
        "scheduled_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending",
        "error_message": None
    }
    post_resp = client.post('/jobs', json=payload)
    job_id = post_resp.get_json()["job_id"]

    # Delete the job
    delete_resp = client.delete(f'/jobs/{job_id}')
    delete_data = delete_resp.get_json()
    assert delete_resp.status_code == 200
    assert delete_data["message"] == "Job deleted successfully"

    # Verify deletion
    get_resp = client.get(f'/jobs/{job_id}')
    assert get_resp.status_code == 404


# ---------------------------
# Tests for ScrapeTarget APIs
# ---------------------------

def test_create_scrape_target(client):
    """Test creating a new ScrapeTarget entry."""
    payload = {
        "name": "Test Target",
        "url": "https://example.com",
        "type": "news"
    }
    response = client.post('/scrape-targets', json=payload)
    data = response.get_json()
    assert response.status_code == 201
    assert "target_id" in data
    assert data["message"] == "Scrape target added successfully"


def test_get_scrape_target(client):
    """Test retrieving a single ScrapeTarget entry."""
    # First create a target
    payload = {
        "name": "Target Get Test",
        "url": "https://example.com/test",
        "type": "blog"
    }
    post_resp = client.post('/scrape-targets', json=payload)
    target_id = post_resp.get_json()["target_id"]

    # Retrieve the created target
    get_resp = client.get(f'/scrape-targets/{target_id}')
    data = get_resp.get_json()
    assert get_resp.status_code == 200
    assert data["id"] == target_id
    assert data["name"] == payload["name"]


def test_get_all_scrape_targets(client):
    """Test retrieving all ScrapeTarget entries."""
    # Create two targets
    for i in range(2):
        payload = {
            "name": f"Target {i}",
            "url": f"https://example.com/{i}",
            "type": "blog"
        }
        client.post('/scrape-targets', json=payload)

    resp = client.get('/scrape-targets')
    data = resp.get_json()
    assert resp.status_code == 200
    # Expecting at least 2 targets
    assert isinstance(data, list)
    assert len(data) >= 2


def test_update_scrape_target(client):
    """Test updating a ScrapeTarget entry."""
    # Create a target to update
    payload = {
        "name": "Target to Update",
        "url": "https://example.com/update",
        "type": "news"
    }
    post_resp = client.post('/scrape-targets', json=payload)
    target_id = post_resp.get_json()["target_id"]

    # Prepare update payload
    update_payload = {
        "name": "Updated Target Name",
        "url": "https://example.com/updated"
    }
    put_resp = client.put(f'/scrape-targets/{target_id}', json=update_payload)
    data = put_resp.get_json()
    assert put_resp.status_code == 200
    assert data["message"] == "Scrape target updated successfully"

    # Verify update
    get_resp = client.get(f'/scrape-targets/{target_id}')
    target_data = get_resp.get_json()
    assert target_data["name"] == "Updated Target Name"
    assert target_data["url"] == "https://example.com/updated"


def test_delete_scrape_target(client):
    """Test deleting a ScrapeTarget entry."""
    # Create a target to delete
    payload = {
        "name": "Target to Delete",
        "url": "https://example.com/delete",
        "type": "news"
    }
    post_resp = client.post('/scrape-targets', json=payload)
    target_id = post_resp.get_json()["target_id"]

    # Delete the target
    delete_resp = client.delete(f'/scrape-targets/{target_id}')
    delete_data = delete_resp.get_json()
    assert delete_resp.status_code == 200
    assert delete_data["message"] == "Scrape target deleted successfully"

    # Verify deletion
    get_resp = client.get(f'/scrape-targets/{target_id}')
    assert get_resp.status_code == 404
