import os
import traceback
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Security, Request
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from services.decision_maker_svc import DecisionMakerSvc
load_dotenv()

API_SECRET_KEY = os.getenv("API_SECRET_KEY")

api_key_header = APIKeyHeader(name="apiKey", auto_error=False)

app = FastAPI(
    title="WaveLineAI",
    description="AI-Services",
    version="0.1.0"
)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_SECRET_KEY:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Error: 401 - Invalid or missing API key",
    )

@app.post("/api/v1/buildDecisionSteps", tags=['APIs'], dependencies=[Depends(get_api_key)])
def buildDecisionSteps(steps: list[dict]):
    try:
        decisionMakerSvc = DecisionMakerSvc(steps=steps)
        return decisionMakerSvc.get_steps_with_decisions()
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(
            status_code=400,
            content={
                "error": str(e),
                "stacktrace": tb
            }
        )


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)