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
import numpy as np

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
        approx = cv2.approxPolyDP(c, 0.01 * peri, True)
        
        if debug:
            debug_image = image
            cv2.drawContours(debug_image, [approx.astype(int)], -1, (0,255,0), 2)
            cv2.imshow("blurred", debug_image)
            cv2.waitKey(0)
            
        # if the contour has four vertices, then we have found
        # the thermostat display 
        if len(approx) == 8:
            displayCnt = approx
            break

    # find stable rotation bounding box
    hull = cv2.convexHull(approx)
    rect = cv2.minAreaRect(displayCnt)
    
    # make rectangle smaller, to only have the display in it
    # get center, width to size
    (center), (w, h), angle = rect

    scaling_w = 0.86  # factor for scaling
    scaling_h = 0.67  # factor for scaling
    shift_x = 7.0

    w_new = max(1, scaling_w*w)
    h_new = max(1, scaling_h*h)
    center = (center[0] + shift_x, center[1])

    rect_smaller = (center, (w_new, h_new), angle)

    # get corner nodes
    box = cv2.boxPoints(rect_smaller)
    box = np.array(box, dtype="float32")
    
    # sort points
    rect_sorted = order_points(box)

    # calculate target sizes
    widthA = np.linalg.norm(rect_sorted[2] - rect_sorted[3])
    widthB = np.linalg.norm(rect_sorted[1] - rect_sorted[0])
    maxWidth = int(max(widthA, widthB))

    heightA = np.linalg.norm(rect_sorted[1] - rect_sorted[2])
    heightB = np.linalg.norm(rect_sorted[0] - rect_sorted[3])
    maxHeight = int(max(heightA, heightB))

    # define target rectangle
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    # transform perspective
    M = cv2.getPerspectiveTransform(rect_sorted, dst)
    transformed = cv2.warpPerspective(gray, M, (maxWidth, maxHeight))
    output = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    # replaced with adaptive thresolding to account for poor lighting
    thresh = cv2.adaptiveThreshold(transformed,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
            cv2.THRESH_BINARY_INV,61,5)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # use dilate or erode only in second and third try
    #kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    kernel = np.ones((4, 1), np.uint8)
    if dilate:
        # dilate black areas to connect the parts of 0s and Cs
        thresh = cv2.dilate(thresh, kernel, iterations=3) # might also try with 2, for some use cases
    elif dilate2:
        thresh = cv2.dilate(thresh, kernel, iterations=4) # might also try with 4, for some use cases
    elif erode:
        thresh = cv2.erode(thresh, kernel, iterations=2)
    else:
        thresh = cv2.dilate(thresh, kernel, iterations=2)
               
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
        # change to better represent digits
        roi = thresh[y:y + h, x:x + w]
            
        # check if roi size is reasonable
        if ((min(roi.shape) > 0) and (roi.shape[0] > 10)):
            digitCnts.append(c)

    # sort the contours from left-to-right, then initialize the
    # actual digits themselves
    digitCnts = contours.sort_contours(digitCnts,
        method="left-to-right")[0]
    digits = []

    # loop over each of the digits
    if debug:
        print("Now iterating digits ...")
        
    for c in digitCnts:

        # load original values
        (x, y, w, h) = cv2.boundingRect(c)
        
        # set min w and h to avoid crashes
        if(w < 5):
            w = 5.0
        if(h < 8):
            h = 8.0
            
        # SPECIAL TREATMENT FOR ° and 1
        
        # variable to store, if 1 is detected
        one_detected = False
        
        if debug:
            print("Checking ROIs ...")
        
        # if h too small, it is the ° and h has to be enlarged to not have a 0
        # if it is very small, it is likely noise
        if(h < 50):
            h = int(1.8*h)
        
        # if w is too small, it is the 1 and w has to be extended + ref point has to be moved
        if(w < 20):
            factor = 3.0
            # check, if x becomes negative
            x = max(x - int((factor-1)*w),0)
            w = int(factor*w)
            
            # set 1 detected for later treatment
            one_detected = True
            
        # END SPECIAL TREATMENT
        
        # extract the digit ROI
        roi = thresh[y:y + h, x:x + w]

        # compute the width and height of each of the 7 segments
        # we are going to examine
        (roiH, roiW) = roi.shape
        
        if debug:
            print("Creating segments ...")
            
        (dW, dH) = (int(roiW * 0.33), int(roiH * 0.15))
        dHC = int(roiH * 0.1)
        
        # define the set of 7 segments
        segments = [
            ((0, 0), (w, dH)),	# top
            ((0, 0), (dW, h // 2)),	# top-left
            ((w - dW, 0), (w, h // 2)),	# top-right
            ((0 + dW , (h // 2) - dHC) , (w - dW , (h // 2) + dHC)), # center
            ((0, h // 2), (dW, h)),	# bottom-left
            ((w - dW, h // 2), (w, h)),	# bottom-right
            ((0, h - dH), (w, h))	# bottom
        ]
        on = [0] * len(segments)

        if debug:
            print("Checking segments ...")
            print("Segments: " + str(segments))
            
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
            if total / float(area) > 0.6:
                on[i]= 1

        # lookup the digit and draw it on the image
        if debug:
            print("Evaluating segments for chars ...")
            
        # check if it was a 1 specially, since detection is unstable by segments
        if one_detected:
            digit = "1"
        
        # check active segments, if not 1
        else:
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
        
        if debug:
            print("Showing results ...")
            
        if debug and (min(roi.shape) > 0):
            roi_debug = cv2.cvtColor(roi.copy(), cv2.COLOR_GRAY2BGR)
            for (i, ((xA, yA), (xB, yB))) in enumerate(segments):
                cv2.rectangle(roi_debug, (xA, yA), (xB, yB), (0, 255, 0), 1)

            cv2.imshow("Segments", roi_debug)
            
            print("Segment: " + str(on))
            cv2.waitKey(0)
        
        # add display of detected areas in picture for debug purposes
        digits.append(digit)
        cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 1)
        cv2.putText(output, str(digit), (x + 2, y + 10),
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

    # check for 'NAs'
    result = digits.__contains__("NA")

    # skip the digit counting, if already errors detected
    if result:
        print("NAs detected")
        return result
    
    # count digits detected prior to °: should always be 4
    counter = 0
    for d in digits:
        if(d == '°'):
            break
        else:
            counter += 1
    
    result = result or (counter < 4)

    print("No NAs detected. Digits counted: " + str(counter) + ". Errors: " + str(result))
    return result

# function to sort points
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # top-left
    rect[2] = pts[np.argmax(s)]  # bottom-right

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left

    return rect

