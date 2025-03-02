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

# Stores past conversations (basic memory)
chat_history = []
speech_speed = 100  # Default speech speed

# 🎭 Emotion Detection Function
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

# 🔊 Optimus Prime Voice Function (Now with Speed Control)
def speak(text):
    """Converts text to speech with a robotic voice."""
    engine = pyttsx3.init()
    engine.setProperty("rate", speech_speed)  # Adjust speech speed dynamically
    engine.setProperty("volume", 1.0)  # Max volume
    engine.setProperty("voice", "english_rp+f5")  # Deep voice (adjustable)

    engine.save_to_file(text, "output.mp3")
    engine.runAndWait()

    # Add robotic effects using pydub
    sound = AudioSegment.from_file("output.mp3")
    sound = sound.low_pass_filter(200)  # Bass boost
    sound = sound + 8  # Increase volume
    play(sound)

# 🎤 Voice Input Function
def voice_input():
    """Captures voice input and converts it to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        try:
            audio = recognizer.listen(source)
            user_input = recognizer.recognize_google(audio)
            print(f"User said: {user_input}")
            return user_input.lower()  # Convert to lowercase for consistency
        except sr.UnknownValueError:
            return "Sorry, I didn't catch that."
        except sr.RequestError:
            return "Speech recognition service unavailable."

# 🚀 Task Execution Function
def execute_task(command):
    """Executes system tasks like opening apps, files, websites, or taking screenshots."""
    command = command.lower()

    # Opening Applications
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
        os.system("code")  # VS Code command
        return "Opening Visual Studio Code..."
    elif "open calculator" in command:
        os.system("calc")
        return "Opening Calculator..."
    
    # Taking a Screenshot
    elif "take a screenshot" in command:
        screenshot_path = os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
        pyautogui.screenshot(screenshot_path)
        return f"Screenshot saved at {screenshot_path}"
    
    # Opening Websites
    elif "open youtube" in command:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube..."
    elif "open google" in command:
        webbrowser.open("https://www.google.com")
        return "Opening Google..."
    elif "open github" in command:
        webbrowser.open("https://github.com")
        return "Opening GitHub..."
    
    # Opening Files (if user provides a path)
    elif "open" in command and ":" in command:
        try:
            filepath = command.split("open ")[1].strip()
            os.startfile(filepath)
            return f"Opening {filepath}..."
        except Exception:
            return "❌ Unable to open the file. Check the path."

    return None  # If no task is matched

# 🧠 Emotion-Based Response Generator
def chatbot_response(user_input, emotion="Neutral"):
    """Generates chatbot responses with memory and emotion-based adaptation."""
    
    chat_history.append({"role": "user", "content": user_input})

    if len(chat_history) > 5:
        chat_history.pop(0)

    # Adjust response based on emotion
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

# 🚀 Improved Main Function (Now with Task Execution)
def main():
    global speech_speed  # Allow modification of speech speed
    print("🚀 OLUFSEN: Your AI Companion is Ready! (Type 'exit' to quit)")
    print("🔊 Say 'voice mode' to switch to voice input")
    print("⚡ Type 'speed [number]' to adjust speech speed (e.g., speed 200)")
    print("🛠️ Try commands like 'Open Notepad', 'Take a screenshot', 'Open YouTube'")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("👋 Goodbye!")
            break
        elif user_input.lower().startswith("speed "):  # Adjust speech speed
            try:
                new_speed = int(user_input.split()[1])
                if 50 <= new_speed <= 300:
                    speech_speed = new_speed
                    print(f"⚡ Speech speed set to {speech_speed}.")
                else:
                    print("⚠️ Speed must be between 50 and 300.")
            except ValueError:
                print("⚠️ Invalid speed value. Enter a number (e.g., speed 150).")
            continue  # Skip response generation for speed commands
        elif user_input == "":
            print("🎤 Switching to Voice Mode...")
            user_input = voice_input()

        # Check if it's a system command
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
