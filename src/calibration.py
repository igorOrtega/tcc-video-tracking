try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle

import os
import glob
import cv2
import numpy as np
from video_capture_feed import VideoCaptureFeed


class CameraCalibration:

    def __init__(self, calibration_config):
        self.calibration_config = calibration_config
        self.criteria = (cv2.TERM_CRITERIA_EPS +
                         cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        self.calibration_images_dir = './calibration_images/'
        self.camera_parameters_save_dir = './camera_calibration_data/'

        self.calibration_image_count = 0
        self.update_saved_image_count()

    def acquire_calibration_images(self, video_source):
        win_name = "Calibration Image Capture"
        cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(
            win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        video_capture = VideoCaptureFeed(video_source)

        while True:
            _, frame = video_capture.next_frame()

            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, "calibration image count: {}".format(
                self.calibration_image_count), (0, 32), font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, "S - Save Image ", (0, 64),
                        font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, "D - Delete All Images ", (0, 96),
                        font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, "Q - Quit ", (0, 128), font,
                        0.6, (0, 255, 0), 2, cv2.LINE_AA)

            cv2.imshow(win_name, frame)

            key = cv2.waitKey(1)

            if key == ord('s'):
                self.try_save_image(frame)

            elif key == ord('d'):
                self.delete_images()

            elif key == ord('q'):
                video_capture.release_camera()
                cv2.destroyAllWindows()
                break

    def try_save_image(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # only saves images with chessboard
        found, _ = cv2.findChessboardCorners(
            gray, (self.calibration_config.chessboard_points_per_row,
                   self.calibration_config.chessboard_points_per_column), None)

        if found:
            self.calibration_image_count = self.calibration_image_count + 1
            save_path = self.calibration_images_dir + 'cal_image' + \
                str(self.calibration_image_count) + '.jpg'
            cv2.imwrite(save_path, gray)

    def delete_images(self):
        paths = glob.glob(self.calibration_images_dir + '*.jpg')
        for image_path in paths:
            os.remove(image_path)
        self.calibration_image_count = 0

    def update_saved_image_count(self):
        paths = glob.glob(self.calibration_images_dir + '*.jpg')
        self.calibration_image_count = len(paths)

    def run_calibration(self):
        image_paths = glob.glob(self.calibration_images_dir + '*.jpg')

        if(len(image_paths) < 30):
            print("Must have at least 30 images for a good calibration, actual count: " +
                  str(len(image_paths)))
            print("Please run calibration_image_capture.py and capture more images")

            return

        objp = np.zeros((self.calibration_config.chessboard_points_per_row *
                         self.calibration_config.chessboard_points_per_column, 3), np.float32)

        objp[:, :2] = np.mgrid[0:self.calibration_config.chessboard_points_per_row,
                               0: self.calibration_config.chessboard_points_per_column].T.reshape(-1, 2)*self.calibration_config.chessboard_square_size

        objpoints = []
        imgpoints = []

        for image_path in image_paths:
            frame = cv2.imread(image_path)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            found, corners = cv2.findChessboardCorners(
                gray, (self.calibration_config.chessboard_points_per_row,
                       self.calibration_config.chessboard_points_per_column), None)
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


def save_config(calibration_config_data):
    # Overwrites any existing file.
    with open('calibration_config_data.pkl', 'wb') as output:
        pickle.dump({
            'chessboard_points_per_row': calibration_config_data.chessboard_points_per_row,
            'chessboard_points_per_column': calibration_config_data.chessboard_points_per_column,
            'chessboard_square_size': calibration_config_data.chessboard_square_size},
            output, pickle.HIGHEST_PROTOCOL)


def load_config():
    with open('calibration_config_data.pkl', 'rb') as file:
        return pickle.load(file)


class CalibrationCofig:

    def __init__(self, chessboard_points_per_row, chessboard_points_per_column, chessboard_square_size):
        self.chessboard_points_per_row = chessboard_points_per_row
        self.chessboard_points_per_column = chessboard_points_per_column
        self.chessboard_square_size = chessboard_square_size

    @classmethod
    def persisted(cls):
        calibration_config_data = load_config()
        return cls(calibration_config_data['chessboard_points_per_row'],
                   calibration_config_data['chessboard_points_per_column'],
                   calibration_config_data['chessboard_square_size'])
