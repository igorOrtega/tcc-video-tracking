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

    def calibrate(self):
        win_name = "Video Source Calibration Image Capture"
        cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(
            win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        red = (0, 0, 255)
        green = (0, 255, 0)

        #Descomentar quando nao for utilizar o DroidCam
        #video_capture = cv2.VideoCapture(self.__video_source, cv2.CAP_DSHOW)
        video_capture = cv2.VideoCapture(self.__video_source)

        video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        calibration_frames = []
        ready_to_calibrate = False
        start_calibration = False
        status_color = red
        while True:
            option = cv2.waitKey(1)

            _, frame = video_capture.read()

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            cv2.putText(frame, "calibration image count: {}. Minimum 50".format(
                len(calibration_frames)), (0, 20), font, font_scale, status_color, 2, cv2.LINE_AA)

            cv2.putText(frame, "ENTER - Capture frame for calibration", (0, 40),
                        font, font_scale, green, 2, cv2.LINE_AA)

            if option == 13:
                found, _ = cv2.findChessboardCorners(gray, (9, 6), None)

                if found:
                    calibration_frames.append(gray)

            if ready_to_calibrate:
                cv2.putText(frame, "C - Start Calibration", (0, 60),
                            font, font_scale, green, 2, cv2.LINE_AA)

                if option == ord('c'):
                    start_calibration = True
                    cv2.putText(frame, "Running, this may take a while ...", (0, 80),
                                font, font_scale, green, 2, cv2.LINE_AA)

            cv2.putText(frame, "Q - Quit ", (0, 105), font,
                        font_scale, green, 2, cv2.LINE_AA)

            cv2.imshow(win_name, frame)

            if start_calibration:
                cv2.waitKey(2000)
                self.__run(calibration_frames)
                cv2.imshow(win_name, frame)
                cv2.waitKey(1000)
                video_capture.release()
                cv2.destroyAllWindows()
                break

            if option == ord('q'):
                video_capture.release()
                cv2.destroyAllWindows()
                break

            if len(calibration_frames) >= 50:
                ready_to_calibrate = True
                status_color = green

    def delete_calibration(self):
        if os.path.isfile('{}/cam_mtx.npy'.format(self.__video_source_dir)):
            os.remove('{}/cam_mtx.npy'.format(self.__video_source_dir))

        if os.path.isfile('{}/dist.npy'.format(self.__video_source_dir)):
            os.remove('{}/dist.npy'.format(self.__video_source_dir))

    def __run(self, calibration_frames):
        objp = np.zeros((9*6, 3), np.float32)
        objp[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2)*float(
            self.__calibration_config.chessboard_square_size)

        objpoints = []
        imgpoints = []

        img_size = calibration_frames[0].shape[::-1]
        for frame in calibration_frames:
            found, corners = cv2.findChessboardCorners(frame, (9, 6), None)
            if found:
                objpoints.append(objp)
                corners2 = cv2.cornerSubPix(
                    frame, corners, (11, 11), (-1, -1), self.__criteria)
                imgpoints.append(corners2)

        ret_val, cam_mtx, dist, _, _ = cv2.calibrateCamera(
            objpoints, imgpoints, img_size, None, None)

        if ret_val:
            if not os.path.exists(self.__video_source_dir):
                os.makedirs(self.__video_source_dir)

            np.save('{}/cam_mtx.npy'.format(self.__video_source_dir), cam_mtx)
            np.save('{}/dist.npy'.format(self.__video_source_dir), dist)


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
