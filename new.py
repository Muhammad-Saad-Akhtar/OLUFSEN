from winsound import PlaySound
from gtts import gTTS
import ollama
import pyttsx3
import speech_recognition as sr
import cv2
import os
import webbrowser
import pyautogui  # For taking screenshots
from deepface import DeepFace
from pydub import AudioSegment
from pydub.playback import play
import datetime
import psutil
import shutil
import wikipedia
import pyjokes
import screen_brightness_control as sbc
import ctypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import threading
from duckduckgo_search import ddg
import requests
import json
import fnmatch
import atexit
import concurrent.futures
import time
import asyncio
import edge_tts


# Memory file for storing user session
MEMORY_FILE = "olufsen_memory.json"

# Initialize memory as a dictionary
memory = {"user_name": "User", "chat_history": []}

def load_memory():
    """Load memory from a JSON file."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {"user_name": "User", "chat_history": []}
    return {"user_name": "User", "chat_history": []}

def save_memory():
    """Save memory to a JSON file."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4)

def remember_user(name):
    """Save the user's name."""
    memory["user_name"] = name
    save_memory()

def update_memory(user_input, bot_response):
    """Stores and manages chat history for better conversation flow."""
    memory["chat_history"].append({"role": "user", "content": user_input})
    memory["chat_history"].append({"role": "assistant", "content": bot_response})
    
    # Limit chat history to last 50 interactions
    memory["chat_history"] = memory["chat_history"][-50:]
    
    save_memory()

# Initialize TTS engine
engine = pyttsx3.init()
voice_mode = False  # Default state
speech_speed = 200  # Default speed (scaling 1-100 to pyttsx3's range)

def set_voice_speed(command):
    """Adjusts voice speed when given a 'speed X' command."""
    global engine, speech_speed

    if command.startswith("speed "):
        try:
            speed = int(command.split(" ")[1])  # Extract speed value
            if 1 <= speed <= 100:
                speech_speed = speed * 2  # Scale to pyttsx3
                engine.setProperty("rate", speech_speed)
                print(f"🔊 Voice speed set to {speed}.")
            else:
                print("⚠ Speed must be between 1 and 100.")
        except ValueError:
            print("⚠ Invalid speed value. Use 'speed 50'.")

import subprocess

async def speak_async(text):
    """Uses Edge-TTS for natural speech synthesis."""
    if not text:
        return

    tts = edge_tts.Communicate(text, "en-US-JennyNeural")
    await tts.save("response.mp3")

    # Cross-platform audio playback
    if os.name == "nt":
        os.system("start response.mp3")  # Windows
    else:
        subprocess.run(["mpg321", "response.mp3"])  # Linux/macOS


def speak(text, force_read=False):
    """Speaks text when 'read' is given or if voice mode is enabled."""
    global voice_mode

    if text.lower() == "read" or force_read:
        if memory["chat_history"]:
            last_response = memory["chat_history"][-1]["content"]
            print(f"📢 Reading: {last_response}")
            asyncio.run(speak_async(last_response))  # Run TTS asynchronously
        else:
            print("⚠ No response to read.")

    elif text.lower() == "voice mode":
        voice_mode = True
        print("🎤 Voice mode activated! OLUFSEN will now read responses.")

    elif text.lower() == "pause voice":
        voice_mode = False
        print("🔇 Voice mode deactivated.")


def listen():
    """Listens to user input when voice mode is enabled."""
    if not voice_mode:
        return ""  # Do nothing if voice mode is off

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            return recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            print("⚠ Could not understand. Try again.")
        except sr.RequestError:
            print("⚠ Speech recognition service is unavailable.")
        except sr.WaitTimeoutError:
            print("⚠ Listening timed out. Try again.")

    return ""


def handle_command(command):
    """Handles user commands for reading, voice mode, and speed control."""
    global voice_mode

    if command == "read":
        speak("read", force_read=True)  # Force reading the last response
    
    elif command == "voice mode":
        voice_mode = True
        print("🎤 Voice mode enabled. OLUFSEN will now read responses.")

    elif command == "pause voice":
        voice_mode = False
        print("🔇 Voice mode paused.")

    else:
        set_voice_speed(command)  # Handle speed change if it's a speed command


def detect_emotion(frame):
    """Analyzes the frame and returns the dominant emotion."""
    try:
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        if result and isinstance(result, list) and "dominant_emotion" in result[0]:
            return result[0]['dominant_emotion']
    except Exception as e:
        print(f"⚠ Emotion detection error: {e}")

    return "Neutral"


