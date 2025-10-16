from machine import ADC, Pin
import neopixel
import time
import random

# microphone 
mic = ADC(Pin(26)) 

#  LED RGB WS2812 (Neopixel) 
NUM_PIXELS = 1
np = neopixel.NeoPixel(Pin(20), NUM_PIXELS)  

def set_color(r, g, b):
    np[0] = (r, g, b)
    np.write()

def fade_out(factor=0.9):
    #Atténuation   LED
    r, g, b = np[0]
    np[0] = (int(r * factor), int(g * factor), int(b * factor))
    np.write()

# === Variables de détection ===
THRESHOLD = 1500      # seuil 
last_beat_time = 0
min_interval = 300     # délai min entre deux battements (ms)

def read_average(samples=50):
    """Calcule la moyenne du signal sonore"""
    total = 0
    for _ in range(samples):
        total += mic.read_u16()
    return total // samples

print("Démarrage du détecteur de battements avec LED WS2812...")
time.sleep(1)

# === Boucle principale ===
while True:
    # Lecture instantanée et moyenne
    level = mic.read_u16()
    avg = read_average()

    # Détection de pic
    if level > avg + THRESHOLD:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_beat_time) > min_interval:
            last_beat_time = now

            # Couleur aléatoire
            r = random.randint(50, 255)
            g = random.randint(50, 255)
            b = random.randint(50, 255)
            set_color(r, g, b)

            print(f" Battement DETECTE ! Couleur = ({r}, {g}, {b})")

    # Effet de fondu (progressif)
    fade_out(0.85)

    # Pause rapide
    time.sleep(0.02)
