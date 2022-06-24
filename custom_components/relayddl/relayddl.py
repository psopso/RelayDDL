import time as t
import sys

from smbus2 import SMBus
bus = SMBus(1)

DEVICE_BUS = 1
DEVICE_ADDR = 0x10
bus = smbus.SMBus(DEVICE_BUS)

def pokus():
  for i in range(1,5):
    bus.write_byte_data(DEVICE_ADDR, i, 0xFF)
    t.sleep(1)
    bus.write_byte_data(DEVICE_ADDR, i, 0x00)
    t.sleep(1)

def switch_on(device, ind):
  bus.write_byte_data(device, ind, 0xFF)

def switch_off(device, ind):
  bus.write_byte_data(device, ind, 0x00)

def switch_is_on(device, ind):
  if bus.read_byte_data(device, ind) == 255 :
    return True
  else:
    return False
