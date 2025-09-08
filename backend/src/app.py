from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agent.my_local_agent.route import app as my_local_agent_app

# Define the FastAPI app
app = FastAPI()

# add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount the app
app.mount("/agent/my_local_agent", my_local_agent_app)
