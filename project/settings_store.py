import json

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {"transport_type": "All"}


def save_settings(settings):
    'Function: Saves the settings to a file on the device'
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file)


def load_settings():
    'Function: Loads saved settings, or returns defaults if none exist'
    try:
        with open(SETTINGS_FILE, "r") as file:
            return json.load(file)
    except (OSError, ValueError):
        return dict(DEFAULT_SETTINGS)