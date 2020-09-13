try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle

from multiprocessing import Process, Queue
import time
import numpy as np
import cv2
import cv2.aruco as aruco
<<<<<<< HEAD:src/tracking.py
from socket_server import DataPublishServer
=======
from video_capture_feed import VideoCaptureFeed
from coordinates_export import CoordinatesExport
>>>>>>> 731f5e6251fadfa65c43fc49722daeb6430f21b8:src/aruco_tracking.py


class ArucoTracking:
    def __init__(self, tracking_config):
        self.tracking_config = tracking_config
        self.camera_parameters_save_dir = '../assets/camera_calibration_data/'
<<<<<<< HEAD:src/tracking.py
        self.data_queue = Queue(1)

        data_publish_server = DataPublishServer(
            self.tracking_config.server_address, self.tracking_config.server_port)

        self.data_publish_server_process = Process(
            target=data_publish_server.start, args=((self.data_queue),))
=======
        self.export_server = CoordinatesExport(None)
>>>>>>> 731f5e6251fadfa65c43fc49722daeb6430f21b8:src/aruco_tracking.py

    def single_marker_tracking(self, video_source, show_window):
        self.data_publish_server_process.start()

        cam_mtx = np.load(self.camera_parameters_save_dir + 'cam_mtx.npy')
        dist = np.load(self.camera_parameters_save_dir + 'dist.npy')

        video_capture = cv2.VideoCapture(video_source, cv2.CAP_DSHOW)

        while True:
            _, frame = video_capture.read()

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

<<<<<<< HEAD:src/tracking.py
            self.publish_coordinates(
                frame_detection_result)
=======
            self.export_server.export_data(frame_detection_result)
>>>>>>> 731f5e6251fadfa65c43fc49722daeb6430f21b8:src/aruco_tracking.py

            if show_window:
                win_name = "Tracking"
                cv2.namedWindow(win_name)

                if np.all(ids is not None):
                    aruco.drawAxis(frame, cam_mtx, dist,
                                   rvec.item, tvec.item, 5)
                    aruco.drawDetectedMarkers(frame, corners)

                cv2.putText(frame, frame_detection_result, (0, 32),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)

                cv2.imshow(win_name, frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()
        self.data_publish_server_process.terminate()

    def publish_coordinates(self, data):
        if self.data_queue.full():
            self.data_queue.get()

        self.data_queue.put(data)


def save_config(tracking_config_data):
    # Overwrites any existing file.
    with open('../assets/configs/tracking_config_data.pkl', 'wb') as output:
        pickle.dump({
            'marker_lenght': tracking_config_data.marker_lenght,
            'selected_marker': tracking_config_data.selected_marker,
            'server_address': tracking_config_data.server_address,
            'server_port': tracking_config_data.server_port}, output, pickle.HIGHEST_PROTOCOL)


def load_config():
    with open('../assets/configs/tracking_config_data.pkl', 'rb') as file:
        return pickle.load(file)


class ArucoTrackingCofig:

    def __init__(self, marker_lenght, selected_marker, server_address, server_port):
        self.marker_lenght = marker_lenght
        self.selected_marker = selected_marker
        self.server_address = server_address
        self.server_port = server_port

    @classmethod
    def persisted(cls):
        tracking_config_data = load_config()
        return cls(tracking_config_data['marker_lenght'],
                   tracking_config_data['selected_marker'],
                   tracking_config_data['server_address'],
                   tracking_config_data['server_port'])
