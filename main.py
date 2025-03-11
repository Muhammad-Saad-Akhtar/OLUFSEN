from winsound import PlaySound
from gtts import gTTS
from joblib import Memory
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
import os
import threading
import fnmatch
import atexit
import concurrent.futures


MEMORY_FILE = "olufsen_memory.json"

def load_memory():
    """Load memory from a JSON file."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as file:
            return json.load(file)
    return {"user_name": "User", "chat_history": []}

def save_memory(new_entry):
    memory_file = "olufsen_memory.json"

    # Load existing memory
    if os.path.exists(memory_file):
        with open(memory_file, "r", encoding="utf-8") as f:
            try:
                chat_memory = json.load(f)
            except json.JSONDecodeError:
                chat_memory = []
    else:
        chat_memory = []

    # Append new entry and limit history size
    chat_memory.append(new_entry)
    chat_memory = chat_memory[-50:]  # Keep only last 50 interactions

    # Save updated memory
    with open(memory_file, "w", encoding="utf-8") as f:
        json.dump(chat_memory, f, indent=4)


def remember_user(name):
    """Save the user's name."""
    Memory["user_name"] = name
    save_memory(Memory)

def update_memory(user_input, bot_response):
    """Stores and manages chat history for better conversation flow."""
    Memory["chat_history"].append({"role": "user", "content": user_input})
    Memory["chat_history"].append({"role": "assistant", "content": bot_response})

    # Keep important context while avoiding memory bloat
    if len(Memory["chat_history"]) > 10:
        summary = "Summary of previous conversation: " + " ".join([msg["content"] for msg in Memory["chat_history"][:5]])
        Memory["chat_history"] = [{"role": "system", "content": summary}] + Memory["chat_history"][-5:]

    save_memory(Memory)

speech_speed = 200  # Default speech speed

# def detect_emotion():
#     """Captures a single frame and detects emotion."""
#     cap = cv2.VideoCapture(0)
#     ret, frame = cap.read()
#     cap.release()
#     cv2.destroyAllWindows()
#     if not ret:
#         return "Neutral"
#     try:
#         analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
#         detected_emotion = analysis[0]['dominant_emotion']
#     except Exception:
#         detected_emotion = "Neutral"
#     return detected_emotion


def speak(text):
    tts = gTTS(text=text, lang="en")
    tts.save("output.mp3")

    sound = AudioSegment.from_mp3("output.mp3")
    sound = sound.low_pass_filter(500)  # Increase cutoff for clarity
    sound.export("output_filtered.mp3", format="mp3")

    PlaySound("output_filtered.mp3")
    os.remove("output.mp3")
    os.remove("output_filtered.mp3")


def voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=10)
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand."
        except sr.RequestError:
            return "Speech service unavailable."
        except sr.WaitTimeoutError:
            return "No voice detected. Try again."


def process_input(user_input):
    print(f"Received input in main.py: {user_input}")  # Debugging
    response = f"Processed: {user_input}"  # Your AI logic should be here
    print(f"Generated response: {response}")  # Debugging
    return response


def system_health():
    """Returns CPU, RAM, and Battery status."""
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    battery = psutil.sensors_battery().percent if psutil.sensors_battery() else "N/A"
    return f"CPU: {cpu_usage}% | RAM: {ram_usage}% | Battery: {battery}%"


def search_file_mt(filename, search_dir="C:\\Users"):
    def search_worker(subdir):
        for root, _, files in os.walk(subdir):
            if filename in files:
                return os.path.join(root, filename)
        return None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        subdirs = [os.path.join(search_dir, d) for d in os.listdir(search_dir) if os.path.isdir(os.path.join(search_dir, d))]
        results = executor.map(search_worker, subdirs)
    
    for result in results:
        if result:
            return f"File found: {result}"
    
    return "File not found."

