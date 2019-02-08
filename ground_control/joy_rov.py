import pygame,time,zmq,pickle,sys
#pygame.init() ### =100%cpu
sys.path.append('../')
import config

pygame.display.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()
name = joystick.get_name()
isxbox = 'Microsoft X-Box One pad' in name
print("Joystick name: {}".format(name))
axes = joystick.get_numaxes()
print( "Number of axes: {}".format(axes))
n_buttons = joystick.get_numbuttons()

clock = pygame.time.Clock()

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://127.0.0.1:%d" % config.zmq_pub_joy)

done = False
cnt=0

start_time=time.time()
joy_log=open('joy.log','wb')

def pub(topic,data):
    socket.send_multipart([topic,data])
    pickle.dump([time.time()-start_time,topic,data],joy_log,-1)

while not done:
    # EVENT PROCESSING STEP
    cnt+=1
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
 
        if event.type == pygame.JOYBUTTONDOWN:
            print("Joystick button pressed.")
            buttons = [joystick.get_button(i) for i in range(n_buttons)]
            print('pub buttons=',buttons)
            #socket.send_multipart([config.topic_button,pickle.dumps(buttons)])
            pub(config.topic_button,pickle.dumps(buttons))
        if event.type == pygame.JOYBUTTONUP:
            print("Joystick button released.")


        
        hat = joystick.get_hat(0)
        if abs(hat[0])>0 or abs(hat[1])>0:
            print('hat',hat)
            socket.send_multipart([config.topic_hat,pickle.dumps(hat)])


        axes_vals = []
        for i in range(axes):
            axis = joystick.get_axis(i)
            if isxbox:
                if abs(axis)<0.1:
                    axis=0.0
            axes_vals.append(axis)
        if cnt%10==0:
            print('axes_vals=',','.join(['{:4.3f}'.format(i) for i in axes_vals]))
        #mixng axes
        
        pub(config.topic_axes,pickle.dumps(axes_vals,-1))
        #socket.send_multipart([config.topic_mixing,pickle.dumps([port,starboard,vertical],-1)])
        #print('{:> 5} P {:> 5.3f} S {:> 5.3f} V {:> 5.3f}'.format(cnt,port,starboard,vertical),end='\r')

    #pygame.time.wait(0)
    clock.tick(30)
pygame.quit()
