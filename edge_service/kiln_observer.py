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
import argparse

# internal imports
import Number_Detection as nd
import RestAPICall as API

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
PICTURE_FILE_SUBDIR = os.path.join(DIR_PATH,'pictures')
#
# relative file path for history file
HISTORY_FILE_SUBDIR = os.path.join(DIR_PATH,'history')
#
# history file name
HISTORY_FILE_NAME = 'history.json'
#
# for debug purpose. Set to 'True', to show messages and more output
DEBUG = False
#
# in depth debug for openCV including opening windows with pictures etc.
DEBUG_OCV = False

# Main service - should always be running, when edge is active
# capture interval can be changed for various use cases

def kiln_observer(capture_interval, anon_key, x_api_key):
    
    # create API object
    api = API.RestAPICalls('https://lgvhvdvlcjsznliufwrk.supabase.co/functions/v1/datapoints-api', anon_key, x_api_key)
    
    while RUN:
        # capture new picture with webcam
        print("PICTURE_FILE_SUBDIR: " + PICTURE_FILE_SUBDIR)
        image_file_name, time_stamp = capture_new_image(PICTURE_FILE_SUBDIR)

        # extract temperature reading
        temperature = extract_termperature(PICTURE_FILE_SUBDIR, image_file_name)

        # write data to history.json
        write_temperature(HISTORY_FILE_SUBDIR, HISTORY_FILE_NAME, temperature, time_stamp)

        # push temperature data to server
        if DEBUG:
            print("Uploading data to server ...")
        upload_successful = api.POSTTemperature(datetime.strptime(time_stamp, "%Y-%m-%d %H-%M-%S").isoformat(), temperature)
        
        if not upload_successful:
            print("Error on uploading. Service stopped!")
            break
        else:
            if DEBUG:
                print("Upload successful!")
            
        # wait until next image shall be taken
        if DEBUG:
            print("Now sleeping " + str(capture_interval / 1000) + " seconds to next reading ...")
            
        time.sleep(capture_interval / 1000)


# capture raw image using openCV and write the file with the current time stamp as prefix
def capture_new_image(picture_file_subdir):

    # Initialize video stream with usb camera, where 0 is the default camera
    video_stream = cv2.VideoCapture(0)

    # set focus manually to avoid blurry images
    video_stream.set(28, 16)
    
    # Capture one frame
    success, frame = video_stream.read()

    if success:
        # get current time stamp from datetime
        current_time_stamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

        # set filename
        filename = current_time_stamp + "_temperature.png"

        # write image to file with datetime timestamp as prefix   
        cv2.imwrite(os.path.join(picture_file_subdir, filename), frame)  
        if DEBUG:
            # show image name and folder
            print("File name is: " + filename)
            print("Folder is: " + picture_file_subdir)
            
        # show image recognition if in depth debug needed
        if DEBUG_OCV:
            cv2.imshow('window_handle', frame)  
            cv2.waitKey(0)                      
            cv2.destroyWindow('window_handle')       
    else:
        raise Exception('Error occurred in capture_new_image: Image could not be captured')

    video_stream.release()

    # return file name for later handling
    return filename, current_time_stamp


def extract_termperature(picture_file_subdir, image_file_name):


    # get absolute image path
    image_path = os.path.join(picture_file_subdir, image_file_name)
    
    try:
        return_char_list = nd.getNumberFromImage(image_path, DEBUG_OCV)
    except:
        return_char_list = "NA"   
    
    temperature = ""

    # concatenate chars from list to string
    for char in return_char_list:
        temperature = temperature + str(char)
            
    # only take string before Â° and convert to integer and return
    if DEBUG:
        print("Image processed. Temperature string: " + temperature)
    if(str.split(temperature, 'Â°')[0].__contains__("NA") or len(temperature) < 2):
        number = -1      
    else:
        number = int(str.split(temperature, 'Â°')[0])  

    if DEBUG:
        print("Image processed. Temperature: " + str(number))

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
    if DEBUG:
        print("Writing .json file to: " + history_file_path)
        
    with open(history_file_path, 'w', encoding='utf-8') as file:
        json.dump(temperaturdaten, file, ensure_ascii=False, indent=4)
    
if __name__ == "__main__":

    # use argparse to read keys and time interval to be set
    parser = argparse.ArgumentParser(description="MyKilnBuddy edge service, to capture and send temperature data from your kiln")
    parser.add_argument("-u", "--url", type=str,
                        help="API url required, add with e.g. -u https://lgvhvdvlcjsznliufwrk.supabase.co/functions/<your-api-name>")
    parser.add_argument("-t", "--time", type=int,
                        help="Time interval for capturing required, add with e.g. -t ")
    parser.add_argument("-a1", "--anon", type=str,
                        help="anon key for authentication required. Add with -a1 XXX")
    parser.add_argument("-a2", "--api", type=str,
                        help="x-api-key for authentication required. Add with -a2 YYY")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show debug output. Activate with -v")
    parser.add_argument("-debug", "--debug_ocv", action="store_true",
                        help="Show openCV debug pictures. Activate with -debug")

    args = parser.parse_args()
    
    #  read, if user wants debug output
    if args.verbose:
        DEBUG=True
    
    # read if user wants to dig really deep into openCV
    if args.debug_ocv:
        DEBUG_OCV = True
        
    # check if all needed input is given
    if not args.time or not args.anon or not args.api:
        parser.error("-t/--time, -a1/--anon, and -a2/--api must be specified")
    else:
        # start service
        kiln_observer(args.time, args.anon, args.api)
