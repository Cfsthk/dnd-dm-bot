from __future__ import annotations
from db.supabase_client import get_client
import config


def log_event(campaign_id: str, speaker: str, content: str, event_type: str = "narrative") -> dict:
    db = get_client()
    result = db.table("events").insert({
        "campaign_id": campaign_id,
        "speaker": speaker,
        "content": content,
        "event_type": event_type,
    }).execute()
    return result.data[0]


def get_recent_events(campaign_id: str, limit: int = None) -> list[dict]:
    if limit is None:
        limit = config.MAX_RECENT_EVENTS
    db = get_client()
    result = (
        db.table("events")
        .select("*")
        .eq("campaign_id", campaign_id)
        .order("sequence_num", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(result.data))


def get_events_after(campaign_id: str, after_sequence: int) -> list[dict]:
    db = get_client()
    result = (
        db.table("events")
        .select("*")
        .eq("campaign_id", campaign_id)
        .gt("sequence_num", after_sequence)
        .order("sequence_num")
        .execute()
    )
    return result.data


def count_events_since_last_summary(campaign_id: str, last_summary_event: int) -> int:
    db = get_client()
    result = (
        db.table("events")
        .select("id", count="exact")
        .eq("campaign_id", campaign_id)
        .gt("sequence_num", last_summary_event)
        .execute()
    )
    return result.count or 0


def save_memory_summary(campaign_id: str, summary_text: str, covers_up_to_event: int) -> dict:
    db = get_client()
    result = db.table("memory_summaries").insert({
        "campaign_id": campaign_id,
        "summary_text": summary_text,
        "covers_up_to_event": covers_up_to_event,
    }).execute()
    return result.data[0]


def get_latest_summary(campaign_id: str) -> dict | None:
    db = get_client()
    result = (
        db.table("memory_summaries")
        .select("*")
        .eq("campaign_id", campaign_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None