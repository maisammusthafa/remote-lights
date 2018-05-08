#!/usr/bin/env python3

import lirc
import serial
import time
import RPi.GPIO as GPIO
import ruamel.yaml

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

sockid = lirc.init("lights", blocking = False)
arduino_serial = serial.Serial('/dev/ttyACM0', 9600)

yaml_file = open('lights.yaml', 'r')
stream = ruamel.yaml.load(yaml_file, ruamel.yaml.RoundTripLoader, preserve_quotes=True)
yaml_file.close()

states = stream['states']
config = stream['config']

increment = config['increment']
rgb_codes = config['rgb_codes']

flash = states['flash']
button = states['button']
color = states['color']
intensity = states['intensity']
leds = states['leds']

GPIO.setup(23, GPIO.OUT)
GPIO.output(23, not flash)

def tx_codes():
    rgb_arr = [round(x * (intensity)) for x in rgb_codes[color]]
    rgb_str = ', '.join(str(e) for e in rgb_arr)
    serial_code = '[{}]'.format(rgb_str)

    arduino_serial.write(serial_code.encode())
    print('{}\t{}\t{}'.format(button, color, round(intensity, 2)))

    global leds
    leds = True
    save_states()

def save_states():
    yaml_file = open('lights.yaml', 'w')

    states['flash'] = flash
    states['button'] = button
    states['color'] = color
    states['intensity'] = intensity
    states['leds'] = leds

    ruamel.yaml.round_trip_dump(stream, open('lights.yaml', 'w'), indent=4)
    yaml_file.close()

if flash:
    GPIO.output(23, not flash)
    print('FLASH\tFLASH\t{}'.format(1.0 if flash else 0.0))

if leds:
    time.sleep(2)
    tx_codes()

while True:
    codeIR = lirc.nextcode()
    if codeIR:
        button = codeIR[0]
        if button == 'FLASH':
            flash = not flash
            GPIO.output(23, not flash)
            print('FLASH\tFLASH\t{}'.format(1.0 if flash else 0.0))
            save_states()
            continue

        if button != 'OFF' and button != 'ON' and button != 'B_UP' and button != 'B_DOWN':
            color = button

        if button == 'ON':
            button = color
            leds = True
        elif button == 'OFF':
            arduino_serial.write('[0, 0, 0]'.encode())
            leds = False
            print('OFF\tOFF\t{}'.format(intensity))
            save_states()
            continue

        if button == 'B_DOWN':
            if intensity <= increment:
                continue
            intensity = round(intensity - increment, 1)
            rgb_arr = [round(x * (intensity)) for x in rgb_codes[color]]
        elif button == 'B_UP':
            if intensity == 1.0:
                continue
            intensity = round(intensity + increment, 1)

        tx_codes()

