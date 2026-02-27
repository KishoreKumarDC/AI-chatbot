import sys
import os
import requests
import speech_recognition as sr

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton
)
from PyQt5.QtCore import Qt, QPoint, QSize, QTimer, QPropertyAnimation
from PyQt5.QtGui import QIcon, QPixmap, QTransform

API_URL = "http://127.0.0.1:8000/chat"

# ================= CHAT WINDOW =================
class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setFixedSize(360, 480)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 235);
                border-radius: 18px;
                border: 1px solid #ddd;
            }

            QTextEdit {
                background: transparent;
                border: none;
                padding: 10px;
                font-size: 13px;
            }

            QLineEdit {
                border-radius: 10px;
                padding: 8px;
                border: 1px solid #ccc;
            }

            QPushButton {
                background-color: #f0f0f0;
                border-radius: 10px;
                padding: 6px;
                border: 1px solid #ccc;
            }

            QPushButton:hover {
                background-color: #e2e2e2;
            }
        """)

        layout = QVBoxLayout()

        # Close button
        top = QHBoxLayout()
        top.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(30)
        close_btn.clicked.connect(self.animate_close)
        top.addWidget(close_btn)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask anything...")
        self.input_field.returnPressed.connect(self.send_message)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)

        voice_btn = QPushButton("🎤")
        voice_btn.clicked.connect(self.voice_input)

        layout.addLayout(top)
        layout.addWidget(self.chat_area)
        layout.addWidget(self.input_field)

        bottom = QHBoxLayout()
        bottom.addWidget(voice_btn)
        bottom.addWidget(send_btn)

        layout.addLayout(bottom)
        self.setLayout(layout)

    # ================= ANIMATION =================
    def animate_open(self):
        self.show()
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(200)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.start()

    def animate_close(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(200)
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.finished.connect(self.hide)
        self.anim.start()

    # ================= VOICE INPUT =================
    def voice_input(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                self.chat_area.append("<i>Listening...</i>")
                audio = recognizer.listen(source)

            text = recognizer.recognize_google(audio)
            self.input_field.setText(text)
            self.send_message()

        except:
            self.chat_area.append("<b>AI:</b> ⚠ Voice not recognized")

    # ================= SEND MESSAGE =================
    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return

        self.chat_area.append(f"<b>You:</b> {message}")
        self.input_field.clear()
        self.chat_area.append("<i>AI is thinking...</i>")

        QApplication.processEvents()  # Prevent UI freeze

        try:
            response = requests.post(
                API_URL,
                json={"message": message},
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "⚠ AI returned empty response.")
            else:
                reply = f"⚠ Backend error ({response.status_code})"

        except requests.exceptions.ConnectionError:
            reply = "⚠ Cannot connect to backend. Is FastAPI running?"

        except Exception:
            reply = "⚠ Unexpected error."

        # Remove thinking message
        self.chat_area.undo()

        self.chat_area.append(f"<b>AI:</b> {reply}")

        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

# ================= FLOATING BUBBLE =================
class FloatingBubble(QWidget):
    def __init__(self):
        super().__init__()

        self.setFixedSize(90, 90)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        self.setAttribute(Qt.WA_TranslucentBackground)

        self.oldPos = None
        self.dragging = False
        self.angle = 0

        base_path = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(base_path, "ai_logo.jpg")

        self.original_pixmap = QPixmap(image_path)

        self.button = QPushButton(self)
        self.button.setFixedSize(90, 90)
        self.button.setStyleSheet("""
            QPushButton {
                border-radius: 45px;
                background-color: #f0f0f0;
                border: 2px solid #ccc;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
        """)

        if not self.original_pixmap.isNull():
            self.update_icon()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_logo)
        self.timer.start(30)

        self.button.mousePressEvent = self.mousePressEvent
        self.button.mouseMoveEvent = self.mouseMoveEvent
        self.button.mouseReleaseEvent = self.mouseReleaseEvent

        self.chat_window = ChatWindow()

    # ================= ROTATION =================
    def rotate_logo(self):
        if not self.original_pixmap.isNull():
            self.angle = (self.angle + 2) % 360
            self.update_icon()

    def update_icon(self):
        rotated = self.original_pixmap.transformed(
            QTransform().rotate(self.angle),
            Qt.SmoothTransformation
        )

        rotated = rotated.scaled(
            70, 70,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.button.setIcon(QIcon(rotated))
        self.button.setIconSize(QSize(70, 70))

    # ================= DRAGGING =================
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()
            self.dragging = False

    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = event.globalPos() - self.oldPos
            if delta.manhattanLength() > 5:
                self.dragging = True

            self.move(self.pos() + delta)
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if not self.dragging:
            self.toggle_chat()

        self.oldPos = None

    # ================= TOGGLE CHAT =================
    def toggle_chat(self):
        if self.chat_window.isVisible():
            self.chat_window.animate_close()
        else:
            self.chat_window.move(self.x() - 380, self.y() - 500)
            self.chat_window.animate_open()

# ================= RUN =================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    bubble = FloatingBubble()
    bubble.move(1000, 500)
    bubble.show()

    sys.exit(app.exec_())