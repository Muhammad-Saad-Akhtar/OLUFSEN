import tempfile
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


MEMORY_FILE = "olufsen_memory.json"

def load_memory():
    """Load memory from a JSON file safely."""
    try:
        if os.path.exists(MEMORY_FILE) and os.path.getsize(MEMORY_FILE) > 0:
            with open(MEMORY_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading memory: {e}")  # Log error

    # Default memory structure
    return {"user_name": "User", "chat_history": [], "speech_speed": 150}

def save_memory(memory):
    """Save memory to a JSON file safely."""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as file:
            json.dump(memory, file, indent=4)
    except IOError as e:
        print(f"Error saving memory: {e}")  # Log error

memory = load_memory()

def remember_user(name):
    """Save the user's name persistently."""
    memory["user_name"] = name
    save_memory(memory)

def add_to_chat_history(user_input, bot_response):
    """Append messages to chat history with a limit."""
    memory["chat_history"].append({"user": user_input, "bot": bot_response})

    # Limit chat history to last 100 messages (adjustable)
    if len(memory["chat_history"]) > 100:
        memory["chat_history"] = memory["chat_history"][-100:]

    save_memory(memory)

def set_speech_speed(speed):
    """Update speech speed setting."""
    memory["speech_speed"] = max(50, min(speed, 300))  # Constrain to 50-300 range
    save_memory(memory)

# Global variables
chat_history = memory["chat_history"]
speech_speed = memory["speech_speed"]

import cv2
from deepface import DeepFace

def detect_emotion():
    """Captures a single frame and detects emotion efficiently."""
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return "Neutral"

    ret, frame = cap.read()
    cap.release()
    cv2.destroyAllWindows()

    if not ret or frame is None:
        return "Neutral"

    try:
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        return analysis[0].get('dominant_emotion', 'Neutral')
    except Exception:
        return "Neutral"


def speak(text):
    """Converts text to speech efficiently."""
    engine = pyttsx3.init()
    engine.setProperty("rate", speech_speed)
    engine.setProperty("volume", 1.0)
    engine.setProperty("voice", "english_rp+f5")

    # Use a temporary file to avoid disk clutter
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
        temp_audio_path = temp_audio.name
        engine.save_to_file(text, temp_audio_path)
        engine.runAndWait()

    # Load and process audio
    sound = AudioSegment.from_file(temp_audio_path).low_pass_filter(200) + 8
    play(sound)

    # Clean up temporary file
    os.remove(temp_audio_path)


def voice_input(self):
    """Captures voice input and converts it to text."""
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        self.chat_display.append("<b>OLUFSEN:</b> Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)  # Adjust for noise dynamically
        
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)  # Limits single utterance length
            text = recognizer.recognize_google(audio).strip()
            
            if text:
                self.chat_display.append(f"<b>You (Voice):</b> {text}")
                self.process_input()
            else:
                self.chat_display.append("<b>OLUFSEN:</b> No speech detected. Try again.")

        except sr.UnknownValueError:
            self.chat_display.append("<b>OLUFSEN:</b> Sorry, I couldn't understand.")
        except sr.RequestError:
            self.chat_display.append("<b>OLUFSEN:</b> Speech service unavailable.")
        except sr.WaitTimeoutError:
            self.chat_display.append("<b>OLUFSEN:</b> No voice detected. Try again.")
        except Exception as e:
            self.chat_display.append(f"<b>OLUFSEN:</b> Error: {str(e)}")


def system_health():
    """Returns CPU, RAM, and Battery status efficiently."""
    cpu_usage = psutil.cpu_percent(interval=0.5)  # Slight delay for more accurate reading
    ram_usage = psutil.virtual_memory().percent

    try:
        battery = psutil.sensors_battery()
        battery_status = f"{battery.percent}%" if battery else "N/A"
    except AttributeError:
        battery_status = "N/A"  # Handle cases where battery info isn't available

    return f"CPU: {cpu_usage}% | RAM: {ram_usage}% | Battery: {battery_status}"


def manage_files(command):
    """Handles file search, renaming, moving, and deleting efficiently."""
    command = command.lower().strip()

    if command.startswith("search file"):
        filename = command.replace("search file ", "").strip()
        home_dir = os.path.expanduser("~")

        for root, _, files in os.walk(home_dir):
            if filename in files:
                return f"File found: {os.path.join(root, filename)}"

        return "File not found."

    elif command.startswith("delete file"):
        filepath = command.replace("delete file ", "").strip()

        if os.path.isfile(filepath):
            try:
                os.remove(filepath)
                return f"Deleted {filepath}"
            except Exception as e:
                return f"Error deleting file: {str(e)}"
        return "File not found."

    elif command.startswith("move file"):
        parts = command.replace("move file ", "").strip().split(" to ", 1)

        if len(parts) == 2:
            src, dest = parts
            if os.path.isfile(src):
                try:
                    shutil.move(src, dest)
                    return f"Moved {src} to {dest}"
                except Exception as e:
                    return f"Error moving file: {str(e)}"
            return "Source file not found."
        return "Invalid command format. Use: 'move file [source] to [destination]'"

    return "Invalid command."


def execute_task(command):
    command = command.lower().strip()
    
    simple_commands = {
        "check emotion": (detect_emotion_real_time, "Real-time emotion detection started. Press 'q' to exit."),
        "list services": (list_services, None),
        "what is your name": (lambda: "My name is OLUFSEN."),
        "who are you": (lambda: "My name is OLUFSEN."),
        "who is your owner": (lambda: "My creator is Muhammad Saad."),
        "who created you": (lambda: "My creator is Muhammad Saad."),
        "tell me a joke": (pyjokes.get_joke, None),
        "shutdown": (lambda: os.system("shutdown /s /t 1") or "Shutting down the PC..."),
        "restart": (lambda: os.system("shutdown /r /t 1") or "Restarting the PC..."),
        "lock the pc": (lambda: os.system("rundll32.exe user32.dll,LockWorkStation") or "Locking the PC..."),
        "check system health": (system_health, None),
        "open notepad": (lambda: os.system("notepad") or "Opening Notepad..."),
        "open chrome": (lambda: os.system("start chrome") or "Opening Chrome..."),
        "open word": (lambda: os.system("start winword") or "Opening Microsoft Word..."),
        "open vscode": (lambda: os.system("code") or "Opening Visual Studio Code..."),
        "open calculator": (lambda: os.system("calc") or "Opening Calculator..."),
        "open youtube": (lambda: webbrowser.open("https://www.youtube.com") or "Opening YouTube..."),
        "open google": (lambda: webbrowser.open("https://www.google.com") or "Opening Google..."),
        "open github": (lambda: webbrowser.open("https://github.com") or "Opening GitHub..."),
    }
    
    if command in simple_commands:
        func, response = simple_commands[command]
        return response if response else func()
    
    if "increase brightness to" in command or "decrease brightness to" in command:
        try:
            brightness_level = int(command.split("to")[1].strip().replace("%", ""))
            sbc.set_brightness(brightness_level)
            return f"Brightness set to {brightness_level}%"
        except Exception:
            return "Failed to change brightness."
    
    if "increase volume to" in command or "decrease volume to" in command:
        try:
            volume_level = int(command.split("to")[1].strip().replace("%", ""))
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(volume_level / 100, None)
            return f"Volume set to {volume_level}%"
        except Exception:
            return "Failed to change volume."
    
    if "take a screenshot" in command:
        screenshot_path = os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
        pyautogui.screenshot(screenshot_path)
        return f"Screenshot saved at {screenshot_path}"
    
    if "what time is it" in command or "current time" in command:
        return f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}"
    
    if "search wikipedia for" in command:
        query = command.replace("search wikipedia for", "").strip()
        try:
            return wikipedia.summary(query, sentences=2)
        except wikipedia.exceptions.DisambiguationError as e:
            return f"Multiple results found: {', '.join(e.options[:3])}"
        except wikipedia.exceptions.PageError:
            return "No Wikipedia page found."
    
    if "open" in command and ":" in command:
        try:
            filepath = command.split("open ")[1].strip()
            os.startfile(filepath)
            return f"Opening {filepath}..."
        except Exception:
            return "❌ Unable to open the file. Check the path."
    
    if "search for" in command or "look up" in command:
        query = command.replace("search for", "").replace("look up", "").strip()
        return web_search(query)
    
    if any(x in command for x in ["search file", "delete file", "move file"]):
        return manage_files(command)
    
    return "Command not recognized."


