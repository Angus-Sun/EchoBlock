import sys
import random
import math
import os     #
import pyaudio
import time
from scipy import signal
import pygame
from socket import *
from pygame.locals import *
import random
import numpy
from scipy.signal import fftconvolve
from numpy import argmax, sqrt, mean, diff, log

NOTE_FREQS = {
    'C3#': 138.60,
    'D3': 146.80,
    'E3b': 155.60,
    'E3': 164.80,
    'F3': 174.60,
    'F3#': 185.00,
    'G3': 196.00,
    'G3#': 207.70,
    'A3': 220.00,
    'B3b': 233.10,
    'B3': 246.90,
    'C4': 261.60,
    'C4#': 277.20,
    'D4': 293.70,
    'E4b': 311.10,
    'E4': 329.60,
    'F4': 349.20,
    'F4#': 370.00,
    'G4': 392.00,
    'G4#': 415.30,
    'A4': 440.00,
    'B4b': 466.20,
    'B4': 493.90,
    'C5': 523.30,
    'C5#': 554.40,
    'D5': 587.30,
    'E5b': 622.30,
    'E5': 659.30,
    'F5': 698.50,
    'F5#': 740.00,
    'G5': 784.00,
    'G5#': 830.60,
    'A5': 880.00,
    'B5b': 932.30,
    'B5': 987.80,
    'C6': 1047.00,
    'C6#': 1109.0,
    'D6': 1175.0,
    'E6b': 1245.0,
    'E6': 1319.0,
    'F6': 1397.0,
    'F6#': 1480.0,
    'G6': 1568.0,
}
NOTES = list(NOTE_FREQS.keys())
# from http://www.swharden.com/blog/2013-05-09-realtime-fft-audio-visualization-with-python/
class SoundRecorder:
    
    def __init__(self):
        self.RATE=48000
        self.BUFFERSIZE=3072 #1024 is a good buffer size 3072 works for Pi
        self.secToRecord=.05
        self.threadsDieNow=False
        self.newAudio=False
    
    def setup(self):
        self.buffersToRecord=int(self.RATE*self.secToRecord/self.BUFFERSIZE)
        if self.buffersToRecord==0: self.buffersToRecord=1
        self.samplesToRecord=int(self.BUFFERSIZE*self.buffersToRecord)
        self.chunksToRecord=int(self.samplesToRecord/self.BUFFERSIZE)
        self.secPerPoint=1.0/self.RATE
        self.p = pyaudio.PyAudio()
        self.inStream = self.p.open(format=pyaudio.paInt16,channels=1,rate=self.RATE,input=True,frames_per_buffer=self.BUFFERSIZE)
        self.xsBuffer=numpy.arange(self.BUFFERSIZE)*self.secPerPoint
        self.xs=numpy.arange(self.chunksToRecord*self.BUFFERSIZE)*self.secPerPoint
        self.audio=numpy.empty((self.chunksToRecord*self.BUFFERSIZE),dtype=numpy.int16)               
    
    def close(self):
        self.p.close(self.inStream)
    
    def getAudio(self):
        audioString=self.inStream.read(self.BUFFERSIZE)
        self.newAudio=True
        return numpy.frombuffer(audioString, dtype=numpy.int16)
    
def find_nearest(array, value):
    index = (numpy.abs(array - value)).argmin()
    return array[index]

def find(condition):
    return list(numpy.nonzero(numpy.ravel(condition))[0])

 # See https://github.com/endolith/waveform-analyzer/blob/master/frequency_estimator.py
def parabolic(f, x): 
    xv = 0.5 * (f[x-1] - f[x+1]) / (f[x-1] - 2 * f[x] + f[x+1]) + x
    yv = f[x] - 0.25 * (f[x-1] - f[x+1]) * (xv - x)
    return (xv, yv)
    
