# Kreeda Backend - Database Schema Design
**Version:** 1.0  
**Date:** October 26, 2025  
**Sport Module:** Cricket (MVP)  
**Author:** System Architecture Team

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Principles](#core-principles)
3. [Schema Layers](#schema-layers)
4. [Detailed Table Specifications](#detailed-table-specifications)
5. [Relationships & Constraints](#relationships--constraints)
6. [Indexes & Performance](#indexes--performance)
7. [Data Flow](#data-flow)
8. [Validation Rules](#validation-rules)

---

## Architecture Overview

### Multi-Tier Data Model
```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: Identity & Authentication                     │
│  - users, user_profiles                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: Sport Profiles                                │
│  - sport_profiles, cricket_player_profiles              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: Teams & Memberships                           │
│  - teams, team_memberships                              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: Matches & Officials                           │
│  - matches, match_officials, match_playing_xi           │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: Live Match Progression                        │
│  - innings, overs, balls, wickets                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 6: Player Performance (Real-time)                │
│  - batting_innings, bowling_figures, partnerships       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 7: Scoring Integrity (Event Sourcing)            │
│  - scoring_events, scoring_disputes, scoring_consensus  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 8: Aggregates & Archives                         │
│  - match_summaries, match_archives                      │
└─────────────────────────────────────────────────────────┘
```

---

## Core Principles

### 1. Event Sourcing for Scoring
- Every scoring action is an immutable event
- Current state derived from event log
- Enables complete audit trail
- Supports replay and dispute resolution

### 2. Flexible Configuration
- JSONB for sport-specific rules
- Support for 3v3 to 11v11 matches
- Customizable match formats
- Preset templates for quick setup

### 3. Multi-Validator Consensus
- Adaptive validation (1-3 validators)
- Majority voting for disputes
- Cryptographic hash chaining
- 99.89% accuracy potential

### 4. Performance Optimization
- Real-time aggregates (updated per ball)
- Strategic indexing
- Materialized views for heavy queries
- Smart archival (7-day retention for casual)

### 5. Multi-Sport Ready
- Sport-agnostic core tables
- Sport-specific extension tables
- ENUM for sport_type everywhere
- Easy to add football, hockey, etc.

---

## Schema Layers

---

## LAYER 1: Identity & Authentication

### 1.1 `users` (Existing - Minimal Changes)
*Core user authentication and authorization*

```sql
CREATE TYPE user_role AS ENUM ('user', 'admin', 'verified_player');

TABLE users (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email             VARCHAR(255) UNIQUE NOT NULL,
  password_hash     VARCHAR(255) NOT NULL,
  google_id         VARCHAR(255) UNIQUE,  -- NEW: For Google OAuth
  role              user_role DEFAULT 'user',
  is_active         BOOLEAN DEFAULT true,
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP DEFAULT NOW()
);

-- Existing: user_auth table can be merged or kept separate
```

### 1.2 `user_profiles` (Existing - Extended)
*User profile information*

```sql
TABLE user_profiles (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id           UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name              VARCHAR(255),
  avatar_url        VARCHAR(500),
  location          VARCHAR(255),
  date_of_birth     DATE,
  bio               TEXT,
  preferences       JSONB DEFAULT '{}',  -- UI prefs, notifications, etc.
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP DEFAULT NOW()
);
```

---

## LAYER 2: Sport Profiles

### 2.1 `sport_profiles`
*Links users to specific sports - one user can have multiple sport profiles*

```sql
CREATE TYPE sport_type AS ENUM ('cricket', 'football', 'hockey', 'basketball');
CREATE TYPE profile_visibility AS ENUM ('public', 'friends', 'private');

TABLE sport_profiles (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sport_type        sport_type NOT NULL,
  
  -- Identity Verification (for claiming pro identities)
  is_verified       BOOLEAN DEFAULT false,
  verification_proof TEXT,  -- How they proved identity (ID doc, video, etc.)
  verified_at       TIMESTAMP,
  verified_by_user_id UUID REFERENCES users(id),  -- Admin who verified
  
  -- Privacy
  visibility        profile_visibility DEFAULT 'public',
  
  -- Metadata
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(user_id, sport_type)  -- One profile per sport per user
);

CREATE INDEX idx_sport_profiles_user ON sport_profiles(user_id);
CREATE INDEX idx_sport_profiles_sport ON sport_profiles(sport_type);
CREATE INDEX idx_sport_profiles_verified ON sport_profiles(is_verified) WHERE is_verified = true;
```

### 2.2 `cricket_player_profiles`
*Cricket-specific player data and career statistics*

```sql
CREATE TYPE playing_role AS ENUM ('batsman', 'bowler', 'all_rounder', 'wicket_keeper');
CREATE TYPE batting_style AS ENUM ('right_hand', 'left_hand');
CREATE TYPE bowling_style AS ENUM (
  'right_arm_fast', 'right_arm_medium', 'right_arm_off_spin', 'right_arm_leg_spin',
  'left_arm_fast', 'left_arm_medium', 'left_arm_orthodox', 'left_arm_chinaman'
);

TABLE cricket_player_profiles (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  sport_profile_id  UUID UNIQUE NOT NULL REFERENCES sport_profiles(id) ON DELETE CASCADE,
  
  -- Player Type
  playing_role      playing_role NOT NULL,
  batting_style     batting_style,
  bowling_style     bowling_style,
  
  -- Career Statistics (Aggregated from matches)
  matches_played    INTEGER DEFAULT 0,
  total_runs        INTEGER DEFAULT 0,
  total_wickets     INTEGER DEFAULT 0,
  catches           INTEGER DEFAULT 0,
  stumpings         INTEGER DEFAULT 0,
  run_outs          INTEGER DEFAULT 0,
  
  -- Batting Stats
  batting_avg       DECIMAL(5,2),  -- Computed: total_runs / times_out
  strike_rate       DECIMAL(5,2),  -- Computed: (total_runs / balls_faced) * 100
  highest_score     INTEGER DEFAULT 0,
  fifties           INTEGER DEFAULT 0,
  hundreds          INTEGER DEFAULT 0,
  balls_faced       INTEGER DEFAULT 0,
  fours             INTEGER DEFAULT 0,
  sixes             INTEGER DEFAULT 0,
  
  -- Bowling Stats
  bowling_avg       DECIMAL(5,2),  -- Computed: runs_conceded / total_wickets
  economy_rate      DECIMAL(4,2),  -- Computed: runs_conceded / overs_bowled
  best_bowling      VARCHAR(10),   -- e.g., "5/23"
  five_wickets      INTEGER DEFAULT 0,
  ten_wickets       INTEGER DEFAULT 0,
  balls_bowled      INTEGER DEFAULT 0,
  runs_conceded     INTEGER DEFAULT 0,
  maidens           INTEGER DEFAULT 0,
  
  -- Profile Info
  jersey_number     INTEGER,
  
  -- Metadata
  stats_last_updated TIMESTAMP,
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cricket_profiles_sport ON cricket_player_profiles(sport_profile_id);
CREATE INDEX idx_cricket_profiles_role ON cricket_player_profiles(playing_role);
```

---

## LAYER 3: Teams & Memberships

### 3.1 `teams`
*Team entities - flexible for casual and professional teams*

```sql
CREATE TYPE team_type AS ENUM ('casual', 'club', 'tournament_registered', 'franchise');

TABLE teams (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name              VARCHAR(255) NOT NULL,
  short_name        VARCHAR(50),  -- e.g., "MI", "CSK"
  sport_type        sport_type NOT NULL,
  team_type         team_type DEFAULT 'casual',
  
  -- Ownership
  created_by_user_id UUID NOT NULL REFERENCES users(id),
  
  -- Branding
  logo_url          VARCHAR(500),
  team_colors       JSONB,  -- {primary: "#FF0000", secondary: "#FFFFFF"}
  
  -- Location (for club/franchise teams)
  home_ground       JSONB,  -- {name: "Wankhede", location: {lat: 18.9, lng: 72.8}, city: "Mumbai"}
  
  -- Status
  is_active         BOOLEAN DEFAULT true,
  disbanded_at      TIMESTAMP,
  
  -- Metadata
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_teams_sport ON teams(sport_type);
CREATE INDEX idx_teams_creator ON teams(created_by_user_id);
CREATE INDEX idx_teams_active ON teams(is_active) WHERE is_active = true;
```

### 3.2 `team_memberships`
*Team rosters - tracks who belongs to which team with what roles*

```sql
CREATE TYPE team_member_role AS ENUM ('player', 'captain', 'vice_captain', 'coach', 'team_admin');
CREATE TYPE membership_status AS ENUM ('active', 'benched', 'injured', 'suspended', 'left');

TABLE team_memberships (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  team_id           UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sport_profile_id  UUID NOT NULL REFERENCES sport_profiles(id),
  
  -- Roles (Player can have multiple roles)
  roles             JSONB NOT NULL DEFAULT '["player"]',  -- Array: ["player", "captain"]
  
  -- Cricket-specific
  cricket_profile_id UUID REFERENCES cricket_player_profiles(id),
  jersey_number     INTEGER,
  
  -- Status
  status            membership_status DEFAULT 'active',
  joined_at         TIMESTAMP DEFAULT NOW(),
  left_at           TIMESTAMP,
  
  -- Metadata
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(team_id, user_id)  -- User can't join same team twice
);

CREATE INDEX idx_memberships_team ON team_memberships(team_id);
CREATE INDEX idx_memberships_user ON team_memberships(user_id);
CREATE INDEX idx_memberships_status ON team_memberships(status) WHERE status = 'active';
```

---

## LAYER 4: Matches & Officials

### 4.1 `matches`
*The core match entity - highly configurable for all match types*

```sql
CREATE TYPE match_type AS ENUM ('t20', 'odi', 'test', 'one_day', 'the_hundred', 'custom');
CREATE TYPE match_category AS ENUM ('casual', 'tournament', 'league', 'friendly', 'practice');
CREATE TYPE match_status AS ENUM (
  'scheduled', 'toss_pending', 'live', 'innings_break', 
  'completed', 'abandoned', 'cancelled', 'disputed'
);
CREATE TYPE match_visibility AS ENUM ('public', 'private', 'friends_only');
CREATE TYPE result_type AS ENUM ('normal', 'tie', 'no_result', 'super_over', 'forfeit');
CREATE TYPE elected_to AS ENUM ('bat', 'bowl');

TABLE matches (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  sport_type        sport_type DEFAULT 'cricket',
  
  -- Match Format
  match_type        match_type NOT NULL,
  match_category    match_category DEFAULT 'casual',
  
  -- Match Rules (JSONB for ultimate flexibility)
  match_rules       JSONB NOT NULL DEFAULT '{
    "players_per_team": 11,
    "overs_per_side": 20,
    "balls_per_over": 6,
    "wickets_to_fall": 10,
    "powerplay_overs": null,
    "death_overs_start": null,
    "allow_same_bowler_consecutive": false,
    "retire_after_runs": null,
    "mandatory_bowling": false,
    "dls_applicable": false,
    "super_over_if_tie": false,
    "boundary_count_rule": false
  }',
  
  -- Match Preset (quick setup)
  match_preset      VARCHAR(50),  -- 'professional_t20', 'gully_cricket', 'box_cricket', etc.
  
  -- Teams
  team_a_id         UUID NOT NULL REFERENCES teams(id),
  team_b_id         UUID NOT NULL REFERENCES teams(id),
  
  -- Toss
  toss_won_by_team_id UUID REFERENCES teams(id),
  elected_to        elected_to,
  toss_completed_at TIMESTAMP,
  
  -- Tournament Context
  tournament_id     UUID,  -- FK to tournaments (Phase 2)
  round_name        VARCHAR(100),  -- "Semi Final", "Group Stage Match 3"
  
  -- Venue
  venue             JSONB NOT NULL,  -- {name, location: {lat, lng}, city, ground_type}
  
  -- Schedule
  scheduled_start_time TIMESTAMP WITH TIME ZONE NOT NULL,
  actual_start_time TIMESTAMP WITH TIME ZONE,
  estimated_end_time TIMESTAMP WITH TIME ZONE,
  actual_end_time   TIMESTAMP WITH TIME ZONE,
  
  -- Status
  match_status      match_status DEFAULT 'scheduled',
  
  -- Discovery & Visibility
  visibility        match_visibility DEFAULT 'public',
  match_code        VARCHAR(8) UNIQUE,  -- e.g., "KRD-AB12" for spectators to join
  is_featured       BOOLEAN DEFAULT false,
  
  -- Result (populated after match ends)
  winning_team_id   UUID REFERENCES teams(id),
  result_type       result_type,
  result_margin     VARCHAR(100),  -- "by 5 wickets", "by 32 runs", "by 1 run (DLS method)"
  player_of_match_user_id UUID REFERENCES users(id),
  
  -- Weather/Conditions
  weather_conditions JSONB,  -- {temperature, humidity, wind_speed, rain}
  pitch_report      TEXT,
  
  -- Metadata
  created_by_user_id UUID NOT NULL REFERENCES users(id),
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP DEFAULT NOW(),
  
  CHECK (team_a_id != team_b_id)  -- Teams must be different
);

CREATE INDEX idx_matches_sport ON matches(sport_type);
CREATE INDEX idx_matches_status ON matches(match_status);
CREATE INDEX idx_matches_teams ON matches(team_a_id, team_b_id);
CREATE INDEX idx_matches_schedule ON matches(scheduled_start_time);
CREATE INDEX idx_matches_code ON matches(match_code);
CREATE INDEX idx_matches_visibility ON matches(visibility) WHERE visibility = 'public';
CREATE INDEX idx_matches_featured ON matches(is_featured) WHERE is_featured = true;
```

### 4.2 `match_officials`
*Scorers, umpires, and other match officials*

```sql
CREATE TYPE official_role AS ENUM ('scorer', 'umpire', 'third_umpire', 'match_referee');
CREATE TYPE official_assignment AS ENUM ('team_a', 'team_b', 'neutral');

TABLE match_officials (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  match_id          UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  user_id           UUID NOT NULL REFERENCES users(id),
  
  -- Role
  role              official_role NOT NULL,
  assignment        official_assignment,  -- Which team they represent (for scorers)
  
  -- Status
  is_active         BOOLEAN DEFAULT true,
  joined_at         TIMESTAMP DEFAULT NOW(),
  left_at           TIMESTAMP,
  
  created_at        TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(match_id, user_id, role)  -- One person can't have duplicate roles
);

CREATE INDEX idx_officials_match ON match_officials(match_id);
CREATE INDEX idx_officials_role ON match_officials(role);
CREATE INDEX idx_officials_active ON match_officials(is_active) WHERE is_active = true;
```

### 4.3 `match_playing_xi`
*The actual playing 11 (or fewer) for each team in a specific match*

```sql
TABLE match_playing_xi (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  match_id          UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  team_id           UUID NOT NULL REFERENCES teams(id),
  user_id           UUID NOT NULL REFERENCES users(id),
  cricket_profile_id UUID REFERENCES cricket_player_profiles(id),
  
  -- Playing Roles (flexible for gully cricket)
  can_bat           BOOLEAN DEFAULT true,
  can_bowl          BOOLEAN DEFAULT true,
  is_wicket_keeper  BOOLEAN DEFAULT false,
  is_captain        BOOLEAN DEFAULT false,
  
  -- Batting/Bowling Order (null if flexible/undecided)
  batting_position  INTEGER CHECK (batting_position BETWEEN 1 AND 11),
  bowling_preference INTEGER,  -- Preferred bowling order
  
  -- Fielding
  fielding_position VARCHAR(50),  -- "Mid-off", "Point", "Fine Leg"
  
  -- Status
  played            BOOLEAN DEFAULT true,  -- Did they actually play?
  substitute_for_user_id UUID REFERENCES users(id),  -- If they're a substitute
  
  created_at        TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(match_id, team_id, user_id)
);

CREATE INDEX idx_playing_xi_match ON match_playing_xi(match_id);
CREATE INDEX idx_playing_xi_team ON match_playing_xi(team_id);
CREATE INDEX idx_playing_xi_user ON match_playing_xi(user_id);
```

---

## LAYER 5: Live Match Progression

### 5.1 `innings`
*Each batting innings in a match*

```sql
TABLE innings (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  match_id          UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  innings_number    INTEGER NOT NULL CHECK (innings_number > 0),  -- 1, 2, 3 (super over), 4
  
  -- Teams
  batting_team_id   UUID NOT NULL REFERENCES teams(id),
  bowling_team_id   UUID NOT NULL REFERENCES teams(id),
  
  -- Live State (updated real-time)
  current_over_number INTEGER DEFAULT 0,
  current_ball_in_over INTEGER DEFAULT 0,
  total_runs        INTEGER DEFAULT 0,
  wickets_fallen    INTEGER DEFAULT 0,
  extras            INTEGER DEFAULT 0,
  
  -- Innings Status
  is_completed      BOOLEAN DEFAULT false,
  all_out           BOOLEAN DEFAULT false,
  declared          BOOLEAN DEFAULT false,
  
  -- Target (for second innings)
  target_runs       INTEGER,  -- First innings total + 1
  
  -- Current Players (nullable if not started)
  striker_user_id   UUID REFERENCES users(id),
  non_striker_user_id UUID REFERENCES users(id),
  current_bowler_user_id UUID REFERENCES users(id),
  next_batsman_user_id UUID REFERENCES users(id),
  
  -- Timing
  started_at        TIMESTAMP,
  completed_at      TIMESTAMP,
  
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(match_id, innings_number)
);

CREATE INDEX idx_innings_match ON innings(match_id);
CREATE INDEX idx_innings_teams ON innings(batting_team_id, bowling_team_id);
CREATE INDEX idx_innings_live ON innings(is_completed) WHERE is_completed = false;
```

### 5.2 `overs`
*Aggregate data for each over*

```sql
TABLE overs (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  innings_id        UUID NOT NULL REFERENCES innings(id) ON DELETE CASCADE,
  over_number       INTEGER NOT NULL CHECK (over_number > 0),
  bowler_user_id    UUID NOT NULL REFERENCES users(id),
  
  -- Over Summary (computed after over completes)
  runs_conceded     INTEGER DEFAULT 0,
  wickets_taken     INTEGER DEFAULT 0,
  legal_deliveries  INTEGER DEFAULT 0,  -- Usually 6, but can be less if innings ends
  extras_in_over    INTEGER DEFAULT 0,
  is_maiden         BOOLEAN DEFAULT false,
  is_completed      BOOLEAN DEFAULT false,
  
  -- Ball-by-ball sequence for UI (e.g., "W 1 4 . 2 6")
  ball_sequence     JSONB DEFAULT '[]',  -- ["W", "1", "4", "0", "2", "6"]
  
  -- Timing
  started_at        TIMESTAMP,
  completed_at      TIMESTAMP,
  
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(innings_id, over_number)
);

CREATE INDEX idx_overs_innings ON overs(innings_id);
CREATE INDEX idx_overs_bowler ON overs(bowler_user_id);
```

### 5.3 `balls`
*The atomic unit of cricket - each ball bowled*

```sql
CREATE TYPE extra_type AS ENUM ('none', 'wide', 'no_ball', 'bye', 'leg_bye', 'penalty');
CREATE TYPE boundary_type AS ENUM ('four', 'six');
CREATE TYPE shot_type AS ENUM (
  'defensive', 'drive', 'cut', 'pull', 'hook', 'sweep', 'reverse_sweep',
  'lofted', 'flick', 'edge', 'missed', 'leave'
);

TABLE balls (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  innings_id        UUID NOT NULL REFERENCES innings(id) ON DELETE CASCADE,
  over_id           UUID NOT NULL REFERENCES overs(id),
  ball_number       DECIMAL(4,1) NOT NULL,  -- e.g., 15.4 (over 15, ball 4)
  
  -- Who's Involved
  bowler_user_id    UUID NOT NULL REFERENCES users(id),
  batsman_user_id   UUID NOT NULL REFERENCES users(id),  -- Striker
  non_striker_user_id UUID REFERENCES users(id),
  
  -- Ball Outcome
  runs_scored       INTEGER DEFAULT 0 CHECK (runs_scored >= 0),
  is_wicket         BOOLEAN DEFAULT false,
  is_boundary       BOOLEAN DEFAULT false,
  boundary_type     boundary_type,
  
  -- Extras
  is_legal_delivery BOOLEAN DEFAULT true,
  extra_type        extra_type DEFAULT 'none',
  extra_runs        INTEGER DEFAULT 0,
  
  -- Advanced Analytics (Optional)
  shot_type         shot_type,
  fielding_position VARCHAR(50),  -- Where ball went
  wagon_wheel_data  JSONB,  -- {angle: 45, distance: 75} for wagon wheel viz
  
  -- Milestones
  is_milestone      BOOLEAN DEFAULT false,
  milestone_type    VARCHAR(50),  -- "fifty", "hundred", "hat_trick", "maiden_over"
  
  -- Validation Metadata
  validation_source VARCHAR(50) DEFAULT 'dual_scorer',  -- 'dual_scorer', 'triple_validation', 'single_scorer', 'umpire_only'
  validation_confidence DECIMAL(3,2) DEFAULT 1.00,  -- 0.00 to 1.00
  
  -- Timestamp
  bowled_at         TIMESTAMP NOT NULL DEFAULT NOW(),
  created_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_balls_innings ON balls(innings_id);
CREATE INDEX idx_balls_over ON balls(over_id);
CREATE INDEX idx_balls_batsman ON balls(batsman_user_id);
CREATE INDEX idx_balls_bowler ON balls(bowler_user_id);
CREATE INDEX idx_balls_wickets ON balls(is_wicket) WHERE is_wicket = true;
CREATE INDEX idx_balls_boundaries ON balls(is_boundary) WHERE is_boundary = true;
CREATE INDEX idx_balls_milestones ON balls(is_milestone) WHERE is_milestone = true;
```

### 5.4 `wickets`
*Detailed dismissal information*

```sql
CREATE TYPE dismissal_type AS ENUM (
  'bowled', 'caught', 'lbw', 'run_out', 'stumped', 
  'hit_wicket', 'handled_ball', 'obstructing_field', 
  'timed_out', 'retired_hurt', 'retired_out'
);

TABLE wickets (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  ball_id           UUID UNIQUE NOT NULL REFERENCES balls(id) ON DELETE CASCADE,
  innings_id        UUID NOT NULL REFERENCES innings(id),
  batsman_out_user_id UUID NOT NULL REFERENCES users(id),
  
  -- Dismissal Details
  dismissal_type    dismissal_type NOT NULL,
  
  -- Credits
  bowler_user_id    UUID REFERENCES users(id),  -- Null for run-outs
  fielder_user_id   UUID REFERENCES users(id),  -- Catcher, keeper, fielder who ran out
  fielder2_user_id  UUID REFERENCES users(id),  -- For relay catches or run-outs
  
  -- Context
  wicket_number     INTEGER NOT NULL CHECK (wicket_number BETWEEN 1 AND 10),
  team_score_at_wicket INTEGER NOT NULL,  -- e.g., 45 when "45/3"
  partnership_runs  INTEGER DEFAULT 0,
  
  -- Timing
  dismissed_at      TIMESTAMP DEFAULT NOW(),
  created_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_wickets_innings ON wickets(innings_id);
CREATE INDEX idx_wickets_batsman ON wickets(batsman_out_user_id);
CREATE INDEX idx_wickets_bowler ON wickets(bowler_user_id);
CREATE INDEX idx_wickets_type ON wickets(dismissal_type);
```

---

## LAYER 6: Player Performance (Real-time Stats)

### 6.1 `batting_innings`
*Individual batsman's performance in an innings*

```sql
TABLE batting_innings (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  innings_id        UUID NOT NULL REFERENCES innings(id) ON DELETE CASCADE,
  batsman_user_id   UUID NOT NULL REFERENCES users(id),
  cricket_profile_id UUID REFERENCES cricket_player_profiles(id),
  batting_position  INTEGER CHECK (batting_position BETWEEN 1 AND 11),
  
  -- Performance (updated real-time)
  runs_scored       INTEGER DEFAULT 0,
  balls_faced       INTEGER DEFAULT 0,
  fours             INTEGER DEFAULT 0,
  sixes             INTEGER DEFAULT 0,
  strike_rate       DECIMAL(5,2),  -- Computed: (runs_scored / balls_faced) * 100
  
  -- Dismissal
  is_out            BOOLEAN DEFAULT false,
  wicket_id         UUID REFERENCES wickets(id),  -- How they got out
  
  -- Special Cases
  is_not_out        BOOLEAN DEFAULT false,  -- Stayed till end
  did_not_bat       BOOLEAN DEFAULT false,  -- Didn't get chance to bat
  retired_hurt      BOOLEAN DEFAULT false,
  retired_hurt_at_runs INTEGER,
  returned_to_bat_after_wicket INTEGER,  -- Which wicket number they came back
  
  -- Milestones
  achieved_fifty    BOOLEAN DEFAULT false,
  achieved_hundred  BOOLEAN DEFAULT false,
  
  -- Timing
  started_batting_at TIMESTAMP,
  ended_batting_at  TIMESTAMP,
  
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(innings_id, batsman_user_id)
);

CREATE INDEX idx_batting_innings_innings ON batting_innings(innings_id);
CREATE INDEX idx_batting_innings_batsman ON batting_innings(batsman_user_id);
CREATE INDEX idx_batting_innings_runs ON batting_innings(runs_scored DESC);
```

### 6.2 `bowling_figures`
*Individual bowler's performance in an innings*

```sql
TABLE bowling_figures (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  innings_id        UUID NOT NULL REFERENCES innings(id) ON DELETE CASCADE,
  bowler_user_id    UUID NOT NULL REFERENCES users(id),
  cricket_profile_id UUID REFERENCES cricket_player_profiles(id),
  
  -- Bowling Figures (the famous "4-0-23-2" format)
  overs_bowled      DECIMAL(4,1) DEFAULT 0.0,  -- 4.2 means 4 overs + 2 balls
  maidens           INTEGER DEFAULT 0,
  runs_conceded     INTEGER DEFAULT 0,
  wickets_taken     INTEGER DEFAULT 0,
  economy_rate      DECIMAL(4,2),  -- Computed: runs_conceded / overs_bowled
  
  -- Extras Conceded
  wides_conceded    INTEGER DEFAULT 0,
  no_balls_conceded INTEGER DEFAULT 0,
  
  -- Milestones
  is_five_wicket_haul BOOLEAN DEFAULT false,
  is_hat_trick      BOOLEAN DEFAULT false,
  
  -- Which Overs Bowled (for analytics)
  overs_list        INTEGER[] DEFAULT ARRAY[]::INTEGER[],  -- [1, 3, 5, 7, ...]
  
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(innings_id, bowler_user_id)
);

CREATE INDEX idx_bowling_innings ON bowling_figures(innings_id);
CREATE INDEX idx_bowling_bowler ON bowling_figures(bowler_user_id);
CREATE INDEX idx_bowling_wickets ON bowling_figures(wickets_taken DESC);
```

### 6.3 `partnerships`
*Batting partnerships between two batsmen*

```sql
TABLE partnerships (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  innings_id        UUID NOT NULL REFERENCES innings(id) ON DELETE CASCADE,
  batsman1_user_id  UUID NOT NULL REFERENCES users(id),
  batsman2_user_id  UUID NOT NULL REFERENCES users(id),
  
  -- Partnership Details
  partnership_number INTEGER NOT NULL,  -- 1st wicket, 2nd wicket, etc.
  partnership_runs  INTEGER DEFAULT 0,
  balls_faced       INTEGER DEFAULT 0,
  
  -- Individual Contributions
  batsman1_runs     INTEGER DEFAULT 0,
  batsman2_runs     INTEGER DEFAULT 0,
  
  -- How It Ended
  ended_by_wicket_id UUID REFERENCES wickets(id),
  ended_at_team_score INTEGER,  -- Team score when partnership broke
  
  -- Milestones
  is_fifty_partnership BOOLEAN DEFAULT false,
  is_hundred_partnership BOOLEAN DEFAULT false,
  
  -- Timing
  started_at        TIMESTAMP,
  ended_at          TIMESTAMP,
  
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_partnerships_innings ON partnerships(innings_id);
CREATE INDEX idx_partnerships_batsmen ON partnerships(batsman1_user_id, batsman2_user_id);
CREATE INDEX idx_partnerships_runs ON partnerships(partnership_runs DESC);
```

---

## LAYER 7: Scoring Integrity (The Crown Jewel)

### 7.1 `scoring_events`
*Immutable event log - every scoring action recorded*

```sql
CREATE TYPE event_type AS ENUM (
  'ball_bowled', 'wicket_fallen', 'over_complete', 'innings_complete',
  'batsman_change', 'bowler_change', 'drinks_break', 'injury_timeout',
  'innings_start', 'match_start', 'match_end', 'toss_completed'
);

CREATE TYPE validation_status AS ENUM (
  'pending',           -- Waiting for other scorer(s)
  'validated',         -- Consensus reached (all agree)
  'auto_validated',    -- Timeout, single entry accepted
  'disputed',          -- Scorers disagree
  'resolved',          -- Dispute resolved by umpire
  'rejected'           -- Marked invalid
);

CREATE TYPE scorer_team_side AS ENUM ('team_a', 'team_b', 'umpire', 'system');

TABLE scoring_events (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  match_id          UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  innings_id        UUID REFERENCES innings(id),
  ball_id           UUID REFERENCES balls(id),  -- Nullable if event isn't a ball
  
  -- Who Recorded This?
  scorer_user_id    UUID NOT NULL REFERENCES users(id),
  scorer_team_side  scorer_team_side NOT NULL,
  
  -- Event Type
  event_type        event_type NOT NULL,
  
  -- Event Data (Flexible JSONB for different event types)
  event_data        JSONB NOT NULL,  -- {runs: 4, batsman: "uuid", bowler: "uuid", ...}
  
  -- Validation State
  validation_status validation_status DEFAULT 'pending',
  
  -- Consensus Tracking
  matching_event_id UUID REFERENCES scoring_events(id),  -- The paired event
  validated_at      TIMESTAMP,
  validated_by_user_id UUID REFERENCES users(id),  -- Umpire who resolved dispute
  
  -- Cryptographic Integrity (Hash Chain)
  event_hash        VARCHAR(64) NOT NULL,  -- SHA256(event_data + previous_event_hash)
  previous_event_hash VARCHAR(64),  -- Creates blockchain-like chain
  signature         VARCHAR(256),  -- HMAC of event_data with scorer's JWT
  
  -- Timestamp (CRITICAL for ordering)
  event_timestamp   TIMESTAMP WITH TIME ZONE NOT NULL,  -- When it happened in match
  sequence_number   BIGSERIAL,  -- Auto-increment for guaranteed ordering
  created_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scoring_events_match ON scoring_events(match_id);
CREATE INDEX idx_scoring_events_innings ON scoring_events(innings_id);
CREATE INDEX idx_scoring_events_scorer ON scoring_events(scorer_user_id);
CREATE INDEX idx_scoring_events_status ON scoring_events(validation_status);
CREATE INDEX idx_scoring_events_sequence ON scoring_events(sequence_number);
CREATE INDEX idx_scoring_events_timestamp ON scoring_events(event_timestamp);
CREATE INDEX idx_scoring_events_pending ON scoring_events(validation_status, match_id) 
  WHERE validation_status = 'pending';
```

### 7.2 `scoring_disputes`
*Log of all scoring conflicts and their resolution*

```sql
CREATE TYPE dispute_type AS ENUM (
  'runs_mismatch', 'wicket_mismatch', 'extra_mismatch', 
  'boundary_mismatch', 'dismissal_type_mismatch', 'other'
);

CREATE TYPE resolution_status AS ENUM ('pending', 'resolved', 'escalated', 'abandoned');

TABLE scoring_disputes (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  match_id          UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  ball_id           UUID REFERENCES balls(id),
  
  -- The Conflicting Events
  scorer_a_event_id UUID NOT NULL REFERENCES scoring_events(id),
  scorer_b_event_id UUID NOT NULL REFERENCES scoring_events(id),
  umpire_event_id   UUID REFERENCES scoring_events(id),  -- If 3-way validation
  
  -- Dispute Details
  dispute_type      dispute_type NOT NULL,
  scorer_a_claim    JSONB NOT NULL,  -- What Scorer A said
  scorer_b_claim    JSONB NOT NULL,  -- What Scorer B said
  umpire_claim      JSONB,  -- What Umpire said (if present)
  
  -- Auto-detected Difference
  difference_summary TEXT,  -- "Scorer A: 4 runs, Scorer B: 1 run"
  
  -- Resolution
  resolution_status resolution_status DEFAULT 'pending',
  resolved_by_user_id UUID REFERENCES users(id),  -- Umpire/admin who resolved
  resolution_method VARCHAR(50),  -- 'umpire_override', 'scorer_concession', 'majority_vote'
  final_decision    JSONB,  -- The accepted version
  resolution_notes  TEXT,
  
  -- Timing
  created_at        TIMESTAMP DEFAULT NOW(),
  resolved_at       TIMESTAMP,
  resolution_time_seconds INTEGER  -- How long it took to resolve
);

CREATE INDEX idx_disputes_match ON scoring_disputes(match_id);
CREATE INDEX idx_disputes_status ON scoring_disputes(resolution_status);
CREATE INDEX idx_disputes_pending ON scoring_disputes(resolution_status) 
  WHERE resolution_status = 'pending';
```

### 7.3 `scoring_consensus`
*Tracks validation outcomes for matched events*

```sql
CREATE TYPE consensus_method AS ENUM (
  'exact_match',      -- All validators agree 100%
  'majority_2_of_3',  -- 2 out of 3 agree
  'umpire_override',  -- Umpire made final call
  'timeout_accept',   -- Timeout, first entry accepted
  'manual_resolve'    -- Human intervention
);

TABLE scoring_consensus (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  match_id          UUID NOT NULL REFERENCES matches(id),
  ball_id           UUID REFERENCES balls(id),
  
  -- Events Being Validated
  event_ids         UUID[] NOT NULL,  -- Array of scoring_event IDs
  
  -- Consensus Result
  consensus_reached BOOLEAN NOT NULL,
  consensus_method  consensus_method NOT NULL,
  confidence_score  DECIMAL(3,2) DEFAULT 1.00,  -- 0.00 to 1.00
  
  -- Final State
  final_state       JSONB NOT NULL,  -- The accepted event data
  applied_to_ball   BOOLEAN DEFAULT false,  -- Has this been written to balls table?
  
  -- Who Made Final Decision
  final_authority_user_id UUID REFERENCES users(id),
  
  -- Timing
  validation_time_ms INTEGER,  -- How long validation took (milliseconds)
  created_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_consensus_match ON scoring_consensus(match_id);
CREATE INDEX idx_consensus_ball ON scoring_consensus(ball_id);
```

---

## LAYER 8: Aggregates & Archives

### 8.1 `match_summaries`
*Pre-computed match statistics for fast retrieval*

```sql
TABLE match_summaries (
  match_id          UUID PRIMARY KEY REFERENCES matches(id) ON DELETE CASCADE,
  
  -- Team A Stats
  team_a_runs       INTEGER DEFAULT 0,
  team_a_wickets    INTEGER DEFAULT 0,
  team_a_overs      DECIMAL(4,1) DEFAULT 0.0,
  team_a_run_rate   DECIMAL(4,2),
  
  -- Team B Stats
  team_b_runs       INTEGER DEFAULT 0,
  team_b_wickets    INTEGER DEFAULT 0,
  team_b_overs      DECIMAL(4,1) DEFAULT 0.0,
  team_b_run_rate   DECIMAL(4,2),
  
  -- Top Performers
  highest_scorer_user_id UUID REFERENCES users(id),
  highest_score     INTEGER,
  best_bowler_user_id UUID REFERENCES users(id),
  best_bowling_figures VARCHAR(10),  -- "5/23"
  
  -- Match Highlights
  total_boundaries  INTEGER DEFAULT 0,
  total_sixes       INTEGER DEFAULT 0,
  total_fours       INTEGER DEFAULT 0,
  highest_partnership INTEGER DEFAULT 0,
  
  -- Scoring Integrity Metrics
  total_balls       INTEGER DEFAULT 0,
  disputed_balls    INTEGER DEFAULT 0,
  dispute_rate      DECIMAL(4,2),  -- Percentage of disputed balls
  avg_validation_time_ms INTEGER,
  
  -- Data Quality
  completeness_score DECIMAL(3,2),  -- 0.00 to 1.00 (how complete is the data?)
  
  -- Computed/Updated
  last_updated_at   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_summaries_highest_scorer ON match_summaries(highest_scorer_user_id);
CREATE INDEX idx_summaries_best_bowler ON match_summaries(best_bowler_user_id);
```

### 8.2 `match_archives`
*Lightweight index for archived matches (full data in S3/MinIO)*

```sql
CREATE TYPE archive_status AS ENUM ('active', 'archived', 'deleted');

TABLE match_archives (
  match_id          UUID PRIMARY KEY REFERENCES matches(id),
  
  -- Archive Location
  archive_status    archive_status DEFAULT 'active',
  archive_location  VARCHAR(500),  -- S3/MinIO URL
  archive_size_bytes BIGINT,
  compression_format VARCHAR(20) DEFAULT 'gzip',
  
  -- Match Summary (for search without fetching full archive)
  match_summary     JSONB NOT NULL,  -- {teams, date, result, venue, key_stats}
  
  -- Participants (for "my matches" queries)
  participant_user_ids UUID[] NOT NULL,
  team_ids          UUID[] NOT NULL,
  
  -- Match Metadata (for filtering)
  match_date        DATE NOT NULL,
  venue_city        VARCHAR(100),
  match_type        match_type,
  
  -- Retention
  retain_permanently BOOLEAN DEFAULT false,
  retention_reason  TEXT,
  scheduled_deletion_at TIMESTAMP,
  
  -- Timing
  archived_at       TIMESTAMP,
  last_accessed_at  TIMESTAMP,
  access_count      INTEGER DEFAULT 0,
  
  created_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_archives_status ON match_archives(archive_status);
CREATE INDEX idx_archives_participants ON match_archives USING GIN(participant_user_ids);
CREATE INDEX idx_archives_date ON match_archives(match_date DESC);
CREATE INDEX idx_archives_retention ON match_archives(retain_permanently) 
  WHERE retain_permanently = true;
```

---

## Relationships & Constraints

### Primary Relationships
```
users (1) ──→ (N) sport_profiles
sport_profiles (1) ──→ (1) cricket_player_profiles
users (1) ──→ (N) team_memberships
teams (1) ──→ (N) team_memberships
teams (2) ──→ (1) matches  -- Team A and Team B
matches (1) ──→ (N) innings
innings (1) ──→ (N) overs
overs (1) ──→ (N) balls
balls (1) ──→ (0..1) wickets
innings (1) ──→ (N) batting_innings
innings (1) ──→ (N) bowling_figures
innings (1) ──→ (N) partnerships
matches (1) ──→ (N) scoring_events
scoring_events (2) ──→ (1) scoring_disputes  -- Two conflicting events
matches (1) ──→ (1) match_summaries
matches (1) ──→ (0..1) match_archives
```

### Referential Integrity Rules
- **CASCADE on team deletion**: Delete all team_memberships
- **CASCADE on match deletion**: Delete all innings, scoring_events, etc.
- **RESTRICT on user deletion**: Cannot delete user with active matches
- **SET NULL on optional FKs**: e.g., umpire_event_id in scoring_disputes

---

## Indexes & Performance

### High-Traffic Query Patterns

**1. Live Match Updates**
```sql
-- Get current match state
SELECT * FROM innings WHERE match_id = ? AND is_completed = false;
-- Index: idx_innings_live

-- Get recent balls
SELECT * FROM balls WHERE innings_id = ? ORDER BY ball_number DESC LIMIT 10;
-- Index: idx_balls_innings + BRIN on ball_number

-- Get current batting/bowling figures
SELECT * FROM batting_innings WHERE innings_id = ? ORDER BY runs_scored DESC;
-- Index: idx_batting_innings_innings
```

**2. Pending Validations (Consensus Engine)**
```sql
-- Get pending events for match
SELECT * FROM scoring_events 
WHERE match_id = ? AND validation_status = 'pending'
ORDER BY sequence_number;
-- Index: idx_scoring_events_pending (partial index)
```

**3. User Dashboard**
```sql
-- Get user's matches
SELECT m.* FROM matches m
JOIN match_playing_xi p ON p.match_id = m.id
WHERE p.user_id = ?
ORDER BY m.scheduled_start_time DESC;
-- Index: idx_playing_xi_user + idx_matches_schedule
```

**4. Public Match Discovery**
```sql
-- Get public live matches
SELECT * FROM matches 
WHERE visibility = 'public' AND match_status = 'live'
ORDER BY actual_start_time DESC;
-- Index: idx_matches_visibility + idx_matches_status (composite)
```

### Suggested Additional Indexes
```sql
-- Composite indexes for common joins
CREATE INDEX idx_balls_innings_over ON balls(innings_id, over_id);
CREATE INDEX idx_wickets_innings_batsman ON wickets(innings_id, batsman_out_user_id);

-- BRIN indexes for time-series data (balls, scoring_events)
CREATE INDEX idx_balls_bowled_at_brin ON balls USING BRIN(bowled_at);
CREATE INDEX idx_events_timestamp_brin ON scoring_events USING BRIN(event_timestamp);

-- GIN indexes for JSONB queries
CREATE INDEX idx_matches_rules_gin ON matches USING GIN(match_rules);
CREATE INDEX idx_scoring_events_data_gin ON scoring_events USING GIN(event_data);

-- Full-text search (for future)
CREATE INDEX idx_teams_name_fulltext ON teams USING GIN(to_tsvector('english', name));
```

---

## Data Flow

### Ball Bowled - Complete Flow
```
1. SCORER INPUT
   ├─ Scorer A enters: {runs: 4, batsman: X, bowler: Y}
   ├─ Scorer B enters: {runs: 4, batsman: X, bowler: Y}
   └─ (Optional) Umpire enters: {runs: 4, batsman: X, bowler: Y}

2. SCORING_EVENTS TABLE
   ├─ 2-3 records created (status: pending)
   ├─ Hash chain computed
   └─ Pushed to Redis Stream

3. CONSENSUS ENGINE (Worker)
   ├─ Matches events within 30-second window
   ├─ Validates: exact match / 2-of-3 / dispute
   └─ Updates validation_status

4. IF VALIDATED:
   ├─ Insert into BALLS table
   ├─ Update OVERS (runs_conceded, ball_sequence)
   ├─ Update INNINGS (total_runs, current_ball)
   ├─ Update BATTING_INNINGS (runs_scored, balls_faced, strike_rate)
   ├─ Update BOWLING_FIGURES (runs_conceded, balls_bowled)
   ├─ Update PARTNERSHIP (partnership_runs)
   ├─ IF wicket: Insert into WICKETS table
   └─ Broadcast via WebSocket

5. IF DISPUTED:
   ├─ Insert into SCORING_DISPUTES
   ├─ Notify scorers + umpire
   ├─ Await resolution
   └─ Loop back to step 4 once resolved

6. AGGREGATION (Async)
   ├─ Update MATCH_SUMMARIES
   ├─ Recompute CRICKET_PLAYER_PROFILES stats (daily batch)
   └─ Generate analytics
```

---

## Validation Rules

### Business Logic Constraints

**Match Creation:**
- `team_a_id != team_b_id`
- `scheduled_start_time > NOW()`
- At least 3 players per team (configurable)
- Valid match_rules JSONB schema

**Innings Progression:**
- Cannot start innings without toss
- Cannot bowl same bowler for consecutive overs (if rule enabled)
- Cannot exceed overs_per_side
- wickets_fallen <= match_rules.wickets_to_fall

**Ball Validation:**
- runs_scored >= 0
- ball_number sequential within over
- batsman/bowler must be in playing XI
- legal_delivery = false if extra_type != 'none'

**Wicket Rules:**
- wicket_number <= 10
- dismissal_type 'bowled/lbw/caught' requires bowler_id
- dismissal_type 'run_out' doesn't credit bowler
- dismissal_type 'retired_hurt' doesn't count as wicket

**Scoring Integrity:**
- scoring_events.event_hash must chain correctly
- matching_event_id must reference valid event
- Can't validate own event (scorer_a_event != scorer_b_event from same user)

---

## Schema Evolution Plan

### Phase 1 (MVP - Current)
✓ All tables defined above
✓ Cricket module complete
✓ Scoring integrity system
✓ Archival mechanism

### Phase 2 (Post-MVP)
- `tournaments` table
- `tournament_teams` table
- `tournament_standings` table
- `tournament_brackets` table (for knockout)
- `player_rankings` table
- `leaderboards` table

### Phase 3 (Multi-Sport)
- `football_player_profiles` table
- `football_matches` extension
- `hockey_player_profiles` table
- Abstract common patterns to `sport_match_config` table

### Phase 4 (Advanced Features)
- `match_highlights` table (key moments)
- `video_clips` table (for video uploads)
- `match_commentary` table (ball-by-ball text)
- `wagering_pools` table (for prediction games)
- `merchandise` table (team jerseys, etc.)

---

## Performance Targets

### Read Performance
- Live match scorecard: < 50ms
- User dashboard (10 matches): < 100ms
- Match archive retrieval: < 3s (from cold storage)
- Public match discovery: < 200ms

### Write Performance
- Ball validation (consensus): < 500ms (target: 200ms)
- Real-time stat updates: < 100ms
- Event sourcing write: < 50ms

### Concurrency
- Support 1,000 concurrent matches
- 100,000 concurrent spectators (WebSocket)
- 10,000 writes/second (scoring events)

### Storage Estimates
- Active match (full data): ~2MB
- Archived match (compressed): ~50KB
- 10,000 matches/day = 500GB/year (before archival)
- After archival: ~50GB/year

---

## Migration Strategy

### Initial Setup
```bash
# Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

# Create enums (all defined above)
# Create tables in order (respecting FK dependencies)
# Create indexes
# Create triggers (for updated_at, stats aggregation)
```

### Alembic Migrations
```python
# Migration naming convention:
# YYYYMMDD_HHMM_description.py

# Example:
# 20251026_1400_create_cricket_core_tables.py
# 20251026_1430_create_scoring_integrity_tables.py
# 20251026_1500_create_indexes.py
```

---

## Appendix: JSONB Schemas

### match_rules JSONB
```json
{
  "players_per_team": 11,
  "overs_per_side": 20,
  "balls_per_over": 6,
  "wickets_to_fall": 10,
  "powerplay_overs": 6,
  "death_overs_start": 16,
  "allow_same_bowler_consecutive": false,
  "retire_after_runs": null,
  "mandatory_bowling": false,
  "max_overs_per_bowler": 4,
  "dls_applicable": false,
  "super_over_if_tie": true,
  "boundary_count_rule": false
}
```

### event_data JSONB (ball_bowled)
```json
{
  "runs": 4,
  "batsman_id": "uuid-123",
  "bowler_id": "uuid-456",
  "is_boundary": true,
  "boundary_type": "four",
  "extra_type": "none",
  "shot_type": "cover_drive",
  "ball_number": "15.4"
}
```

### venue JSONB
```json
{
  "name": "Wankhede Stadium",
  "location": {
    "lat": 18.9388,
    "lng": 72.8258
  },
  "city": "Mumbai",
  "country": "India",
  "ground_type": "turf",
  "capacity": 33000
}
```

---

## Security Considerations

### Row-Level Security (RLS)
```sql
-- Enable RLS on sensitive tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE scoring_events ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY user_profile_select ON user_profiles
  FOR SELECT USING (
    visibility = 'public' OR 
    user_id = current_setting('app.user_id')::uuid
  );
```

### Data Encryption
- Passwords: bcrypt (already implemented)
- Tokens: JWT with RS256
- At-rest: PostgreSQL TDE (Transparent Data Encryption)
- In-transit: SSL/TLS for all connections

### Audit Trail
- All mutations logged via triggers
- Scoring events immutable (INSERT only, never UPDATE/DELETE)
- Hash chain prevents tampering
- Admin actions logged separately

---

## Monitoring & Observability

### Key Metrics to Track
- Pending validations queue depth
- Average validation time
- Dispute resolution rate
- WebSocket connection count
- Database connection pool usage
- Query performance (p50, p95, p99)

### Alerts
- Pending validations > 100 (system overload)
- Dispute resolution time > 60s (manual intervention needed)
- Database connections > 80% (scaling needed)
- Archive failures (data retention risk)

---

**End of Schema Design Document**

*This schema is designed for scalability, integrity, and flexibility. It supports everything from backyard gully cricket to professional T20 tournaments, with a unique focus on tamper-proof scoring that sets Kreeda apart from all competitors.*

*Version 1.0 - Ready for Implementation*
