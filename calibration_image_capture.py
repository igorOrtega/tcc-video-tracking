import cv2
import cv2.aruco as aruco
import numpy as np
import os
import glob
import copy

CALIBRATION_IMAGES_DIR = "calibration_images/"
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

def capture_loop():
    win_name = "capturing..."
    calibration_image_count = getSavedImageCount()

    video = cv2.VideoCapture(0)

    while True:
        retval, image = video.read()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Find the chess board corners
        found, corners = cv2.findChessboardCorners(gray, (9, 6), None)
        
        # If found, add object points, image points (after refining them)
        if found:
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            draw_image = copy.deepcopy(image)
            cv2.drawChessboardCorners(draw_image, (9, 6), corners2, found)
            cv2.imshow(win_name, draw_image)
        else:
            cv2.imshow(win_name, image)

        key = cv2.waitKey(1)

        if(key == ord('s')):
            if(found):
                calibration_image_count = calibration_image_count + 1
                save_path = CALIBRATION_IMAGES_DIR + 'cal_image' + str(calibration_image_count) + '.jpg'
                cv2.imwrite(save_path, gray)
                print("image saved to calibration, count: " + str(calibration_image_count))
            else:
                print("corners not found")

        elif(key == ord('q')):
            video.release()
            cv2.destroyAllWindows()
            break

def deleteImages():
    paths = glob.glob(CALIBRATION_IMAGES_DIR + '*.jpg')

    for image_path in paths:
        os.remove(image_path)

def getSavedImageCount():
    paths = glob.glob(CALIBRATION_IMAGES_DIR + '*.jpg')
    return len(paths)

if __name__ == "__main__":

    print("Current calibration image count: " + str(getSavedImageCount()))

    choose = ""
    while choose != 'q':
        choose = input("press 'c' to capture more images, d' to delete current images or 'q' to quit \n\n")[0]

        if choose == 'c':
            capture_loop()
        elif choose == 'd':
            deleteImages()

        print("Current calibration image count: " + str(getSavedImageCount()))
        




    


