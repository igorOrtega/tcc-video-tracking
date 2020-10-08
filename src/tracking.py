try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle

import os
import json
import socket
from multiprocessing import Process, Queue
import time
import numpy as np
import cv2
import cv2.aruco as aruco


class SingleMarkerTrackingScheduler:
    def __init__(self, start_tracking, stop_tracking):
        self.start_tracking = start_tracking
        self.stop_tracking = stop_tracking

    def main(self):

        while True:
            self.start_tracking.wait()
            self.start_tracking.clear()

            tracking_config = SingleMarkerTrackingCofig.persisted()
            queue = Queue(1)

            server_process = Process(target=DataPublishServer(
                server_ip=tracking_config.server_ip,
                server_port=int(tracking_config.server_port),
                queue=queue
            ).listen)
            server_process.start()

            tracking_process = Process(target=SingleMarkerTracking(
                queue=queue,
                device_number=tracking_config.device_number,
                device_parameters_dir=tracking_config.device_parameters_dir,
                show_video=tracking_config.show_video,
                marker_length=tracking_config.marker_length).track)
            tracking_process.start()

            while True:
                time.sleep(1)

                if not tracking_process.is_alive():
                    server_process.terminate()
                    self.stop_tracking.clear()
                    break

                if self.stop_tracking.wait(0):
                    tracking_process.terminate()
                    server_process.terminate()
                    break


class SingleMarkerTracking:
    def __init__(self, queue, device_number, device_parameters_dir, show_video, marker_length):
        self.__data_queue = queue
        self.__device_number = device_number
        self.__device_parameters_dir = device_parameters_dir
        self.__show_video = show_video
        self.__marker_length = marker_length

    def track(self):
        cam_mtx = np.load(
            "{}/cam_mtx.npy".format(self.__device_parameters_dir))
        dist = np.load(
            "{}/dist.npy".format(self.__device_parameters_dir))

        video_capture = cv2.VideoCapture(
            self.__device_number, cv2.CAP_DSHOW)

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
                    corners, float(self.__marker_length), cam_mtx, dist)

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

            if self.__show_video:
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


class DataPublishServer:

    def __init__(self, server_ip, server_port, queue):
        self.server_ip = server_ip
        self.__server_port = server_port
        self.__queue = queue

    def listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.server_ip, self.__server_port))

        try:
            sock.listen(1)
            connection, _ = sock.accept()

            while True:
                data = self.__queue.get()
                connection.send(data.encode())

        except:
            sock.close()
            self.listen()


class SingleMarkerTrackingCofig:

    def __init__(self, device_number, device_parameters_dir, show_video, marker_length, server_ip, server_port):
        self.device_number = device_number
        self.device_parameters_dir = device_parameters_dir
        self.show_video = show_video
        self.marker_length = marker_length
        self.server_ip = server_ip
        self.server_port = server_port

    @classmethod
    def persisted(cls):
        if not os.path.exists('../assets/configs/'):
            os.makedirs('../assets/configs/')

        try:
            with open('../assets/configs/tracking_config_data.pkl', 'rb') as file:
                tracking_config_data = pickle.load(file)

                return cls(tracking_config_data['device_number'],
                           tracking_config_data['device_parameters_dir'],
                           tracking_config_data['show_video'],
                           tracking_config_data['marker_length'],
                           tracking_config_data['server_ip'],
                           tracking_config_data['server_port'])
        except FileNotFoundError:
            return cls(0, "", True, "", "", "")

    def persist(self):
        # Overwrites any existing file.
        with open('../assets/configs/tracking_config_data.pkl', 'wb+') as output:
            pickle.dump({
                'device_number': self.device_number,
                'device_parameters_dir': self.device_parameters_dir,
                'show_video': self.show_video,
                'marker_length': self.marker_length,
                'server_ip': self.server_ip,
                'server_port': self.server_port}, output, pickle.HIGHEST_PROTOCOL)
