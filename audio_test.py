import sounddevice as sd
import numpy as np

print("Available audio devices:")
for i, dev in enumerate(sd.query_devices()):
    print(f"{i}: {dev['name']} (inputs: {dev['max_input_channels']}, outputs: {dev['max_output_channels']})")

# Select device index (change if needed)
device_index = int(input("Enter input device index to test: "))
samplerate = 16000
channels = 1
duration = 3  # seconds

print(f"Recording {duration} seconds from device {device_index}...")
sd.default.device = device_index
recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='float32')
sd.wait()
print("Recording complete. Playing back...")
sd.play(recording, samplerate)
sd.wait()
print("Playback complete. Audio shape:", recording.shape) 