from machine import Pin, PWM
from time import localtime, sleep
import network
import ntptime


#  Configuration Wi-Fi 
SSID = "Proximus-Home-9330_EXT"       
PASSWORD = "wzucy776xxk99"  

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)


print("Connexion au Wi-Fi...")
while not wlan.isconnected():
    sleep(0.5)
print("Connecte a", SSID)

#  Synchronisation heure via Internet 
ntptime.settime()
print("Heure synchronisee !")

#  Initialisation du servo 
servo = PWM(Pin(20))
servo.freq(50) 

def set_angle(angle):
    """Convertion  angle  en signal PWM pour le servo."""
    duty_min = 2000   
    duty_max = 8500  
    duty = int(duty_min + (angle / 180) * (duty_max - duty_min))
    servo.duty_u16(duty)


while True:
    annee, mois, jour, heure, minute, seconde, *_ = localtime()
    heure = (heure + 2) % 24  # UTC+2
    
    angle = ((12 - (heure % 12)) % 12) * (180 / 12) # conversion heure -> angle
    print(f"Heure : {heure:02d}:{minute:02d}  |  Angle servo : {angle:.1f}°")
    
    set_angle(angle)
    sleep(60)  # mis à jour chaque minute