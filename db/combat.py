from __future__ import annotations
from typing import Optional
from db.supabase_client import get_client


def create_combat_session(campaign_id: str, grid_width: int = 10, grid_height: int = 10) -> dict:
    db = get_client()
    result = db.table("combat_sessions").insert({
        "campaign_id": campaign_id,
        "status": "initiative",
        "initiative_order": [],
        "current_turn": 0,
        "round_num": 1,
        "grid_width": grid_width,
        "grid_height": grid_height,
    }).execute()
    return result.data[0]


def get_active_combat(campaign_id: str) -> Optional[dict]:
    db = get_client()
    result = (
        db.table("combat_sessions")
        .select("*")
        .eq("campaign_id", campaign_id)
        .neq("status", "ended")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def update_combat(combat_id: str, updates: dict) -> dict:
    db = get_client()
    result = db.table("combat_sessions").update(updates).eq("id", combat_id).execute()
    return result.data[0]


def end_combat(combat_id: str) -> None:
    update_combat(combat_id, {"status": "ended"})


def add_entity(combat_id, entity_type, name, x, y, hp, max_hp, ac, user_id=None, char_id=None, emoji="👾") -> dict:
    db = get_client()
    result = db.table("combat_entities").insert({
        "combat_id": combat_id, "entity_type": entity_type, "name": name,
        "x": x, "y": y, "hp": hp, "max_hp": max_hp, "ac": ac,
        "user_id": user_id, "char_id": char_id, "emoji": emoji,
        "conditions": [], "active": True,
    }).execute()
    return result.data[0]


def get_entities(combat_id: str) -> list[dict]:
    db = get_client()
    result = (
        db.table("combat_entities")
        .select("*")
        .eq("combat_id", combat_id)
        .eq("active", True)
        .execute()
    )
    return result.data


def update_entity(entity_id: str, updates: dict) -> dict:
    db = get_client()
    result = db.table("combat_entities").update(updates).eq("id", entity_id).execute()
    return result.data[0]


def move_entity(entity_id: str, x: int, y: int) -> dict:
    return update_entity(entity_id, {"x": x, "y": y})


def damage_entity(entity_id: str, new_hp: int) -> dict:
    return update_entity(entity_id, {"hp": new_hp})


def remove_entity(entity_id: str) -> None:
    update_entity(entity_id, {"active": False})