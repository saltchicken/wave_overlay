"""A simple example of recording from speakers ('What you hear') using the WASAPI loopback device"""

import pyaudiowpatch as pyaudio
import time
import wave

duration = 5.0

filename = "loopback_record.wav"
    
    
def record_stream():
    p = pyaudio.PyAudio()
    """
    Create PyAudio instance via context manager.
    """
    try:
        # Get default WASAPI info
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    except OSError:
        print("Looks like WASAPI is not available on the system. Exiting...")
        exit()
    
    # Get default WASAPI speakers
    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
    
    if not default_speakers["isLoopbackDevice"]:
        for loopback in p.get_loopback_device_info_generator():
            """
            Try to find loopback device with same name(and [Loopback suffix]).
            Unfortunately, this is the most adequate way at the moment.
            """
            if default_speakers["name"] in loopback["name"]:
                default_speakers = loopback
                break
        else:
            print("Default loopback output device not found.\n\nRun `python -m pyaudiowpatch` to check available devices.\nExiting...\n")
            exit()
            
    print(f"Recording from: ({default_speakers['index']}){default_speakers['name']}")
    
    wave_file = wave.open(filename, 'wb')
    wave_file.setnchannels(default_speakers["maxInputChannels"])
    wave_file.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
    wave_file.setframerate(int(default_speakers["defaultSampleRate"]))
    
    def callback(in_data, frame_count, time_info, status):
        """Write frames and return PA flag"""
        wave_file.writeframes(in_data)
        return (in_data, pyaudio.paContinue)
    
    sample_rate = int(default_speakers["defaultSampleRate"])
    
    stream = p.open(format=pyaudio.paInt16,
            channels=default_speakers["maxInputChannels"],
            rate=int(default_speakers["defaultSampleRate"]),
            frames_per_buffer=pyaudio.get_sample_size(pyaudio.paInt16),
            input=True,
            input_device_index=default_speakers["index"]
            )
    return stream, wave_file, sample_rate