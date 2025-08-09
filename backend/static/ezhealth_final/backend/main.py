from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import auth,image

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(image.router, prefix="/images", tags=["Image Upload"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "EzHealth API is Running"}
