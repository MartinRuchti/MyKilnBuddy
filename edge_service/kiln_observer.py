# Module name: kiln_observer
# 
# AUTOR: Martin Ruchti
#
# Note: This module is part of the "myKilnBuddy" solution, that grabs your kiln temperatures 
# and sends it to your server, to be read by your mobile device app

#
# IMPORTS
#
import cv2
from datetime import datetime
import os
import json
import time

# internal imports
import Number_Detection as nd

# GLOBAL VARIABLES
#
# defines the image capture interval in milliseconds
CAPTURE_INTERVAL = 1000
#
# defines, if your service should be runnning. Set to 'False' to stop the service
RUN = True
#
# get current directory for absolute paths
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
#
# relative file path for pictures
PICTURE_FILE_SUBDIR = os.path.join(DIR_PATH,'/pictures')
#
# relative file path for history file
HISTORY_FILE_SUBDIR = os.path.join(DIR_PATH,'/history')
#
# history file name
HISTORY_FILE_NAME = '/history.json'
#
# for debug purpose. Set to 'True', to show messages and more output
DEBUG = True

# Main service - should always be running, when edge is active
# capture interval can be changed for various use cases

def kiln_observer(capture_interval = 1000):
    
    while RUN:
        # capture new picture with webcam
        image_file_name, time_stamp = capture_new_image(PICTURE_FILE_SUBDIR)

        # extract temperature reading
        temperature = extract_termperature(PICTURE_FILE_SUBDIR, image_file_name)

        # write data to history.json
        write_temperature(HISTORY_FILE_SUBDIR, temperature, time_stamp)

        # wait until next image shall be taken
        time.sleep(CAPTURE_INTERVAL / 1000)


# capture raw image using openCV and write the file with the current time stamp as prefix
def capture_new_image(picture_file_subdir):

    # Initialize video stream with usb camera, where 0 is the default camera
    video_stream = cv2.VideoCapture(0)

    # Capture one frame
    success, frame = video_stream.read()

    if success:
        # get current time stamp from datetime
        current_time_stamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

        # set filename
        filename = current_time_stamp + "temperature.png"

        # write image to file with datetime timestamp as prefix   
        cv2.imwrite(os.path.join(picture_file_subdir, filename), frame)  
        if DEBUG:
            # show image until key is pressed
            cv2.imshow(filename, frame)  
            cv2.waitKey(0)                      
            cv2.destroyWindow(filename)       
    else:
        raise Exception('Error occurred in capture_new_image: Image could not be captured')

    video_stream.release()

    # return file name for later handling
    return filename, current_time_stamp


def extract_termperature(picture_file_subdir, image_file_name):


    # get absolute image path
    image_path = os.path.join(picture_file_subdir, image_file_name)
    
    try:
        return_char_list = nd.getNumberFromImage(image_path, DEBUG)
    except:
        return_char_list = "NA"   
    
    temperature = ""

    # concatenate chars from list to string
    for char in return_char_list:
        temperature = temperature + str(char)
            
    # only take string before ° and convert to integer and return
    if(str.split(temperature, '°')[0].__contains__("NA") or len(temperature) < 2):
        number = -1      
    else:
        number = int(str.split(temperature, '°')[0])  

    if DEBUG:
        print("Image processed. Temperature: " + number)

    return number


def write_temperature(history_file_subdir, history_file_name, temperature, time_stamp):
    
    # get full history file path
    history_file_path = os.path.join(history_file_subdir, history_file_name)

    # if file does not exist yet, make it
    if not os.path.isfile(history_file_path):
        # if file does not exist yet, create empty data container
        temperaturdaten = []
    else:
        # if file exists, read existing data
        with open(history_file_path, 'r') as file:
            temperaturdaten = json.load(file)

    # append data
    if temperature is not None:
        temperaturdaten.append({
            "timestamp": time_stamp,
            "temperatur": temperature})
    
    # write new data to history file
    with open(history_file_path, 'w', encoding='utf-8') as file:
        json.dump(temperaturdaten, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":

    # run the main functionality
    # TODO: add argparse for time interval to be set
    kiln_observer(1000)