import RPi.GPIO as GPIO
import time
import subprocess
import pyaudio
import pygame
import wave
import datetime
import os
import requests
import json
from openai import OpenAI
import openai
from elevenlabs import generate
from elevenlabs import set_api_key
import serial
import time

# GPIO pins
BUTTON_PIN = 17

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Audio Settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

openai_api_key = "put_your_api_key_here"
openAI_client = OpenAI(api_key=openai_api_key)
elevenlabs_api_key = "put_your_api_key_here"
voice_id = "Rachel"
#output_path = "output_speech_{timestamp}.mp3"
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Setup serial connection to Arduino - adjust '/dev/ttyS0' and baud rate as needed
ser = serial.Serial('/dev/ttyS0', 9600, timeout=1)

def send_loading_state(state):
    """Send a loading state command to the Arduino."""
    ser.write((state + "\n").encode())
    time.sleep(1)  # Wait a bit for Arduino to process the command


def generate_audio_with_elevenlabs(modified_transcription, voice="Rachel", model="eleven_multilingual_v2"):

    set_api_key(elevenlabs_api_key)
    
    try:
        # Call the ElevenLabs generate function directly
        audio_content = generate(text=modified_transcription, voice=voice, model=model)
        
        # Assuming 'audio_content' is the binary content of the generated audio
        # Save the audio to a file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output_speech_{timestamp}.mp3"  # Specify your desired output path
        with open(output_path, 'wb') as audio_file:
            audio_file.write(audio_content)
        
        print("Audio generated successfully and saved to:", output_path)
        return output_path
    except Exception as e:
        print(f"Failed to generate audio: {e}")
        return None
        

def modify_transcription_with_gpt(transcription, openai_api_key):
    #openai_api_key = "put_your_api_key_here"
    #client = OpenAI(api_key=openai_api_key)
    # Define how you want to modify the transcription text
    modifying_prompt_text = "Imagine you're giving advice or recommendations as the city of Barcelon. Give a response with maximum 200 characters."

    # Combine the transcription with your modifying instructions
    combined_prompt = f"{modifying_prompt_text}\n{transcription}"

    try:
        completion = openAI_client.chat.completions.create(
            model="gpt-3.5-turbo", # Specify the GPT-3.5 Turbo model
            #messages=combined_prompt,  # Use the combined prompt
            messages=[{"role": "system", "content":modifying_prompt_text},{"role": "user", "content": transcription}]
        )
        modified_text = completion.choices[0].message.content
        print("Modified Text:", modified_text)
        
        # Save modified text to a file
        modified_text_file_path = f"modified_text_{timestamp}.txt"
        with open(modified_text_file_path, 'w') as file:
            file.write(modified_text)
        
        return modified_text
    except Exception as e:
        print(f"Failed to modify transcription: {e}")
        return None


def transcribe_audio_with_openai(audio_file_path):
    #openai_api_key = "put_your_api_key_here"  # Replace with your OpenAI API key
    client = OpenAI(api_key=openai_api_key)
    
    print(audio_file_path)
    
    file_name = os.path.basename(audio_file_path)
    
    with open(audio_file_path, 'rb') as audio_file:
        text = client.audio.transcriptions.create(model="whisper-1", file=audio_file, response_format="text")       
        print(text)
        
        # Save transcription to a file
        transcription_file_path = f"transcription_{timestamp}.txt"
        with open(transcription_file_path, 'w') as file:
            file.write(text)
            
    return text


# Function to start recording audio
def record_audio():
    # Generate a unique filename based on the current timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recording_{timestamp}.wav"
    
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("Recording...")
    frames = []

    while GPIO.input(BUTTON_PIN) == GPIO.LOW:
        print('press')
        data = stream.read(CHUNK, exception_on_overflow = False)
        frames.append(data)

    print("Stopped recording.")
    stream.stop_stream()
    stream.close()
    audio.terminate()

    

    # Save the audio to a WAV file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return filename

def play_audio(output_path):
    # Initialize pygame mixer
    pygame.mixer.init()
    # Load the audio file
    pygame.mixer.music.load(output_path)
    
    # Play the audio
    pygame.mixer.music.play()
    # Wait for the music to play before proceeding, you can adjust this logic as needed
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
        

def main():
    print("Press the button to start recording...")
    #openai_api_key = "put_your_api_key_here"
    try:
        #ser.open()  # Ensure the serial port is open
        while True:
            # Wait for the button press to start recording
            GPIO.wait_for_edge(BUTTON_PIN, GPIO.FALLING)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            send_loading_state("loading 1")
            filename = record_audio()
            print(f"Audio saved as {filename}")
            
            # Transcribe the recorded audio
            transcription = transcribe_audio_with_openai(filename)
            send_loading_state("loading 2")
            if transcription and isinstance(transcription, str):
                print("Transcription:", transcription)
            
            # Send the transcription to GPT-3.5 Turbo for modification
            modified_transcription = modify_transcription_with_gpt(transcription, openai_api_key)
            send_loading_state("loading 3")
            if modified_transcription:
                print("Modified Transcription:", modified_transcription)
                
            # Generate audio from the modified transcription
            output_audio_path = generate_audio_with_elevenlabs(modified_transcription)
            send_loading_state("loading 4")
            # Play the generated audio
            if output_audio_path:
                # Play the generated audio using the updated path
                play_audio(output_audio_path)
            # Example usage




            send_loading_state("reset")  # Example command to reset or clear the LEDs

            

            
            # Avoid capturing a press multiple times due to button bounce
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Program terminated.")
    finally:
        GPIO.cleanup()
        #ser.close()  # Close the serial port when done

if __name__ == "__main__":
    main()
