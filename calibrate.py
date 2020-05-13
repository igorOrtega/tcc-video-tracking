import cv2
import numpy as np
import glob

SAVE_DIR = "camera_calibration_data/"
CALIBRATION_FRAMES_DIR = "calibration_images/"

def loadImages():
    image_paths = glob.glob(CALIBRATION_FRAMES_DIR + '*.jpg')
    
    frames = []
    if(len(image_paths) < 30):
        print("Must have at least 30 images for a good calibration, actual count: " + str(len(image_paths)))
        print("Please run calibration_image_capture.py and capture more images")
        return frames
    else:
        for image_path in image_paths:
            frames.append(cv2.imread(image_path))

        return frames



def runCalibration(frames):
    chess_square_size = 2.55
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    objp = np.zeros((9*6, 3), np.float32)
    objp[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2)*chess_square_size

    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        found, corners = cv2.findChessboardCorners(gray, (9, 6), None)
        if found:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)

    
    print(">==> Starting calibration")
    ret_val, cam_mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

    if(not ret_val):
        print("Calibration Error!")
    else:
        print("Camera Matrix")
        print(cam_mtx)
        np.save(SAVE_DIR+'cam_mtx.npy', cam_mtx)

        print("Distortion Coeff")
        print(dist)
        np.save(SAVE_DIR+'dist.npy', dist)

        print("r vecs")
        print(rvecs[2])

        print("t Vecs")
        print(tvecs[2])

    print(">==> Calibration ended")

if __name__ == "__main__":
    calibration_frames = loadImages()

    if(len(calibration_frames) > 0):
        runCalibration(calibration_frames)
    