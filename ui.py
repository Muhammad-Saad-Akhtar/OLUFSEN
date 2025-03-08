from typing import Self
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QLineEdit
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer, QRunnable, QThreadPool, QMetaObject, Q_ARG, pyqtSlot
import sys
import os
import threading
from click import command
import speech_recognition as sr
import pyautogui
import webbrowser

# ✅ Importing all functions from main.py
from main import (
    speak, detect_emotion_real_time, manage_files, web_search, list_services,
    execute_task, chatbot_response, system_health, take_screenshot,
    voice_input, process_input, remember_user, load_memory, save_memory
)

class Worker(QRunnable):
    def __init__(self, text, ui_instance):
        super().__init__()
        self.text = text
        self.ui_instance = ui_instance

    def run(self):
        try:
            response = execute_task(self.text) or chatbot_response(self.text)
        except Exception as e:
            response = f"Error: {str(e)}"
        QMetaObject.invokeMethod(self.ui_instance, "display_response", Qt.QueuedConnection, Q_ARG(str, response))

class OlufsenUI(QWidget):
 
    def __init__(self):
        super().__init__()
        self.memory = load_memory()
        self.initUI()
        self.threadpool = QThreadPool()

    def execute_task_async(self, command):
        worker = Worker(command, self)  # Proper indentation
        self.threadpool.start(worker)

    def initUI(self):
        self.setWindowTitle("OLUFSEN")
        self.setGeometry(200, 200, 600, 800)
        self.setStyleSheet("background-color: #121212; color: white;")
        
        layout = QVBoxLayout()
        
        self.title_label = QLabel("OLUFSEN")
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

        self.detect_emotion_button = QPushButton("Detect Real-Time Emotion", self)
        self.detect_emotion_button.setStyleSheet("background-color: #E91E63; border-radius: 10px; padding: 10px;")
        self.detect_emotion_button.clicked.connect(lambda: threading.Thread(target=detect_emotion_real_time).start())
        layout.addWidget(self.detect_emotion_button)

        self.file_management_button = QPushButton("File Management", self)
        self.file_management_button.setStyleSheet("background-color: #2196F3; border-radius: 10px; padding: 10px;")
        self.file_management_button.clicked.connect(self.file_management)
        layout.addWidget(self.file_management_button)
        
        self.web_search_button = QPushButton("Web Search", self)
        self.web_search_button.setStyleSheet("background-color: #FFEB3B; border-radius: 10px; padding: 10px;")
        self.web_search_button.clicked.connect(self.web_search)
        layout.addWidget(self.web_search_button)

        self.list_services_button = QPushButton("List Services", self)
        self.list_services_button.setStyleSheet("background-color: #4CAF50; border-radius: 10px; padding: 10px;")
        self.list_services_button.clicked.connect(self.list_services)
        layout.addWidget(self.list_services_button)

        self.shutdown_button = QPushButton("Shutdown PC", self)
        self.shutdown_button.setStyleSheet("background-color: #D32F2F; border-radius: 10px; padding: 10px;")
        self.shutdown_button.clicked.connect(lambda: self.execute_task_async("shutdown"))
        layout.addWidget(self.shutdown_button)

        self.remember_user_button = QPushButton("Remember User", self)
        self.remember_user_button.setStyleSheet("background-color: #FFC107; border-radius: 10px; padding: 10px;")
        self.remember_user_button.clicked.connect(self.remember_user)
        layout.addWidget(self.remember_user_button)

        self.system_status = QLabel("System Status: Loading...", self)
        self.system_status.setFont(QFont("Arial", 12))
        layout.addWidget(self.system_status)
        
        self.refresh_status()
        self.setLayout(layout)

    def process_input(self):
        user_text = self.user_input.text()
        if user_text:
            self.chat_display.append(f"<b>You:</b> {user_text}")
            worker = Worker(user_text, self)
            self.threadpool.start(worker)
            self.user_input.clear()

    @pyqtSlot(str)
    def display_response(self, response):
        self.chat_display.append(f"<b>OLUFSEN:</b> {response}")
        threading.Thread(target=speak, args=(response,)).start()
    
    def take_screenshot(self):
        take_screenshot()
        self.chat_display.append("<b>OLUFSEN:</b> Screenshot taken!")

    def voice_input(self):
     text = voice_input()
     if text.lower() in ["sorry, i couldn't understand.", "speech service unavailable.", "no voice detected. try again."]:
        self.chat_display.append(f"<b>OLUFSEN:</b> {text}")  # Notify user
     else:
        self.chat_display.append(f"<b>You (Voice):</b> {text}")
        self.user_input.setText(text)
        self.process_input()


    def shutdown_pc(self):
        os.system("shutdown /s /t 1")
        self.chat_display.append("<b>OLUFSEN:</b> Shutting down the PC...")

    def file_management(self):
        response = manage_files("search file test.txt")
        self.chat_display.append(f"<b>OLUFSEN:</b> {response}")

    def web_search(self):
        response = web_search("Latest AI News")
        self.chat_display.append(f"<b>OLUFSEN:</b> {response}")

    def list_services(self):
        response = list_services()
        self.chat_display.append(f"<b>OLUFSEN:</b> {response}")

    def remember_user(self):
        user_name = self.user_input.text().strip()  # Get the user's actual input
        if user_name:
            remember_user(user_name)  #  Save the entered name
            self.chat_display.append(f"<b>OLUFSEN:</b> I will remember you as {user_name}.")
        else:
            self.chat_display.append("<b>OLUFSEN:</b> Please enter your name first.")

    def refresh_status(self):
     self.system_status.setText(f"System Status: {system_health()}")
     QTimer.singleShot(15000, self.refresh_status)  # Update every 15 seconds instead of 5




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OlufsenUI()
    window.show()
    sys.exit(app.exec_())
