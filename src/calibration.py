try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle

import os
import copy
import glob
import cv2
import numpy as np
import cv2.aruco as aruco


def mean(nums):
    return float(sum(nums)) / max(len(nums), 1)


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
        win_name = "Calibration Image Capture"
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


class MarkerCubeCalibration:
    def __init__(self, device_number, device_parameters_dir, main_id, marker_length):
        self.__device_number = device_number
        self.__device_parameters_dir = device_parameters_dir
        self.__main_id = main_id
        self.__marker_length = marker_length

    def calibration(self):
        cam_mtx = np.load(
            "{}/cam_mtx.npy".format(self.__device_parameters_dir))
        dist = np.load(
            "{}/dist.npy".format(self.__device_parameters_dir))

        win_name = "Marker Cube Calibration"
        cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(
            win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        video_capture = cv2.VideoCapture(self.__device_number, cv2.CAP_DSHOW)

        offsets = {}
        # offset_transformation = None
        # calculations = 0
        # errx_values = []
        # erry_values = []
        # errz_values = []
        while True:
            _, frame = video_capture.read()

            parameters = aruco.DetectorParameters_create()
            parameters.adaptiveThreshConstant = 10

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_color = (0, 255, 0)

            corners, ids, _ = aruco.detectMarkers(
                cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                aruco.Dictionary_get(aruco.DICT_6X6_250),
                parameters=parameters)

            rvec, tvec, _ = aruco.estimatePoseSingleMarkers(
                corners, float(self.__marker_length), cam_mtx, dist)

            main_marker_detected = False
            main_index = 0

            if np.all(ids is not None):
                choosen_index = 0
                choosen_id = ids[0][0]

                for i in range(0, ids.size):
                    if tvec[choosen_index][0][2] > tvec[i][0][2]:
                        choosen_id = ids[i][0]
                        choosen_index = i

                    if ids[i][0] == self.__main_id:
                        main_marker_detected = True
                        main_index = i

                other_rotation = copy.deepcopy(rvec[choosen_index])
                other_translation = copy.deepcopy(tvec[choosen_index])

                other_rotation_matrix = np.zeros(shape=(3, 3))
                cv2.Rodrigues(other_rotation, other_rotation_matrix)

                other_transformation = np.concatenate(
                    (other_rotation_matrix, np.transpose(other_translation)), axis=1)
                other_transformation = np.concatenate(
                    (other_transformation, np.array([[0, 0, 0, 1]])))

                if main_marker_detected and choosen_id != self.__main_id:
                    main_rotation = copy.deepcopy(rvec[main_index])
                    main_translation = copy.deepcopy(tvec[main_index])

                    main_rotation_matrix = np.zeros(shape=(3, 3))
                    cv2.Rodrigues(main_rotation, main_rotation_matrix)

                    main_transformation = np.concatenate(
                        (main_rotation_matrix, np.transpose(main_translation)), axis=1)
                    main_transformation = np.concatenate(
                        (main_transformation, np.array([[0, 0, 0, 1]])))

                    if choosen_id not in offsets:
                        offsets[choosen_id] = {}
                        offsets[choosen_id]["transformation"] = None
                        offsets[choosen_id]["calculations"] = 0

                    if offsets[choosen_id]["transformation"] is None or offsets[choosen_id]["calculations"] < 200:
                        offsets[choosen_id]["transformation"] = np.dot(
                            np.linalg.inv(main_transformation), other_transformation)
                        offsets[choosen_id]["calculations"] += 1

                        # rotation_offset_matrix = np.dot(
                        #     np.linalg.inv(main_rotation_matrix), other_rotation_matrix)

                    # errx = tvec[0][0][0] - tvec[1][0][0]
                    # erry = tvec[0][0][1] - tvec[1][0][1]
                    # errz = tvec[0][0][2] - tvec[1][0][2]

                    # cv2.putText(frame, 'errx {:.2f} erry {:.2f} errz {:.2f} tvec 0'.format(
                    #     errx, erry, errz), (0, 60), font, font_scale, font_color, 2, cv2.LINE_AA)

                    # if offsets[other_id]["calculations"] == 200:
                    #     errx_values.append(errx)
                    #     erry_values.append(erry)
                    #     errz_values.append(errz)
                    #     cv2.putText(frame, 'mean errx {:.2f} mean erry {:.2f} mean errz {:.2f} tvec 0'.format(mean(
                    #         errx_values), mean(erry_values), mean(errz_values)), (0, 80), font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'calcs {:.2f}'.format(
                        offsets[choosen_id]["calculations"]), (0, 400), font, font_scale, font_color, 2, cv2.LINE_AA)
                    # cv2.putText(frame, '{:.2f} {:.2f} {:.2f} tvec 1'.format(
                    #     tvec[1][0][0], tvec[1][0][1], tvec[1][0][2]), (0, 80), font, font_scale, font_color, 2, cv2.LINE_AA)
                    # cv2.putText(frame, 'rotation_offset_right_y: {:.2f}'.format(rotation_offset_matrix[1][0]), (0, 140),
                    #             font, font_scale, font_color, 2, cv2.LINE_AA)
                    # cv2.putText(frame, 'rotation_offset_right_z: {:.2f}'.format(rotation_offset_matrix[2][0]), (0, 160),
                    #             font, font_scale, font_color, 2, cv2.LINE_AA)
                    # cv2.putText(frame, 'rotation_offset_up_x: {:.2f}'.format(rotation_offset_matrix[0][1]), (0, 180),
                    #             font, font_scale, font_color, 2, cv2.LINE_AA)
                    # cv2.putText(frame, 'rotation_offset_up_y: {:.2f}'.format(rotation_offset_matrix[1][1]), (0, 200),
                    #             font, font_scale, font_color, 2, cv2.LINE_AA)
                    # cv2.putText(frame, 'rotation_offset_up_z: {:.2f}'.format(rotation_offset_matrix[2][1]), (0, 220),
                    #             font, font_scale, font_color, 2, cv2.LINE_AA)
                    # cv2.putText(frame, 'rotation_offset_forward_x: {:.2f}'.format(rotation_offset_matrix[0][2]), (0, 240),
                    #             font, font_scale, font_color, 2, cv2.LINE_AA)
                    # cv2.putText(frame, 'rotation_offset_forward_y: {:.2f}'.format(rotation_offset_matrix[1][2]), (0, 260),
                    #             font, font_scale, font_color, 2, cv2.LINE_AA)
                    # cv2.putText(frame, 'rotation_offset_forward_z: {:.2f}'.format(rotation_offset_matrix[2][2]), (0, 280),
                    #             font, font_scale, font_color, 2, cv2.LINE_AA)

                if choosen_id == self.__main_id:
                    aruco.drawAxis(frame, cam_mtx, dist,
                                   rvec[choosen_index], tvec[choosen_index], 5)

                    choosen_rot = np.zeros(shape=(3, 3))
                    cv2.Rodrigues(rvec[choosen_index], choosen_rot)
                    cv2.putText(frame, 'translation_x: {:.2f}'.format(tvec[choosen_index][0][0]), (0, 60),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'translation_y: {:.2f}'.format(tvec[choosen_index][0][1]), (0, 80),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'translation_z: {:.2f}'.format(tvec[choosen_index][0][2]), (0, 100),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_right_x: {:.2f}'.format(choosen_rot[0][0]), (0, 120),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_right_y: {:.2f}'.format(choosen_rot[1][0]), (0, 140),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_right_z: {:.2f}'.format(choosen_rot[2][0]), (0, 160),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_up_x: {:.2f}'.format(choosen_rot[0][1]), (0, 180),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_up_y: {:.2f}'.format(choosen_rot[1][1]), (0, 200),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_up_z: {:.2f}'.format(choosen_rot[2][1]), (0, 220),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_forward_x: {:.2f}'.format(choosen_rot[0][2]), (0, 240),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_forward_y: {:.2f}'.format(choosen_rot[1][2]), (0, 260),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_forward_z: {:.2f}'.format(choosen_rot[2][2]), (0, 280),
                                font, font_scale, font_color, 2, cv2.LINE_AA)

                elif choosen_id in offsets and offsets[choosen_id]["transformation"] is not None and offsets[choosen_id]["calculations"] == 200:
                    result = np.dot(
                        offsets[choosen_id]["transformation"], np.linalg.inv(other_transformation))

                    result = np.linalg.inv(result)
                    new_tvec = result[:, 3]
                    new_tvec = np.delete(new_tvec, (3))
                    tvec[choosen_index] = new_tvec.T

                    result = np.delete(result, 3, 0)
                    result = np.delete(result, 3, 1)
                    new_rot, _ = cv2.Rodrigues(result)
                    rvec[choosen_index] = new_rot.T

                    aruco.drawAxis(frame, cam_mtx, dist,
                                   rvec[choosen_index], tvec[choosen_index], 5)

                    choosen_rot = np.zeros(shape=(3, 3))
                    cv2.Rodrigues(rvec[choosen_index], choosen_rot)
                    cv2.putText(frame, 'translation_x: {:.2f}'.format(tvec[choosen_index][0][0]), (0, 60),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'translation_y: {:.2f}'.format(tvec[choosen_index][0][1]), (0, 80),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'translation_z: {:.2f}'.format(tvec[choosen_index][0][2]), (0, 100),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_right_x: {:.2f}'.format(choosen_rot[0][0]), (0, 120),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_right_y: {:.2f}'.format(choosen_rot[1][0]), (0, 140),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_right_z: {:.2f}'.format(choosen_rot[2][0]), (0, 160),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_up_x: {:.2f}'.format(choosen_rot[0][1]), (0, 180),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_up_y: {:.2f}'.format(choosen_rot[1][1]), (0, 200),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_up_z: {:.2f}'.format(choosen_rot[2][1]), (0, 220),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_forward_x: {:.2f}'.format(choosen_rot[0][2]), (0, 240),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_forward_y: {:.2f}'.format(choosen_rot[1][2]), (0, 260),
                                font, font_scale, font_color, 2, cv2.LINE_AA)
                    cv2.putText(frame, 'rotation_forward_z: {:.2f}'.format(choosen_rot[2][2]), (0, 280),
                                font, font_scale, font_color, 2, cv2.LINE_AA)

                aruco.drawDetectedMarkers(frame, corners)

            cv2.putText(frame, "Q - Quit ", (0, 465), font,
                        font_scale, font_color, 2, cv2.LINE_AA)

            cv2.imshow(win_name, frame)

            key = cv2.waitKey(1)

            if key == ord('m'):
                pass

            elif key == ord('q'):
                video_capture.release()
                cv2.destroyAllWindows()
                break


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


if __name__ == "__main__":
    tst = MarkerCubeCalibration(
        0, "C:/Users/Igor Ortega/Documents/python/Projects/tcc-video-tracking/assets/camera_calibration_data/Logitech_HD_Webcam_C270", 1, 3.9)

    tst.calibration()
