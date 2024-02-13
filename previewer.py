from picamera import PiCamera
from time import sleep
import sys

class Previewer:
    def __init__(self):
        self.camera = PiCamera()
    
    def preview(self,delay=-1):
        self.camera.start_preview()
        if delay > 0:
            sleep(delay)
        else:
            # press enter to stop
            while True:
                rec = sys.stdin.read(1)
                if rec != None:
                    if rec == '\x0a': 
                        break
        
        self.camera.stop_preview()
    
    


if __name__ == "__main__":
    previewer = Previewer()
    previewer.preview()

