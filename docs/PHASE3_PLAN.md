# Phase 3: Live Scoring & Event Sourcing - Implementation Plan

**Start Date**: October 31, 2025  
**Branch**: `feature/phase3-live-scoring`  
**Estimated Duration**: 3-4 sessions  
**Target**: Complete ball-by-ball scoring with multi-validator consensus

---

## 🎯 Phase 3 Objectives

Implement the **core value proposition** of Kreeda: real-time ball-by-ball scoring with integrity validation, performance tracking, and complete match history.

### Key Features
1. **Event-Sourced Ball Recording** - Immutable ball-by-ball records
2. **Multi-Validator Consensus** - TRIPLE/DUAL/SINGLE/HONOR validation tiers
3. **Real-Time Aggregation** - Live batting/bowling statistics
4. **WebSocket Broadcasting** - Live match updates for spectators
5. **Match Archives** - Complete replay capability

---

## 📋 Task Breakdown (18 Tasks)

### Planning & Setup (Task 1)
- ✅ Create feature branch `feature/phase3-live-scoring`
- ✅ Update copilot-instructions.md with Phase 2 completion
- ✅ Create this implementation plan
- 🔲 Verify all models exist in `src/models/cricket/`
- 🔲 Review API_DESIGN.md for endpoint specifications

### Schemas Layer (Tasks 2-3, 6)

**Task 2: Innings Management Schemas** (`src/schemas/cricket/innings.py`)
```python
# Request/Response schemas for innings management
- InningsCreateRequest(innings_number, batting_team_id, bowling_team_id, target_score?)
- InningsResponse(id, innings_number, current_score, wickets_fallen, overs_bowled)
- InningsStateSchema(batsmen, bowler, overs_remaining, required_run_rate)
- InningsUpdateRequest(actual_end_time, is_completed, runs_scored, wickets_fallen)
```

**Task 3: Ball-by-Ball Scoring Schemas** (`src/schemas/cricket/ball.py`)
```python
# Event sourcing schemas for balls and wickets
- BallCreateRequest(over_id, ball_number, bowler_id, striker_id, non_striker_id, runs_scored, extras, is_wicket)
- BallResponse(id, ball_number, runs_total, extras, wicket_details, commentary)
- WicketDetailsSchema(dismissal_type, fielder_id, bowler_credited)
- ExtraDetailsSchema(extra_type, runs_awarded, penalty)
```

**Task 6: Scoring Integrity Schemas** (`src/schemas/cricket/scoring_integrity.py`)
```python
# Multi-validator consensus schemas
- ScoringEventRequest(scorer_id, event_hash, ball_data, previous_hash)
- ScoringEventResponse(id, status: PENDING/VALIDATED/DISPUTED, validation_tier)
- DisputeCreateRequest(event_id, dispute_reason, evidence_url)
- ConsensusValidationResponse(is_validated, consensus_reached, disputed_fields)
```

### Services Layer (Tasks 4-5, 7-8, 11)

**Task 4: InningsService** (`src/services/cricket/innings.py`)
```python
class InningsService:
    @staticmethod
    async def start_innings(match_id, innings_number, batting_team_id, db):
        """
        Create new innings, validate match status is LIVE
        Initialize first over, set opening batsmen
        """
    
    @staticmethod
    async def get_current_state(innings_id, db):
        """
        Derive current state from ball events:
        - Total runs (calculated from balls)
        - Wickets fallen (from wicket records)
        - Current batsmen, bowler
        - Required run rate (for chases)
        """
    
    @staticmethod
    async def end_innings(innings_id, db):
        """
        Mark innings complete, calculate final totals
        Trigger next innings or match completion
        """
```

**Task 5: BallService** (`src/services/cricket/ball.py`)
```python
class BallService:
    @staticmethod
    async def record_ball(ball_request: BallCreateRequest, db):
        """
        Event sourcing pattern:
        1. Validate ball sequence (no gaps, correct over)
        2. Create immutable Ball record
        3. If wicket: Create Wicket record
        4. Update aggregates (batting_innings, bowling_figures)
        5. Broadcast event via WebSocket
        """
    
    @staticmethod
    async def validate_ball_sequence(innings_id, over_number, ball_number, db):
        """
        Ensure balls recorded in order:
        - Ball numbers 1-6 per over (or balls_per_over from match_rules)
        - No duplicate balls
        - Previous ball exists (except first ball)
        """
    
    @staticmethod
    async def get_ball_history(innings_id, db):
        """
        Retrieve complete ball-by-ball log for replay
        Include wickets, milestones, extras
        """
```

