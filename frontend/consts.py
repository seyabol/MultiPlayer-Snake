import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config_file = os.path.join(BASE_DIR, 'config.json')
if os.path.exists(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
else:
    data = {}

# Game settings
back_color = tuple(data.get('back_color', [30, 30, 40]))
fruit_color = tuple(data.get('fruit_color', [255, 60, 60]))
block_color = tuple(data.get('block_color', [139, 69, 19]))

cell_size = int(data.get('cell_size', 34))
table_size = int(data.get('table_size', 22))
block_cells = data.get('block_cells', [])

height = int(data.get('height', 900))
width = int(data.get('width', 1200))

snakes = data.get('snakes', [])

server_url = os.getenv('SERVER_URL', data.get('server_url', 'http://localhost:3000'))

# UI Colors
ui_primary = (100, 150, 255)
ui_secondary = (70, 70, 90)
ui_text = (255, 255, 255)
ui_success = (0, 255, 100)
ui_error = (255, 50, 50)
ui_warning = (255, 200, 0)


def grid_origin():
    grid_w = table_size * cell_size
    grid_h = table_size * cell_size

    sx = (width - grid_w) // 2
    sy = 150

    if sy + grid_h > height - 30:
        sy = max(110, (height - grid_h) // 2)

    return sx, sy


# Controls use pygame.key.name() values
DEFAULT_CONTROLS = {
    'up': 'UP', 'down': 'DOWN', 'left': 'LEFT', 'right': 'RIGHT',
    'w': 'UP', 's': 'DOWN', 'a': 'LEFT', 'd': 'RIGHT',
}
