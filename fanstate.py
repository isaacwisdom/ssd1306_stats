#This is a test of the ability to read a GPIO pin from an external program.
#Other Raspberry Pi GPIO programs seem to support this ability, but it seems that CircuitPython does not.
import board
import digitalio

fan = digitalio.DigitalInOut(board.D24)
fan.direction = digitalio.Direction.OUTPUT

print("setting d24 on")
fan.value = True
print(fan.value)

print("setting d24 off")
fan.value = False
print(fan.value)