**Task 7: ScoringIntegrityService** (`src/services/cricket/scoring_integrity.py`)
```python
class ScoringIntegrityService:
    @staticmethod
    async def submit_scoring_event(event: ScoringEventRequest, db):
        """
        Multi-validator consensus algorithm:
        
        VALIDATION_TIER logic:
        - TRIPLE: 3 scorers (umpire + 2 independent)
          → 2/3 consensus required
        - DUAL: 2 scorers (Team A + Team B)
          → Both must match
        - SINGLE: 1 trusted scorer
          → Auto-validated
        - HONOR: Self-scoring
          → No validation
        """
    
    @staticmethod
    async def validate_dual_scoring(event_a, event_b, db):
        """
        Compare two scoring events:
        - Hash match → auto-validate
        - Hash mismatch → create dispute
        - Fields to compare: runs, extras, wicket, striker, bowler
        """
    
    @staticmethod
    async def resolve_dispute(dispute_id, resolution: DisputeResolution, db):
        """
        Resolution hierarchy:
        1. Umpire override
        2. Video review
        3. Majority vote (TRIPLE)
        4. Captain consensus
        5. Abandon ball
        """
    
    @staticmethod
    def calculate_event_hash(innings_id, ball_number, ball_data, prev_hash):
        """
        Blockchain-like hashing:
        SHA256(innings_id + ball_number + json(ball_data) + prev_hash)
        Creates immutable chain
        """
```

**Task 8: PerformanceAggregationService** (`src/services/cricket/performance.py`)
```python
class PerformanceAggregationService:
    @staticmethod
    async def update_batting_innings(ball: Ball, db):
        """
        Real-time batting statistics:
        - runs_scored += ball.runs_scored
        - balls_faced += 1
        - strike_rate = (runs_scored / balls_faced) * 100
        - Update BattingInnings record
        """
    
    @staticmethod
    async def update_bowling_figures(ball: Ball, db):
        """
        Real-time bowling statistics:
        - balls_bowled += 1
        - runs_conceded += ball.runs_scored + ball.extras
        - wickets_taken += 1 if ball.is_wicket
        - economy = (runs_conceded / overs_bowled) * 6
        - Update BowlingFigures record
        """
    
    @staticmethod
    async def update_partnership(ball: Ball, db):
        """
        Track partnership between current batsmen:
        - runs_added += ball.runs_scored
        - balls_faced += 1
        - partnership_rate calculation
        """
    
    @staticmethod
    async def calculate_match_statistics(match_id, db):
        """
        Post-innings aggregations:
        - Top scorers
        - Best bowling figures
        - Highest partnerships
        - Fastest fifties/centuries
        """
```

**Task 11: MatchArchiveService** (`src/services/cricket/archive.py`)
```python
class MatchArchiveService:
    @staticmethod
    async def create_match_summary(match_id, db):
        """
        Generate post-match summary:
        - Final scores, result
        - Top performers (batting, bowling)
        - Match highlights (milestones, turning points)
        - Save to match_summaries table
        """
    
    @staticmethod
    async def generate_ball_by_ball_replay(innings_id, db):
        """
        Complete ball-by-ball narrative:
        - Each ball with commentary
        - Wicket details
        - Milestone achievements
        - Save to match_archives table (JSONB)
        """
    
    @staticmethod
    async def extract_highlights(match_id, db):
        """
        Identify key moments:
        - Wickets
        - Boundaries (4s, 6s)
        - Milestones (50s, 100s)
        - Match-turning overs
        - Hat-tricks, maiden overs
        """
```

### Routers Layer (Tasks 9-10)

**Task 9: Live Scoring Router** (`src/routers/cricket/live_scoring.py`)
```python
# Endpoints for ball-by-ball scoring
POST   /api/v1/cricket/innings - Start new innings
GET    /api/v1/cricket/innings/{id} - Get innings state
POST   /api/v1/cricket/innings/{id}/balls - Record ball
GET    /api/v1/cricket/innings/{id}/balls - Get ball history
POST   /api/v1/cricket/innings/{id}/end - End innings

POST   /api/v1/cricket/scoring/events - Submit scoring event (multi-validator)
GET    /api/v1/cricket/scoring/disputes - List disputes
POST   /api/v1/cricket/scoring/disputes/{id}/resolve - Resolve dispute
```

**Task 10: WebSocket Router** (`src/routers/cricket/websocket.py`)
```python
# Real-time match updates
WS     /ws/matches/{match_id}/live - Connect to live match

# Event types broadcasted:
- BALL_BOWLED: {ball, innings_state, striker, bowler}
- WICKET_FALLEN: {wicket, dismissed_batsman, new_batsman}
- OVER_COMPLETE: {over_number, runs_in_over, wickets_in_over}
- INNINGS_COMPLETE: {innings_number, total_runs, total_wickets}
- MATCH_COMPLETE: {winner, result_type, margin}
- SCORING_DISPUTE_RAISED: {dispute, conflicting_events}
- MILESTONE_ACHIEVED: {type: "FIFTY"|"CENTURY"|"HAT_TRICK", player}
```

