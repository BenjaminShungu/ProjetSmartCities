from machine import Pin, I2C, ADC, PWM
from dht20 import DHT20
import time

# ===== CONFIGURATION DES BROCHES =====
# I2C0 pour DHT20 (SDA=GP4, SCL=GP5)
i2c0 = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

# I2C1 pour écran OLED (SDA=GP6, SCL=GP7)
i2c1 = I2C(1, scl=Pin(7), sda=Pin(6), freq=100000)

# Potentiomètre (résistance variable) sur ADC0 (GP26)
potentiometer = ADC(Pin(26))

# LED sur GP15
led = Pin(15, Pin.OUT)

# Buzzer sur GP14 (avec PWM pour le son)
buzzer = PWM(Pin(14))
buzzer.freq(2000)  # Fréquence du son à 2kHz
buzzer.duty_u16(0)  # Éteint au départ

# ===== CLASSE POUR L'ÉCRAN OLED GROVE =====
class GroveOLED:
    def __init__(self, i2c, addr=0x3E):
        self.i2c = i2c
        self.addr = addr
        self.init_display()
    
    def init_display(self):
        """Initialise l'écran OLED"""
        commands = [
            0x2A, 0x71, 0x5C, 0x28, 0x08, 0x2A, 0x79,
            0xD5, 0x70, 0x78, 0x09, 0x06, 0x72, 0x00,
            0x2A, 0x79, 0xDA, 0x10, 0xDC, 0x00, 0x81,
            0x7F, 0xD9, 0xF1, 0xDB, 0x40, 0x78, 0x28,
            0x01, 0x80, 0x0C
        ]
        for cmd in commands:
            self.write_command(cmd)
            time.sleep_ms(5)
    
    def write_command(self, cmd):
        """Envoie une commande à l'écran"""
        self.i2c.writeto(self.addr, bytes([0x00, cmd]))
    
    def write_data(self, data):
        """Envoie des données à l'écran"""
        self.i2c.writeto(self.addr, bytes([0x40, data]))
    
    def clear(self):
        """Efface l'écran"""
        self.write_command(0x01)
        time.sleep_ms(2)
    
    def set_cursor(self, row, col):
        """Position le curseur (row: 0-1, col: 0-15)"""
        addr = 0x80 if row == 0 else 0xC0
        self.write_command(addr + col)
    
    def print(self, text, row=0, col=0):
        """Affiche du texte à la position spécifiée"""
        self.set_cursor(row, col)
        for char in text[:16]:
            self.write_data(ord(char))
    
    def clear_line(self, row):
        """Efface une ligne complète"""
        self.print(" " * 16, row, 0)

# ===== FONCTIONS UTILITAIRES =====
def read_setpoint():
    """Lit le potentiomètre et convertit en température de consigne (15-35°C)"""
    adc_value = potentiometer.read_u16()  # Valeur 0-65535
    # Convertir en température 15-35°C
    temp_setpoint = 15 + (adc_value / 65535) * 20
    return round(temp_setpoint, 1)

def activate_buzzer():
    """Active le buzzer"""
    buzzer.duty_u16(32768)  # 50% duty cycle

def deactivate_buzzer():
    """Désactive le buzzer"""
    buzzer.duty_u16(0)

# ===== INITIALISATION =====
print("Initialisation du système...")
time.sleep(1)

# Initialiser le capteur DHT20
sensor = DHT20(0x38, i2c0)
print("DHT20 initialisé")

# Initialiser l'écran OLED
oled = GroveOLED(i2c1)
print("Écran OLED initialisé")

# Variables pour le clignotement
led_state = False
last_led_toggle = time.ticks_ms()
led_interval = 1000  # Intervalle par défaut (ms)

# ===== BOUCLE PRINCIPALE =====
print("Démarrage du système de contrôle de température...")
oled.clear()

while True:
    try:
        # Lire la température de consigne (potentiomètre)
        temp_setpoint = read_setpoint()
        
        # Lire la température mesurée (DHT20)
        data = sensor.measurements
        temp_measured = data['t']
        humidity = data['rh']
        
        # Calculer la différence
        temp_diff = temp_measured - temp_setpoint
        
        # Afficher sur l'écran LCD
        oled.clear_line(0)
        oled.clear_line(1)
        
        # Ligne 1: Set temperature
        oled.print(f"Set: {temp_setpoint:.1f}C", 0, 0)
        
        # Ligne 2: Ambient temperature
        if temp_diff > 3:
            # Mode ALARM
            oled.print("ALARM! {:.1f}C".format(temp_measured), 1, 0)
            led_interval = 250  # LED clignote rapidement (2 Hz)
            activate_buzzer()
        elif temp_diff > 0:
            # Température supérieure à la consigne
            oled.print(f"Amb: {temp_measured:.1f}C", 1, 0)
            led_interval = 1000  # LED bat à 0.5 Hz
            deactivate_buzzer()
        else:
            # Température normale
            oled.print(f"Amb: {temp_measured:.1f}C", 1, 0)
            led_interval = 0  # LED éteinte
            led.value(0)
            deactivate_buzzer()
        
        # Gérer le clignotement de la LED
        current_time = time.ticks_ms()
        if led_interval > 0 and time.ticks_diff(current_time, last_led_toggle) >= led_interval:
            led_state = not led_state
            led.value(led_state)
            last_led_toggle = current_time
        
        # Affichage dans la console pour debug
        print(f"Consigne: {temp_setpoint:.1f}°C | Mesurée: {temp_measured:.1f}°C | "
              f"Diff: {temp_diff:.1f}°C | Hum: {humidity:.1f}%")
        
        # Attendre environ 1 seconde
        time.sleep(1)
        
    except Exception as e:
        print(f"Erreur: {e}")
        oled.clear()
        oled.print("ERROR!", 0, 0)
        oled.print("Check sensors", 1, 0)
        time.sleep(2)