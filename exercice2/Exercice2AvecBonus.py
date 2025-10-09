from machine import Pin, PWM, ADC 
from time import sleep

# === Configuration ===
pot = ADC(Pin(28))           
buzzer = PWM(Pin(18))        
button = Pin(16, Pin.IN, Pin.PULL_DOWN)  
led = Pin(20, Pin.OUT)      

# === Fréquences des notes ===
NOTES = {
    "C4": 262, "C#4": 277, "D4": 294, "D#4": 311, "Eb4": 311, "E4": 330, "F4": 349, "F#4": 370,
    "Gb4": 370, "G4": 392, "G#4": 415, "Ab4": 415, "A4": 440, "A#4": 466, "Bb4": 466, "B4": 494,
    "C5": 523, "C#5": 554, "D5": 587, "D#5": 622, "Eb5": 622, "E5": 659, "F5": 698, "F#5": 740,
    "Gb5": 740, "G5": 784, "G#5": 830, "Ab5": 830, "A5": 880, "A#5": 932, "Bb5": 932, "B5": 988,
    "C6": 1047, "D6": 1175, "E6": 1319, "F6": 1397, "G6": 1568, 0: 0
}

mario_theme = [
    ("E5", 8), ("E5", 8), (0, 8), ("E5", 8), (0, 8), ("C5", 8), ("E5", 8), (0, 8),
    ("G5", 4), (0, 4), ("G4", 4), (0, 4),
    ("C5", 8), (0, 8), ("G4", 8), (0, 8), ("E4", 8), (0, 8),
    ("A4", 8), (0, 8), ("B4", 8), (0, 8), ("Bb4", 8), ("A4", 8), (0, 8),
    ("G4", 6), ("E5", 6), ("G5", 6), ("A5", 8), (0, 8),
    ("F5", 8), ("G5", 8), (0, 8), ("E5", 8), (0, 8), ("C5", 8), ("D5", 8), ("B4", 8), (0, 8)
]


beethoven_elise = [
    ("E5", 8), ("D#5", 8), ("E5", 8), ("D#5", 8), ("E5", 8), ("B4", 8), ("D5", 8), ("C5", 8),
    ("A4", 4), (0, 8),
    ("C4", 8), ("E4", 8), ("A4", 8), ("B4", 4), (0, 8),
    ("E4", 8), ("G#4", 8), ("B4", 8), ("C5", 4), (0, 8),
    # Deuxième phrase
    ("E5", 8), ("D#5", 8), ("E5", 8), ("D#5", 8), ("E5", 8), ("B4", 8), ("D5", 8), ("C5", 8),
    ("A4", 4), (0, 8),
    ("C4", 8), ("E4", 8), ("A4", 8), ("B4", 4), (0, 8),
    ("E4", 8), ("C5", 8), ("B4", 8), ("A4", 4), (0, 8)
]

tempo = 60  # BPM

def play_tone(note, duration_ms, volume):
    if note == 0:
        buzzer.duty_u16(0)
        led.value(0)
        sleep(duration_ms / 1000)
    else:
        buzzer.freq(NOTES[note])
        buzzer.duty_u16(volume)

        # Allumer la LED pendant la moitié de la note
        led.value(1)
        sleep(duration_ms * 0.5 / 1000)
        # Éteindre la LED pendant l’autre moitié
        led.value(0)
        sleep(duration_ms * 0.5 / 1000)

        buzzer.duty_u16(0)

# === Liste des mélodies disponibles ===
melodies = [("Mario", mario_theme), ("Pour Elise", beethoven_elise)]
melody_index = 0
last_button_state = 0  

try:
    while True:
        name, theme = melodies[melody_index]
        print(f"Lecture : {name}")

        for note, dur in theme:
            current_button_state = button.value()

            # front montant
            if last_button_state == 0 and current_button_state == 1:
                melody_index = (melody_index + 1) % len(melodies)
                print(f"Changement de melodie : {melodies[melody_index][0]}")
                sleep(0.3)  # anti-rebond
                break  # sortir de la boucle pour changer de mélodie

            last_button_state = current_button_state

            # Lecture du potentiomètre pour volume
            pot_value = pot.read_u16()
            volume = max(int((pot_value / 65535) * 4000), 500)  # volume minimal audible
            note_duration = (60000 / tempo) / dur
            play_tone(note, note_duration, volume)

        sleep(1)  # pause avant de recommencer

except KeyboardInterrupt:
    print("\nArret des melodies")
    buzzer.duty_u16(0)
    buzzer.deinit()
    led.value(0)
