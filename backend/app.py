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
import io

from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from groq import Groq

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
#app.mount("/static", StaticFiles(directory="backend/static"), name="static")
# =============================
# ENV CONFIG
# =============================

AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")  # groq or ollama
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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
# LOAD BLIP (Image Caption)
# =============================

device = "cuda" if torch.cuda.is_available() else "cpu"

processor = BlipProcessor.from_pretrained(
    "Salesforce/blip-image-captioning-base",
    use_fast=False
)

blip_model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base"
)

blip_model.to(device)
blip_model.eval()

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
    else:
        return call_groq(prompt)

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
# IMAGE CHAT
# =============================

@app.post("/image-chat")
async def image_chat(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        inputs = processor(images=image, return_tensors="pt").to(device)

        with torch.no_grad():
            output = blip_model.generate(**inputs)

        caption = processor.decode(output[0], skip_special_tokens=True)

        prompt = f"""
Image description:
{caption}

Explain this image in detail.
"""

        reply = generate_ai_response(prompt)

        return {"reply": reply}

    except Exception as e:
        return {"reply": f"Image error: {str(e)}"}

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



