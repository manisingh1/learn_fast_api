import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db
from app.models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_create_artist():
    response = client.post(
        "/artists/",
        json={"name": "test-artist"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-artist"
    assert "id" in data


def test_create_album():
    response = client.post(
        "/artists/",
        json={"name": "test-artist"},
    )
    response = client.post(
        "/albums/",
        json={
            "name": "ep 1",
            "release_date": "2024-01-20",
            "price": 10.00,
            "artist_name": "test-artist",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "ep 1"


def test_get_artist_and_album():
    response = client.post(
        "/artists/",
        json={"name": "test-artist"},
    )
    response = client.post(
        "/albums/",
        json={
            "name": "ep 1",
            "release_date": "2024-01-20",
            "price": 10.00,
            "artist_name": "test-artist",
        },
    )
    response = client.get("/albums/test-artist")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "ep 1"


def test_get_artist_and_album_with_filters():
    response = client.post(
        "/artists/",
        json={"name": "test-artist"},
    )
    response = client.post(
        "/albums/",
        json={
            "name": "ep 1",
            "release_date": "2024-01-20",
            "price": 10.00,
            "artist_name": "test-artist",
        },
    )
    response = client.get("/albums/test-artist", params={"min_price": 11.00})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

    response = client.get("/albums/test-artist", params={"max_price": 9.00})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

    response = client.get("/albums/test-artist", params={"min_date": "2024-01-19"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    response = client.get("/albums/test-artist", params={"max_date": "2023-01-19"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_make_album_no_artist_returns_404():
    response = client.post(
        "/albums/",
        json={
            "name": "ep 1",
            "release_date": "2024-01-20",
            "price": 10.00,
            "artist_name": "test-artist",
        },
    )
    assert response.status_code == 404