def chatbot_response(user_input, emotion="Neutral"):
    """Generates chatbot responses with memory and emotion-based adaptation."""
    
    # Load user's name and chat history with default values
    user_name = memory.get("user_name", "User")
    chat_history = memory.setdefault("chat_history", [])

    # Personalize greeting
    if "my name is" in user_input.lower():
        name = user_input.split("my name is")[-1].strip()
        remember_user(name)
        return f"Nice to meet you, {name}! I'll remember your name."
    
    # Maintain chat history size
    chat_history.append({"role": "user", "content": user_input})
    if len(chat_history) > 5:
        chat_history.pop(0)
    
    # Prepend emotion-based context if applicable
    emotion_prefix = {
        "happy": "You seem happy! ",
        "sad": "I sense sadness. Let me help. ",
        "angry": "You sound upset. I’ll keep things calm. ",
        "surprise": "Wow, you seem surprised! "
    }.get(emotion, "")
    user_input = emotion_prefix + user_input
    
    # Generate response using Llama 2
    response = ollama.chat(model="llama2", messages=chat_history)
    bot_response = response['message']['content']
    
    # Save response in memory
    chat_history.append({"role": "assistant", "content": bot_response})
    save_memory(memory)
    
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

    print("\n".join(f"{i}. {service}" for i, service in enumerate(services, start=1)))

