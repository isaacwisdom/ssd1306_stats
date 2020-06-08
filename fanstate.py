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
