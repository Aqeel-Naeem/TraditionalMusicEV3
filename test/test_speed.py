# import ev3_dc as ev3
# import time

# # Replace with the MAC address of a brick you know has a motor connected
# my_ev3 = ev3.EV3(protocol=ev3.BLUETOOTH, host='00:16:53:41:95:2e')
# motor = ev3.Motor(ev3.PORT_A, ev3_obj=my_ev3)

# print("Spinning at speed 10...")
# motor.start_move(speed=10)
# time.sleep(3)
# motor.stop()

# time.sleep(1)  # brief pause between tests

# print("Spinning at speed 100...")
# motor.start_move(speed=100)
# time.sleep(3)
# motor.stop()

# print("Done.")

import ev3_dc as ev3
import time

my_ev3 = ev3.EV3(protocol=ev3.BLUETOOTH, host='00:16:53:41:95:2e')
motor = ev3.Motor(ev3.PORT_A, ev3_obj=my_ev3)  # replace PORT_X with chime's actual port

print("Hit at speed 20...")
motor.start_move_for(duration=0.3, speed=20)
time.sleep(2)

print("Hit at speed 100...")
motor.start_move_for(duration=0.3, speed=100)
time.sleep(2)

print("Done.")