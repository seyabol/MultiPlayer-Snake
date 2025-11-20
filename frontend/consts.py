import json
import os

# Load configuration
config_file = 'config.json'
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        data = json.load(f)
else:
    # Default configuration
    data = {
        "cell_size": 30,
        "back_color": [30, 30, 40],
        "fruit_color": [255, 60, 60],
        "block_color": [139, 69, 19],
        "block_cells": [
            [14, 14], [13, 14], [12, 14], [15, 14], [16, 14]
        ],
        "sx": 30,
        "sy": 50,
        "table_size": 20,
        "height": 800,
        "width": 800,
        "server_url": "http://localhost:3000",
        "snakes": [
            {
                "keys": {
                    "w": "UP",
                    "s": "DOWN",
                    "a": "LEFT",
                    "d": "RIGHT"
                },
                "sx": 10,
                "sy": 10,
                "color": [0, 240, 0],
                "direction": "LEFT"
            },
            {
                "keys": {
                    "i": "UP",
                    "k": "DOWN",
                    "j": "LEFT",
                    "l": "RIGHT"
                },
                "sx": 1,
                "sy": 15,
                "color": [0, 120, 240],
                "direction": "RIGHT"
            }
        ]
    }

# Game settings
back_color = tuple(data['back_color'])
fruit_color = tuple(data['fruit_color'])   
block_color = tuple(data['block_color'])
cell_size = data['cell_size']
block_cells = data['block_cells']
table_size = data['table_size']
height = data['height']
width = data['width']
snakes = data['snakes']
sx = data['sx']
sy = data['sy']
server_url = data.get('server_url', 'http://localhost:3000')

# UI Colors
ui_primary = (100, 150, 255)
ui_secondary = (70, 70, 90)
ui_text = (255, 255, 255)
ui_success = (0, 255, 100)
ui_error = (255, 50, 50)
ui_warning = (255, 200, 0)