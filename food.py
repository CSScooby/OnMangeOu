import requests
import json
from app import GOOGLE_API_KEY  # Import de la clé API

def get_something(lat, lng, type):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=2000&type={type}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    type = response.json()
    with open('restaurants_debug.json', 'w', encoding='utf-8') as f:
        json.dump(type, f, ensure_ascii=False, indent=4)
    return type['results']
