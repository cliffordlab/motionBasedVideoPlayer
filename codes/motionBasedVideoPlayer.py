#!/usr/bin/python3
"""
Author: Pradyumna Byppanahalli Suresha (alias Pradyumna94)
Last Modified: May 20th, 2020
License:
BSD-3 License
Copyright [2020] [Clifford Lab]
Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
may be used to endorse or promote products derived from this software without
specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from picamera.array import PiRGBArray
from picamera import PiCamera
from time import time,sleep
import numpy as np
import errno
import sys
import cv2
import os



class VideoPlayer:
    """
    """
    def __init__(self,
                 VIDEO_BASE_FOLDER='/home/pi/motionBasedVideoPlayer/data/picameraVideos/',
                 resolution = (320, 256),
                 framerate = 30,
                 max_signal_length = 100):
        """Definitions"""
        self.VIDEO_BASE_FOLDER = VIDEO_BASE_FOLDER
        self.current_time_ms = lambda: int(round(time() * 1000))
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        sleep(0.1)
    
    def get_video_filename(self):
        """Open a h264 file to write video frames and return the file name"""
        return self.VIDEO_BASE_FOLDER+str(self.clock)+'_video.h264'


    def motionDetector(self, poll_time = 0.03, cap = []):
        """
        Thread for computing average red, green, blue and grey in video frames.
        Uses cv2 and numpy module to compute the average channel intensities
        
        Parameters
        ----------
        poll_time: float
            Expects a float value that specifies the sleep time between two Raspberry Pi Camera frames
        """
        self.clock = self.current_time_ms()
        self.camera.start_recording(self.get_video_filename())
        cv2.startWindowThread()
        frameOld = np.zeros([self.camera.resolution[1], self.camera.resolution[0]], dtype=np.uint8)
        
        if (not cap.isOpened()):
            printf("Video object is not open...")
            return
        
        idx = 1
        for frame in self.camera.capture_continuous(self.rawCapture,
                                format="bgr",
                                use_video_port=True):
            
            frame = frame.array
            #frameb = frame[:,:,0] # Ignore Blue channel
            #frameg = frame[:,:,1] # Ignore Green channel
            #framer = frame[:,:,2] # Ignore Red channel
            framegs = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY) # Extract Grayscale channel
            
            # Take the difference (frameDiff) between current frame (framegs) and the previous frame (frameOld)
            frameDiff = np.array(np.absolute(np.array(framegs, dtype=int) - np.array(frameOld, dtype=int)), dtype=np.uint8)
            
            # Assign current frame to frameOld to be used in next iteration
            frameOld = framegs

            # Compute baseline and scaled motion signal values for the current frame
            nonZeroPixelCount = np.count_nonzero(frameDiff)
            motionSignalBaseline = np.mean(np.mean(frameDiff))
            motionSignalScaled = np.sum(frameDiff)/nonZeroPixelCount
            
            # Modify below line to specify how many frames to skip based on the above motion signals.
            # I round the motionSignalScaled value and bound it within 1 and 50
            #print(int(motionSignalScaled))
            nFrameSkip = min(int(motionSignalScaled), 200)
            nFrameSkip = max(1, nFrameSkip)
            # Uncomment below to Binarize nFrameSkip
            #if (nFrameSkip > 15):
            #    nFrameSkip = 100
            #else:
            #    nFrameSkip = 0
            
            idx = idx + nFrameSkip
                
            # If display video has ended, then restart
            if (not cap.isOpened()):
                cap.release()
                # Copy the cloned archive back to the original variable
                return
                
            # Skip Video frames
            # Method 1: Very slow on RasPi
            #for ii in range(int(nFrameSkip)):
            #    ret, dispFrame = cap.read()
            
            # Method 2: Seek idx^th frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            
            # If video has ended return
            if (not cap.isOpened()):
                cap.release()
                cv2.destroyAllWindows()
                self.camera.stop_recording()
                return
            
            # Skip nFrameSkip frames 
            ret, dispFrame = cap.read()
            idx = idx + 1
            
            # If video has ended return
            if (not cap.isOpened()):
                cap.release()
                cv2.destroyAllWindows()
                self.camera.stop_recording()
                return
            
            # Get next frame
            ret, dispFrame = cap.read()
            idx = idx + 1
            
            # Show Video frame 
            try:
                cv2.imshow('frame',dispFrame)
            except:
                # If video has ended return
                cap.release()
                cv2.destroyAllWindows()
                self.camera.stop_recording()
                return
            
            # Routine to exit 
            k = cv2.waitKey(30) & 0xff
            if k == 27:
                print("Video Stream stops. Press Ctrl+C now.")
                cv2.destroyAllWindows()
                self.camera.stop_recording()
                sys.exit("Ctrl-C was pressed")

            self.rawCapture.truncate(0)
            # Optionally sleep for poll_time seconds
            #sleep(poll_time)

if __name__ == "__main__":
    
    try:
        os.mkdir('/home/pi/motionBasedVideoPlayer/data/picameraVideos')
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass
    
    
    videoFile = '/home/pi/motionBasedVideoPlayer/data/displayVideos/test.mp4' 
    
    while True:
        vidPlayer = VideoPlayer()
        cap = cv2.VideoCapture(videoFile)
        vidPlayer.motionDetector(poll_time = 0, cap = cap)