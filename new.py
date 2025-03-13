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
import subprocess
import validators


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
speech_speed = 220  # Default speed 

def set_voice_speed(command):
    """Adjusts voice speed when given a 'speed X' command."""
    global engine, speech_speed

    if command.startswith("speed "):
        try:
            speed = int(command.split(" ")[1])  # Extract speed value
            if 150 <= speed <= 300:
                speech_speed = speed * 2  # Scale to pyttsx3
                engine.setProperty("rate", speech_speed)
                print(f" Voice speed set to {speed}.")
            else:
                print(" Speed must be between 150 and 300.")
        except ValueError:
            print(" Invalid speed value. Use 'speed 200'.")


async def speak_async(text):
    """Uses Edge-TTS for natural speech synthesis (Non-blocking)."""
    if not text:
        return

    tts = edge_tts.Communicate(text, "en-US-JennyNeural")
    await tts.save("response.mp3")

    # Cross-platform non-blocking audio playback
    if os.name == "nt":
        subprocess.Popen(["start", "response.mp3"], shell=True)  # Windows (Non-blocking)
    else:
        subprocess.Popen(["mpg321", "response.mp3"])  # Linux/macOS

def speak(text, force_read=False):
    """Speaks text when 'read' is given or if voice mode is enabled."""
    global voice_mode

    if text.lower() == "read" or force_read:
        if memory["chat_history"]:
            last_response = memory["chat_history"][-1]["content"]
            print(f"📢 Reading: {last_response}")

            asyncio.run(speak_async(last_response))
        else:
            print("⚠ No response to read.")

    elif text.lower() == "pause voice":
        voice_mode = False
        print(" Voice mode deactivated.")


def listen():
    """Listens to user input when voice mode is enabled."""
    if not voice_mode:
        return ""  # Do nothing if voice mode is off

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print(" Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            return recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            print(" Could not understand. Try again.")
        except sr.RequestError:
            print(" Speech recognition service is unavailable.")
        except sr.WaitTimeoutError:
            print(" Listening timed out. Try again.")

    return ""


emotion_detection_active = False  # Global flag to control detection

def detect_emotion(frame, frame_count):
    """Analyzes the frame and returns the dominant emotion every 10 frames using GPU."""
    if frame_count % 10 != 0:  # Process every 10th frame
        return None  # Skip processing

    try:

        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False, 
                                  detector_backend="opencv")  # Fastest with GPU

        if isinstance(result, list) and result and "dominant_emotion" in result[0]:
            return result[0]['dominant_emotion']

    except Exception as e:
        print(f"⚠ Emotion detection error: {e}")

    return "Neutral"


def detect_emotion_real_time():
    """Starts emotion detection only when requested and stops when 'E' is pressed."""
    global emotion_detection_active

    if emotion_detection_active:
        print("⚠ Emotion detection is already running!")
        return

    emotion_detection_active = True  # Set flag to active
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print(" Error: Could not open webcam")
        emotion_detection_active = False
        return

    frame_count = 0
    print(" Detecting emotion... Press 'e' to stop.")

    while emotion_detection_active:
        ret, frame = cap.read()
        if not ret:
            print(" Error: Failed to capture frame")
            break

        emotion = detect_emotion(frame, frame_count)
        if emotion:
            cv2.putText(frame, f"Emotion: {emotion}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                        1, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow("Emotion Detection", frame)
        frame_count += 1

        if cv2.waitKey(1) & 0xFF == ord('e'):  # Press 'E' to stop detection
            print(" Emotion detection stopped.")
            emotion_detection_active = False
            break

    cap.release()
    cv2.destroyAllWindows()

def start_emotion_detection():
    """Starts emotion detection in a separate thread when commanded."""
    threading.Thread(target=detect_emotion_real_time, daemon=True).start()


def chatbot_response(user_input, model="llama2"):
    """Generates chatbot responses using the LLaMA model with memory."""
    user_name = memory.get("user_name", "User")

    try:
        response = ollama.chat(model=model, messages=[{"role": "user", "content": user_input}])

        #  Fix: Extract the correct chatbot response
        if isinstance(response, dict) and "message" in response and "content" in response["message"]:
            bot_response = response["message"]["content"]
        elif isinstance(response, dict) and "response" in response:
            bot_response = response["response"]
        else:
            bot_response = "I didn't understand that."

    except Exception as e:
        print(f"⚠ Error generating chatbot response: {e}")
        bot_response = "I'm having trouble generating a response. Try again later."

    update_memory(user_input, bot_response)  # Store only text, not objects
    return bot_response


# Utility Functions
def take_screenshot():
    screenshot_path = os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
    pyautogui.screenshot(screenshot_path)
    return f"Screenshot saved at {screenshot_path}"

def handle_brightness(command):
    try:
        if "increase" in command:
            current_brightness = sbc.get_brightness()[0]
            new_brightness = min(100, current_brightness + 10)
        elif "decrease" in command:
            current_brightness = sbc.get_brightness()[0]
            new_brightness = max(0, current_brightness - 10)
        else:
            new_brightness = int(command.split("to")[1].strip().replace("%", ""))

        sbc.set_brightness(new_brightness)
        return f"Brightness set to {new_brightness}%"
    except Exception:
        return "Failed to change brightness."

def handle_volume(command):
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        current_volume = volume.GetMasterVolumeLevelScalar() * 100

        if "increase" in command:
            new_volume = min(100, current_volume + 10)
        elif "decrease" in command:
            new_volume = max(0, current_volume - 10)
        else:
            new_volume = int(command.split("to")[1].strip().replace("%", ""))

        volume.SetMasterVolumeLevelScalar(new_volume / 100, None)
        return f"Volume set to {new_volume}%"
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


def search_files(filename, search_path="C:\\"):  # Default to C:\
    """Searches for a file with a given name or pattern."""
    found_files = []

    print(f" Searching for '{filename}' in {search_path}...")

    # Walk through the directory tree
    for root, _, files in os.walk(search_path):
        for file in files:
            if fnmatch.fnmatch(file.lower(), filename.lower()):
                found_files.append(os.path.join(root, file))

    if found_files:
        return f" Found {len(found_files)} file(s):\n" + "\n".join(found_files)
    else:
        return " No matching files found."

def manage_files(command):
    """Handles file search and future file management."""
    if "search file" in command:
        filename = command.replace("search file", "").strip()
        return search_files(filename)  # Call the file search function

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


def open_application(app_name):
    """Attempts to open any desktop application by name or .exe file."""
    
    # Common built-in Windows applications
    apps = {
        "notepad": "notepad.exe",
        "chrome": "chrome.exe",
        "word": "winword.exe",
        "vscode": "code",
        "calculator": "calc.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
    }

    #  If the app is in the predefined list, launch it
    if app_name.lower() in apps:
        try:
            subprocess.Popen(apps[app_name.lower()], shell=True)
            return f" Opening {app_name.capitalize()}..."
        except Exception as e:
            return f" Failed to open {app_name.capitalize()}: {e}"

    #  Try to find the application in common installation paths
    common_paths = [
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\Windows\\System32"
    ]
    
    for path in common_paths:
        for root, _, files in os.walk(path):
            for file in files:
                if file.lower() == f"{app_name.lower()}.exe":
                    try:
                        exe_path = os.path.join(root, file)
                        subprocess.Popen(exe_path, shell=True)
                        return f" Opening {app_name.capitalize()} from {exe_path}..."
                    except Exception as e:
                        return f" Failed to open {exe_path}: {e}"

    # As a last resort, try launching the app directly by name
    try:
        subprocess.Popen(app_name, shell=True)
        return f"Attempting to open {app_name.capitalize()}..."
    except Exception:
        return " Application not recognized."


def open_website(site):
    """Opens a website, handling both predefined and custom sites."""
    sites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://github.com"
    }
    
    url = sites.get(site.lower(), f"https://{site.lower()}.com")

    # Validate the URL before opening
    if not validators.url(url):
        return " Invalid website name."
    
    webbrowser.open(url)
    return f"Opening {url}..."


