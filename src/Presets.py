import json
import os

DEFAULT_PRESETS = {
    "Preset1": {
        "name": "Preset1",
        "output_size_x": 600,
        "output_size_y": 800,
        "dpi": 300,
        "top_margin": 0.5,
        "bottom_margin": 0.2,
        "left_right_margin": 0.0,
        "unit": "px"
    },
    "Preset2": {
        "name": "Preset2",
        "output_size_x": 800,
        "output_size_y": 1000,
        "dpi": 300,
        "top_margin": 0.4,
        "bottom_margin": 0.2,
        "left_right_margin": 0.0,
        "unit": "px"
    },
    "Preset3": {
        "name": "Preset3",
        "output_size_x": 1080,
        "output_size_y": 1080,
        "dpi": 96,
        "top_margin": 0.3,
        "bottom_margin": 0.3,
        "left_right_margin": 0.0,
        "unit": "px"
    },
    "Preset4": {
        "name": "Preset4",
        "output_size_x": 1080,
        "output_size_y": 1080,
        "dpi": 96,
        "top_margin": 0.5,
        "bottom_margin": 0.5,
        "left_right_margin": 0.0,
        "unit": "px"
    }
}

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "InternalData", "presets.json")

def load_presets():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        save_presets(DEFAULT_PRESETS)
        return DEFAULT_PRESETS

def save_presets(presets):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(presets, f, indent=4, ensure_ascii=False)