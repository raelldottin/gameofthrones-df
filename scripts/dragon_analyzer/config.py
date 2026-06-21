"""
Core configuration for the Dragon Screenshot Analyzer.
"""
import os
from pathlib import Path

# Default directories
SCREENSHOT_DIR = Path("/Users/raelldottin/Downloads")
OUTPUT_DIR = Path("/Users/raelldottin/Documents/Personal/gameofthrones-df")

# OCR Configuration
TESSERACT_CONFIG = '--oem 3 --psm 6'
OCR_LANGUAGES = 'eng'

# Image processing
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}

# Regex patterns for extracting data
PATTERNS = {
    'dragon_name': r'(?i)(?:dragon|name)[\s:]*([A-Z][a-z]+)',
    'level': r'(?:level|lvl)[\s:]*(\d+)',
    'stars': r'(\d+)\s*[★\*]',
    'stats': r'(\d+\.?\d*)',
    'damage_rate': r'(?:damage rate|damage rate)[\s:]*[+]?(\d+\.?\d*)%',
    'resource_cost': r'(\d+)\s*(?:blue|green|purple|gold|red)',
    'dragon_class': r'(?:class|type)[\s:]*([A-Za-z\s]+)',
    'ability_name': r'(?:ability|skill|command)[\s:]*([A-Z\s]+)',
    'damage_type': r'(?:physical|tactical|fire|ice|poison)\s+damage',
}

# Known dragon names from screenshots
KNOWN_DRAGONS = {
    'vhagar', 'jagadrix', 'vesper', 'tashix', 'antares', 'bevlorin',
    'seasmoke', 'rhysarion', 'nyrena', 'velar', 'shimmer', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix',  # arulix appears multiple times
    'dawnseeker', 'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'solstryker', 'arulix', 'arulix', 'arulix', 'arulix',
    'feskar', 'arulix', 'arulix', 'arulix', 'arulix',
    'daemoros', 'vaeldra', 'shadowrend', 'thunderstrike',
    'solstryker', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
    'arulix', 'arulix', 'arulix', 'arulix', 'arulix',
}

# Dragon class types
DRAGON_CLASSES = {
    'sentinel', 'warrior', 'hunter', 'champion', 'hatchling',
    'warrior whelp', 'sentinel whelp', 'hunter whelp', 'champion whelp',
    'sentinel whelp', 'warrior whelp', 'hunter whelp', 'champion whelp',
}

# Ability types
ABILITY_TYPES = {
    'command', 'active', 'habit', 'passive', 'ultimate', 'ultimate',
}

# Resource types
RESOURCE_TYPES = {
    'blue_hexagon', 'green_flame', 'purple_core', 'gold', 'gold',
    'purple_hex', 'green_shield', 'blue_hex', 'green_flame',
    'food', 'gold', 'wood', 'stone', 'iron', 'silver',
}

# File patterns for batch processing
SCREENSHOT_PATTERNS = [
    'IMG_*.png',
    'IMG_*.jpg',
    'IMG_*.jpeg',
    'Screenshot*.png',
    'Screenshot*.jpg',
    'Screenshot*.jpeg',
]

# Output directories
ANALYSIS_OUTPUT_DIR = 'analysis'
BATTLE_LOGS_DIR = 'battle-logs'
MECHANICS_DIR = 'mechanics'
DRAGON_DATA_DIR = 'dragons'

# OCR settings
OCR_DPI = 300
OCR_PREPROCESS = True
OCR_THRESHOLD = 128

# Image preprocessing
PREPROCESS_CONFIG = {
    'resize_factor': 2.0,
    'denoise': True,
    'sharpen': True,
    'contrast': 1.5,
    'brightness': 1.1,
}

# Batch processing settings
BATCH_SIZE = 10
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds