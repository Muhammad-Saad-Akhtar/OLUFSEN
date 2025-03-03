import Ad_features as af
import ollama
import datetime
import os
import webbrowser
import wikipedia
import pyjokes
import pyttsx3
import speech_recognition as sr
import psutil
import shutil
import pyautogui
import screen_brightness_control as sbc
import ctypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import requests
from duckduckgo_search import ddg

def detect_emotion():
    return af.detect_emotion()

def speak(text):
    af.speak(text)

def voice_input():
    return af.voice_input()

def system_health():
    return f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}% | Battery: {psutil.sensors_battery().percent if psutil.sensors_battery() else 'N/A'}%"

def manage_files(command):
    return af.manage_files(command)

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
    elif "what is your name" in command or "who are you" in command:
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
    elif "check system health" in command:
        return system_health()
    elif "search wikipedia for" in command:
        query = command.replace("search wikipedia for", "").strip()
        try:
            return wikipedia.summary(query, sentences=2)
        except wikipedia.exceptions.DisambiguationError as e:
            return f"Multiple results found: {e.options[:3]}"
        except wikipedia.exceptions.PageError:
            return "No Wikipedia page found."
    elif "open youtube" in command:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube..."
    elif "open google" in command:
        webbrowser.open("https://www.google.com")
        return "Opening Google..."
    elif "open github" in command:
        webbrowser.open("https://github.com")
        return "Opening GitHub..."
    elif "take a screenshot" in command:
        screenshot_path = os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
        pyautogui.screenshot(screenshot_path)
        return f"Screenshot saved at {screenshot_path}"
    elif "search for" in command:
        query = command.replace("search for", "").strip()
        return af.web_search(query)
    return None

def chatbot_response(user_input, emotion="Neutral"):
    chat_history = []
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

def main():
    print("🚀 OLUFSEN: Your AI Companion is Ready! (Type 'exit' to quit)")
    print("🔊 Say 'voice mode' to switch to voice input")
    print("🛠️ Try commands like 'Open Notepad', 'Take a screenshot', 'Open YouTube'")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("👋 Goodbye!")
            break
        elif user_input == "":
            print("🎤 Switching to Voice Mode...")
            user_input = voice_input()
        detected_emotion = detect_emotion()
        print(f"🧠 Detected Emotion: {detected_emotion}")
        task_response = execute_task(user_input)
        if task_response:
            print(f"🔹 {task_response}")
            speak(task_response)
            continue
        bot_response = chatbot_response(user_input, detected_emotion)
        print(f"OLUFSEN: {bot_response}")
        speak(bot_response)

if __name__ == "__main__":
    main()
