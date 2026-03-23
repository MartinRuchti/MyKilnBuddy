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
import requests

# internal imports
import Number_Detection as nd
import RestAPICall as API

#
# get current directory for absolute paths
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
#
# relative file path for pictures
PICTURE_FILE_SUBDIR = os.path.join(DIR_PATH,'pictures')
#


# Main function is used, to test pictures with number detection
# used to optimize the detection to your camera output

def extract_termperature(image_file_name) -> None:


    # get absolute image path
    image_path = os.path.join(PICTURE_FILE_SUBDIR, image_file_name)
    
    try:
        return_char_list = nd.getNumberFromImage(image_path, True)
    except:
        return_char_list = "NA"   
    
    temperature = ""

    # concatenate chars from list to string
    for char in return_char_list:
        temperature = temperature + str(char)
            
    # only take string before ° and convert to integer and return
    print("Image processed. Temperature string: " + temperature)

    if(str.split(temperature, '°')[0].__contains__("NA") or len(temperature) < 2):
        number = -1      
    else:
        number = int(str.split(temperature, '°')[0])  

    print("Image processed. Temperature: " + str(number))

    
if __name__ == "__main__":

    # use argparse to read keys and time interval to be set
    parser = argparse.ArgumentParser(description="MyKilnBuddy edge service, to capture and send temperature data from your kiln")
    parser.add_argument("-p", "--picture_name", type=str,
                        help="picture name required. Add with -p <your_picture_name>.")

    args = parser.parse_args()
        
    # check if all needed input is given
    if not args.picture_name:
        parser.error("-p <your_picture_name> required!")
    else:
        # test image
        extract_termperature(args.picture_name)
