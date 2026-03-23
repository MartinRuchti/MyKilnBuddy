# LIBRARY TO AXTRACT NUMBERS FROM SEGMENT DISPLAY
# AUTHOR: MARTIN RUCHTI
# CONTACT: info@martin-ruchti.com

#
# NOTE: This library is inteded to be used for detecting numbers on a Nabertherm 
#       pottery kiln. Other segmented displays might also work, but wheren't tested
#

# IMPORTS
from imutils.perspective import four_point_transform
from imutils import contours
import imutils
import cv2

# LOOKUP FOR SEGMENT NUMBERS
# special segments for '°', since display doesn't allways show full circle in pictures
DIGITS_LOOKUP = {
	(1, 1, 1, 0, 1, 1, 1): 0,
	(0, 0, 1, 0, 0, 1, 0): 1,
	(1, 0, 1, 1, 1, 0, 1): 2,
	(1, 0, 1, 1, 0, 1, 1): 3,
	(0, 1, 1, 1, 0, 1, 0): 4,
	(1, 1, 0, 1, 0, 1, 1): 5,
	(1, 1, 0, 1, 1, 1, 1): 6,
	(1, 0, 1, 0, 0, 1, 0): 7,
	(1, 1, 1, 1, 1, 1, 1): 8,
	(1, 1, 1, 1, 0, 1, 1): 9,
    (1, 1, 1, 1, 0, 0, 0): '°',
    (1, 1, 1, 0, 0, 0, 0): '°',
    (1, 1, 0, 0, 1, 0, 1): 'C'
}

# MAIN FUNCTIONALITY TO TRANSFORM PICTURE TO NUMBER
# This function is called from other scripts, when detection is needed
def getNumberFromImage(filePathName, debug = False):

    digitsOrig = getNumberFromImageInternal(filePathName, debug)
    digits = digitsOrig

    # 
    # NOTE: Sometimes, the black and white schemes of the picture have either segments, that are fused together, 
    #       or segments, that are separated, where they shouldn't. For this, on fail there are some steps of erode and 
    #       dillute performed, in the hope, to detect the right number. This enhaces stability of detection.
    # 

    # initialize variables to control, whether dilution had success
    diluteFailed = False
    diluteFailed2 = False

    # check if errors occured
    # if not, return result, otherwise dilate picture
    if(not digits_contain_errors(digitsOrig)):
        if debug:
            print("First number detection was successful.")
        return digitsOrig
    else:
        if debug:
            print("Failed! Trying number detection with dillute 1 ...")
        digits = getNumberFromImageInternal(filePathName, debug, dilate=True, dilate2=False, erode=False)

    # check if errors occured again and dilate harder if so
    if(digits_contain_errors(digits)):
        diluteFailed = True
        # Fix for false dil 2!!
        if debug:
            print("Failed! Trying number detection with dillute 2 ...")
        digits = getNumberFromImageInternal(filePathName, debug, dilate=False, dilate2=True, erode=False)

    # check if errors occured again and erode if so
    if(digits_contain_errors(digits)):
        diluteFailed2 = True
        if debug:
            print("Failed! Trying number detection with erode 1 ...")
        digits = getNumberFromImageInternal(filePathName, debug, dilate=False, dilate2=False, erode=True)

    # return new result without errors or original
    if(digits_contain_errors(digits)):
        if debug:
            print("Failed! Returning first try.")
        return digitsOrig
    else:
        if debug:
            print("Success!")
            if diluteFailed:
                if diluteFailed2:
                    print("===============================> SAVED BY ERODE!")
                else:
                    print("===============================> SAVED BY DILUTE2!")
            else:
                print("===============================> SAVED BY DILUTE!")

        # return successful result
        return digits

