self.device_index = None
for i in range(self.p.get_device_count()):
    dev = self.p.get_device_info_by_index(i)
    if 'pulse' in dev['name'].lower():  # Check for PulseAudio device
        self.device_index = i
        print(f"Using PulseAudio device: {dev['name']}")
        break

if self.device_index is None:
    raise ValueError("No PulseAudio device found.")  # Ensure PulseAudio is found

# Open the stream using the PulseAudio device index
self.inStream = self.p.open(format=pyaudio.paInt16,
                             channels=1,
                             rate=self.RATE,
                             input=True,
                             input_device_index=self.device_index,  # Use PulseAudio device index
                             frames_per_buffer=self.BUFFERSIZE)
