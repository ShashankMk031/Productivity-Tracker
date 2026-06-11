from fastapi import APIRouter
from database.db import get_db
from schemas.response import APIResponse
from services.scoring_service import calculate_productivity_scores

router = APIRouter(prefix="/scores", tags=["Scores"])

@router.get("/today")
def get_today_scores():
    with get_db() as db:
        scores = calculate_productivity_scores(db)
        return APIResponse(data=scores)