# See https://github.com/endolith/waveform-analyzer/blob/master/frequency_estimator.py
def freq_from_autocorr(raw_data_signal, fs):                          
    corr = fftconvolve(raw_data_signal, raw_data_signal[::-1], mode='full')
    corr = corr[len(corr) // 2:]
    d = diff(corr)
    start = find(d > 0)[0]
    peak = argmax(corr[start:]) + start
    px, py = parabolic(corr, peak)
    return fs / px   

def closest_value_index(array, guessValue):
    # Find closest element in the array, value wise
    closestValue = find_nearest(array, guessValue)
    # Find indices of closestValue
    indexArray = numpy.where(array==closestValue)
    # Numpys 'where' returns a 2D array with the element index as the value
    return indexArray[0][0]

def loudness(chunk):
    data = numpy.array(chunk, dtype=float) / 32768.0
    ms = math.sqrt(numpy.sum(data ** 2.0) / len(data))
    if ms < 10e-8: ms = 10e-8
    return 10.0 * math.log(ms, 10.0)

import time

def get_player_input(expected_sequence, recorder, sound_gate=23):
    recorder.setup()
    player_sequence = []
    previous_note_freq = None 
    count = 0
    for i, expected_note in enumerate(expected_sequence):
        print(f"Play: {expected_note}")
        time.sleep(1)  
        while True:
            raw_data = recorder.getAudio()
            if raw_data is None:
                print("Error: No audio data received.")
                continue
            signal_level = round(abs(loudness(raw_data)), 2)
            if signal_level > sound_gate:  
                continue
            try:
                freq = round(freq_from_autocorr(raw_data, recorder.RATE), 2)
                print(f"Detected Frequency: {freq} Hz")
            except:
                time.sleep(0.1)
                continue  
            # If we're still playing the previous note, do nothing and continue listening
            if previous_note_freq is not None and abs(freq - previous_note_freq) < 5:
                count += 1
                if (count < 7):
                    print("Still playing the previous note, waiting...")
                    continue
            break 
        previous_note_freq = freq
        closest_note = min(NOTE_FREQS, key=lambda note: abs(NOTE_FREQS[note] - freq))
        player_sequence.append(closest_note)
        freq = None
        print(f"You played: {closest_note} ({freq} Hz)")

        if closest_note != expected_note:
            print("womp womp u died")
            recorder.close()  
            return player_sequence  
    recorder.close()
    return player_sequence

pygame.mixer.init()
def play_note(note):
    print(note)
    audio_folder = './Notes'
    
    audio_filename = f"{note}.mp3"
    print(audio_filename)
    audio_path = os.path.join(audio_folder, audio_filename)
    
    if os.path.exists(audio_path):
        sound = pygame.mixer.Sound(audio_path)
        sound.play()
    
class Echoblock():
    def main(self):
        sequence = []
        round_num = 1
        
        while True:
            print(f"Round {round_num}")
            sequence.append(random.choice(NOTES))
            print("Listen to the sequence:")
            for note in sequence:
                play_note(note)
                time.sleep(1)

            print("Your turn!")
            player_sequence = get_player_input(sequence, SoundRecorder())
            
            if player_sequence != sequence:
                break  # Break the loop if the sequence doesn't match
            print("Correct! Next round beginning...")
            round_num += 1
            time.sleep(1)
        
            """while trys != 0:
                trys += 1
                SR.setup()
                raw_data_signal = SR.getAudio()
                signal_level = round(abs(loudness(raw_data_signal)), 2)
                
                try:
                    inputnote = round(freq_from_autocorr(raw_data_signal, SR.RATE),2)
                
                except:
                    inputnote == 0
                
                SR.close()
                
                if inputnote > frequencies[len(tunedNotes)-1]:
                    continue
                
                if inputnote < frequencies[0]:
                    continue
                
                if signal_level > soundgate:
                    continue
                
                targetnote = closest_value_index(frequencies, round(inputnote, 2))
                position = (screen_size[0] // 2, screen_size[1] // 2)
                
                for event in pygame.event.get():
                    if event.type == QUIT:
                        SR.close()
                        return
                
                screen.fill(screen_colour)
                
                if shownotes:
                    font = pygame.font.Font(None, 100)
                    err = abs(frequencies[targetnote]-inputnote)
                    if err < 1.5:
                        text = font.render(str(tunedNotes[frequencies[targetnote]]), 1, (0,255,0))
                    if err >= 1.5 and err <=2.5:
                        text = font.render(str(tunedNotes[frequencies[targetnote]]), 1, (255,255,255))
                    if err > 2.5:
                        text = font.render(str(tunedNotes[frequencies[targetnote]]), 1, (255,0,0))
                    screen.blit(text, (position))
                
                pygame.display.flip()
                pygame.display.update()"""
        
if __name__ == '__main__':
    pygame.init()
    Echoblock().main()