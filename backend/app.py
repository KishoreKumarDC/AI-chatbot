from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import os
import json
import requests
import subprocess
import sys

from groq import Groq
from serpapi.google_search import GoogleSearch

# =============================
# BASIC CONFIG
# =============================

app = FastAPI()

BASE_DIR = "backend"
TEMPLATE_DIR = f"{BASE_DIR}/templates"
STATIC_DIR = f"{BASE_DIR}/static"
USER_FILE = f"{BASE_DIR}/users.json"

templates = Jinja2Templates(directory=TEMPLATE_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# =============================
# ENV CONFIG
# =============================
from dotenv import load_dotenv
import os

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# HF_MODEL_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"
HF_MODEL_URL = "https://router.huggingface.co/hf-inference/models/google/vit-base-patch16-224"

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "tinyllama"
GROQ_MODEL = "llama-3.1-8b-instant"

client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)

# =============================
# CORS
# =============================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================
# USER STORAGE
# =============================

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

# =============================
# AI FUNCTIONS
# =============================

def call_ollama(prompt: str):
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }

        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        return r.json().get("response", "").strip()

    except:
        return "⚠ Ollama not running."

def call_groq(prompt: str):

    try:

        if not client:
            return "⚠ GROQ_API_KEY not set."

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional AI assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠ Groq error: {str(e)}"

def generate_ai_response(prompt: str):

    if AI_PROVIDER == "ollama":
        return call_ollama(prompt)

    return call_groq(prompt)

# =============================
# IMAGE RECOGNITION (HUGGINGFACE)
# =============================

def recognize_image(image_bytes):

    try:

        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/octet-stream"
        }

        response = requests.post(
            HF_MODEL_URL,
            headers=headers,
            data=image_bytes,
            timeout=30
        )

        if response.status_code != 200:
            print("HF Status:", response.status_code)
            print("HF Response:", response.text)
            return "object"

        result = response.json()

        if isinstance(result, list) and len(result) > 0:
            return result[0].get("label", "object")

        return "object"

    except Exception as e:
        print("HF error:", e)
        return "object"
    
# =============================
# IMAGE SEARCH (SERPAPI)
# =============================

def search_images(query):

    try:

        params = {
            "engine": "google_images",
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 5
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        images = []

        if "images_results" in results:

            for img in results["images_results"][:5]:

                images.append({
                    "title": img.get("title"),
                    "thumbnail": img.get("thumbnail"),
                    "link": img.get("link")
                })

        return images

    except Exception as e:

        print("Image search error:", e)
        return []

# =============================
# AUTH ROUTES
# =============================

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):

    users = load_users()

    if username in users:
        return HTMLResponse("User exists.<br><a href='/register'>Back</a>")

    users[username] = {"password": password}
    save_users(users)

    return RedirectResponse("/", status_code=302)

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):

    users = load_users()

    if username in users and users[username]["password"] == password:

        response = RedirectResponse("/dashboard", status_code=302)
        response.set_cookie("user", username, httponly=True)

        return response

    return HTMLResponse("Invalid login.<br><a href='/'>Try again</a>")

@app.get("/logout")
def logout():

    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("user")

    return response

# =============================
# DASHBOARD
# =============================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):

    user = request.cookies.get("user")

    if not user:
        return RedirectResponse("/", status_code=302)

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "username": user}
    )

@app.get("/chat-ui", response_class=HTMLResponse)
def chat_ui(request: Request):

    user = request.cookies.get("user")

    if not user:
        return RedirectResponse("/", status_code=302)

    return templates.TemplateResponse("chat-ui.html", {"request": request})

# =============================
# CHAT API
# =============================

@app.post("/chat")
async def chat(data: dict):

    msg = data.get("message", "").strip()

    if not msg:
        return {"reply": "Please enter message."}

    if msg.lower() in ["hi", "hello", "hey"]:
        return {"reply": "Hello 👋 How can I help you?"}

    reply = generate_ai_response(msg)

    return {"reply": reply}

# =============================
# IMAGE CHAT (UPLOAD IMAGE)
# =============================

@app.post("/image-chat")
async def image_chat(file: UploadFile = File(...)):

    try:

        image_bytes = await file.read()

        # Step 1 detect object
        label = recognize_image(image_bytes)

        # Step 2 search similar images
        images = search_images(label)

        titles = "\n".join([img["title"] for img in images if img["title"]])

        prompt = f"""
User uploaded an image.

Detected object: {label}

Image titles:
{titles}

Explain what this object is.
"""

        explanation = generate_ai_response(prompt)

        return {
            "detected_object": label,
            "images": images,
            "reply": explanation
        }

    except Exception as e:

        return {"reply": str(e)}

# =============================
# DESKTOP AI CONTROL
# =============================

desktop_process = None

@app.post("/launch-ai")
def launch_ai():

    global desktop_process

    if desktop_process is None or desktop_process.poll() is not None:

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        script_path = os.path.join(project_root, "ai_chat.py")

        desktop_process = subprocess.Popen([sys.executable, script_path])

    return RedirectResponse("/dashboard", status_code=303)

@app.post("/close-ai")
def close_ai():

    global desktop_process

    if desktop_process and desktop_process.poll() is None:

        desktop_process.terminate()
        desktop_process = None

    return RedirectResponse("/dashboard", status_code=303)

print("HF KEY:", HF_API_KEY)
