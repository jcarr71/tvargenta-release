import RPi.GPIO as GPIO
import time

# Configuracion
CLK = 17  # GPIO17 (Pin 11)
DT = 18   # GPIO18 (Pin 12)
SW = 27   # GPIO27 (Pin 13)

GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

last_clk = GPIO.input(CLK)

print("Move el encoder (CTRL+C for salir)")

try:
    while True:
        current_clk = GPIO.input(CLK)
        current_dt = GPIO.input(DT)

        if current_clk != last_clk and current_clk == 0:
            if current_dt != current_clk:
                print("⏩ Giro horario")
            else:
                print("⏪ Giro antihorario")
        last_clk = current_clk

        if GPIO.input(SW) == 0:
            print("🔘 Boton presionado")
            time.sleep(0.3)

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nSaliendo...")
finally:
    GPIO.cleanup()
