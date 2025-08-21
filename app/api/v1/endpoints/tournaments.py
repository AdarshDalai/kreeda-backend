from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_tournaments():
    """Get all tournaments."""
    return {"message": "Get tournaments endpoint - Coming soon!"}

@router.post("/")
async def create_tournament():
    """Create a new tournament."""
    return {"message": "Create tournament endpoint - Coming soon!"}

@router.get("/{tournament_id}")
async def get_tournament(tournament_id: str):
    """Get tournament by ID."""
    return {"message": f"Get tournament {tournament_id} endpoint - Coming soon!"}

@router.get("/{tournament_id}/matches")
async def get_tournament_matches(tournament_id: str):
    """Get all matches in a tournament."""
    return {"message": f"Get tournament {tournament_id} matches endpoint - Coming soon!"}
