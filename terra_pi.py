#!/usr/bin/env python3
# -- coding: utf-8 --

import RPi.GPIO as GPIO
import schedule
import time
import logging
import yaml
import json
import os
import datetime
import signal
import sys

log_format = '[%(asctime)s][%(levelname)s][%(name)s][%(funcName)s:%(lineno)d]: %(message)s'
logging.basicConfig(filename="log.txt", filemode='a', datefmt='%H:%M:%S', format=log_format, level=logging.DEBUG)
logger = logging.getLogger()

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)


def turn_light_mode(pin: int, name: str, is_on: bool) -> None:
    logging.info(f"{name} setup {'OFF' if GPIO.input(pin) == 0 else 'ON'}")
    GPIO.output(pin, GPIO.LOW if is_on else GPIO.HIGH)


def turn_fogging_mode(pin: int, elapsed_time: int, name: str) -> None:
    logging.info(f"{name} mode setup ON for {elapsed_time} secondes")
    GPIO.output(pin, GPIO.LOW)
    time.sleep(elapsed_time)
    logging.info(f"{name} mode setup OFF")
    GPIO.output(pin, GPIO.HIGH)


def get_fogger_scheduler(fogging_class: list) -> None:
    logger.info(f"Get fogger Scheduler for {fogging_class['name']}")
    for item in fogging_class['hours']:
        logger.info(f"Get Scheduler {fogging_class['name']} hour for {item}")
        schedule.every().day.at(item['hour']).do(turn_fogging_mode, fogging_class['pin'], item['elapsed_time'], fogging_class['name'])


def get_light_scheduler(light_class: list) -> None:
    logger.info(f"Get light Scheduler for {light_class['name']}")
    schedule.every().day.at(light_class['start']).do(turn_light_mode, light_class['pin'], light_class['name'])
    schedule.every().day.at(light_class['end']).do(turn_light_mode, light_class['pin'], light_class['name'])
    
    
def turn_on_light_if_in_range_on_boot(light_class: list):
    logger.info(f"Check if {light_class['name']} need to be on or offgit add . ")
    now = datetime.datetime.now()
    start = datetime.datetime.strptime(light_class['start'], '%H:%M').replace(year=now.year, month=now.month, day=now.day)
    end = datetime.datetime.strptime(light_class['end'], '%H:%M').replace(year=now.year, month=now.month, day=now.day)
    if now > start:
        turn_light_mode(light_class['pin'], light_class['name'], True)
    if now > end:
        turn_light_mode(light_class['pin'], light_class['name'], False)


def init_gpio(gpio_pin: list) -> None:
    logger.info(f"Initialize GPIO : {gpio_pin}")
    for pin in gpio_pin:
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)


def get_active_pin(config: dict):
    logger.info(f"Get active pin")
    active_pin = []
    for item in config:
        if item['active']:
            logger.info(f"Activate {item}")
            active_pin.append(item['pin'])
    return active_pin


def get_class_items(config):
    logger.info(f"Get class items")
    fogging, light = [], []
    for item in config:
        if item['class'] == "fogging":
            fogging.append(item)
        if item['class'] == "light":
            light.append(item)
    return fogging, light


def get_config() -> dict:
    logger.info(f"Get config")
    if os.path.exists('./config.yaml'):
        with open('./config.yaml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            return config
    else:
        raise FileNotFoundError


def signal_handler(sig, frame):
    logger.info(f"Turn off all GPIO after CTRL + c")
    for pin in active_pin:
        GPIO.output(pin, GPIO.HIGH)
    sys.exit(0)


def main():
    logger.info("\n")
    logger.info(f"Init Terra py script")
    config = get_config()
    fogging, light = get_class_items(config)
    global active_pin
    active_pin = get_active_pin(config)
    init_gpio(active_pin)
    for light_item in light:
        get_light_scheduler(light_item)
    for fogger_item in fogging:
        get_fogger_scheduler(fogger_item)
    for light_item in light:
        turn_on_light_if_in_range_on_boot(light_item)
    while True:
        schedule.run_pending()
        time.sleep(1)


signal.signal(signal.SIGINT, signal_handler)
main()
