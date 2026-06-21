"""
Main analyzer module for dragon screenshot analysis.
"""
import json
from pathlib import Path
from typing import Optional
from loguru import logger

from .models import DragonData, ArmyComposition
from .ocr import DragonScreenshotOCR, create_ocr_processor
from .config import SCREENSHOT_DIR, OUTPUT_DIR


class DragonAnalyzer:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or OUTPUT_DIR
        self.ocr = DragonScreenshotOCR()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "dragons").mkdir(exist_ok=True)
        (self.output_dir / "battle-logs").mkdir(exist_ok=True)
        (self.output_dir / "analysis").mkdir(exist_ok=True)
    
    def analyze_screenshot(self, image_path: Path) -> Optional[DragonData]:
        """Analyze a single screenshot and extract dragon data."""
        logger.info(f"Analyzing screenshot: {image_path}")
        
        try:
            # Load image
            import cv2
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            
            # Extract data using OCR
            dragon_name = self.ocr.extract_dragon_name(image)
            level = self.ocr.extract_level(image)
            stats = self.ocr.extract_stats(image)
            abilities = self.ocr.extract_ability_info(image)
            
            # Create dragon data model
            from .models import Dragon, DragonClass, DragonData, Ability, AbilityType, DamageType
            
            dragon = Dragon(
                name=dragon_name,
                level=level or 1,
                stars=0,  # Would need OCR for stars
                dragon_class=DragonClass.SENTINEL,  # Default
            )
            
            # Parse abilities
            ability_models = []
            for ability_data in abilities:
                ability = Ability(
                    name=ability_data.get("name", "Unknown"),
                    ability_type=AbilityType.COMMAND,
                    description=ability_data.get("description", ""),
                )
                ability_models.append(ability)
            
            dragon_data = DragonData(
                dragon=dragon,
                abilities=ability_models,
                source_image=str(image_path),
                confidence=0.7,  # Default confidence
            )
            
            # Save to file
            output_file = self.output_dir / "dragons" / f"{dragon_name.lower().replace(' ', '_')}.json"
            with open(output_file, 'w') as f:
                json.dump(dragon_data.model_dump(), f, indent=2)
            
            logger.info(f"Saved dragon data to {output_file}")
            return dragon_data
            
        except Exception as e:
            logger.error(f"Failed to analyze {image_path}: {e}")
            return None
    
    def batch_analyze(self, directory: Path, pattern: str = "IMG_*.png") -> list[DragonData]:
        """Analyze all screenshots in a directory."""
        results = []
        for image_path in directory.glob(pattern):
            if image_path.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
                result = self.analyze_screenshot(image_path)
                if result:
                    results.append(result)
        return results
    
    def save_analysis(self, data: dict, filename: str) -> Path:
        """Save analysis results to file."""
        output_file = self.output_dir / "analysis" / filename
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        return output_file
    
    def load_dragon_data(self, name: str) -> Optional[DragonData]:
        """Load dragon data from file."""
        from .models import DragonData
        file_path = self.output_dir / "dragons" / f"{name.lower().replace(' ', '_')}.json"
        if file_path.exists():
            with open(file_path) as f:
                return DragonData.model_validate_json(f.read())
        return None
    
    def export_army_compositions(self) -> Path:
        """Export current army compositions to file."""
        # This would be populated from user input
        output_file = self.output_dir / "analysis" / "army_compositions.json"
        # Placeholder for actual army data
        data = {
            "armies": [],
            "last_updated": "2024-01-01",
        }
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        return output_file


def create_analyzer(output_dir: Optional[Path] = None) -> DragonAnalyzer:
    """Factory function to create analyzer instance."""
    return DragonAnalyzer(output_dir)