def manage_files(command):
    """Handles file searching, renaming, moving, and deleting."""

    if "search file" in command:
        filename = command.replace("search file ", "").strip()
        return search_file_mt(filename)

    elif "delete file" in command:
        filepath = command.replace("delete file ", "").strip()
        if os.path.exists(filepath):
            os.remove(filepath)
            return f"Deleted {filepath}"
        return "File not found."

    elif "move file" in command:
        parts = command.replace("move file ", "").strip().split(" to ")
        if len(parts) == 2 and os.path.exists(parts[0]):
            shutil.move(parts[0], parts[1])
            return f"Moved {parts[0]} to {parts[1]}"
        return "Invalid file path."

    return "Invalid command."


def execute_task(command):
    command = command.lower()

    if command == "check emotion":
        thread = threading.Thread(target=detect_emotion_real_time)
        thread.start()
        active_threads.append(thread)  # Track thread
        return "Real-time emotion detection started. Press 'q' to exit."


    elif command == "list services":
     return list_services()  # FIXED: Was missing a `return`


    elif "increase brightness to" in command or "decrease brightness to" in command:
        try:
            brightness_level = int(command.split("to")[1].strip().replace("%", ""))
            sbc.set_brightness(brightness_level)
            return f"Brightness set to {brightness_level}%"
        except Exception:
            return "Failed to change brightness."

    elif "increase volume to" in command or "decrease volume to" in command:
        try:
            volume_level = int(command.split("to")[1].strip().replace("%", ""))
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(volume_level / 100, None)
            return f"Volume set to {volume_level}%"
        except Exception:
            return "Failed to change volume."

    elif command in ["what is your name", "who are you"]:
        return "My name is OLUFSEN."

    elif command in ["who is your owner", "who created you"]:
        return "My creator is Muhammad Saad."

    elif command == "tell me a joke":
        return pyjokes.get_joke()

    elif command == "shutdown":
        os.system("shutdown /s /t 1")
        return "Shutting down the PC..."

    elif command == "restart":
        os.system("shutdown /r /t 1")
        return "Restarting the PC..."

    elif command == "lock the pc":
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "Locking the PC..."

    elif command == "check system health":
        return system_health()

    elif "search file" in command or "delete file" in command or "move file" in command:
        return manage_files(command)

    elif "open notepad" in command:
        os.system("notepad")
        return "Opening Notepad..."

    elif "open chrome" in command:
        os.system("start chrome")
        return "Opening Chrome..."

    elif "open word" in command:
        os.system("start winword")
        return "Opening Microsoft Word..."

    elif "open vscode" in command:
        os.system("code")
        return "Opening Visual Studio Code..."

    elif "open calculator" in command:
        os.system("calc")
        return "Opening Calculator..."


    elif "open youtube" in command:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube..."

    elif "open google" in command:
        webbrowser.open("https://www.google.com")
        return "Opening Google..."

    elif "open github" in command:
        webbrowser.open("https://github.com")
        return "Opening GitHub..."

    elif "what time is it" in command or "current time" in command:
        now = datetime.datetime.now().strftime("%I:%M %p")
        return f"The current time is {now}"

    elif "search wikipedia for" in command:
        query = command.replace("search wikipedia for", "").strip()
        try:
            summary = wikipedia.summary(query, sentences=2)
            return summary
        except wikipedia.exceptions.DisambiguationError as e:
            return f"Multiple results found: {e.options[:3]}"
        except wikipedia.exceptions.PageError:
            return "No Wikipedia page found."

    elif "open" in command and ":" in command:
        try:
            filepath = command.split("open ")[1].strip()
            os.startfile(filepath)
            return f"Opening {filepath}..."
        except Exception:
            return "❌ Unable to open the file. Check the path."

    elif "search for" in command or "look up" in command:
        query = command.replace("search for", "").replace("look up", "").strip()
        return web_search(query)

    return None  # Default case if no command matches

def take_screenshot():
    screenshot_path = os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
    pyautogui.screenshot(screenshot_path)
    return f"Screenshot saved at {screenshot_path}"

