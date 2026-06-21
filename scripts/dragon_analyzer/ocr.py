"""
OCR processor for extracting text from screenshots.
"""
import cv2
import numpy as np
import pytesseract
from PIL import Image
from typing import Optional
from loguru import logger

from .config import TESSERACT_CONFIG, PREPROCESS_CONFIG


class OCRProcessor:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or PREPROCESS_CONFIG
        self.tesseract_config = TESSERACT_CONFIG
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Bilateral filter + Otsu threshold + Morphology close (best for this game's UI)
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return thresh
    
    def extract_text(self, image: np.ndarray, region: Optional[tuple] = None) -> str:
        """Extract text from image using Tesseract OCR."""
        if region:
            x, y, w, h = region
            image = image[y:y+h, x:x+w]
        
        processed = self.preprocess(image)
        
        try:
            text = pytesseract.image_to_string(
                processed,
                config=self.tesseract_config
            )
            return text.strip()
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""
    
    def extract_text_from_pil(self, image: Image.Image, region: Optional[tuple] = None) -> str:
        """Extract text from PIL Image."""
        if region:
            image = image.crop(region)
        
        # Convert to OpenCV format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        return self.extract_text(opencv_image)
    
    def find_text_regions(self, image: np.ndarray, min_area: int = 100) -> list[tuple]:
        """Find text regions in image using contour detection."""
        processed = self.preprocess(image)
        
        # Find contours
        contours, _ = cv2.findContours(
            processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= min_area:
                x, y, w, h = cv2.boundingRect(contour)
                # Filter by aspect ratio (text is usually wider than tall)
                aspect_ratio = w / h if h > 0 else 0
                if 0.5 <= aspect_ratio <= 20:
                    regions.append((x, y, w, h))
        
        # Sort by position (top to bottom, left to right)
        regions.sort(key=lambda r: (r[1], r[0]))
        return regions


class DragonScreenshotOCR(OCRProcessor):
    """Specialized OCR for Game of Thrones: Dragon Fire / Winter is Coming screenshots.
    
    Calibrated for 2796x1290 resolution screenshots (iPhone screenshots).
    """
    
    # Known UI regions (absolute pixel coordinates for 2796x1290 resolution)
    # Format: (x, y, w, h) in pixels
    REGIONS = {
        # Battle Report screen
        'battle_header': (0, 0, 2796, 120),
        'left_sidebar': (0, 120, 600, 1170),
        'right_panel': (600, 120, 2196, 1170),
        'round_nav': (0, 120, 200, 1170),
        
        # Right panel sub-regions (relative to right_panel origin)
        'right_header': (0, 0, 2196, 400),
        'right_abilities': (0, 400, 1000, 600),
        'right_battle_grid': (1000, 400, 1000, 600),
        
        # Left sidebar sub-regions
        'left_reports_list': (0, 0, 600, 1170),
        
        # Battle report bottom (dragon info)
        'battle_bottom': (0, 900, 2796, 390),
        
        # Troop Formation screen
        'troop_formation_left': (0, 120, 600, 1170),
        'troop_formation_right': (1800, 150, 900, 300),
        
        # Dragon roster (left sidebar)
        'dragon_roster': (0, 120, 600, 1170),
        
        # Battle report bottom dragon info
        'battle_dragons': (0, 900, 2796, 390),
    }
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        # Image dimensions for coordinate conversion
        self.img_width = 2796
        self.img_height = 1290
    
    def _get_region(self, region_key: str, image: np.ndarray) -> np.ndarray:
        """Extract a region from the image using predefined coordinates."""
        img_h, img_w = image.shape[:2]
        if region_key not in self.REGIONS:
            raise ValueError(f"Unknown region: {region_key}")
        x, y, reg_w, reg_h = self.REGIONS[region_key]
        # Scale if image dimensions differ from calibration
        scale_x = img_w / self.img_width
        scale_y = img_h / self.img_height
        x = int(x * scale_x)
        y = int(y * scale_y)
        reg_w = int(reg_w * scale_x)
        reg_h = int(reg_h * scale_y)
        return image[y:y+reg_h, x:x+reg_w]
    
    def extract_battle_header(self, image: np.ndarray) -> dict:
        """Extract battle header info (target, location, time, buffs)."""
        region = self._get_region('battle_header', image)
        text = self.extract_text(region)
        return self._parse_battle_header(text)
    
    def extract_left_sidebar(self, image: np.ndarray) -> list[dict]:
        """Extract dragon roster from left sidebar."""
        region = self._get_region('left_sidebar', image)
        text = self.extract_text(region)
        return self._parse_left_sidebar(text)
    
    def extract_right_panel(self, image: np.ndarray) -> dict:
        """Extract right panel data (battle details, abilities, grid)."""
        region = self._get_region('right_panel', image)
        text = self.extract_text(region)
        return self._parse_right_panel(text)
    
    def extract_battle_bottom(self, image: np.ndarray) -> list[dict]:
        """Extract dragon info from battle report bottom."""
        region = self._get_region('battle_bottom', image)
        text = self.extract_text(region)
        return self._parse_battle_bottom(text)
    
    def extract_troop_formation(self, image: np.ndarray) -> dict:
        """Extract troop formation screen data."""
        left = self._get_region('troop_formation_left', image)
        right = self._get_region('troop_formation_right', image)
        left_text = self.extract_text(left)
        right_text = self.extract_text(right)
        return self._parse_troop_formation(left_text, right_text)
    
    def extract_battle_dragons(self, image: np.ndarray) -> list[dict]:
        """Extract dragon info from battle report bottom."""
        region = self._get_region('battle_dragons', image)
        text = self.extract_text(region)
        return self._parse_battle_dragons(text)
    
    def _parse_battle_header(self, text: str) -> dict:
        import re
        result = {}
        # Target
        target_match = re.search(r'ATTACKED\s+LV\.\s*(\d+)\s+(\w+)', text)
        if target_match:
            result['target_level'] = int(target_match.group(1))
            result['target_type'] = target_match.group(2)
        # Location
        loc_match = re.search(r'([A-Za-z\s]+)\s*\((\d+),\s*(\d+)\)', text)
        if loc_match:
            result['location'] = loc_match.group(1).strip()
            result['coords'] = (int(loc_match.group(1)), int(loc_match.group(2)))
        # Timestamp
        time_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s+UTC)', text)
        if time_match:
            result['timestamp'] = time_match.group(1)
        # Buffs
        if 'Troop Type Advantage' in text:
            result['troop_advantage'] = True
        if 'Affinity' in text:
            result['affinity'] = True
        return result
    
    def _parse_left_sidebar(self, text: str) -> list[dict]:
        import re
        dragons = []
        # Pattern 1: VICTORY <Tier> Tier <Level> <Stars> <Time>
        # e.g. "VICTORY Iron Tier 9 1 Hour ago" or "VICTORY Iron Tier 9 * 1 Hour ago"
        pattern1 = r'VICTORY\s+(\w+)\s+Tier\s+(\d+)\s+\*?\s*(\d+)\s+(\d+)\s*Hours?\s+ago'
        matches1 = re.findall(pattern1, text, re.IGNORECASE)
        for match in matches1:
            dragons.append({
                'tier': match[0],
                'level': int(match[1]),
                'stars': int(match[2]),
                'time_ago': match[3] + ' hour(s) ago'
            })
        
        # Pattern 2: VICTORY <Tier> Tier <Level> <Stars> <Time> (with star symbol)
        pattern2 = r'VICTORY\s+(\w+)\s+Tier\s+(\d+)\s+\*?\s*(\d+)\s*Stars?\s+(\d+)\s*Hours?\s+ago'
        matches2 = re.findall(pattern2, text, re.IGNORECASE)
        for match in matches2:
            # Check if not already added
            existing = any(d['tier'] == match[0] and d['level'] == int(match[1]) for d in dragons)
            if not existing:
                dragons.append({
                    'tier': match[0],
                    'level': int(match[1]),
                    'stars': int(match[2]),
                    'time_ago': match[3] + ' hours ago'
                })
        return dragons
    
    def _parse_right_panel(self, text: str) -> dict:
        import re
        result = {}
        # Kills
        kills = re.findall(r'[#@]\s*x?(\d+,?\d*)', text)
        if kills:
            result['kills'] = [int(k.replace(',', '')) for k in kills]
        # Commands/Abilities
        abilities = re.findall(r'(Shadowflame|Sudden Strike|Lure|Breath of Fire|Calculated Assault|Whirlwind|Basic Attack)', text)
        result['abilities'] = list(set(abilities))
        return result
    
    def _parse_battle_bottom(self, text: str) -> list[dict]:
        import re
        dragons = []
        # Pattern 1: Name HP/MaxHP Bonus (e.g. "Daemoros 4070 /4668 +20% to Dragon")
        pattern1 = r'(\w+(?:\s+\w+)?)\s+(\d+)\s*/\s*(\d+)\s+([^|]+)'
        matches1 = re.findall(pattern1, text)
        for match in matches1:
            dragons.append({
                'name': match[0].strip(),
                'hp': int(match[1]),
                'max_hp': int(match[2]),
                'bonus': match[3].strip()
            })
        
        # Pattern 2: Just HP/MaxHP (for top row units)
        # e.g. "31 / 4668 / 4970 / 4567" - but this seems to be HP values
        # Pattern 2: Standalone HP values with context
        return dragons
    
    def _parse_troop_formation(self, left_text: str, right_text: str) -> dict:
        import re
        result = {}
        # Parse left sidebar for dragon roster
        pattern = r'(\w+(?:\s+\w+)?)\s+Level\s+(\d+)\s+(\d+)\s*Stars?'
        matches = re.findall(pattern, left_text, re.IGNORECASE)
        result['dragons'] = [
            {'name': m[0].strip(), 'level': int(m[1]), 'stars': int(m[2])}
            for m in matches
        ]
        # Parse right panel for selected dragon
        target = re.search(r'([A-Za-z]+)\s+Lv\.\s*(\d+)\s+(\w+)', right_text)
        if target:
            result['selected'] = {
                'name': target.group(1),
                'level': int(target.group(2)),
                'type': target.group(3)
            }
        return result
    
    def _parse_battle_dragons(self, text: str) -> list[dict]:
        import re
        dragons = []
        # Pattern: Name HP/MaxHP Bonus
        # e.g. "Daemoros 4070 /4668 +20% to Dragon"
        pattern = r'(\w+)\s+(\d+)\s*/\s*(\d+)\s+([^|]+)'
        matches = re.findall(pattern, text)
        for match in matches:
            dragons.append({
                'name': match[0].strip(),
                'hp': int(match[1]),
                'max_hp': int(match[2]),
                'bonus': match[3].strip()
            })
        return dragons


def create_ocr_processor(config: Optional[dict] = None) -> OCRProcessor:
    """Factory function to create OCR processor."""
    return OCRProcessor(config)