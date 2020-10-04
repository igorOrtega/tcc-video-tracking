try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle

import os
import glob
import cv2
import numpy as np


class CameraCalibration:

    def __init__(self, calibration_config):
        self.calibration_config = calibration_config
        self.criteria = (cv2.TERM_CRITERIA_EPS +
                         cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        self.calibration_images_dir = '../assets/calibration_images/'
        self.camera_parameters_save_dir = '../assets/camera_calibration_data/'

        self.calibration_image_count = 0
        self.update_saved_image_count()

    def acquire_calibration_images(self, video_source):
        win_name = "Calibration Image Capture"
        cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(
            win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        video_capture = cv2.VideoCapture(video_source, cv2.CAP_DSHOW)

        while True:
            _, frame = video_capture.read()

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
                video_capture.release()
                cv2.destroyAllWindows()
                break

    def try_save_image(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # only saves images with chessboard
        found, _ = cv2.findChessboardCorners(gray, (9, 6), None)

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

        objp = np.zeros((9 * 6, 3), np.float32)
        objp[:, :2] = np.mgrid[0:9,
                               0:6].T.reshape(-1, 2)*self.calibration_config.chessboard_square_size

        objpoints = []
        imgpoints = []

        for image_path in image_paths:
            frame = cv2.imread(image_path)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            found, corners = cv2.findChessboardCorners(gray, (9, 6), None)
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


class CalibrationConfig:

    def __init__(self, chessboard_square_size):
        self.chessboard_square_size = chessboard_square_size

    @classmethod
    def persisted(cls):
        if not os.path.exists('../assets/configs/'):
            os.makedirs('../assets/configs/')

        try:
            with open('../assets/configs/calibration_config_data.pkl', 'rb') as file:
                calibration_config_data = pickle.load(file)
                return cls(calibration_config_data['chessboard_square_size'])
        except FileNotFoundError:
            return cls("")

    def persist(self):
        # Overwrites any existing file.
        with open('../assets/configs/calibration_config_data.pkl', 'wb+') as output:
            pickle.dump({
                'chessboard_square_size': self.chessboard_square_size}, output, pickle.HIGHEST_PROTOCOL)
