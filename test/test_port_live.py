import ev3_dc as ev3
import time

my_ev3 = ev3.EV3(protocol=ev3.BLUETOOTH, host='00:16:53:41:95:2e')
print("First connection:")
print(my_ev3.sensors_as_dict)

my_ev3.__del__()  # properly close this connection first
time.sleep(2)      # give the brick a moment to release it

input("Now physically unplug a motor, then press Enter...")

my_ev3_2 = ev3.EV3(protocol=ev3.BLUETOOTH, host='00:16:53:41:95:2e')
print("After a brand new connection:")
print(my_ev3_2.sensors_as_dict)