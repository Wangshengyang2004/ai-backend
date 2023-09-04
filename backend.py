from fastapi import FastAPI, HTTPException, Depends
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from uuid import uuid4
from typing import Optional
import re
import psutil
import socket

app = FastAPI()

# Connect to MongoDB
client = AsyncIOMotorClient("mongodb://localhost:27017/")
db = client['hangman_game']
leaderboard_collection = db['leaderboard']

# In-memory database to store game states
game_states = {}

#OpenAI Call
def openai_call(difficulty: Optional[str] = "medium"):
    base_query =  """
    Now let's play a game of hangman and 
    your duty is give me a random question and the hint of it. 
    In your response, be short, and please show me the word as, say, 
    {word: (one word for what the player will guess)}. 
    And give me a hint as {hint: (base on the word)}. 
    For example, you can say "Ok, let's play a game of hangman. 
    The word is {word: banana}. The hint is {hint: kind of fruit}."
    """
    difficulty_query = f"{difficulty} difficulty"
    query = base_query + difficulty_query
    # Send query to OpenAI API
    return "This is a sample reponse. {word: banana} {hint: kind of fruit}"

# Get word from OpenAI response
def get_random_word():
    response = openai_call()
    match = re.search(r"\{word: (.+?)\}", response)
    return match.group(1) if match else "No word found"

# Get hint from OpenAI response
def generate_hint():
    response = openai_call()
    match = re.search(r"\{hint: (.+?)\}", response)
    return match.group(1) if match else "No hint found"

# Function to get game state
def get_game_state(session_id: str):
    return game_states.get(session_id, None)

# Initialize game state
@app.get("/start")
async def start_game(difficulty: Optional[str] = "medium"):
    session_id = str(uuid4())
    current_word = get_random_word()
    remaining_tries = 6 if difficulty == "medium" else (9 if difficulty == "easy" else 3)
    guessed_letters = []
    hints = []
    game_states[session_id] = {
        "current_word": current_word,
        "remaining_tries": remaining_tries,
        "guessed_letters": guessed_letters,
        "hints": hints,
        "difficulty": difficulty
    }
    return {"session_id": session_id, "status": "Game started", "remaining_tries": remaining_tries}

# Get hint
@app.get("/hint/{session_id}")
async def get_hint(session_id: str, state: dict = Depends(get_game_state)):
    if state is None:
        raise HTTPException(status_code=404, detail="Invalid session_id")
    hint = generate_hint()
    state['hints'].append(hint)
    return {"status": "Hint generated", "hint": hint}

@app.get("/guess/{session_id}/{letter}")
async def guess_letter(session_id: str, letter: str, state: dict = Depends(get_game_state)):
    if state is None:
        raise HTTPException(status_code=404, detail="Invalid session_id")
    current_word = state['current_word']
    remaining_tries = state['remaining_tries']
    guessed_letters = state['guessed_letters']
    hints = state['hints']
    if letter in guessed_letters:
        return {"status": "Letter already guessed", "guessed_letters": guessed_letters, "remaining_tries": remaining_tries}
    guessed_letters.append(letter)
    if letter not in current_word:
        remaining_tries -= 1
    state['remaining_tries'] = remaining_tries
    state['guessed_letters'] = guessed_letters
    if remaining_tries <= 0:
        return {"status": "Game Over", "guessed_letters": guessed_letters, "remaining_tries": remaining_tries, "hints": hints}
    if all(l in guessed_letters for l in current_word):
        return {"status": "You Won!", "guessed_letters": guessed_letters, "remaining_tries": remaining_tries, "hints": hints}
    return {"status": "Guess received", "guessed_letters": guessed_letters, "remaining_tries": remaining_tries, "hints": hints}

@app.post("/leaderboard/{username}/{score}")
async def update_leaderboard(username: str, score: int):
    await leaderboard_collection.insert_one({"username": username, "score": score})
    return {"status": "Score updated"}

@app.get("/leaderboard")
async def get_leaderboard():
    leaderboard = []
    async for document in leaderboard_collection.find().sort("score", -1).limit(10):
        leaderboard.append(document)
    return {"leaderboard": leaderboard}

@app.get("/end/{session_id}")
async def end_game(session_id: str, state: dict = Depends(get_game_state)):
    if state is None:
        raise HTTPException(status_code=404, detail="Invalid session_id")
    del game_states[session_id]
    return {"status": "Game ended"}

@app.get("/status/{session_id}")
async def game_status(session_id: str, state: dict = Depends(get_game_state)):
    if state is None:
        raise HTTPException(status_code=404, detail="Invalid session_id")
    return {"status": "Game in Progress", "game_state": state}

@app.get("/alive")
async def read_alive():

    # Check CPU Usage
    cpu_percent = psutil.cpu_percent()
    if cpu_percent < 80:
        cpu_status = "CPU usage is healthy"
    else:
        cpu_status = "CPU usage is high"

    # Check MongoDB
    try:
        client = AsyncIOMotorClient("mongodb://localhost:27017/")
        db = client['alive']
        await db.info.insert_one({"test": "1"})
        await db.info.delete_one({"test": "1"})
        db_status = "MongoDB is alive"
    except Exception as e:
        db_status = f"MongoDB error: {e}"


    # IP Address
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    # Memory Usage
    memory_info = psutil.virtual_memory()
    memory_percent = memory_info.percent

    # Disk Usage
    disk_info = psutil.disk_usage('/')
    disk_percent = disk_info.percent
    info = {
        "status": "I'm alive!",
        "db_status": db_status,
        "cpu_status": cpu_status,
        "cpu_percent": f"{cpu_percent}%",
        "ip_address": ip_address,
        "memory_percent": f"{memory_percent}%",
        "disk_percent": f"{disk_percent}%"
    }
    db.insert_one(info)
    return info



