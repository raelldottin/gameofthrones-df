"""
Data models for dragon analysis.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class DragonClass(str, Enum):
    SENTINEL = "Sentinel"
    WARRIOR = "Warrior"
    HUNTER = "Hunter"
    CHAMPION = "Champion"


class DragonRarity(str, Enum):
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"


class AbilityType(str, Enum):
    COMMAND = "Command"
    HABIT = "Habit"
    PASSIVE = "Passive"


class DamageType(str, Enum):
    PHYSICAL = "Physical"
    TACTICAL = "Tactical"
    FIRE = "Fire"
    ICE = "Ice"
    POISON = "Poison"


class Dragon(BaseModel):
    name: str
    level: int
    stars: int = Field(ge=0, le=5)
    dragon_class: DragonClass
    health: Optional[int] = None
    attack: Optional[int] = None
    defense: Optional[int] = None
    speed: Optional[int] = None
    energy: Optional[int] = None
    max_energy: Optional[int] = None


class Ability(BaseModel):
    name: str
    ability_type: AbilityType
    damage_type: Optional[DamageType] = None
    damage_rate: Optional[float] = None
    description: str
    cooldown: Optional[int] = None
    trigger_condition: Optional[str] = None
    scaling_stat: Optional[str] = None
    mitigation_stat: Optional[str] = None
    level: int = 1
    max_level: int = 5


class Habit(BaseModel):
    name: str
    trigger: str
    effect: str
    stats: dict[str, list[float]] = Field(default_factory=dict)
    cost: dict[str, int] = Field(default_factory=dict)
    level: int = 1
    max_level: int = 5


class DragonData(BaseModel):
    dragon: Dragon
    abilities: list[Ability] = Field(default_factory=list)
    habits: list[Habit] = Field(default_factory=list)
    loyal_bond: Optional[dict] = None
    source_image: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ArmyComposition(BaseModel):
    name: str
    vanguard: str
    left_flank: str
    right_flank: str
    troop_type: str
    target_type: str
    validated: bool = False
    win_rate: Optional[float] = None
    notes: str = ""