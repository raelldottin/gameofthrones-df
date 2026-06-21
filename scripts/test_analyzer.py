"""
Test script for dragon analyzer.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.dragon_analyzer import DragonAnalyzer, DragonData, Dragon, DragonClass


def test_analyzer_creation():
    """Test that analyzer can be created."""
    analyzer = DragonAnalyzer()
    assert analyzer is not None
    print("✓ Analyzer created successfully")


def test_model_creation():
    """Test model creation."""
    dragon = Dragon(
        name="Test Dragon",
        level=30,
        stars=3,
        dragon_class=DragonClass.SENTINEL,
    )
    assert dragon.name == "Test Dragon"
    assert dragon.level == 30
    print("✓ Dragon model created successfully")


def test_dragon_data_model():
    """Test DragonData model."""
    from scripts.dragon_analyzer import DragonData, Dragon, DragonClass, Ability, AbilityType
    
    dragon = Dragon(
        name="Test Dragon",
        level=30,
        stars=3,
        dragon_class=DragonClass.SENTINEL,
    )
    
    ability = Ability(
        name="Test Ability",
        ability_type=AbilityType.COMMAND,
        description="Test description",
    )
    
    data = DragonData(
        dragon=dragon,
        abilities=[ability],
    )
    assert data.dragon.name == "Test Dragon"
    assert len(data.abilities) == 1
    print("✓ DragonData model created successfully")


def main():
    print("Running tests...")
    test_analyzer_creation()
    test_model_creation()
    test_dragon_data_model()
    print("\n✓ All tests passed!")


if __name__ == "__main__":
    main()