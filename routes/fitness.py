from datetime import datetime

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/fitness", tags=["Fitness Sync"])

# In-memory storage for fitness connections and data
fitness_connections_db: dict[int, dict] = {}
fitness_data_db: dict[int, dict] = {}


@router.post("/connect", summary="Connect to fitness service")
async def fitness_connect(user_id: int):
    pass
    fitness_connections_db[user_id] = {
        "connected": True,
        "connected_at": datetime.now().isoformat(),
    }
    return {
        "user_id": user_id,
        "status": "connected",
        "connected_at": fitness_connections_db[user_id]["connected_at"],
    }


@router.post("/disconnect", summary="Disconnect integration")
async def fitness_disconnect(user_id: int):
    pass
    if user_id in fitness_connections_db:
        fitness_connections_db[user_id]["connected"] = False
        fitness_connections_db[user_id]["disconnected_at"] = datetime.now().isoformat()
        return {
            "user_id": user_id,
            "status": "disconnected",
            "disconnected_at": fitness_connections_db[user_id]["disconnected_at"],
        }
    raise HTTPException(
        status_code=404, detail="No active fitness connection found for user."
    )


@router.get("/data", summary="Fetch recent fitness data")
async def fitness_data(user_id: int):
    pass
    # Simulate fitness data
    data = fitness_data_db.get(
        user_id,
        {
            "workouts": [
                {
                    "date": (datetime.now()).date().isoformat(),
                    "type": "run",
                    "duration": 30,
                    "calories": 300,
                }
            ],
            "steps": 10000,
            "calories": 2200,
        },
    )
    return {"user_id": user_id, **data}
