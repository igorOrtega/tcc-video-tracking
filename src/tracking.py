try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle

import os
import json
from multiprocessing import Process, Queue
import time
import numpy as np
import cv2
import cv2.aruco as aruco
from socket_server import DataPublishServer


class SingleMarkerTrackingExecution:
    def __init__(self):
        self.__data_queue = Queue(1)

        self.async_run_process = None
        self.server_process = None

    def run_async(self, tracking_config, camera_parameters_save_dir):
        self.__start_server(tracking_config.server_ip,
                            tracking_config.server_port)

        self.async_run_process = Process(
            target=SingleMarkerTracking(
                camera_parameters_save_dir, self.__data_queue).track,
            args=((tracking_config.video_source),
                  (tracking_config.marker_lenght),
                  (tracking_config.show_video),))
        self.async_run_process.start()

    def stop_async(self):
        if self.async_run_process is not None:
            self.async_run_process.terminate()
            self.async_run_process = None

        self.__stop_server()

    def run_sync(self, tracking_config, camera_parameters_save_dir):
        self.__start_server(tracking_config.server_ip,
                            tracking_config.server_port)

        tracking = SingleMarkerTracking(
            camera_parameters_save_dir, self.__data_queue)
        tracking.track(tracking_config.video_source,
                       tracking_config.marker_lenght,
                       tracking_config.show_video)

        self.__stop_server()

    def __start_server(self, server_ip, server_port):
        self.server_process = Process(target=DataPublishServer(server_ip, int(server_port)).start,
                                      args=((self.__data_queue),))
        self.server_process.start()

    def __stop_server(self):
        if self.server_process is not None:
            self.server_process.terminate()
            self.server_process = None


class SingleMarkerTracking:
    def __init__(self, camera_parameters_save_dir, data_queue):
        self.__camera_parameters_save_dir = camera_parameters_save_dir
        self.__data_queue = data_queue

    def track(self, video_source, marker_lenght, show_video):
        cam_mtx = np.load(
            "{}/cam_mtx.npy".format(self.__camera_parameters_save_dir))
        dist = np.load(
            "{}/dist.npy".format(self.__camera_parameters_save_dir))

        video_capture = cv2.VideoCapture(video_source, cv2.CAP_DSHOW)

        while True:
            _, frame = video_capture.read()

            parameters = aruco.DetectorParameters_create()
            parameters.adaptiveThreshConstant = 10

            corners, ids, _ = aruco.detectMarkers(
                cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                aruco.Dictionary_get(aruco.DICT_6X6_250),
                parameters=parameters)

            frame_detection_result = {}
            if np.all(ids is not None):
                rvec, tvec, _ = aruco.estimatePoseSingleMarkers(
                    corners, float(marker_lenght), cam_mtx, dist)

                frame_detection_result['timestamp'] = time.time()
                frame_detection_result['success'] = 1
                frame_detection_result['tx'] = tvec.item(0)
                frame_detection_result['ty'] = tvec.item(1)
                frame_detection_result['tz'] = tvec.item(2)
                frame_detection_result['rx'] = rvec.item(0)
                frame_detection_result['ry'] = rvec.item(1)
                frame_detection_result['rz'] = rvec.item(2)

            else:
                frame_detection_result['timestamp'] = time.time()
                frame_detection_result['success'] = 0

            self.__publish_coordinates(json.dumps(frame_detection_result))

            if show_video:
                win_name = "Tracking"
                cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
                cv2.setWindowProperty(
                    win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

                if np.all(ids is not None):
                    aruco.drawAxis(frame, cam_mtx, dist,
                                   rvec[0], tvec[0], 5)
                    aruco.drawDetectedMarkers(frame, corners)

                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                font_color = (0, 255, 0)

                cv2.putText(frame, 'timestamp: {}'.format(frame_detection_result['timestamp']), (0, 20),
                            font, font_scale, font_color, 2, cv2.LINE_AA)
                cv2.putText(frame, 'success: {}'.format(frame_detection_result['success']), (0, 40),
                            font, font_scale, font_color, 2, cv2.LINE_AA)

                if frame_detection_result['success'] == 1:
                    cv2.putText(frame, 'tx: {:.2f}'.format(frame_detection_result['tx']), (0, 60),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'ty: {:.2f}'.format(frame_detection_result['ty']), (0, 80),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'tz: {:.2f}'.format(frame_detection_result['tz']), (0, 100),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rx: {:.2f}'.format(frame_detection_result['rx']), (0, 120),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'ry: {:.2f}'.format(frame_detection_result['ry']), (0, 140),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rz: {:.2f}'.format(frame_detection_result['rz']), (0, 160),
                                font, font_scale, font_color, 2, cv2.LINE_AA)

                cv2.putText(frame, "Q - Quit ", (0, 465), font,
                            font_scale, font_color, 2, cv2.LINE_AA)

                cv2.imshow(win_name, frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

    def __publish_coordinates(self, data):
        if self.__data_queue.full():
            self.__data_queue.get()

        self.__data_queue.put(data)


class SingleMarkerTrackingCofig:

    def __init__(self, video_source, show_video, marker_lenght, server_ip, server_port):
        self.video_source = video_source
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

                return cls(tracking_config_data['video_source'],
                           tracking_config_data['show_video'],
                           tracking_config_data['marker_lenght'],
                           tracking_config_data['server_ip'],
                           tracking_config_data['server_port'])
        except FileNotFoundError:
            return cls(0, True, "", "", "")

    def persist(self):
        # Overwrites any existing file.
        with open('../assets/configs/tracking_config_data.pkl', 'wb+') as output:
            pickle.dump({
                'video_source': self.video_source,
                'show_video': self.show_video,
                'marker_lenght': self.marker_lenght,
                'server_ip': self.server_ip,
                'server_port': self.server_port}, output, pickle.HIGHEST_PROTOCOL)
