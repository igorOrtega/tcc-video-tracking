import glob
import cv2
import numpy as np


class CameraCalibration:

    def __init__(self, chessboard_points_per_row, chessboard_points_per_column, camera_parameters_save_dir, calibration_images_dir, chessboard_square_size):
        self.chessboard_points_per_row = chessboard_points_per_row
        self.chessboard_points_per_column = chessboard_points_per_column
        self.camera_parameters_save_dir = camera_parameters_save_dir
        self.calibration_images_dir = calibration_images_dir
        self.chessboard_square_size = chessboard_square_size

        self.criteria = (cv2.TERM_CRITERIA_EPS +
                         cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    def load_images(self):
        image_paths = glob.glob(self.calibration_images_dir + '*.jpg')

        frames = []
        if(len(image_paths) < 30):
            print("Must have at least 30 images for a good calibration, actual count: " +
                  str(len(image_paths)))
            print("Please run calibration_image_capture.py and capture more images")
            return frames

        for image_path in image_paths:
            frames.append(cv2.imread(image_path))

        return frames

    def main_loop(self):
        frames = self.load_images()

        if(len(frames) == 0):
            return

        objp = np.zeros((self.chessboard_points_per_row *
                         self.chessboard_points_per_column, 3), np.float32)
        objp[:, :2] = np.mgrid[0:self.chessboard_points_per_row,
                               0:self.chessboard_points_per_column].T.reshape(-1, 2)*self.chessboard_square_size

        # Arrays to store object points and image points from all the images.
        objpoints = []  # 3d point in real world space
        imgpoints = []  # 2d points in image plane.

        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            found, corners = cv2.findChessboardCorners(
                gray, (self.chessboard_points_per_row, self.chessboard_points_per_column), None)
            if found:
                objpoints.append(objp)
                corners2 = cv2.cornerSubPix(
                    gray, corners, (11, 11), (-1, -1), self.criteria)
                imgpoints.append(corners2)

        print(">==> Starting calibration")
        ret_val, cam_mtx, dist, _, _ = cv2.calibrateCamera(
            objpoints, imgpoints, gray.shape[::-1], None, None)

        if(not ret_val):
            print("Calibration Error!")
        else:
            print("Camera Matrix")
            print(cam_mtx)
            np.save(self.camera_parameters_save_dir +
                    'cam_mtx.npy', cam_mtx)

            print("Distortion Coeff")
            print(dist)
            np.save(self.camera_parameters_save_dir+'dist.npy', dist)

        print(">==> Calibration ended")


if __name__ == "__main__":

    # test

    camera_calibration = CameraCalibration(
        9, 6, "camera_calibration_data/", "calibration_images/", 2.5)

    camera_calibration.main_loop()
