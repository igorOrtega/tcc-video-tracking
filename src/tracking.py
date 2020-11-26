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
from marker_detection_settings import SINGLE_DETECTION, CUBE_DETECTION


class TrackingScheduler:
    def __init__(self, start_tracking, stop_tracking):
        self.start_tracking = start_tracking
        self.stop_tracking = stop_tracking

    def main(self):

        while True:
            self.start_tracking.wait()
            self.start_tracking.clear()

            tracking_config = TrackingCofig.persisted()
            queue = Queue(1)

            client_process = Process(target=DataPublishClientUDP(
                server_ip=tracking_config.server_ip,
                server_port=int(tracking_config.server_port),
                queue=queue
            ).listen)
            client_process.start()

            tracking_process = Process(target=Tracking(
                queue=queue,
                device_number=tracking_config.device_number,
                device_parameters_dir=tracking_config.device_parameters_dir,
                show_video=tracking_config.show_video,
                marker_detection_settings=tracking_config.marker_detection_settings).track)
            tracking_process.start()

            while True:
                time.sleep(1)

                if not tracking_process.is_alive():
                    client_process.terminate()
                    self.stop_tracking.clear()
                    break

                if self.stop_tracking.wait(0):
                    tracking_process.terminate()
                    client_process.terminate()
                    self.stop_tracking.clear()
                    break