def chatbot_response(user_input, emotion="Neutral"):
    """Generates chatbot responses with memory and emotion-based adaptation."""
    
    # Load user's name
    user_name = Memory.get("user_name", "User")

    # Personalize greeting
    if "my name is" in user_input:
        name = user_input.split("my name is")[-1].strip()
        remember_user(name)
        return f"Nice to meet you, {name}! I'll remember your name."

    # Use memory for chat history
    Memory["chat_history"].append({"role": "user", "content": user_input})
    if len(Memory["chat_history"]) > 5:
        Memory["chat_history"].pop(0)

    # Modify input based on emotion
    if emotion == "happy":
        user_input = f"You seem happy! {user_input}"
    elif emotion == "sad":
        user_input = f"I sense sadness. Let me help. {user_input}"
    elif emotion == "angry":
        user_input = f"You sound upset. I’ll keep things calm. {user_input}"
    elif emotion == "surprise":
        user_input = f"Wow, you seem surprised! {user_input}"

    # Generate response using Llama 2
    response = ollama.chat(model="llama2", messages=Memory["chat_history"])
    bot_response = response['message']['content']
    
    # Save response in memory
    Memory["chat_history"].append({"role": "assistant", "content": bot_response})
    save_memory(Memory)

    return bot_response

def list_services():
    services = [
        "Voice Command Recognition",
        "Text-based Chatbot Interaction",
        "Take Screenshot",
        "Shutdown PC",
        "Toggle Dark/Light Mode",
        "System Health Check",
        "Open Website (Web Browser)",
        "Execute Custom Tasks",
        "AI-Based Responses",
        "Speech-to-Text Processing",
        "Real-Time User Interaction",
        "File Management",
        "Emotion Detection",
        "Volume/Brightness Control",
        "Real-Time Weather Updates",
        "Search Wikipedia/Google",
        "Open Applications/Files",
        "Jokes and Fun Commands",
        "AI-Based Memory Storage",
        "Real-Time System Monitoring",
    ]
    
    return "\n".join([f"{i}. {service}" for i, service in enumerate(services, start=1)])


def detect_emotion_real_time():
    cap = cv2.VideoCapture(0)  # Open the webcam
    if not cap.isOpened():
        print("Error: Could not access the webcam.")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break  # Exit loop if frame not captured
        
        detected_emotion = detected_emotion(frame)
        detected_emotion = detected_emotion if detected_emotion else "Unknown"

        cv2.putText(frame, f"Emotion: {detected_emotion}", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Emotion Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
            break

    cap.release()
    cv2.destroyAllWindows()



    
def web_search(query):
    results = ddg(query, max_results=5)
    if results:
        return [
            {
                "title": result.get("title", "No title available"),
                "link": result.get("href", "No link available"),
                "body": result.get("body", "No detailed result available.")
            }
            for result in results
        ]
    return [{"title": "No results found", "link": "", "body": ""}]

# Track active threads
active_threads = []

import threading

def cleanup_threads():
    for thread in threading.enumerate():
        if thread is not threading.main_thread():
            thread.join(timeout=2)  # Allow up to 2 seconds for threads to exit gracefully

atexit.register(cleanup_threads)  # Ensures cleanup on exit


def main():
    global speech_speed
    print("🚀 OLUFSEN: Your AI Companion is Ready! (Type 'exit' to quit)")
    print("🔊 Say 'voice mode' to switch to voice input")
    print("⚡ Type 'speed [number]' to adjust speech speed")
    print("🛠️ Try commands like 'Open Notepad', 'Take a screenshot', 'Open YouTube'")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("👋 Goodbye!")
            break
        elif user_input.lower().startswith("speed "):
            try:
                new_speed = int(user_input.split()[1])
                if 50 <= new_speed <= 300:
                    speech_speed = new_speed
                    print(f"⚡ Speech speed set to {speech_speed}.")
                else:
                    print("⚠️ Speed must be between 50 and 300.")
            except ValueError:
                print("⚠️ Invalid speed value.")
            continue
        elif user_input == "":
            print("🎤 Switching to Voice Mode...")
            user_input = voice_input()
        task_response = execute_task(user_input)
        if task_response:
            print(f"🔹 {task_response}")
            speak(task_response)
            continue
        detected_emotion = detected_emotion()
        print(f"🧠 Detected Emotion: {detected_emotion}")
        bot_response = chatbot_response(user_input, detected_emotion)
        print(f"OLUFSEN: {bot_response}")
        speak(bot_response)
if __name__ == "__main__":
    main()
