import RPi.GPIO as GPIO
import time

TRIG = 23
ECHO = 24

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    time.sleep(2)

def get_distance():
    # Send trigger pulse
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    # Wait for echo start
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()

    # Wait for echo end
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    # Calculate pulse duration
    pulse_duration = pulse_end - pulse_start

    # Convert to cm
    distance = pulse_duration * 17150
    distance = round(distance, 2)

    return distance

if __name__ == "__main__":
    try:
        setup()
        while True:
            dist = get_distance()
            print(f"Distance: {dist} cm")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Measurement stopped by user")
        GPIO.cleanup()

