from __future__ import annotations
from db import events as events_db
from dm.deepseek_client import chat
import config


async def maybe_compress_memory(campaign_id: str) -> bool:
    """Check if compression is needed. Returns True if compression ran."""
    summary = events_db.get_latest_summary(campaign_id)
    covered_up_to = summary["covers_up_to_event"] if summary else 0
    new_count = events_db.count_events_since_last_summary(campaign_id, covered_up_to)

    if new_count < config.MEMORY_COMPRESSION_THRESHOLD:
        return False

    uncompressed = events_db.get_events_after(campaign_id, covered_up_to)
    if not uncompressed:
        return False

    last_sequence = uncompressed[-1]["sequence_num"]
    event_text = "\n".join(
        f"[{e['event_type']}] {e['speaker']}: {e['content']}"
        for e in uncompressed
    )

    messages = [
        {
            "role": "system",
            "content": (
                "你是一個DnD遊戲記錄員。請將以下遊戲事件壓縮成簡潔的重點摘要，"
                "用繁體中文廣東話書寫。保留所有重要的：玩家決定、NPC互動、獲得物品、"
                "重要戰鬥結果、已揭露劇情。格式：每點一行，用「-」開頭。最多20點。"
            ),
        },
        {"role": "user", "content": f"請壓縮以下遊戲記錄：\n\n{event_text}"},
    ]

    summary_text = await chat(messages, temperature=0.3, max_tokens=800)
    events_db.save_memory_summary(campaign_id, summary_text, last_sequence)
    return True


async def generate_recap(campaign_id: str) -> str:
    """Generate a dramatic player-facing recap of the adventure so far."""
    summary = events_db.get_latest_summary(campaign_id)
    recent = events_db.get_recent_events(campaign_id, 10)
    recent_text = "\n".join(f"{e['speaker']}: {e['content']}" for e in recent)
    prior_summary = summary["summary_text"] if summary else "（冒險剛開始）"

    messages = [
        {
            "role": "system",
            "content": (
                "你是一位DnD地下城主，請用生動的廣東話繁體中文，"
                "為玩家朗讀一段「之前的故事」回顧，像電視劇的上集回顧一樣，"
                "大約150-200字，充滿戲劇感。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"早期事件摘要：\n{prior_summary}\n\n"
                f"最近發生的事：\n{recent_text}\n\n"
                "請生成回顧。"
            ),
        },
    ]
    return await chat(messages, temperature=0.8, max_tokens=600)