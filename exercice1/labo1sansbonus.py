import machine
import time


led = machine.Pin(16, machine.Pin.OUT)
button = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_DOWN)

# Variables d'état
mode = 0          
last_button = 0   # mémorise l'état précédent du bouton
last_toggle = 0   # temps du dernier changement LED
led_state = 0     

while True:
    # Lecture bouton (détection front montant)
    current_button = button.value()
    if current_button == 1 and last_button == 0:
        mode = (mode + 1) % 3   # cycle entre 0, 1, 2
        print("Bouton pressed :", mode)
        time.sleep(0.2)         # anti-rebond

    last_button = current_button

    # Gestion des modes
    if mode == 0:   # LED éteinte
        led.value(0)

    elif mode == 1:  #  (0,5 Hz -> période 2s)
        if time.ticks_ms() - last_toggle > 1000:  #  state ON 1 s OFF 1s 1s=1000ms
            led_state = not led_state
            led.value(led_state)
            last_toggle = time.ticks_ms()

    elif mode == 2:  #  (2 Hz -> période 0,5s)
        if time.ticks_ms() - last_toggle > 250:  
            led_state = not led_state  # mis a true
            led.value(led_state)
            last_toggle = time.ticks_ms()