### Testing (Tasks 12-16)

**Task 12: Manual Testing Script** (`scripts/test_phase3.py`)
```python
# Test scenarios:
1. Start innings with opening batsmen
2. Record 6-ball over with regular runs
3. Record wicket and batsman change
4. Test dual-scorer validation (matching events)
5. Test dual-scorer validation (mismatched events → dispute)
6. Test umpire override resolution
7. End innings and verify aggregates
8. Test ball sequence validation (reject out-of-order balls)
9. Test complete match (2 innings) with archive generation
10. Verify WebSocket event broadcasting
```

**Task 13: InningsService Unit Tests**
```python
# 10-12 tests covering:
- start_innings: success, match not live, invalid teams
- get_current_state: calculate from events, empty innings
- end_innings: success, already ended, validate totals
- validate opening batsmen selection
- error handling for invalid innings state
```

**Task 14: BallService Unit Tests**
```python
# 12-15 tests covering:
- record_ball: normal delivery, boundary, extra, wicket
- validate_ball_sequence: correct order, duplicate ball, gap in sequence
- get_ball_history: full replay, filter by over
- event sourcing immutability (no updates to past balls)
- aggregate updates triggered correctly
```

**Task 15: ScoringIntegrityService Unit Tests**
```python
# 15-18 tests covering:
- submit_scoring_event: SINGLE (auto-validate), HONOR (no validation)
- validate_dual_scoring: matching events, mismatched events
- calculate_event_hash: blockchain integrity, hash chain validation
- resolve_dispute: umpire override, video review, captain consensus
- consensus algorithm for TRIPLE validation (2/3 majority)
```

**Task 16: Integration Tests**
```python
# 5-7 comprehensive workflow tests:
1. Complete innings workflow (start → balls → wickets → end)
2. Dual-scorer consensus flow (event submission → validation → ball creation)
3. Dispute resolution flow (mismatch → dispute → resolution → ball creation)
4. Performance aggregation (balls → batting_innings + bowling_figures updates)
5. Match archive generation (complete match → summary + replay)
6. WebSocket event broadcasting (ball recorded → event sent to all connections)
```

---

## 🏗️ Architecture Patterns

### Event Sourcing Implementation

```python
# Every ball creates immutable record
ball = Ball(
    id=uuid4(),
    innings_id=innings_id,
    over_id=over_id,
    ball_number=3,
    bowler_id=bowler_id,
    striker_id=striker_id,
    runs_scored=4,
    extras=0,
    is_wicket=False,
    created_at=datetime.utcnow()
)

# Current innings state DERIVED from events
total_runs = db.query(func.sum(Ball.runs_scored + Ball.extras))
                .filter(Ball.innings_id == innings_id)
                .scalar()

# NEVER update past balls - use disputed flag if needed
# Corrections create new dispute resolution records
```

### Multi-Validator Consensus

```python
# DUAL validation example
scorer_a_event = ScoringEvent(
    scorer_id=team_a_scorer_id,
    ball_data={"runs": 4, "wicket": False, ...},
    event_hash=calculate_hash(...)
)

scorer_b_event = ScoringEvent(
    scorer_id=team_b_scorer_id,
    ball_data={"runs": 4, "wicket": False, ...},
    event_hash=calculate_hash(...)
)

if scorer_a_event.event_hash == scorer_b_event.event_hash:
    # Auto-validate and create Ball record
    create_ball_from_consensus(scorer_a_event.ball_data)
else:
    # Create dispute
    create_dispute(scorer_a_event, scorer_b_event)
    notify_officials(dispute_id)
```

### WebSocket Event Broadcasting

```python
# On ball recorded
async def broadcast_ball_event(match_id: UUID, ball: Ball):
    connections = active_connections[match_id]
    
    event = {
        "type": "BALL_BOWLED",
        "data": {
            "ball": BallResponse.from_orm(ball),
            "innings_state": await get_innings_state(ball.innings_id),
            "striker": await get_batsman(ball.striker_id),
            "bowler": await get_bowler(ball.bowler_id)
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    for connection in connections:
        await connection.send_json(event)
```

---

## 📊 Database Tables Used

### Event Sourcing Tables
- **innings** - Innings metadata (match_id, batting_team, target_score)
- **overs** - Over records (innings_id, over_number, bowler_id)
- **balls** - Immutable ball records (over_id, ball_number, runs, extras, wicket)
- **wickets** - Dismissal details (ball_id, dismissal_type, fielder_id)

