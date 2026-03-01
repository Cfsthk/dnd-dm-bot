from __future__ import annotations
from typing import Optional
from db.supabase_client import get_client


def create_campaign(chat_id: int, module: str = "lmop") -> dict:
    db = get_client()
    result = db.table("campaigns").insert({
        "chat_id": str(chat_id),
        "module": module,
        "status": "character_creation",
        "current_location": "phandalin_outskirts",
        "act": 1,
    }).execute()
    return result.data[0]


def get_active_campaign(chat_id: int) -> Optional[dict]:
    db = get_client()
    result = (
        db.table("campaigns")
        .select("*")
        .eq("chat_id", str(chat_id))
        .neq("status", "ended")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def update_campaign(campaign_id: str, updates: dict) -> dict:
    db = get_client()
    result = db.table("campaigns").update(updates).eq("id", campaign_id).execute()
    return result.data[0]


def end_campaign(campaign_id: str) -> None:
    update_campaign(campaign_id, {"status": "ended"})


def set_world_state(campaign_id: str, key: str, value: str) -> None:
    db = get_client()
    db.table("world_state").upsert(
        {"campaign_id": campaign_id, "key": key, "value": value},
        on_conflict="campaign_id,key",
    ).execute()


def get_world_state(campaign_id: str) -> dict:
    db = get_client()
    result = db.table("world_state").select("key,value").eq("campaign_id", campaign_id).execute()
    return {row["key"]: row["value"] for row in result.data}