import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add the backend directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ephemeris_server import app, calculate_longitude, determine_zodiac

client = TestClient(app)

@pytest.mark.parametrize("julian_date, target", [
    (2451545.0, 1),
    (2451545.0, 2),
    (2451545.0, 3),
    (2451545.0, 4),
])
def test_get_planet(julian_date, target):
    response = client.get("/planet", params={"julian_date": julian_date, "target": target})
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["julian_date"] == julian_date
    assert json_response["target"] == target
    assert "position" in json_response
    assert "velocity" in json_response

def test_get_planet_invalid_params():
    response = client.get("/planet", params={"julian_date": "invalid", "target": "invalid"})
    assert response.status_code == 422

def test_get_current_planet_data():
    response = client.get("/current_planet_data", params={"target": 1})
    assert response.status_code == 200
    json_response = response.json()
    assert "julian_date" in json_response
    assert "target" in json_response
    assert "position" in json_response
    assert "velocity" in json_response

def test_get_zodiac():
    response = client.get("/zodiac", params={"julian_date": 2451545.0, "target": 1})
    assert response.status_code == 200
    json_response = response.json()
    assert "zodiac" in json_response
    assert "longitude" in json_response

def test_get_zodiac_with_ayanamsa():
    response = client.get("/zodiac", params={"julian_date": 2451545.0, "target": 1, "ayanamsa": 23.5})
    assert response.status_code == 200
    json_response = response.json()
    assert "zodiac" in json_response
    assert "longitude" in json_response
    assert json_response["ayanamsa"] == 23.5

def test_rate_limiting():
    for _ in range(6):
        response = client.get("/planet", params={"julian_date": 2451545.0, "target": 1})
    assert response.status_code == 429  # Too Many Requests

# Additional tests for calculate_longitude function
@pytest.mark.parametrize("position, expected_longitude", [
    ([1, 0, 0], 0.0),
    ([0, 1, 0], 90.0),
    ([-1, 0, 0], 180.0),
    ([0, -1, 0], 270.0),
])
def test_calculate_longitude(position, expected_longitude):
    longitude = calculate_longitude(position)
    assert longitude == expected_longitude

# Additional tests for determine_zodiac function
@pytest.mark.parametrize("longitude, ayanamsa, expected_zodiac", [
    (0.0, 0.0, "Aries"),
    (30.0, 0.0, "Taurus"),
    (60.0, 0.0, "Gemini"),
    (90.0, 0.0, "Cancer"),
    (120.0, 0.0, "Leo"),
    (150.0, 0.0, "Virgo"),
    (180.0, 0.0, "Libra"),
    (210.0, 0.0, "Scorpio"),
    (240.0, 0.0, "Sagittarius"),
    (270.0, 0.0, "Capricorn"),
    (300.0, 0.0, "Aquarius"),
    (330.0, 0.0, "Pisces"),
    (0.0, 23.5, "Pisces"),
    (30.0, 23.5, "Aries"),
    (60.0, 23.5, "Taurus"),
    (90.0, 23.5, "Gemini"),
    (120.0, 23.5, "Cancer"),
    (150.0, 23.5, "Leo"),
    (180.0, 23.5, "Virgo"),
    (210.0, 23.5, "Libra"),
    (240.0, 23.5, "Scorpio"),
    (270.0, 23.5, "Sagittarius"),
    (300.0, 23.5, "Capricorn"),
    (330.0, 23.5, "Aquarius"),
])
def test_determine_zodiac(longitude, ayanamsa, expected_zodiac):
    zodiac = determine_zodiac(longitude, ayanamsa)
    assert zodiac == expected_zodiac

# Additional tests for get_distance endpoint
@pytest.mark.parametrize("julian_date, target1, target2, expected_distance", [
    (2451545.0, 1, 2, 0.5),  # Example values, replace with actual expected distances
    (2451545.0, 2, 3, 1.0),
    (2451545.0, 3, 4, 1.5),
])
def test_get_distance(julian_date, target1, target2, expected_distance):
    response = client.get("/distance", params={"julian_date": julian_date, "target1": target1, "target2": target2})
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["julian_date"] == julian_date
    assert json_response["target1"] == target1
    assert json_response["target2"] == target2
    assert "distance" in json_response
    # Note: Replace the expected_distance with actual expected values
    # assert json_response["distance"] == expected_distance