list_services()


import cv2
from deepface import DeepFace

def detect_emotion_real_time():
    """Opens a real-time emotion detection window using DeepFace."""
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to RGB for DeepFace
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Emotion detection with DeepFace
        detected_emotion = "Neutral"
        try:
            analysis = DeepFace.analyze(rgb_frame, actions=['emotion'], enforce_detection=False)
            detected_emotion = analysis[0].get('dominant_emotion', "Neutral")
        except Exception:
            pass  # If an error occurs, fallback to "Neutral"

        # Display emotion on the frame
        cv2.putText(frame, f"Emotion: {detected_emotion}", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Real-Time Emotion Detection", frame)

        # Exit on 'e' key press
        if cv2.waitKey(1) & 0xFF == ord('e'):
            break

    cap.release()
    cv2.destroyAllWindows()

detect_emotion_real_time()

import requests

def web_search(query):
    """Search DuckDuckGo and return the first relevant result."""
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json"
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raises an error for HTTP issues

        data = response.json()
        abstract = data.get("AbstractText", "").strip()
        related_topics = data.get("RelatedTopics", [])

        if abstract:
            return abstract
        elif related_topics and isinstance(related_topics, list):
            return related_topics[0].get("Text", "No relevant results found.")
        else:
            return "No relevant search results found."

    except requests.exceptions.RequestException:
        return "Failed to fetch search results. Please check your connection."

# Example usage
# print(web_search("Machine Learning"))

def main():
    global speech_speed
    print("🚀 OLUFSEN: Your AI Companion is Ready! (Type 'exit' to quit)")
    print("🔊 Say 'voice mode' to switch to voice input")
    print("⚡ Type 'speed [number]' to adjust speech speed")
    print("🛠️ Type 'list services' to open services list")

    while True:
        user_input = input("You: ").strip().lower()

        if user_input == "exit":
            print("👋 Goodbye!")
            break

        elif user_input.startswith("speed "):
            try:
                new_speed = int(user_input.split()[1])
                if 50 <= new_speed <= 300:
                    speech_speed = new_speed
                    print(f"⚡ Speech speed set to {speech_speed}.")
                else:
                    print("⚠️ Speed must be between 50 and 300.")
            except (ValueError, IndexError):
                print("⚠️ Invalid speed value. Usage: speed [50-300]")
            continue

        elif user_input == "":
            print("🎤 Switching to Voice Mode...")
            user_input = voice_input()

        # Execute predefined tasks
        task_response = execute_task(user_input)
        if task_response:
            print(f"🔹 {task_response}")
            speak(task_response)
            continue

        # Detect emotion for chatbot response
        detected_emotion = detect_emotion()
        print(f"🧠 Detected Emotion: {detected_emotion}")

        # Generate AI chatbot response
        bot_response = chatbot_response(user_input, detected_emotion)
        print(f"OLUFSEN: {bot_response}")
        speak(bot_response)

if __name__ == "__main__":
    main()
