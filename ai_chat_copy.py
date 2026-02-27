import sys
import requests
import speech_recognition as sr

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel
)
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QLinearGradient


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

        # Glass effect
        #self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
    QWidget {
        background-color: #f5f5f5;
        border-radius: 15px;
    }
""")

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 220);
                border-radius: 20px;
                border: 1px solid rgba(200, 200, 200, 120);
            }

            QTextEdit {
                background: transparent;
                border: none;
                padding: 12px;
                font-size: 13px;
                color: #222;
            }

            QLineEdit {
                background-color: rgba(255,255,255,180);
                border-radius: 12px;
                padding: 8px;
                border: 1px solid #ddd;
            }

            QPushButton {
                background-color: white;
                color: #333;
                border-radius: 12px;
                padding: 6px;
                border: 1px solid #ddd;
            }

            QPushButton:hover {
                background-color: #f2f2f2;
            }
        """)

        layout = QVBoxLayout()

        # Top bar
        top_bar = QHBoxLayout()
        top_bar.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedWidth(30)
        self.close_btn.clicked.connect(self.animate_close)
        top_bar.addWidget(self.close_btn)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask anything...")
        self.input_field.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)

        self.voice_btn = QPushButton("🎤")
        self.voice_btn.clicked.connect(self.voice_input)

        layout.addLayout(top_bar)
        layout.addWidget(self.chat_area)
        layout.addWidget(self.input_field)

        bottom = QHBoxLayout()
        bottom.addWidget(self.voice_btn)
        bottom.addWidget(self.send_btn)

        layout.addLayout(bottom)
        self.setLayout(layout)

    # Smooth animation
    def animate_open(self):
        self.show()
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.start()

    def animate_close(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.finished.connect(self.hide)
        self.anim.start()

    # Voice input
    def voice_input(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.chat_area.append("<i>Listening...</i>")
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            self.input_field.setText(text)
            self.send_message()
        except:
            self.chat_area.append("<b>AI:</b> ⚠ Voice not recognized")

    # Send message
    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return

        self.chat_area.append(f"<b>You:</b> {message}")
        self.input_field.clear()

        try:
            response = requests.post(
                API_URL,
                json={"message": message},
                timeout=60
            )
            data = response.json()
            reply = data.get("reply", "No response")
            self.chat_area.append(f"<b>AI:</b> {reply}")
        except:
            self.chat_area.append("<b>AI:</b> ⚠ Cannot connect to backend")

        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )


# ================= FLOATING BUBBLE =================
import os
from PyQt5.QtWidgets import QWidget, QPushButton
from PyQt5.QtCore import Qt, QPoint, QSize, QTimer
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtGui import QTransform


class FloatingBubble(QWidget):
    def __init__(self):
        super().__init__()

        self.setFixedSize(100, 100)

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        self.setAttribute(Qt.WA_TranslucentBackground)

        # -------- VARIABLES --------
        self.oldPos = None
        self.dragging = False
        self.angle = 0

        # -------- IMAGE LOAD --------
        base_path = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(base_path, "ai_logo.jpg")

        self.original_pixmap = QPixmap(image_path)

        # -------- BUTTON --------
        self.button = QPushButton(self)
        self.button.setFixedSize(100, 100)
        self.button.move(0, 0)

        self.button.setStyleSheet("""
            QPushButton {
                border-radius: 50px;
                background-color: #e6e6e6;
                border: 2px solid #cccccc;
            }
            QPushButton:hover {
                background-color: #dddddd;
            }
        """)

        if self.original_pixmap.isNull():
            print("❌ Image failed to load.")
        else:
            self.update_icon()

        # -------- ROTATION TIMER --------
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_logo)
        self.timer.start(30)

        # IMPORTANT: override button mouse events
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
            75, 75,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.button.setIcon(QIcon(rotated))
        self.button.setIconSize(QSize(75, 75))

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
            self.chat_window.move(self.x() - 380, self.y() - 520)
            self.chat_window.animate_open()
            
# ================= RUN =================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    bubble = FloatingBubble()
    bubble.move(1000, 500)
    bubble.show()

    sys.exit(app.exec_())