def cleanup_threads():
    """Ensures proper thread cleanup on exit."""
    for thread in threading.enumerate():
        if thread is not threading.main_thread() and thread.is_alive():
            print(f"Stopping thread: {thread.name}")
            thread.join(timeout=2)

import os
import pyjokes

def main():
    """Main function for OLUFSEN AI assistant."""
    print("OLUFSEN is Ready!")

    while True:
        user_input = input("You: ").strip().lower()

        if user_input == "exit":
            print("Goodbye!")
            break

        elif user_input in ["detect emotion", "detect emotions", "check emotions", "check emotion"]:
            print("Starting emotion detection...")
            start_emotion_detection()

        elif user_input.startswith("speed "):
            set_voice_speed(user_input)  # Adjust voice speed

        elif user_input in ["take screenshot", "take a screenshot", "take ss", "take a ss"]:
            print("Taking a screenshot...")
            print(take_screenshot())

        elif user_input == "shutdown":
            print(shutdown_pc())

        elif user_input == "restart":
            print(restart_pc())

        elif user_input == "lock the pc":
            print(lock_pc())

        elif user_input in ["what is your name", "who are you"]:
            print("OLUFSEN: My name is OLUFSEN.")

        elif user_input in ["who is your owner", "who created you"]:
            print("OLUFSEN: My creator is Muhammad Saad.")

        elif user_input == "tell me a joke":
            print(pyjokes.get_joke())

        elif user_input in ["current time", "what time is it"]:
            print(check_time())

        elif "increase brightness to" in user_input or "decrease brightness to" in user_input:
            print(handle_brightness(user_input))

        elif "increase volume to" in user_input or "decrease volume to" in user_input:
            print(handle_volume(user_input))

        elif "search wikipedia for" in user_input:
            print(search_wikipedia(user_input))

        elif any(x in user_input for x in ["search file", "delete file", "move file"]):
            print(manage_files(user_input))

        elif "open website" in user_input:
            site_name = user_input.replace("open website", "").strip()
            print(open_website(site_name))  # Always treat it as a website

        elif "open" in user_input and ":" in user_input:  # Opening files by path
            try:
                filepath = user_input.split("open ")[1].strip()
                os.startfile(filepath)
                print(f"Opening {filepath}...")
            except Exception as e:
                print(f"Unable to open the file. Error: {e}")

        elif "open" in user_input:
            app_name = user_input.replace("open ", "").strip()

            if "." in app_name:
                print(open_website(app_name))
            else:
                print(open_application(app_name)) 

        else:
            # Chatbot response
            bot_response = chatbot_response(user_input)
            print(f"OLUFSEN: {bot_response}")

            # Voice response if enabled
            if voice_mode:
                speak(bot_response)
            elif user_input == "read":  # Read last response only if requested
                speak("read", force_read=True)

# Ensure the script runs properly
if __name__ == "__main__":  
    main()
