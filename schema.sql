-- ============================================================
-- DnD AI DM Bot - Supabase Schema
-- Run this in your Supabase SQL editor
-- ============================================================

-- Enable UUID generation
create extension if not exists "pgcrypto";

-- ============================================================
-- 1. CAMPAIGNS
-- ============================================================
create table if not exists campaigns (
    id              uuid primary key default gen_random_uuid(),
    chat_id         text not null,
    module          text not null default 'lmop',
    status          text not null default 'character_creation',
                    -- character_creation | active | paused | ended
    current_location text not null default 'phandalin_outskirts',
    act             int not null default 1,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

create index if not exists idx_campaigns_chat_id on campaigns(chat_id);
create index if not exists idx_campaigns_status  on campaigns(status);

-- ============================================================
-- 2. CHARACTERS
-- ============================================================
create table if not exists characters (
    id               uuid primary key default gen_random_uuid(),
    campaign_id      uuid not null references campaigns(id) on delete cascade,
    user_id          text not null,
    username         text not null,
    name             text not null,
    class            text not null,
    race             text not null,
    background       text not null default '',
    level            int not null default 1,
    hp               int not null default 10,
    max_hp           int not null default 10,
    stats            jsonb not null default '{}',
    saving_throws    jsonb not null default '{}',
    skills           jsonb not null default '{}',
    inventory        jsonb not null default '[]',
    spells           jsonb not null default '{}',
    spell_slots      jsonb not null default '{}',
    conditions       jsonb not null default '[]',
    emoji            text not null default '🧙',
    proficiency_bonus int not null default 2,
    armor_class      int not null default 10,
    speed            int not null default 30,
    personality      text not null default '',
    active           boolean not null default true,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now()
);

create index if not exists idx_characters_campaign on characters(campaign_id);
create index if not exists idx_characters_user     on characters(user_id);
create unique index if not exists idx_characters_campaign_user
    on characters(campaign_id, user_id) where active = true;

-- ============================================================
-- 3. EVENTS (session log)
-- ============================================================
create table if not exists events (
    id           uuid primary key default gen_random_uuid(),
    campaign_id  uuid not null references campaigns(id) on delete cascade,
    sequence_num bigint generated always as identity,
    speaker      text not null,
    content      text not null,
    event_type   text not null default 'narrative',
                 -- narrative | player_action | combat | system | ooc
    created_at   timestamptz not null default now()
);

create index if not exists idx_events_campaign_seq
    on events(campaign_id, sequence_num);

-- ============================================================
-- 4. MEMORY SUMMARIES (compressed older history)
-- ============================================================
create table if not exists memory_summaries (
    id                  uuid primary key default gen_random_uuid(),
    campaign_id         uuid not null references campaigns(id) on delete cascade,
    summary_text        text not null,
    covers_up_to_event  bigint not null default 0,
    created_at          timestamptz not null default now()
);

create index if not exists idx_memory_campaign on memory_summaries(campaign_id);

-- ============================================================
-- 5. WORLD STATE (key-value facts about the campaign world)
-- ============================================================
create table if not exists world_state (
    id           uuid primary key default gen_random_uuid(),
    campaign_id  uuid not null references campaigns(id) on delete cascade,
    key          text not null,
    value        text not null,
    updated_at   timestamptz not null default now(),
    unique(campaign_id, key)
);

create index if not exists idx_world_state_campaign on world_state(campaign_id);

-- ============================================================
-- 6. COMBAT SESSIONS
-- ============================================================
create table if not exists combat_sessions (
    id               uuid primary key default gen_random_uuid(),
    campaign_id      uuid not null references campaigns(id) on delete cascade,
    status           text not null default 'initiative',
                     -- initiative | active | ended
    initiative_order jsonb not null default '[]',
    current_turn     int not null default 0,
    round_num        int not null default 1,
    grid_width       int not null default 10,
    grid_height      int not null default 10,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now()
);

create index if not exists idx_combat_campaign on combat_sessions(campaign_id);

-- ============================================================
-- 7. COMBAT ENTITIES (players + monsters on the grid)
-- ============================================================
create table if not exists combat_entities (
    id           uuid primary key default gen_random_uuid(),
    combat_id    uuid not null references combat_sessions(id) on delete cascade,
    entity_type  text not null,  -- player | monster | npc
    name         text not null,
    x            int not null default 0,
    y            int not null default 0,
    hp           int not null default 10,
    max_hp       int not null default 10,
    ac           int not null default 10,
    user_id      text,           -- set for player entities
    char_id      uuid,           -- FK to characters for players
    emoji        text not null default '👾',
    conditions   jsonb not null default '[]',
    active       boolean not null default true,
    created_at   timestamptz not null default now()
);

create index if not exists idx_entities_combat  on combat_entities(combat_id);
create index if not exists idx_entities_active  on combat_entities(combat_id, active);

-- ============================================================
-- Auto-update updated_at triggers
-- ============================================================
create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create or replace trigger trg_campaigns_updated
    before update on campaigns
    for each row execute function update_updated_at();

create or replace trigger trg_characters_updated
    before update on characters
    for each row execute function update_updated_at();

create or replace trigger trg_combat_updated
    before update on combat_sessions
    for each row execute function update_updated_at();