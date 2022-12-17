#!/usr/bin/env python3

import cv2
import rospy
import numpy as np
from cv_bridge import CvBridge
from typing import cast
from duckietown.dtros import DTROS, TopicType, NodeType
from duckietown_msgs.msg import (
    WheelsCmdStamped
)
from sensor_msgs.msg import CompressedImage, Image

class movement(DTROS):

    def __init__(self, node_name):
        super(movement, self).__init__(node_name=node_name, node_type=NodeType.DRIVER)
        self.wheelPub = rospy.Publisher("/ubuntu/wheels_driver_node/wheels_cmd", WheelsCmdStamped, queue_size=1, dt_topic_type=TopicType.CONTROL)
        #self.imgSub = rospy.Subscriber("/ubuntu/camera_node/image/compressed", CompressedImage, queue_size=20, callback = self.imageProcessCallback)
        self.imgPub = rospy.Publisher("testImage",Image, queue_size=1, dt_topic_type=TopicType.DEBUG)
        
        # 0: stop, 1: forward, 2: turn
        self.number = 0

        self.bridge = CvBridge()

        self.cap = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)

        #set dimensions to be 160x120 for faster processing time
        self.cap.set(3,160)
        self.cap.set(4,120)

        #tune the wheels to be moving at the same speed
        self.tuneRight = 0.125
        self.tuneLeft = 0.15

        self.run()

    def run(self):
        #10 images a second
        rate = rospy.Rate(10)

        while not rospy.is_shutdown():

            self.imageProcessing()
            self.move()

            rate.sleep
        
    def imageProcessing(self):

        #retrieve the image
        try:
            _, image = self.cap.read()
            height, width, channels = image.shape
            rospy.loginfo(height)
        except:
            image = []
            rospy.loginfo("no image")
        
        width = int(image.shape[1])
        height = int(image.shape[0])

        rospy.loginfo(height)

        if image != []:
            rospy.loginfo("image detected")

            #convert to HSV color space for processing
            image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            #define range for green
            lower1 = np.array([30,70,50])
            upper1 = np.array([102,255,255])
            mask1 = cv2.inRange(image, lower1, upper1)

            #define range for blue
            lower2 = np.array([100,150,0])
            upper2 = np.array([140,255,255])
            mask2 = cv2.inRange(image, lower2, upper2)
            
            mask = mask2
            
            try:
                #find number of blue pixels
                numB = len(cv2.findNonZero(mask2))
            except:
                numB = 0

            try:
                #find number of green pixels
                numG = len(cv2.findNonZero(mask1))
            except:
                numG = 0

            rospy.loginfo("green")
            rospy.loginfo(numG)
            rospy.loginfo("blue")
            rospy.loginfo(numB)

            #decide which command to send based on colors
            if numB > 30 or numG > 30:
                if numB > numG:
                    rospy.loginfo("I see blue. Turning")
                    number = 2
                if numG > numB:
                    rospy.loginfo("I see green. Going forward")
                    number = 1
            else:
                number = 0

            #publish debug image of the mask
            # image = cv2.cvtColor(image, cv2.COLOR_HSV2BGR)
            # image = cv2.bitwise_and(image,image, mask=mask)
            # image_msg = self.bridge.cv2_to_imgmsg(image, "bgr8")

            # self.imgPub.publish(image_msg)
        


    def move(self):
        self.msg = WheelsCmdStamped()

        # Put the wheel commands in a message and publish
        # Record the time the command was given to the wheels_driver
        self.msg.header.stamp = rospy.get_rostime()

        if self.number == 0:
            self.msg.vel_left = 0
            self.msg.vel_right = 0
        elif self.number == 1:
            self.msg.vel_left = self.tuneLeft
            self.msg.vel_right = self.tuneRight
        elif self.number == 2:
            self.msg.vel_left = -self.tuneLeft
            self.msg.vel_right = self.tuneRight
        else:
            self.msg.vel_left = 0
            self.msg.vel_right = 0
        self.wheelPub.publish(self.msg)
            






        

if __name__ == "__main__":
    node = movement(node_name="wheels_driver_node")
