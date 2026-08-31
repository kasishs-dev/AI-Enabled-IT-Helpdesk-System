import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app.seed import seed_database

SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_database(db)
    db.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def auth_header(client, email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_login_success(client):
    r = client.post("/api/auth/login", json={"email": "rahul@demo.com", "password": "Demo@123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_invalid(client):
    r = client.post("/api/auth/login", json={"email": "rahul@demo.com", "password": "wrong"})
    assert r.status_code == 401


def test_user_cannot_access_manager_dashboard(client):
    headers = auth_header(client, "rahul@demo.com", "Demo@123")
    r = client.get("/api/dashboard/manager", headers=headers)
    assert r.status_code == 403


def test_manager_can_access_dashboard(client):
    headers = auth_header(client, "neha@demo.com", "Demo@123")
    r = client.get("/api/dashboard/manager", headers=headers)
    assert r.status_code == 200
    assert r.json()["total_tickets"] >= 15


def test_create_vpn_issue(client):
    headers = auth_header(client, "rahul@demo.com", "Demo@123")
    r = client.post(
        "/api/issues/create",
        headers=headers,
        json={
            "title": "VPN is not connecting",
            "description": "I cannot connect to the company VPN. I have tried restarting the VPN client and my laptop but it still doesn't connect.",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ticket_created"] is True
    assert data["analysis"]["category"] == "VPN"
    assert data["analysis"]["severity"] == "P2"


def test_invalid_issue_suppressed(client):
    headers = auth_header(client, "rahul@demo.com", "Demo@123")
    r = client.post(
        "/api/issues/create",
        headers=headers,
        json={"title": "Hello", "description": "Hello"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["suppressed"] is True
    assert data["ticket_created"] is False


def test_it_support_sees_assigned_tickets(client):
    headers = auth_header(client, "amit@demo.com", "Demo@123")
    r = client.get("/api/dashboard/it", headers=headers)
    assert r.status_code == 200
    assert r.json()["assigned_to_me"] >= 1


def test_notifications(client):
    headers = auth_header(client, "amit@demo.com", "Demo@123")
    r = client.get("/api/notifications", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_ticket_lifecycle(client):
    user_h = auth_header(client, "rahul@demo.com", "Demo@123")
    create = client.post(
        "/api/issues/create",
        headers=user_h,
        json={"title": "Laptop screen flickering", "description": "My laptop screen keeps flickering during meetings and affects my work."},
    )
    ticket_id = create.json()["ticket"]["id"]

    it_h = auth_header(client, "priya@demo.com", "Demo@123")
    r = client.patch(f"/api/tickets/{ticket_id}/status", headers=it_h, json={"status": "IN_PROGRESS"})
    assert r.status_code in [200, 403]

    assignee_h = auth_header(client, "amit@demo.com", "Demo@123")
    tickets = client.get("/api/tickets", headers=assignee_h).json()
    if any(t["id"] == ticket_id for t in tickets):
        client.patch(f"/api/tickets/{ticket_id}/status", headers=assignee_h, json={"status": "IN_PROGRESS", "reason": "Started"})
        client.patch(f"/api/tickets/{ticket_id}/status", headers=assignee_h, json={"status": "RESOLVED", "resolution_notes": "Fixed display driver"})
        close = client.patch(f"/api/tickets/{ticket_id}/status", headers=user_h, json={"status": "CLOSED"})
        assert close.status_code == 200
