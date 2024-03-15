#include <Adafruit_NeoPixel.h>
#ifdef __AVR__
  #include <avr/power.h>
#endif

#define PIN        6  // Change to the correct pin
#define NUMPIXELS 60 // Adjust based on your LED strip

Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  pixels.begin();
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    if (command.startsWith("loading")) {
      int state = command.charAt(8) - '0';  // Extract the state number
      updateLEDs(state);
    } else if (command == "reset") {
      pixels.clear();
      pixels.show();
    }
  }
}

void updateLEDs(int state) {
  // Clear previous state
  pixels.clear();

  // Calculate how many LEDs to light up based on the state
  int ledsToLight = state * (NUMPIXELS / 4);  // Example: Divide strip into 4 segments

  for(int i = 0; i < ledsToLight; i++) {
    pixels.setPixelColor(i, pixels.Color(150, 0, 0));  // Example: Set to green
  }
  pixels.show();
}
```


In the Raspberry Pi, we integrated these lines in the main code:

```
import serial
import time

# Setup serial connection to Arduino - adjust '/dev/ttyS0' and baud rate as needed
ser = serial.Serial('/dev/ttyS0', 9600, timeout=1)

def send_loading_state(state):
    """Send a loading state command to the Arduino."""
    ser.write((state + "\n").encode())
    time.sleep(1)  # Wait a bit for Arduino to process the command
    
def main():
        while True:
            # Wait for the button press to start recording
            GPIO.wait_for_edge(BUTTON_PIN, GPIO.FALLING)
            send_loading_state("loading 1")
            
            
            # Transcribe the recorded audio
            transcription = transcribe_audio_with_openai(filename)
            send_loading_state("loading 2")
    
            
            # Send the transcription to GPT-3.5 Turbo for modification
            modified_transcription = modify_transcription_with_gpt(transcription, openai_api_key)
            send_loading_state("loading 3")
            
            
            # Generate audio from the modified transcription
            output_audio_path = generate_audio_with_elevenlabs(modified_transcription)
            send_loading_state("loading 4")
            
            
            # Play the generated audio
            if output_audio_path:
                # Play the generated audio using the updated path
                play_audio(output_audio_path)


            send_loading_state("reset")  # reset the LEDs
