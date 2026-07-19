from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.users.users import user_router
from routes.categories.categories import category_router
from routes.notes.notes import note_router
from routes.ai.ai import ai_router

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(category_router)
app.include_router(note_router)
app.include_router(ai_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}