from __future__ import annotations
from typing import Optional
from db.supabase_client import get_client


def create_character(campaign_id: str, user_id: int, username: str, sheet: dict) -> dict:
    db = get_client()
    result = db.table("characters").insert({
        "campaign_id": campaign_id,
        "user_id": str(user_id),
        "username": username,
        "name": sheet["name"],
        "class": sheet["class"],
        "race": sheet["race"],
        "background": sheet.get("background", ""),
        "level": 1,
        "hp": sheet["hp"],
        "max_hp": sheet["hp"],
        "stats": sheet["stats"],
        "saving_throws": sheet.get("saving_throws", {}),
        "skills": sheet.get("skills", {}),
        "inventory": sheet.get("inventory", []),
        "spells": sheet.get("spells", {}),
        "spell_slots": sheet.get("spell_slots", {}),
        "conditions": [],
        "emoji": sheet.get("emoji", "🧙"),
        "proficiency_bonus": 2,
        "armor_class": sheet.get("armor_class", 10),
        "speed": sheet.get("speed", 30),
        "personality": sheet.get("personality", ""),
    }).execute()
    return result.data[0]


def get_characters(campaign_id: str) -> list[dict]:
    db = get_client()
    result = (
        db.table("characters")
        .select("*")
        .eq("campaign_id", campaign_id)
        .eq("active", True)
        .execute()
    )
    return result.data


def get_character_by_user(campaign_id: str, user_id: int) -> Optional[dict]:
    db = get_client()
    result = (
        db.table("characters")
        .select("*")
        .eq("campaign_id", campaign_id)
        .eq("user_id", str(user_id))
        .eq("active", True)
        .execute()
    )
    return result.data[0] if result.data else None


def update_character(char_id: str, updates: dict) -> dict:
    db = get_client()
    result = db.table("characters").update(updates).eq("id", char_id).execute()
    return result.data[0]


def update_hp(char_id: str, new_hp: int) -> dict:
    return update_character(char_id, {"hp": new_hp})


def add_condition(char_id: str, condition: str, current_conditions: list) -> dict:
    if condition not in current_conditions:
        current_conditions.append(condition)
    return update_character(char_id, {"conditions": current_conditions})


def remove_condition(char_id: str, condition: str, current_conditions: list) -> dict:
    updated = [c for c in current_conditions if c != condition]
    return update_character(char_id, {"conditions": updated})


def add_to_inventory(char_id: str, item: str, current_inventory: list) -> dict:
    current_inventory.append(item)
    return update_character(char_id, {"inventory": current_inventory})