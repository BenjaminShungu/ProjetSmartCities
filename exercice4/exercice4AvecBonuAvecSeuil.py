from machine import ADC, Pin
import neopixel
import time
import random

# === Configuration du microphone ===
micro = ADC(Pin(26))  # Microphone 

# === Configuration de la LED RGB WS2812 (Neopixel) ===
NB_LEDS = 1
bande_led = neopixel.NeoPixel(Pin(20), NB_LEDS)

def definir_couleur(r, g, b):
    bande_led[0] = (r, g, b)
    bande_led.write()

def attenuation(facteur=0.9):
    """Attenue progressivement la LED"""
    r, g, b = bande_led[0]
    bande_led[0] = (int(r * facteur), int(g * facteur), int(b * facteur))
    bande_led.write()

# === Variables de detection ===
SEUIL = 1500        
dernier_battement_temps = 0
intervalle_min = 300  # Duree minimale entre deux battements (ms)

# === Variables pour calcul du BPM ===
liste_intervalles = []        # intervalles entre battements
last_log_time = time.ticks_ms()   
LOG_INTERVAL = 60000              

def lecture_moyenne(nb_lectures=50):
    """Calcule moyenne du signal sonore"""
    total = 0
    for _ in range(nb_lectures):
        total += micro.read_u16()
    return total // nb_lectures

def calculer_bpm():
    """Calcule le BPM moyen a partir des intervalles entre battements"""
    if len(liste_intervalles) < 2:
        return 0
    intervalle_moyen = sum(liste_intervalles) / len(liste_intervalles)
    bpm = 60000 / intervalle_moyen
    return bpm

def enregistrer_bpm_fichier(bpm):
    """Ecrit le BPM moyen dans un fichier texte"""
    try:
        with open("bpm_log.txt", "a") as fichier:
            temps = time.localtime()
            heure = f"{temps[3]:02d}:{temps[4]:02d}:{temps[5]:02d}"
            fichier.write(f"[{heure}] BPM moyen: {bpm:.2f}\n")
        print(f" BPM {bpm:.2f} enregistre dans bpm_log.txt")
    except Exception as e:
        print("Erreur ecriture fichier :", e)

print("Demarrage du detecteur de battements avec mesure du BPM...")
time.sleep(1)

#  Boucle principale 
while True:
    niveau = micro.read_u16()
    moyenne = lecture_moyenne()

    # Detection de battement
    if niveau > moyenne + SEUIL:
        maintenant = time.ticks_ms()
        if time.ticks_diff(maintenant, dernier_battement_temps) > intervalle_min:
            if dernier_battement_temps != 0:
                intervalle = time.ticks_diff(maintenant, dernier_battement_temps)
                liste_intervalles.append(intervalle)
                # uniquement les 20 derniers intervalles
                if len(liste_intervalles) > 20:
                    liste_intervalles.pop(0)

            dernier_battement_temps = maintenant

            # Couleur aleatoire sur la LED
            r = random.randint(50, 255)
            g = random.randint(50, 255)
            b = random.randint(50, 255)
            definir_couleur(r, g, b)

            bpm = calculer_bpm()
            if bpm > 0:
                print(f" Battement detecte ! BPM ≈ {bpm:.1f} | Couleur = ({r}, {g}, {b})")

    # Ecriture du BPM moyen toutes les 60 secondes
    maintenant = time.ticks_ms()
    if time.ticks_diff(maintenant, last_log_time) >= LOG_INTERVAL:
        bpm_moyen = calculer_bpm()
        if bpm_moyen > 0:
            enregistrer_bpm_fichier(bpm_moyen)
        liste_intervalles.clear()
        last_log_time = maintenant

    # Effet fondu sur la LED
    attenuation(0.85)
    time.sleep(0.02)