def detect_emotion_real_time():
    """Starts emotion detection only when requested and stops when 'E' is pressed."""
    cap = cv2.VideoCapture(0)  # Start webcam when called
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return

    print("🔍 Detecting emotion... Press 'E' to stop.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame")
            break

        # Detect emotion
        emotion = detect_emotion(frame)
        cv2.putText(frame, f"Emotion: {emotion}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow("Emotion Detection", frame)

        # Press 'E' to stop detection
        if cv2.waitKey(1) & 0xFF == ord('e'):
            print("Emotion detection stopped.")
            break

    cap.release()
    cv2.destroyAllWindows()

def chatbot_response(user_input, emotion="Neutral"):
    """Generates chatbot responses with memory and emotion-based adaptation."""
    user_name = memory.get("user_name", "User")

    try:
        response = ollama.chat(model="llama2", messages=[{"role": "user", "content": user_input}])
        bot_response = response.get('message', {}).get('content', "I didn't understand that.")
    except Exception as e:
        print(f"⚠ Error generating chatbot response: {e}")
        bot_response = "I'm having trouble generating a response. Try again later."

    update_memory(user_input, bot_response)
    return bot_response

# Global List to Track Active Threads
active_threads = []

# Utility Functions
def take_screenshot():
    screenshot_path = os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
    pyautogui.screenshot(screenshot_path)
    return f"Screenshot saved at {screenshot_path}"

def handle_brightness(command):
    import screen_brightness_control as sbc
    try:
        brightness_level = int(command.split("to")[1].strip().replace("%", ""))
        sbc.set_brightness(brightness_level)
        return f"Brightness set to {brightness_level}%"
    except Exception:
        return "Failed to change brightness."

def handle_volume(command):
    try:
        volume_level = int(command.split("to")[1].strip().replace("%", ""))
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(volume_level / 100, None)
        return f"Volume set to {volume_level}%"
    except Exception:
        return "Failed to change volume."

def search_wikipedia(command):
    query = command.replace("search wikipedia for", "").strip()
    try:
        summary = wikipedia.summary(query, sentences=2)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Multiple results found: {e.options[:3]}"
    except wikipedia.exceptions.PageError:
        return "No Wikipedia page found."

def check_time():
    now = datetime.datetime.now().strftime("%I:%M %p")
    return f"The current time is {now}"

def manage_files(command):
    # Placeholder: Implement file management logic (search, delete, move)
    return "File management feature not implemented yet."

def shutdown_pc():
    os.system("shutdown /s /t 1")
    return "Shutting down the PC..."

def restart_pc():
    os.system("shutdown /r /t 1")
    return "Restarting the PC..."

def lock_pc():
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return "Locking the PC..."

def open_application(app):
    apps = {
        "notepad": "notepad",
        "chrome": "start chrome",
        "word": "start winword",
        "vscode": "code",
        "calculator": "calc"
    }
    if app in apps:
        os.system(apps[app])
        return f"Opening {app.capitalize()}..."
    return "Application not recognized."

def open_website(site):
    sites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://github.com"
    }
    if site in sites:
        webbrowser.open(sites[site])
        return f"Opening {site.capitalize()}..."
    return "Website not recognized."
def execute_task(command):
    command = command.lower()

    commands = {
        "check emotion": lambda: threading.Thread(target=detect_emotion_real_time, daemon=True).start() or "Real-time emotion detection started. Press 'q' to exit.",
        "take screenshot": take_screenshot,
        "shutdown": shutdown_pc,
        "restart": restart_pc,
        "lock the pc": lock_pc,
        "what is your name": lambda: "My name is OLUFSEN.",
        "who are you": lambda: "My name is OLUFSEN.",
        "who is your owner": lambda: "My creator is Muhammad Saad.",
        "who created you": lambda: "My creator is Muhammad Saad.",
        "tell me a joke": pyjokes.get_joke,
        "current time": check_time,
        "what time is it": check_time,
    }

    # Direct command match
    if command in commands:
        return commands[command]()

    # Handle complex commands
    if "increase brightness to" in command or "decrease brightness to" in command:
        return handle_brightness(command)

    if "increase volume to" in command or "decrease volume to" in command:
        return handle_volume(command)

    if "search wikipedia for" in command:
        return search_wikipedia(command)

    if "search file" in command or "delete file" in command or "move file" in command:
        return manage_files(command)

    if "open" in command:
        app_name = command.replace("open ", "").strip()
        return open_application(app_name)

    if "open" in command and ":" in command:  # Opening files by path
        try:
            filepath = command.split("open ")[1].strip()
            os.startfile(filepath)
            return f"Opening {filepath}..."
        except Exception:
            return "❌ Unable to open the file. Check the path."

    # Catch-all case for unknown commands
    return "🤖 I didn't understand that command."


def cleanup_threads():
    """Ensures proper thread cleanup on exit."""
    for thread in threading.enumerate():
        if thread is not threading.main_thread() and thread.is_alive():
            print(f"Stopping thread: {thread.name}")
            thread.join(timeout=2)


def execute_command(command):
    """Executes a command in a separate thread if needed."""
    thread_commands = ["shutdown", "restart", "check system health"]

    if command in thread_commands:
        thread = threading.Thread(target=execute_task, args=(command,), daemon=True)
        thread.start()
        return f"⏳ Executing '{command}' in the background..."
    else:
        return execute_task(command)  # Run normally if not a long-running task

def main():
    """Main function for OLUFSEN AI assistant."""
    print("🚀 OLUFSEN: Your AI Companion is Ready! (Type 'exit' to quit)")

    while True:
        user_input = input("You: ").strip().lower()

        if user_input == "exit":
            print("👋 Goodbye!")
            break

        elif user_input in ["detect emotion", "check emotion"]:
            print("🟢 Starting emotion detection in a separate thread...")
            threading.Thread(target=detect_emotion_real_time, daemon=True).start()

        elif user_input.startswith("speed "):
            set_voice_speed(user_input)  # Adjust voice speed

        elif user_input == "take screenshot":
            print("📸 Taking a screenshot...")
            print(take_screenshot())  # Run instantly

        else:
            bot_response = execute_task(user_input)  # Ensure correct function name

            if bot_response:
                print(f"OLUFSEN: {bot_response}")
                if voice_mode:  # Auto-read in voice mode
                    speak(bot_response)
                elif user_input == "read":  # Read last response only if requested
                    speak("read", force_read=True)
            else:
                print("🤖 I didn't understand that command.")

# Ensure proper indentation
if __name__ == "__main__":  
    print(" Reaching main() function.")
    main()
