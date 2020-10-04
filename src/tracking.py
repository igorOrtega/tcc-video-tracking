try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle

import os
from multiprocessing import Process, Queue
import time
import numpy as np
import cv2
import cv2.aruco as aruco
from socket_server import DataPublishServer


class SingleMarkerTracking:
    def __init__(self, tracking_config):
        self.__tracking_config = tracking_config
        self.__camera_parameters_save_dir = '../assets/camera_calibration_data/'
        self.__data_queue = Queue(1)

        data_publish_server = DataPublishServer(
            self.__tracking_config.server_ip, int(self.__tracking_config.server_port))

        self.__data_publish_server_process = Process(
            target=data_publish_server.start, args=((self.__data_queue),))

    def single_marker_tracking(self, video_source):
        self.__data_publish_server_process.start()

        cam_mtx = np.load(self.__camera_parameters_save_dir + 'cam_mtx.npy')
        dist = np.load(self.__camera_parameters_save_dir + 'dist.npy')

        video_capture = cv2.VideoCapture(video_source, cv2.CAP_DSHOW)

        while True:
            _, frame = video_capture.read()

            parameters = aruco.DetectorParameters_create()
            parameters.adaptiveThreshConstant = 10

            corners, ids, _ = aruco.detectMarkers(
                cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                aruco.Dictionary_get(aruco.DICT_6X6_250),
                parameters=parameters)

            frame_detection_result = None
            if np.all(ids is not None):
                rvec, tvec, _ = aruco.estimatePoseSingleMarkers(
                    corners, float(self.__tracking_config.marker_lenght), cam_mtx, dist)

                frame_detection_result = "timestamp:{}|success:1|tx:{:.2f}|ty:{:.2f}|tz:{:.2f}|rx:{:.2f}|ry:{:.2f}|rz:{:.2f}".format(
                    time.time(), tvec.item(0), tvec.item(1), tvec.item(2), rvec.item(0), rvec.item(1), rvec.item(2))

            else:
                frame_detection_result = "timestamp:{}|success:0".format(
                    time.time())

            self.__publish_coordinates(
                frame_detection_result)

            if self.__tracking_config.show_video:
                win_name = "Tracking"
                cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
                cv2.setWindowProperty(
                    win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

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
        self.__data_publish_server_process.terminate()

    def __publish_coordinates(self, data):
        if self.__data_queue.full():
            self.__data_queue.get()

        self.__data_queue.put(data)


class SingleMarkerTrackingCofig:

    def __init__(self, show_video, marker_lenght, server_ip, server_port):
        self.show_video = show_video
        self.marker_lenght = marker_lenght
        self.server_ip = server_ip
        self.server_port = server_port

    @classmethod
    def persisted(cls):
        if not os.path.exists('../assets/configs/'):
            os.makedirs('../assets/configs/')

        try:
            with open('../assets/configs/tracking_config_data.pkl', 'rb') as file:
                tracking_config_data = pickle.load(file)

                return cls(tracking_config_data['show_video'],
                           tracking_config_data['marker_lenght'],
                           tracking_config_data['server_ip'],
                           tracking_config_data['server_port'])
        except FileNotFoundError:
            return cls(True, "", "", "")

    def persist(self):
        # Overwrites any existing file.
        with open('../assets/configs/tracking_config_data.pkl', 'wb+') as output:
            pickle.dump({
                'show_video': self.show_video,
                'marker_lenght': self.marker_lenght,
                'server_ip': self.server_ip,
                'server_port': self.server_port}, output, pickle.HIGHEST_PROTOCOL)
