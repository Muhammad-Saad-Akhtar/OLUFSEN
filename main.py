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
# Stores past conversations (basic memory)
chat_history = []
speech_speed = 150  # Default speech speed

def detect_emotion():
    """Captures a single frame and detects emotion."""
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    cv2.destroyAllWindows()
    if not ret:
        return "Neutral"
    try:
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        detected_emotion = analysis[0]['dominant_emotion']
    except Exception:
        detected_emotion = "Neutral"
    return detected_emotion

def speak(text):
    """Converts text to speech."""
    engine = pyttsx3.init()
    engine.setProperty("rate", speech_speed)
    engine.setProperty("volume", 1.0)
    engine.setProperty("voice", "english_rp+f5")
    engine.save_to_file(text, "output.mp3")
    engine.runAndWait()
    sound = AudioSegment.from_file("output.mp3")
    sound = sound.low_pass_filter(200)
    sound = sound + 8
    play(sound)

def voice_input():
    """Captures voice input and converts it to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        try:
            audio = recognizer.listen(source)
            user_input = recognizer.recognize_google(audio)
            print(f"User said: {user_input}")
            return user_input.lower()
        except sr.UnknownValueError:
            return "Sorry, I didn't catch that."
        except sr.RequestError:
            return "Speech recognition service unavailable."

def system_health():
    """Returns CPU, RAM, and Battery status."""
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    battery = psutil.sensors_battery().percent if psutil.sensors_battery() else "N/A"
    return f"CPU: {cpu_usage}% | RAM: {ram_usage}% | Battery: {battery}%"

def manage_files(command):
    """Handles file search, renaming, moving, and deleting."""
    if "search file" in command:
        filename = command.replace("search file ", "").strip()
        for root, dirs, files in os.walk(os.path.expanduser("~")):
            if filename in files:
                return f"File found: {os.path.join(root, filename)}"
        return "File not found."
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


def execute_task(command):
    if "increase brightness to" in command or "decrease brightness to" in command:
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
        try:
            volume_level = int(command.split("to")[1].strip().replace("%", ""))
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x319, 0, (0xA0000 | volume_level))
            return f"Volume set to {volume_level}%"
        except Exception:
            return "Failed to change volume."
    if "what is your name" in command or "who are you" in command:
        return "My name is OLUFSEN."
    elif "who is your owner" in command or "who created you" in command:
        return "My creator is Muhammad Saad."
    elif "tell me a joke" in command:
        return pyjokes.get_joke()
    elif "shutdown" in command:
        os.system("shutdown /s /t 1")
        return "Shutting down the PC..."
    elif "restart" in command:
        os.system("shutdown /r /t 1")
        return "Restarting the PC..."
    elif "lock the pc" in command:
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "Locking the PC..."
    if "what is your name" in command or "who are you" in command:
        return "My name is OLUFSEN."
    elif "who is your owner" in command or "who created you" in command:
        return "My creator is Muhammad Saad."
    if "check system health" in command:
        return system_health()
    elif "search file" in command or "delete file" in command or "move file" in command:
        return manage_files(command)
    if "check system health" in command:
        return system_health()
        return system_health()
    """Executes system tasks."""
    command = command.lower()
    if "open notepad" in command:
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
    elif "take a screenshot" in command:
        screenshot_path = os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
        pyautogui.screenshot(screenshot_path)
        return f"Screenshot saved at {screenshot_path}"
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
    return None

def chatbot_response(user_input, emotion="Neutral"):
    """Generates chatbot responses with memory and emotion-based adaptation."""
    chat_history.append({"role": "user", "content": user_input})
    if len(chat_history) > 5:
        chat_history.pop(0)
    if emotion == "happy":
        user_input = f"You seem happy! {user_input}"
    elif emotion == "sad":
        user_input = f"I sense sadness. Let me help. {user_input}"
    elif emotion == "angry":
        user_input = f"You sound upset. I’ll keep things calm. {user_input}"
    elif emotion == "surprise":
        user_input = f"Wow, you seem surprised! {user_input}"
    response = ollama.chat(model="llama2", messages=chat_history)
    bot_response = response['message']['content']
    chat_history.append({"role": "assistant", "content": bot_response})
    return bot_response


def web_search(query):
    """Search DuckDuckGo and return the first result."""
    url = f"https://api.duckduckgo.com/?q={query}&format=json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data.get("AbstractText"):
            return data["AbstractText"]
        elif data.get("RelatedTopics"):
            return data["RelatedTopics"][0]["Text"] if data["RelatedTopics"] else "No results found."
        else:
            return "No relevant search results found."
    else:
        return "Failed to fetch search results."
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
        detected_emotion = detect_emotion()
        print(f"🧠 Detected Emotion: {detected_emotion}")
        bot_response = chatbot_response(user_input, detected_emotion)
        print(f"OLUFSEN: {bot_response}")
        speak(bot_response)
if __name__ == "__main__":
    main()
