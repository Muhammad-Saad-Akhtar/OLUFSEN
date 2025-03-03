import cv2
import numpy as np
import pyttsx3
import speech_recognition as sr
import os
import json
import sqlite3
import webbrowser
import requests
import mediapipe as mp
import face_recognition
import paho.mqtt.client as mqtt
import psutil
import shutil
import datetime
from deepface import DeepFace
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from coqui_tts import TTS

# Database Setup for Memory
conn = sqlite3.connect('olufsen_memory.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY, user TEXT, bot TEXT, timestamp TEXT)''')
conn.commit()

# Initialize Text-to-Speech Engine
def speak(text, emotion="neutral"):
    """Converts text to speech with emotion-based modulation."""
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    if emotion == "happy":
        engine.setProperty('rate', 180)
    elif emotion == "sad":
        engine.setProperty('rate', 120)
    elif emotion == "angry":
        engine.setProperty('rate', 200)
    else:
        engine.setProperty('rate', 150)
    engine.say(text)
    engine.runAndWait()

# Voice Recognition
def voice_input():
    """Captures voice input and converts to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source)
            return recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            return "Sorry, I didn't catch that."
        except sr.RequestError:
            return "Speech recognition service unavailable."

# Emotion Detection
def detect_emotion():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return "Neutral"
    try:
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        return analysis[0]['dominant_emotion']
    except:
        return "Neutral"

# Face Recognition Security
def recognize_face():
    """Recognizes if the user is authorized."""
    known_face_encodings = []  # Load from database or images
    known_face_names = ["Muhammad Saad"]
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return "Unknown"
    face_encodings = face_recognition.face_encodings(frame)
    if face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encodings[0])
        if True in matches:
            return known_face_names[matches.index(True)]
    return "Unknown"

# Gesture Control
def recognize_hand_gesture():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands()
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if not ret:
        return "No Gesture"
    results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    if results.multi_hand_landmarks:
        return "Hand Detected"
    return "No Gesture"

# Web Search Automation
def web_search(query):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.google.com")
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    driver.implicitly_wait(3)
    results = driver.find_elements(By.CSS_SELECTOR, "h3")
    driver.quit()
    return results[0].text if results else "No results found."

# IoT Smart Home Control
def control_smart_home(command):
    """Sends MQTT command to control IoT devices."""
    mqtt_client = mqtt.Client()
    mqtt_client.connect("broker.hivemq.com", 1883, 60)
    mqtt_client.publish("home/control", command)
    return f"Sent command: {command}"

# Cybersecurity Monitoring
def monitor_security():
    """Detects unauthorized microphone/camera usage."""
    for proc in psutil.process_iter(['pid', 'name']):
        if "camera" in proc.info['name'].lower() or "mic" in proc.info['name'].lower():
            return f"Security Alert: {proc.info['name']} is accessing your camera/mic!"
    return "No security threats detected."

if __name__ == "__main__":
    print("OLUFSEN Advanced Module Loaded.")
