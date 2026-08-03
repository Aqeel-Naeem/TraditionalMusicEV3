import ev3_dc as ev3

my_ev3 = ev3.EV3(protocol=ev3.BLUETOOTH, host='00:16:53:46:be:aa')
print("Connected to:", my_ev3)

motor = ev3.Motor(ev3.PORT_A, ev3_obj=my_ev3)
motor.start_move_for(duration=1, speed=50)