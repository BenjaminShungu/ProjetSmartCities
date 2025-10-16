from machine import Pin, I2C, ADC, PWM
from dht20 import DHT20
import time
import math

# ===== CONFIGURATION DES BROCHES =====
i2c0 = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
i2c1 = I2C(1, scl=Pin(7), sda=Pin(6), freq=100000)
potentiometer = ADC(Pin(26))

# LED avec PWM pour dimmer
led = PWM(Pin(20))
led.freq(1000)
led.duty_u16(0)

# Buzzer
buzzer = PWM(Pin(18))
buzzer.freq(2000)
buzzer.duty_u16(0)

# ===== CLASSE POUR L'ÉCRAN OLED GROVE =====
class GroveOLED:
    def __init__(self, i2c, addr=0x3E):
        self.i2c = i2c
        self.addr = addr
        self.init_display()
    
    def init_display(self):
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
        self.i2c.writeto(self.addr, bytes([0x00, cmd]))
    
    def write_data(self, data):
        self.i2c.writeto(self.addr, bytes([0x40, data]))
    
    def clear(self):
        self.write_command(0x01)
        time.sleep_ms(2)
    
    def set_cursor(self, row, col):
        addr = 0x80 if row == 0 else 0xC0
        self.write_command(addr + col)
    
    def print(self, text, row=0, col=0):
        self.set_cursor(row, col)
        for char in text[:16]:
            self.write_data(ord(char))
    
    def clear_line(self, row):
        self.print(" " * 16, row, 0)

# ===== FONCTIONS UTILITAIRES =====
def read_setpoint():
    """Lecture du potentiomètre avec moyennage pour réduire le bruit"""
    # Moyenne sur plusieurs lectures
    sum_value = 0
    for _ in range(10):
        sum_value += potentiometer.read_u16()
        time.sleep_ms(1)
    
    adc_value = sum_value // 10
    temp_setpoint = 15 + (adc_value / 65535) * 20
    return round(temp_setpoint, 1)

def activate_buzzer():
    buzzer.duty_u16(32768)

def deactivate_buzzer():
    buzzer.duty_u16(0)

def led_breathing(phase):
    """Effet de respiration (dimmer progressif) pour la LED"""
    brightness = int((math.sin(phase) + 1) * 32767.5)
    led.duty_u16(brightness)

def led_blink_fast():
    """Clignotement rapide on/off"""
    return 65535  

# ===== INITIALISATION =====
print("Initialisation du système...")
time.sleep(1)

sensor = DHT20(0x38, i2c0)
print("DHT20 initialisé")

oled = GroveOLED(i2c1)
print("Écran OLED initialisé")

# Variables pour les effets
breathing_phase = 0
last_led_update = time.ticks_ms()
led_update_interval = 50  # ms entre chaque mise à jour LED

blink_state = False
last_blink_toggle = time.ticks_ms()
blink_interval = 500  # ms pour clignotement ALARM

scroll_position = 0
last_scroll_update = time.ticks_ms()
scroll_interval = 300  # ms entre chaque défilement

last_sensor_read = time.ticks_ms()
sensor_read_interval = 1000  # Lire le capteur toutes les secondes

# Variable pour stabiliser la consigne
previous_setpoint = read_setpoint()
setpoint_threshold = 0.3  # Seuil de changement minimum

oled.clear()
print("Démarrage du système de contrôle de température...")

# ===== BOUCLE PRINCIPALE =====
temp_measured = None
humidity = None
temp_setpoint = read_setpoint()

while True:
    try:
        current_time = time.ticks_ms()
        
        # Lecture du capteur (toutes les secondes)
        if time.ticks_diff(current_time, last_sensor_read) >= sensor_read_interval:
            temp_setpoint = read_setpoint()
            
            try:
                data = sensor.measurements
                temp_measured = data['t']
                humidity = data['rh']
            except Exception as e:
                print("Erreur lecture DHT20:", e)
                temp_measured = None
                humidity = None
            
            last_sensor_read = current_time

        # Calculer la différence
        if temp_measured is not None:
            temp_diff = temp_measured - temp_setpoint
        else:
            temp_diff = 0

        # === GESTION DES ÉTATS ===
        if temp_measured is None:
            # ERREUR CAPTEUR
            oled.clear_line(0)
            oled.clear_line(1)
            oled.print(f"Set: {temp_setpoint:.1f}C", 0, 0)
            oled.print("Capteur erreur", 1, 0)
            deactivate_buzzer()
            led.duty_u16(0)
            
        elif temp_diff > 3:
            # === MODE ALARME ===
            activate_buzzer()
            
            # LED: Clignotement rapide
            if time.ticks_diff(current_time, last_led_update) >= 125:
                blink_state = not blink_state
                led.duty_u16(65535 if blink_state else 0)
                last_led_update = current_time
            
            # Affichage: Défilement + clignotement de "ALARM"
            oled.clear_line(0)
            oled.print(f"Set: {temp_setpoint:.1f}C", 0, 0)
            
            # Clignotement du texte ALARM
            if time.ticks_diff(current_time, last_blink_toggle) >= blink_interval:
                blink_state = not blink_state
                last_blink_toggle = current_time
            
            # Défilement de "ALARM! TEMP °C"
            if time.ticks_diff(current_time, last_scroll_update) >= scroll_interval:
                scroll_position = (scroll_position + 1) % 16
                last_scroll_update = current_time
            
            if blink_state:
                alarm_text = f"ALARM! {temp_measured:.1f}C     "
                visible_text = (alarm_text * 2)[scroll_position:scroll_position + 16]
                oled.clear_line(1)
                oled.print(visible_text, 1, 0)
            else:
                oled.clear_line(1)
            
        elif temp_diff > 0:
            # === MODE TEMPÉRATURE ÉLEVÉE ===
            deactivate_buzzer()
            
            # LED: Effet breathing (dimmer progressif)
            if time.ticks_diff(current_time, last_led_update) >= led_update_interval:
                breathing_phase += 0.1
                led_breathing(breathing_phase)
                last_led_update = current_time
            
            # Affichage normal
            oled.clear_line(0)
            oled.clear_line(1)
            oled.print(f"Set: {temp_setpoint:.1f}C", 0, 0)
            oled.print(f"Amb: {temp_measured:.1f}C", 1, 0)
            
        else:
            # === MODE NORMAL ===
            deactivate_buzzer()
            led.duty_u16(0)
            
            # Affichage normal
            oled.clear_line(0)
            oled.clear_line(1)
            oled.print(f"Set: {temp_setpoint:.1f}C", 0, 0)
            oled.print(f"Amb: {temp_measured:.1f}C", 1, 0)

        # Debug console
        if temp_measured is not None:
            print(f"Consigne: {temp_setpoint:.1f}°C | Mesurée: {temp_measured:.1f}°C | "
                  f"Diff: {temp_diff:.1f}°C | Hum: {humidity:.1f}%")
        else:
            print(f"Consigne: {temp_setpoint:.1f}°C | Mesurée: ERREUR")

        time.sleep_ms(10)  # Petite pause pour ne pas surcharger le CPU

    except Exception as e:
        print(f"Erreur système: {e}")
        oled.clear()
        oled.print("SYSTEM ERROR", 0, 0)
        oled.print("Check sensors", 1, 0)
        deactivate_buzzer()
        led.duty_u16(0)
        time.sleep(2)