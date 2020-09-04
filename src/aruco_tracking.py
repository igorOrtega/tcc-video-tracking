try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle

import time
import numpy as np
import cv2
import cv2.aruco as aruco
from video_capture_feed import VideoCaptureFeed


class ArucoTracking:
    def __init__(self, tracking_config):
        self.tracking_config = tracking_config

        self.camera_parameters_save_dir = '../assets/camera_calibration_data/'

    def single_marker_tracking(self, video_source, show_window):
        cam_mtx = np.load(self.camera_parameters_save_dir + 'cam_mtx.npy')
        dist = np.load(self.camera_parameters_save_dir + 'dist.npy')

        video_capture = VideoCaptureFeed(video_source)

        while True:
            _, frame = video_capture.next_frame()

            parameters = aruco.DetectorParameters_create()
            parameters.adaptiveThreshConstant = 10

            corners, ids, _ = aruco.detectMarkers(
                cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                aruco.Dictionary_get(self.tracking_config.selected_marker),
                parameters=parameters)

            frame_detection_result = None
            if np.all(ids is not None):
                rvec, tvec, _ = aruco.estimatePoseSingleMarkers(
                    corners, self.tracking_config.marker_lenght, cam_mtx, dist)

                frame_detection_result = "timestamp:{}|success:1|tx:{:.2f}|ty:{:.2f}|tz:{:.2f}|rx:{:.2f}|ry:{:.2f}|rz:{:.2f}".format(
                    time.time(), tvec.item(0), tvec.item(1), tvec.item(2), rvec.item(0), rvec.item(1), rvec.item(2))

            else:
                frame_detection_result = "timestamp:{}|success:0".format(
                    time.time())

            # export
            print(frame_detection_result)

            if show_window:
                win_name = "Tracking"
                cv2.namedWindow(win_name)

                aruco.drawAxis(frame, cam_mtx, dist,
                               rvec.item, tvec.item, 5)
                aruco.drawDetectedMarkers(frame, corners)
                cv2.putText(frame, frame_detection_result, (0, 32),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)

                cv2.imshow(win_name, frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release_camera()
        cv2.destroyAllWindows()


def save_config(tracking_config_data):
    # Overwrites any existing file.
    with open('../assets/configs/tracking_config_data.pkl', 'wb') as output:
        pickle.dump({
            'marker_lenght': tracking_config_data.marker_lenght,
            'selected_marker': tracking_config_data.selected_marker}, output, pickle.HIGHEST_PROTOCOL)


def load_config():
    with open('../assets/configs/tracking_config_data.pkl', 'rb') as file:
        return pickle.load(file)


class ArucoTrackingCofig:

    def __init__(self, marker_lenght, selected_marker):
        self.marker_lenght = marker_lenght
        self.selected_marker = selected_marker

    @classmethod
    def persisted(cls):
        tracking_config_data = load_config()
        return cls(tracking_config_data['marker_lenght'],
                   tracking_config_data['selected_marker'])