# INTERNAL FUNCTION TO WRAP THE MAJORITY OF THE FUNCTIONALITY
# This Function should only be called from this script
def getNumberFromImageInternal(filePathName, debug, dilate=False, dilate2=False, erode=False):
    # load image
    image = cv2.imread(filePathName)

    # set helper bool to know if char ° is already detected - erase garbage after C
    celsius_char_detected = False

    # pre-process the image by resizing it, converting it to
    # graycale, blurring it, and computing an edge map
    image = imutils.resize(image, height=500)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 9), 0)
    edged = cv2.Canny(blurred, 50, 150, 255)

    # find contours in the edge map, then sort them by their
    # size in descending order
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    displayCnt = None
    # loop over the contours
    for c in cnts:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        # if the contour has four vertices, then we have found
        # the thermostat display
        if len(approx) == 4:
            displayCnt = approx
            break
	
    # extract the thermostat display, apply a perspective transform
    # to it
    transformed = four_point_transform(gray, displayCnt.reshape(4, 2))
    output = four_point_transform(image, displayCnt.reshape(4, 2))

    # replaced with adaptive thresolding to account for poor lighting
    thresh = cv2.adaptiveThreshold(transformed,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
            cv2.THRESH_BINARY_INV,61,5)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # use dilate or erode only in second and third try
    if dilate:
        # dilate black areas to connect the parts of 0s and Cs
        thresh = cv2.dilate(thresh, (7, 7), iterations=4) # might also try with 2, for some use cases
    elif dilate2:
        thresh = cv2.dilate(thresh, (7, 7), iterations=7) # might also try with 4, for some use cases
    elif erode:
        thresh = cv2.erode(thresh, (7, 7), iterations=3)

    #cv2.imshow("thresh", thresh)
    if debug:
        newfileName = str.split(filePathName, '.')[0] + "__THD.jpg"
        cv2.imwrite(newfileName, thresh)

    # find contours in the thresholded image, then initialize the
    # digit contours lists
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    digitCnts = []

    # loop over the digit area candidates
    for c in cnts:
        # compute the bounding box of the contour
        (x, y, w, h) = cv2.boundingRect(c)
        # if the contour is sufficiently large, it must be a digit
        # change to besser represent digits
        if w >= 10 and (h >= 30 and h <= 80):
            digitCnts.append(c)

    # sort the contours from left-to-right, then initialize the
    # actual digits themselves
    digitCnts = contours.sort_contours(digitCnts,
        method="left-to-right")[0]
    digits = []

    # loop over each of the digits
    for c in digitCnts:

        # load original values
        (x, y, w, h) = cv2.boundingRect(c)

        # SPECIAL TREATMENT FOR ° and 1
        # if h too small, it is the ° and h has to be enlarged to not have a 0
        if(h < 50):
            h = int(1.8*h)
        
        # if w is too small, it is the 1 and w has to be extended + ref point has to be moved
        if(w < 20):
            if debug: print ("found 1. w was: " + str(w))
            factor = 3
            x = x - int((factor-1)*w)
            w = int(factor*w)
        # END SPECIAL TREATMENT

        # extract the digit ROI
        roi = thresh[y:y + h, x:x + w]

        # compute the width and height of each of the 7 segments
        # we are going to examine
        (roiH, roiW) = roi.shape
        (dW, dH) = (int(roiW * 0.25), int(roiH * 0.15))
        dHC = int(roiH * 0.05)
        # define the set of 7 segments
        segments = [
            ((0, 0), (w, dH)),	# top
            ((0, 0), (dW, h // 2)),	# top-left
            ((w - dW, 0), (w, h // 2)),	# top-right
            ((0, (h // 2) - dHC) , (w, (h // 2) + dHC)), # center
            ((0, h // 2), (dW, h)),	# bottom-left
            ((w - dW, h // 2), (w, h)),	# bottom-right
            ((0, h - dH), (w, h))	# bottom
        ]
        on = [0] * len(segments)

        # loop over the segments
        for (i, ((xA, yA), (xB, yB))) in enumerate(segments):
            # extract the segment ROI, count the total number of
            # thresholded pixels in the segment, and then compute
            # the area of the segment
            segROI = roi[yA:yB, xA:xB]
            total = cv2.countNonZero(segROI)
            area = (xB - xA) * (yB - yA)
            # if the total number of non-zero pixels is greater than
            # 50% of the area, mark the segment as "on"
            if total / float(area) > 0.5:
                on[i]= 1

        # lookup the digit and draw it on the image
        #check if tuple is contained
        if DIGITS_LOOKUP.__contains__(tuple(on)):
            digit = DIGITS_LOOKUP[tuple(on)]
            if(digit == "°"): celsius_char_detected = True
        else:
            # ToDo: better replacement later
            if celsius_char_detected:
                digit = "C"
                break
            else:
                digit = "NA"
        
        # add display of detected areas in picture for debug purposes
        digits.append(digit)
        cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 1)
        cv2.putText(output, str(digit), (x - 2, y - 2),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

    # show debug output
    if debug:
        newfileName = str.split(filePathName, '.')[0] + "__CHECK.jpg"
        cv2.imwrite(newfileName, output)
    
    # if desirable, errernous pictures can be shown
    if(debug and digits.__contains__("NA")):
        cv2.imshow("thres", thresh)
        cv2.imshow("Output", output)
        cv2.waitKey(0)

    return digits

def digits_contain_errors(digits) -> bool:

    result = False

    # check for 'NAs'
    result = result or digits.__contains__("NA")

    # skip the digit counting, if already errors detected
    if result:
        return result
    
    # count digits detected prior to °: should always be 4
    counter = 0
    for d in digits:
        if(d == '°'):
            break
        else:
            counter += 1
    
    result = result or (counter < 4)

    return result