class Tracking:
    def __init__(self, queue, device_number, device_parameters_dir, show_video, marker_detection_settings):
        self.__data_queue = queue
        self.__device_number = device_number
        self.__device_parameters_dir = device_parameters_dir
        self.__show_video = show_video
        self.__marker_detection_settings = marker_detection_settings

    def track(self):
        video_capture = cv2.VideoCapture(
            self.__device_number, cv2.CAP_DSHOW)

        while True:
            _, frame = video_capture.read()

            detection_result = None
            if self.__marker_detection_settings.identifier == SINGLE_DETECTION:
                detection_result = self.__single_marker_detection(frame)
            elif self.__marker_detection_settings.identifier == CUBE_DETECTION:
                detection_result = self.__markers_cube_detection(frame)
            else:
                raise Exception("Invalid detection identifier. Received: {}".format(self.__marker_detection_settings.identifier))

            self.__publish_coordinates(json.dumps(detection_result))

            if self.__show_video:
                self.__show_video_result(frame, detection_result)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

    def __single_marker_detection(self, frame):

        corners, ids = self.__detect_markers(frame)

        marker_rvec = None
        marker_tvec = None
        if np.all(ids is not None):
            marker_found = False
            marker_index = None

            for i in range(0, ids.size):
                if ids[i][0] == self.__marker_detection_settings.marker_id:
                    marker_found = True
                    marker_index = i
                    break

            if marker_found:
                cam_mtx, dist = self.__camera_parameters()
                rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(
                    corners, float(self.__marker_detection_settings.marker_length), cam_mtx, dist)

                marker_rvec = rvecs[marker_index]
                marker_tvec = tvecs[marker_index]
                aruco.drawAxis(frame, cam_mtx, dist,
                               marker_rvec, marker_tvec, 5)

        return self.__detection_result(marker_rvec, marker_tvec)

    def __markers_cube_detection(self, frame):
        corners, ids = self.__detect_markers(frame)

        main_marker_rvec = None
        main_marker_tvec = None
        if np.all(ids is not None):

            cam_mtx, dist = self.__camera_parameters()
            rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(
                corners, float(self.__marker_detection_settings.markers_length), cam_mtx, dist)

            choosen_marker_index = 0
            choosen_marker_id = ids[0][0]
            for i in range(0, ids.size):
                if tvecs[choosen_marker_index][0][2] > tvecs[i][0][2]:
                    choosen_marker_id = ids[i][0]
                    choosen_marker_index = i

            if choosen_marker_id == self.__marker_detection_settings.main_marker_id:
                main_marker_rvec = rvecs[choosen_marker_index]
                main_marker_tvec = tvecs[choosen_marker_index]
            else:
                choosen_marker_rotation_mtx = np.zeros(shape=(3, 3))
                cv2.Rodrigues(rvecs[choosen_marker_index],
                              choosen_marker_rotation_mtx)
                choosen_marker_transformation = np.concatenate(
                    (choosen_marker_rotation_mtx, np.transpose(tvecs[choosen_marker_index])), axis=1)
                choosen_marker_transformation = np.concatenate(
                    (choosen_marker_transformation, np.array([[0, 0, 0, 1]])))

                choosen_marker_transformation = np.dot(
                    self.__marker_detection_settings.transformations[choosen_marker_id],
                    np.linalg.inv(choosen_marker_transformation))

                choosen_marker_transformation = np.linalg.inv(
                    choosen_marker_transformation)

                tvec_t = np.delete(
                    choosen_marker_transformation[:, 3], (3))
                main_marker_tvec = tvec_t.T

                choosen_marker_transformation = np.delete(
                    choosen_marker_transformation, 3, 0)
                choosen_marker_transformation = np.delete(
                    choosen_marker_transformation, 3, 1)

                rvec_t, _ = cv2.Rodrigues(choosen_marker_transformation)
                main_marker_rvec = rvec_t.T

            aruco.drawAxis(frame, cam_mtx, dist,
                               main_marker_rvec, main_marker_tvec, 5)

        return self.__detection_result(main_marker_rvec, main_marker_tvec)

    def __detect_markers(self, frame):
        parameters = aruco.DetectorParameters_create()
        parameters.adaptiveThreshConstant = 7
        parameters.cornerRefinementMethod = aruco.CORNER_REFINE_CONTOUR

        corners, ids, _ = aruco.detectMarkers(
            cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
            aruco.Dictionary_get(aruco.DICT_6X6_250),
            parameters=parameters)

        aruco.drawDetectedMarkers(frame, corners)

        return corners, ids

    def __camera_parameters(self):
        cam_mtx = np.load(
            "{}/cam_mtx.npy".format(self.__device_parameters_dir))
        dist = np.load(
            "{}/dist.npy".format(self.__device_parameters_dir))

        return cam_mtx, dist

    def __detection_result(self, rvec, tvec):
        detection_result = {}

        detection_result['timestamp'] = time.time()

        success = rvec is not None and tvec is not None
        detection_result['success'] = success

        if success:
            rot_mtx = np.zeros(shape=(3, 3))
            cv2.Rodrigues(rvec, rot_mtx)

            detection_result['translation_x'] = tvec.item(0)
            detection_result['translation_y'] = tvec.item(1)
            detection_result['translation_z'] = tvec.item(2)
            detection_result['rotation_right_x'] = rot_mtx.item(0, 0)
            detection_result['rotation_right_y'] = rot_mtx.item(1, 0)
            detection_result['rotation_right_z'] = rot_mtx.item(2, 0)
            detection_result['rotation_up_x'] = rot_mtx.item(0, 1)
            detection_result['rotation_up_y'] = rot_mtx.item(1, 1)
            detection_result['rotation_up_z'] = rot_mtx.item(2, 1)
            detection_result['rotation_forward_x'] = rot_mtx.item(0, 2)
            detection_result['rotation_forward_y'] = rot_mtx.item(1, 2)
            detection_result['rotation_forward_z'] = rot_mtx.item(2, 2)

        return detection_result

    def __publish_coordinates(self, data):
        if self.__data_queue.full():
            self.__data_queue.get()

        self.__data_queue.put(data)

    def __show_video_result(self, frame, detection_result):
        win_name = "Tracking"
        cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(
            win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        font_color = (0, 255, 0)

        cv2.putText(frame, 'timestamp: {}'.format(detection_result['timestamp']), (0, 20),
                    font, font_scale, font_color, 2, cv2.LINE_AA)
        cv2.putText(frame, 'success: {}'.format(detection_result['success']), (0, 40),
                    font, font_scale, font_color, 2, cv2.LINE_AA)

        if detection_result['success'] == 1:
            cv2.putText(frame, 'translation_x: {:.2f}'.format(detection_result['translation_x']), (0, 60),
                        font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(frame, 'translation_y: {:.2f}'.format(detection_result['translation_y']), (0, 80),
                        font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(frame, 'translation_z: {:.2f}'.format(detection_result['translation_z']), (0, 100),
                        font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(frame, 'rotation_right_x: {:.2f}'.format(detection_result['rotation_right_x']), (0, 120),
                        font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(frame, 'rotation_right_y: {:.2f}'.format(detection_result['rotation_right_y']), (0, 140),
                        font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(frame, 'rotation_right_z: {:.2f}'.format(detection_result['rotation_right_z']), (0, 160),
                        font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(frame, 'rotation_up_x: {:.2f}'.format(detection_result['rotation_up_x']), (0, 180),
                        font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(frame, 'rotation_up_y: {:.2f}'.format(detection_result['rotation_up_y']), (0, 200),
                        font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(frame, 'rotation_up_z: {:.2f}'.format(detection_result['rotation_up_z']), (0, 220),
                        font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(frame, 'rotation_forward_x: {:.2f}'.format(detection_result['rotation_forward_x']), (0, 240),
                        font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(frame, 'rotation_forward_y: {:.2f}'.format(detection_result['rotation_forward_y']), (0, 260),
                        font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(frame, 'rotation_forward_z: {:.2f}'.format(detection_result['rotation_forward_z']), (0, 280),
                        font, font_scale, font_color, 2, cv2.LINE_AA)

        cv2.putText(frame, "Q - Quit ", (0, 465), font,
                    font_scale, font_color, 2, cv2.LINE_AA)

        cv2.imshow(win_name, frame)


class DataPublishClientUDP:

    def __init__(self, server_ip, server_port, queue):
        self.server_ip = server_ip
        self.__server_port = server_port
        self.__queue = queue

    def listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        while True:
            data = self.__queue.get()
            sock.sendto(data.encode(), (self.server_ip, self.__server_port))


class TrackingCofig:

    def __init__(self, device_number, device_parameters_dir, show_video,
                 server_ip, server_port, marker_detection_settings):
        self.device_number = device_number
        self.device_parameters_dir = device_parameters_dir
        self.show_video = show_video
        self.server_ip = server_ip
        self.server_port = server_port
        self.marker_detection_settings = marker_detection_settings

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
                           tracking_config_data['server_ip'],
                           tracking_config_data['server_port'],
                           tracking_config_data['marker_detection_settings'])
        except FileNotFoundError:
            return cls(0, "", True, "", "", None)

    def persist(self):
        # Overwrites any existing file.
        with open('../assets/configs/tracking_config_data.pkl', 'wb+') as output:
            pickle.dump({
                'device_number': self.device_number,
                'device_parameters_dir': self.device_parameters_dir,
                'show_video': self.show_video,
                'server_ip': self.server_ip,
                'server_port': self.server_port,
                'marker_detection_settings': self.marker_detection_settings}, output, pickle.HIGHEST_PROTOCOL)
