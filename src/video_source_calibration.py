try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle

import os
import glob
import cv2
import numpy as np
import cv2.aruco as aruco


class VideoSourceCalibration:

    def __init__(self, video_source_dir, video_source, calibration_config):
        self.__criteria = (cv2.TERM_CRITERIA_EPS +
                           cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        self.__video_source_dir = video_source_dir
        self.__video_source = video_source
        self.__calibration_config = calibration_config
        self.calibration_image_count = 0

        self.__update_saved_image_count()

    def acquire_calibration_images(self):
        win_name = "Video Source Calibration Image Capture"
        cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(
            win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        video_capture = cv2.VideoCapture(self.__video_source, cv2.CAP_DSHOW)

        while True:
            _, frame = video_capture.read()

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_color = (0, 255, 0)

            cv2.putText(frame, "calibration image count: {}".format(
                self.calibration_image_count), (0, 32), font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(frame, "S - Save Image ", (0, 64),
                        font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(frame, "Q - Quit ", (0, 96), font,
                        font_scale, font_color, 2, cv2.LINE_AA)

            cv2.imshow(win_name, frame)

            key = cv2.waitKey(1)

            if key == ord('s'):
                self.__try_save_image(frame)

            elif key == ord('q'):
                video_capture.release()
                cv2.destroyAllWindows()
                break

    def run_calibration(self):
        objp = np.zeros((9*6, 3), np.float32)
        objp[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2)*float(
            self.__calibration_config.chessboard_square_size)

        objpoints = []
        imgpoints = []

        for image_path in glob.glob(self.__get_image_path('*')):
            frame = cv2.imread(image_path)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            found, corners = cv2.findChessboardCorners(gray, (9, 6), None)
            if found:
                objpoints.append(objp)
                corners2 = cv2.cornerSubPix(
                    gray, corners, (11, 11), (-1, -1), self.__criteria)
                imgpoints.append(corners2)

        ret_val, cam_mtx, dist, _, _ = cv2.calibrateCamera(
            objpoints, imgpoints, gray.shape[::-1], None, None)

        if ret_val:
            np.save('{}/cam_mtx.npy'.format(self.__video_source_dir), cam_mtx)
            np.save('{}/dist.npy'.format(self.__video_source_dir), dist)

    def delete_images(self):
        paths = glob.glob(self.__get_image_path('*'))
        for image_path in paths:
            os.remove(image_path)

        if os.path.exists(self.__get_images_dir()):
            os.rmdir(self.__get_images_dir())

        self.calibration_image_count = 0

    def delete_calibration(self):
        if os.path.isfile('{}/cam_mtx.npy'.format(self.__video_source_dir)):
            os.remove('{}/cam_mtx.npy'.format(self.__video_source_dir))

        if os.path.isfile('{}/dist.npy'.format(self.__video_source_dir)):
            os.remove('{}/dist.npy'.format(self.__video_source_dir))

    def __update_saved_image_count(self):
        paths = glob.glob(self.__get_image_path('*'))
        self.calibration_image_count = len(paths)

    def __get_image_path(self, img_name):
        return '{}/{}.jpg'.format(self.__get_images_dir(), img_name)

    def __get_images_dir(self):
        return '{}/calibration_images'.format(self.__video_source_dir)

    def __try_save_image(self, frame):
        if not os.path.exists(self.__get_images_dir()):
            os.makedirs(self.__get_images_dir())

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # only saves images with chessboard
        found, _ = cv2.findChessboardCorners(gray, (9, 6), None)

        if found:
            self.calibration_image_count = self.calibration_image_count + 1
            save_path = self.__get_image_path(
                str(self.calibration_image_count))
            cv2.imwrite(save_path, gray)

class VideoSourceCalibrationConfig:

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
