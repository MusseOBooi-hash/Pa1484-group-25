try:
    import requests
except ImportError:
    import urequests as requests

from secrets import TRAFIKLAB_KEY

API_URL = "https://realtime-api.trafiklab.se/v1/departures/{}?key={}"

# Stops the user can choose between (name shown in the dropdown, Trafiklab id)
STOPS = [
    {"name": "Karlskrona C", "id": "740098084"},
    {"name": "Campus Grasvik", "id": "740032188"},
    {"name": "Karlskrona centrum", "id": "740023372"},
    {"name": "Fisktorget", "id": "740020700"},
    {"name": "Bergasa station", "id": "740001537"},
    {"name": "Amiralen", "id": "740031800"},
    {"name": "Lyckeby centrum", "id": "740000663"},
    {"name": "Nattraby centrum", "id": "740024966"},
    {"name": "Rodeby centrum", "id": "740000521"},
    {"name": "Jamjo centrum", "id": "740000333"},
]

# Trafiklab transport modes translated to the names used in the dropdown
TRANSPORT_TYPES = {"BUS": "Bus", "TRAIN": "Train", "BOAT": "Ferry"}

# The display font has no Swedish letters, so they are replaced
LETTERS = {"å": "a", "ä": "a", "ö": "o", "Å": "A", "Ä": "A", "Ö": "O",
           "é": "e", "ø": "o", "Ø": "O"}


# The function replaces letters the display font cannot show
def to_ascii(text):
    return "".join(LETTERS.get(letter, letter) for letter in text)


# The function turns one Trafiklab departure into a row for the table
def parse_departure(item):
    time_text = item.get("realtime") or item.get("scheduled") or ""
    delay_minutes = (item.get("delay") or 0) // 60
    if item.get("canceled"):
        status = "Cancelled"
    elif delay_minutes > 0:
        status = "+{} min".format(delay_minutes)
    else:
        status = "On time"
    route = item.get("route") or {}
    return {
        "Time": time_text[11:16],
        "Line": to_ascii(route.get("designation") or ""),
        "Destination": to_ascii(route.get("direction") or ""),
        "Status": status,
        "Type": TRANSPORT_TYPES.get(route.get("transport_mode"), "Other"),
    }


# The function turns a whole Trafiklab answer into a list of table rows
def parse_departures(data):
    return [parse_departure(item) for item in data.get("departures", [])]


# The function gets live departures for a stop, or None if it fails
def get_departures(stop_id):
    try:
        response = requests.get(API_URL.format(stop_id, TRAFIKLAB_KEY))
        try:
            if response.status_code != 200:
                return None
            data = response.json()
        finally:
            response.close()
        return parse_departures(data)
    except Exception:
        return None