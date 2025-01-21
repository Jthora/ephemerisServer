from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import FastAPI, Request
from jplephem.spk import SPK
from datetime import datetime, timezone
import numpy as np
import asyncio

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
kernel = SPK.open('./ephemeris/de440s.bsp')

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    response = await call_next(request)
    return response

@app.get("/planet")
@limiter.limit("5/second")
async def get_planet(request: Request, julian_date: float, target: int, observer: int = 0):
    """Fetch planetary position for a given Julian Date and target."""
    position, velocity = kernel[observer, target].compute_and_differentiate(julian_date)
    return {
        "julian_date": julian_date,
        "target": target,
        "position": position.tolist(),  # Convert NumPy array to list
        "velocity": velocity.tolist(),
    }

@app.get("/current_planet_data")
async def get_current_planet_data(target: int, observer: int = 0):
    """Fetch planetary position for the current time."""
    now = datetime.now(timezone.utc)
    julian_date = 2451545.0 + (now - datetime(2000, 1, 1, 12, tzinfo=timezone.utc)).total_seconds() / 86400.0
    position, velocity = kernel[observer, target].compute_and_differentiate(julian_date)
    return {
        "julian_date": julian_date,
        "target": target,
        "position": position.tolist(),
        "velocity": velocity.tolist(),
    }

def calculate_longitude(position):
    # Convert radians to degrees and adjust range to [0, 360]
    longitude = np.degrees(np.arctan2(position[1], position[0]))
    if longitude < 0:
        longitude += 360
    return longitude

def determine_zodiac(longitude, ayanamsa=0.0):
    # Adjust longitude for ayanamsa
    sidereal_longitude = (longitude - ayanamsa) % 360
    # Determine the zodiac sign based on the adjusted longitude
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    index = int(sidereal_longitude / 30)
    return signs[index]

@app.get("/zodiac")
async def get_zodiac(julian_date: float, target: int, ayanamsa: float = 0.0):
    position, _ = kernel[0, target].compute_and_differentiate(julian_date)
    longitude = calculate_longitude(position)
    zodiac = determine_zodiac(longitude, ayanamsa)
    return {"zodiac": zodiac, "longitude": longitude, "ayanamsa": ayanamsa}

@app.get("/distance")
async def get_distance(julian_date: float, target1: int, target2: int):
    """Calculate the distance between two planets for a given Julian Date."""
    position1, _ = kernel[0, target1].compute_and_differentiate(julian_date)
    position2, _ = kernel[0, target2].compute_and_differentiate(julian_date)
    distance = np.linalg.norm(position1 - position2)
    return {
        "julian_date": julian_date,
        "target1": target1,
        "target2": target2,
        "distance": distance
    }