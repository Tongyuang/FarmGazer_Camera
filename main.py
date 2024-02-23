# /usr/bin/python3

from motor.ServoKit import *
from picamera import PiCamera
from time import sleep
import tty, sys, termios
import os
from datetime import datetime
from blob_upload import blob_uploader
import numpy as np
from flask import Flask, Response
import threading
import io

from image_description import get_desc_by_img_url,post_comment

img_blob_prefix ="https://farmgazerstorage.blob.core.windows.net/images/"
img_blob_suffix = "?sv=2022-11-02&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2024-03-16T08:07:06Z&st=2024-02-09T02:07:06Z&spr=https&sig=flmsaOix%2Biud3OTwOB20SI4MMx3bCRV0BDOpCgwcJls%3D"

app = Flask(__name__)


global image_ctr
image_ctr = 16

global stream_cur_frame_bytes
stream_cur_frame_bytes = None

#stream = io.BytesIO()
# initalize camera
camera = PiCamera()
#stream = io.BytesIO()

class ImageCapAttr:
    # Class-level default attributes
    defaults = {
        'stream': False,
        'save': True,
        'save_dir': "/home/pi/code/FarmGazer_Camera/data",
        'farm': "Kevinfarm",
        'field': "Plant01",
        'date': "2024-02-08",
        'resolution': (1920, 1080),
        'upload': False
    }
    
    def __init__(self, **kwargs):
        # Iterate over the defaults and set them, overridden by any kwargs provided
        for attr_name, default_value in self.defaults.items():
            setattr(self, attr_name, kwargs.get(attr_name, default_value))
            
class pan_tilt_motor:
    def __init__(self):
        # create a motor
        self.servoKit = ServoKit(4)
        self.motor_step = 5
            
    def step(self,motor_id=0,direction=0):
        
        # motor: 0 for pan and 1 for tilt
        assert motor_id in [0,1]
        
        # direction: -1 or 1
        assert direction in [-1,1]
        
        self.servoKit.setAngle(motor_id, self.servoKit.getAngle(motor_id) 
                               - direction*self.motor_step)
    
    def setAngle(self,motor_id,angle=90):
        # set angle
        # motor: 0 for pan and 1 for tilt
        assert motor_id in [0,1]
        if angle<0:
            angle = 0
        elif angle > 180:
            angle = 180
        self.servoKit.setAngle(motor_id, angle)     
    
    def setAngles(self,angles=(90,90)):   
        assert isinstance(angles,tuple) and len(angles)==2
        self.setAngle(0,angles[0])
        self.setAngle(1,angles[1])
    

def parseKey(k, motor, camera, uploader, attr:ImageCapAttr):#image_dir='/home/pi/Pictures/'):
    # motor is pan_tilt_motor
    # camera is pi camera
    global image_ctr
    global stream_cur_frame_bytes
    # control the motor in WASD
    if k == 's':
        motor.step(1,1)
    elif k == 'w':
        motor.step(1,-1)
    elif k == 'd':
        motor.step(0,1)
    elif k == 'a':
        motor.step(0,-1)
    
    # control the camera
    if k == 'r':
        # sleep to get the lighting condition
        print(f'start capturing...')
        image_name = '{}_{}_{}_{}.jpg'.format(attr.farm,attr.field,attr.date,image_ctr)
        sleep(2)
        
        if attr.stream and attr.upload:
            # do not capture, read from stream directly
            print('uploading to default storage...')
            uploader.upload(stream_cur_frame_bytes,blob_name=image_name)
            image_ctr += 1
            print('Done')
            return
        
        if attr.save:
            image_pth = os.path.join(attr.save_dir,image_name)
            camera.capture(image_pth)
            print(f'image saved at %s' % image_pth)
            
            if attr.upload:
                print('uploading to default storage...')
                uploader.upload(image_pth,blob_name=image_name)
                print('Done')
        else:
            # not save, put it into a numpy array
            output = np.empty((attr.resolution[0], attr.resolution[1], 3), dtype=np.uint8)
            camera.capture(output, 'rgb')
            # upload to blob
            if attr.upload:
                print('uploading to default storage...')
                uploader.upload(output,blob_name=image_name)   
                print('Done')         
        image_ctr += 1

def generate_camera_stream(camera):
    """Generator function that captures images from the camera and yields them for the video stream."""
    while True:
        global stream_cur_frame_bytes
        stream = io.BytesIO()
        camera.capture(stream, format='jpeg')
        stream.seek(0)
        frame = stream.read()
        stream_cur_frame_bytes = frame
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Route for serving the video feed."""
    return Response(generate_camera_stream(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def run_flask_app():
    """Function to run the Flask app."""
    app.run(host='0.0.0.0', port=5000, threaded=True)

def main():
    # set para
    date = datetime.now().strftime("%Y-%m-%d")
    attr = ImageCapAttr(stream=True, save=True,date=date,resolution=(1920,1080),upload=True)
    
    camera.resolution = attr.resolution
    # initialize pan_tilt_motor
    motor = pan_tilt_motor()
    
    # uploader
    uploader = blob_uploader()
    
    # Start video stream in a separate thread
    threading.Thread(target=run_flask_app, daemon=True).start()
    
    # key
    k = ''
    filedescriptors = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin)
    print(f'press q to exit')
    while(True):
        
        k = sys.stdin.read(1)[0]
        if k != 'q':
            parseKey(k, motor, camera,uploader,attr)
        else:
            # break
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, filedescriptors)
            break
        

def debug(farmname='debug'):
    date = datetime.now().strftime("%Y-%m-%d")
    attr = ImageCapAttr(farm=farmname,stream=True, save=True,date=date,resolution=(1920,1080),upload=True)
    
    camera.resolution = attr.resolution
    # initialize pan_tilt_motor
    motor = pan_tilt_motor()
    sleep(2)
    actions = [(90,100),(30,90),(150,90),(90,30)]
    
    uploader = blob_uploader()
    img_desc = None
    for i in range(len(actions)):
        
        motor.setAngles(actions[i])
        image_name = "temp_{}.jpg".format(i)
        sleep(2)
        # set image path
        image_pth = os.path.join(attr.save_dir,image_name)
        # take picture
        camera.capture(image_pth)
        # upload
        print('uploading to default storage...')
        blob_name ='{}_{}_{}_{}.jpg'.format(attr.farm,attr.field,attr.date,i)
        uploader.upload(image_pth,blob_name=blob_name)
        if img_desc is None:
            print('Calling OpenAI API...')
            img_url = img_blob_prefix + blob_name + img_blob_suffix
            img_desc = get_desc_by_img_url(url_in = img_url)
            print(img_desc)
            print('Uploading comments to blob storage')
            post_comment(image_id = blob_name, user_name = 'OPENAI_DESC', comment_text=img_desc)
        print('Done')
        
  
if __name__ == "__main__":
    #main()    
    debug()


    