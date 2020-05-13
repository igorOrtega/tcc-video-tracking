import cv2
import cv2.aruco as aruco
import numpy as np
import copy


criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

def runCalibration(images):

    CHESS_SQUARE_SIZE = 2.55

    objp = np.zeros((9*6, 3), np.float32)
    objp[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1,2)*CHESS_SQUARE_SIZE

    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    for img in images:

        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, img_corners = cv2.findChessboardCorners(img_gray, (9, 6), None)
        # If found, add object points, image points (after refining them)
        if ret:
            objpoints.append(objp)
            img_corners2 = cv2.cornerSubPix(img_gray, img_corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(img_corners2)
    
    print(">==> Starting calibration")
    ret, cam_mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

    #print(ret)
    print("Camera Matrix")
    print(cam_mtx)
    # np.save(savedir+'cam_mtx.npy', cam_mtx)

    print("Distortion Coeff")
    print(dist)
    # np.save(savedir+'dist.npy', dist)

    print("r vecs")
    print(rvecs[2])

    print("t Vecs")
    print(tvecs[2])



    print(">==> Calibration ended")

if __name__ == "__main__":

    win_name = "capturing..."
    video = cv2.VideoCapture(0)
    images = []

    while True:
        retval, frame = video.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Find the chess board corners
        found, corners = cv2.findChessboardCorners(gray, (9, 6), None)
        
        # If found, add object points, image points (after refining them)
        if found:
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            draw_frame = copy.deepcopy(frame)
            cv2.drawChessboardCorners(draw_frame, (9, 6), corners2, found)
            cv2.imshow(win_name, draw_frame)
        else:
            cv2.imshow(win_name, frame)

        key = cv2.waitKey(1)

        if(key == ord('s')):
            if(found):
                images.append(frame)
                print("image saved to calibration, count: " + str(len(images)))
            else:
                print("corners not found, count: " + str(len(images)))

        elif(key == ord('c')):
            if(len(images) >= 15):
                video.release()
                cv2.destroyAllWindows()
                runCalibration(images)
                break
            else:
                print("need to save at least 15 images, count: " + str(len(images))) 
        elif(key == ord('q')):
            video.release()
            cv2.destroyAllWindows()
            break



"""
while True:

    retval, frame = video.read()

    # operations on the frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # set dictionary size depending on the aruco marker selected
    aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)

    # detector parameters can be set here (List of detection parameters[3])
    parameters = aruco.DetectorParameters_create()
    parameters.adaptiveThreshConstant = 10

    # lists of ids and the corners belonging to each id
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    print(corners)

    cv2.imshow("Testing...", frame)

    key = cv2.waitKey(1)

    if(key == ord('q')):
        break
"""

