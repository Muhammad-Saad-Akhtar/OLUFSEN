from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QLineEdit
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer, QRunnable, QThreadPool, QMetaObject, Q_ARG
import sys
import main  # Import your OLUFSEN AI backend file
import webbrowser
import pyautogui
import os
import speech_recognition as sr

class Worker(QRunnable):
    def __init__(self, text, callback):
        super().__init__()
        self.text = text
        self.callback = callback

    def run(self):
        response = main.execute_task(self.text) or main.chatbot_response(self.text)
        QMetaObject.invokeMethod(self.callback, "call", Qt.QueuedConnection, Q_ARG(str, response))

class OlufsenUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.threadpool = QThreadPool()

    def initUI(self):
        self.setWindowTitle("OLUFSEN AI Assistant")
        self.setGeometry(200, 200, 600, 700)
        self.setStyleSheet("background-color: #121212; color: white;")
        
        layout = QVBoxLayout()
        
        self.title_label = QLabel("OLUFSEN AI", self)
        self.title_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background-color: #1E1E1E; border: none; padding: 10px;")
        layout.addWidget(self.chat_display)
        
        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("Type your message here...")
        self.user_input.setStyleSheet("background-color: #333; border-radius: 10px; padding: 8px;")
        self.user_input.returnPressed.connect(self.process_input)
        layout.addWidget(self.user_input)
        
        self.send_button = QPushButton("Send", self)
        self.send_button.setStyleSheet("background-color: #00C853; border-radius: 10px; padding: 10px;")
        self.send_button.clicked.connect(self.process_input)
        layout.addWidget(self.send_button)
        
        self.voice_button = QPushButton("🎙️ Voice Command", self)
        self.voice_button.setStyleSheet("background-color: #6200EA; border-radius: 10px; padding: 10px;")
        self.voice_button.clicked.connect(self.voice_input)
        layout.addWidget(self.voice_button)
        
        self.screenshot_button = QPushButton("Take Screenshot", self)
        self.screenshot_button.setStyleSheet("background-color: #FF6F00; border-radius: 10px; padding: 10px;")
        self.screenshot_button.clicked.connect(self.take_screenshot)
        layout.addWidget(self.screenshot_button)
        
        self.theme_button = QPushButton("Toggle Dark/Light Mode", self)
        self.theme_button.setStyleSheet("background-color: #00796B; border-radius: 10px; padding: 10px;")
        self.theme_button.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_button)
        
        self.shutdown_button = QPushButton("Shutdown PC", self)
        self.shutdown_button.setStyleSheet("background-color: #D32F2F; border-radius: 10px; padding: 10px;")
        self.shutdown_button.clicked.connect(self.shutdown_pc)
        layout.addWidget(self.shutdown_button)
        
        self.system_status = QLabel("System Status: Loading...", self)
        self.system_status.setFont(QFont("Arial", 12))
        layout.addWidget(self.system_status)
        
        self.refresh_status()
        self.setLayout(layout)
        self.dark_mode = True  # Track theme mode
        
    def process_input(self):
        user_text = self.user_input.text()
        if user_text:
            self.chat_display.append(f"<b>You:</b> {user_text}")
            worker = Worker(user_text, self.display_response)
            self.threadpool.start(worker)
            self.user_input.clear()

    def display_response(self, response):
        QMetaObject.invokeMethod(self.chat_display, "append", Qt.QueuedConnection, Q_ARG(str, f"<b>OLUFSEN:</b> {response}"))
    
    def voice_input(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.chat_display.append("<b>OLUFSEN:</b> Listening...")
            try:
                audio = recognizer.listen(source, timeout=5)  # Timeout prevents freezing
                text = recognizer.recognize_google(audio)
                self.chat_display.append(f"<b>You (Voice):</b> {text}")
                self.process_input()
            except sr.UnknownValueError:
                self.chat_display.append("<b>OLUFSEN:</b> Sorry, I couldn't understand.")
            except sr.RequestError:
                self.chat_display.append("<b>OLUFSEN:</b> Speech service unavailable.")
    
    def take_screenshot(self):
        screenshot_path = os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
        pyautogui.screenshot(screenshot_path)
        self.chat_display.append(f"<b>OLUFSEN:</b> Screenshot saved at {screenshot_path}")

    def shutdown_pc(self):
        os.system("shutdown /s /t 1")
        self.chat_display.append("<b>OLUFSEN:</b> Shutting down the PC...")
    
    def toggle_theme(self):
        if self.dark_mode:
            self.setStyleSheet("background-color: #F5F5F5; color: black;")
            self.chat_display.setStyleSheet("background-color: #E0E0E0; color: black;")
            self.user_input.setStyleSheet("background-color: #FFFFFF; color: black;")
            self.dark_mode = False
        else:
            self.setStyleSheet("background-color: #121212; color: white;")
            self.chat_display.setStyleSheet("background-color: #1E1E1E; color: white;")
            self.user_input.setStyleSheet("background-color: #333; color: white;")
            self.dark_mode = True
    
    def refresh_status(self):
        self.system_status.setText(f"System Status: {main.system_health()}")
        QTimer.singleShot(5000, self.refresh_status)  # Refresh every 5 seconds

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OlufsenUI()
    window.show()
    sys.exit(app.exec_())
