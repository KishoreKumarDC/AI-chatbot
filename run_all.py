
import subprocess
import sys
import os

 # Get current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_backend():
      return subprocess.Popen(
           ["uvicorn", "backend.app:app", "--reload"],
         cwd=BASE_DIR
      )


def run_telegram():
     return subprocess.Popen(
         [sys.executable, "telegram_bot.py"],
         cwd=BASE_DIR
     )

if __name__ == "__main__":
     print("🚀 Starting Backend...")
     backend = run_backend()

     print("🤖 Starting Telegram Bot...")
     telegram = run_telegram()

     print("🖥 Starting Desktop AI...")
     

     backend.wait()
     telegram.wait()
    