### Scoring Integrity Tables
- **scoring_events** - Multi-validator event submissions (scorer_id, event_hash, status)
- **scoring_disputes** - Mismatched events (event_a_id, event_b_id, dispute_reason)
- **scoring_consensus** - Resolution records (dispute_id, resolution_method, final_ball_id)

### Performance Aggregation Tables
- **batting_innings** - Live batting stats (runs, balls, strike_rate)
- **bowling_figures** - Live bowling stats (overs, runs, wickets, economy)
- **partnerships** - Partnership tracking (batsman_a_id, batsman_b_id, runs, balls)

### Archive Tables
- **match_summaries** - Post-match summaries (winner, top_scorers, best_bowlers)
- **match_archives** - Complete ball-by-ball replay (JSONB with all balls)

---

## 🎯 Success Criteria

### Functional Requirements
- ✅ Record balls with event sourcing pattern (immutable records)
- ✅ Multi-validator consensus working for DUAL/TRIPLE tiers
- ✅ Real-time aggregation updates (batting, bowling, partnerships)
- ✅ WebSocket broadcasting live events to spectators
- ✅ Complete match archive generation with replay capability
- ✅ Dispute resolution workflow (raise → notify → resolve)

### Quality Requirements
- ✅ 80%+ test coverage on new services
- ✅ 100% test pass rate (target: 60+ tests total)
- ✅ Professional commit history (1 commit per task)
- ✅ Comprehensive documentation (schemas, services, workflows)
- ✅ Manual testing script validates all workflows

### Performance Requirements
- Ball recording latency: < 100ms
- WebSocket broadcast: < 50ms after ball recorded
- Innings state calculation: < 200ms (derived from events)
- Aggregate updates: Real-time (< 100ms)

---

## 📚 Reference Documents

### Design Documents
- `docs/API_DESIGN.md` - Complete endpoint specifications (live scoring section)
- `docs/schema.md` - Event sourcing patterns, consensus algorithm details
- `.github/copilot-instructions.md` - Development guidelines

### Key Files to Review
- `src/models/cricket/innings.py` - Innings model (verify exists)
- `src/models/cricket/ball.py` - Ball, Wicket models (verify exists)
- `src/models/cricket/scoring.py` - ScoringEvent, Dispute models (verify exists)
- `src/models/cricket/performance.py` - BattingInnings, BowlingFigures (verify exists)
- `src/models/cricket/archive.py` - MatchSummary, MatchArchive (verify exists)

---

## 🚀 Implementation Timeline

### Session 1 (Tasks 1-5): Event Sourcing Foundation
- ✅ Task 1: Planning & setup
- 🔲 Task 2: Innings schemas
- 🔲 Task 3: Ball schemas
- 🔲 Task 4: InningsService
- 🔲 Task 5: BallService

### Session 2 (Tasks 6-8): Scoring Integrity & Aggregation
- 🔲 Task 6: Scoring integrity schemas
- 🔲 Task 7: ScoringIntegrityService (consensus algorithm)
- 🔲 Task 8: PerformanceAggregationService

### Session 3 (Tasks 9-12): Routers & Manual Testing
- 🔲 Task 9: Live scoring router
- 🔲 Task 10: WebSocket implementation
- 🔲 Task 11: Archive service
- 🔲 Task 12: Manual testing script

### Session 4 (Tasks 13-18): Testing & Merge
- 🔲 Task 13-15: Unit tests (innings, ball, scoring integrity)
- 🔲 Task 16: Integration tests
- 🔲 Task 17: Code review & documentation
- 🔲 Task 18: Merge to master with tag v3.0.0-phase3-live-scoring

---

## 🎓 Lessons from Phase 2 (Applied to Phase 3)

1. **Test incrementally**: Write unit tests for each service as implemented
2. **Manual testing first**: Create test script early to discover bugs
3. **Simplify integration tests**: Focus on workflows, not field validation
4. **Professional commits**: One commit per task with detailed messages
5. **Document as you go**: Update schemas with examples and explanations

---

## ✨ Next Steps

**Current Task**: Task 1 - Verify models exist, review API design

**Action Items**:
1. Check if all models exist in `src/models/cricket/`
2. Review `docs/API_DESIGN.md` for live scoring endpoints
3. Commit this plan document
4. Begin Task 2: Innings schemas implementation

---

**Phase 3 Status**: 🚧 IN PROGRESS (Task 1/18)  
**Branch**: `feature/phase3-live-scoring`  
**Next Milestone**: Event Sourcing Foundation (Tasks 1-5)
