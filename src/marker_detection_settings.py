try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle

import os
import cv2
import numpy as np
import cv2.aruco as aruco

CUBE_DETECTION = "MARKERS CUBE"
SINGLE_DETECTION = "SINGLE MARKER"


class SingleMarkerDetectionSettings():

    def __init__(self, marker_length, marker_id):
        self.identifier = SINGLE_DETECTION
        self.marker_length = marker_length
        self.marker_id = marker_id

    def persist(self):
        # Overwrites any existing file.
        with open('../assets/configs/single_marker.pkl', 'wb+') as output:
            pickle.dump({
                'marker_length': self.marker_length,
                'marker_id': self.marker_id}, output, pickle.HIGHEST_PROTOCOL)

    @classmethod
    def persisted(cls):
        if not os.path.exists('../assets/configs/'):
            os.makedirs('../assets/configs/')

        try:
            with open('../assets/configs/single_marker.pkl', 'rb') as file:
                settings = pickle.load(file)

                return cls(settings['marker_length'],
                           settings['marker_id'])

        except FileNotFoundError:
            return cls("", "")


class MarkersCubeDetectionSettings():

    def __init__(self, markers_length, main_marker_id, other_marker_ids, transformations):
        self.identifier = CUBE_DETECTION
        self.markers_length = markers_length
        self.main_marker_id = main_marker_id
        self.other_marker_ids = other_marker_ids
        self.transformations = transformations

    def persist(self, cube_id):
        # Overwrites any existing file.
        with open('../assets/configs/marker_cubes/{}.pkl'.format(cube_id), 'wb+') as output:
            pickle.dump({
                'markers_length': self.markers_length,
                'main_marker_id': self.main_marker_id,
                'other_marker_ids': self.other_marker_ids,
                'transformations': self.transformations}, output, pickle.HIGHEST_PROTOCOL)

    @classmethod
    def persisted(cls, cube_id):
        if not os.path.exists('../assets/configs/marker_cubes/'):
            os.makedirs('../assets/configs/marker_cubes/')

        try:
            with open('../assets/configs/marker_cubes/{}.pkl'.format(cube_id), 'rb') as file:
                settings = pickle.load(file)

                return cls(settings['markers_length'],
                           settings['main_marker_id'],
                           settings['other_marker_ids'],
                           settings['transformations'])

        except FileNotFoundError:
            return cls("", "", ["", "", "", ""], None)


class MarkerCubeMapping:

    def __init__(self, cube_id, video_source_dir, video_source, markers_length, main_marker_id, other_ids):
        self.__cube_id = cube_id
        self.__video_source_dir = video_source_dir
        self.__video_source = video_source
        self.__markers_length = markers_length
        self.__main_marker_id = main_marker_id
        self.__other_ids = other_ids

        self.__acquire_min_count = 10

    def map(self):
        transformations = {}
        for other_id in self.__other_ids:
            transformations[other_id] = []

        cam_mtx = np.load(
            "{}/cam_mtx.npy".format(self.__video_source_dir))
        dist = np.load(
            "{}/dist.npy".format(self.__video_source_dir))

        win_name = "Markers Cube Calibration Image Capture"
        cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(
            win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        video_capture = cv2.VideoCapture(self.__video_source, cv2.CAP_DSHOW)

        while True:
            _, frame = video_capture.read()
            option = cv2.waitKey(1)

            done = True
            for other_id in self.__other_ids:
                done &= len(transformations[other_id]
                            ) == self.__acquire_min_count

            if not done:
                corners, ids = self.__detect_markers(frame)

                font = cv2.FONT_HERSHEY_SIMPLEX
                scale = 0.6
                blue = (255, 0, 0)
                red = (0, 0, 255)
                green = (0, 255, 0)

                if np.all(ids is not None):

                    if ids.size <= 2:

                        main_marker_index = None
                        other_marker_index = None
                        for i in range(0, ids.size):
                            if ids[i][0] == self.__main_marker_id:
                                main_marker_index = i
                            else:
                                other_marker_index = i

                        if main_marker_index is None:
                            cv2.putText(frame, "Cannot detect main marker!",
                                        (0, 20), font, scale, blue, 2, cv2.LINE_AA)
                        elif other_marker_index is None:
                            cv2.putText(frame, "Only main marker detected!",
                                        (0, 20), font, scale, blue, 2, cv2.LINE_AA)
                        else:
                            rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(
                                corners, float(self.__markers_length), cam_mtx, dist)

                            cv2.putText(frame, "marker {} (main) -> marker {} mapping".format(
                                ids[main_marker_index][0], ids[other_marker_index][0]), (0, 20), font, scale, blue, 2, cv2.LINE_AA)

                            acquired_transformations_count = len(
                                transformations[ids[other_marker_index][0]])
                            if acquired_transformations_count < self.__acquire_min_count:
                                cv2.putText(frame, "Press 'ENTER' {} times, in diffetent angles".format(
                                    self.__acquire_min_count), (0, 40), font, scale, blue, 2, cv2.LINE_AA)
                                cv2.putText(frame, "Count: {}".format(
                                    acquired_transformations_count), (0, 60), font, scale, red, 2, cv2.LINE_AA)

                                # enter
                                if option == 13:
                                    main_marker_transformation = self.__get_transformation_matrix(
                                        rvecs[main_marker_index], tvecs[main_marker_index])
                                    other_marker_transformation = self.__get_transformation_matrix(
                                        rvecs[other_marker_index], tvecs[other_marker_index])

                                    transformation_other_to_main = np.dot(np.linalg.inv(
                                        main_marker_transformation), other_marker_transformation)
                                    transformations[ids[other_marker_index][0]].append(
                                        transformation_other_to_main)

                            else:
                                cv2.putText(frame, "Done!", (0, 40),
                                            font, scale, green, 2, cv2.LINE_AA)

                    else:
                        cv2.putText(frame, "Too many markers detected!", (0, 20), font,
                                    scale, blue, 2, cv2.LINE_AA)
                else:
                    cv2.putText(frame, "No markers detected!", (0, 20), font,
                                scale, blue, 2, cv2.LINE_AA)

                cv2.putText(frame, "Q - Quit ", (0, 465), font,
                            scale, blue, 2, cv2.LINE_AA)
            else:
                cv2.putText(frame, "Markers cube mapping finished, saving ...", (0, 40), font,
                            scale, green, 2, cv2.LINE_AA)

            cv2.imshow(win_name, frame)

            if done:
                for other_id in self.__other_ids:
                    transformations[other_id] = self.__mean_transformation(
                        transformations[other_id])

                settings = MarkersCubeDetectionSettings(
                    self.__markers_length, self.__main_marker_id, self.__other_ids, transformations)
                settings.persist(self.__cube_id)

                cv2.waitKey(1000)
                video_capture.release()
                cv2.destroyAllWindows()
                break

            if option == ord('q'):
                video_capture.release()
                cv2.destroyAllWindows()
                break

    def __detect_markers(self, frame):
        parameters = aruco.DetectorParameters_create()
        parameters.adaptiveThreshConstant = 10

        corners, ids, _ = aruco.detectMarkers(
            cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
            aruco.Dictionary_get(aruco.DICT_6X6_250),
            parameters=parameters)

        aruco.drawDetectedMarkers(frame, corners)

        return corners, ids

    def __get_transformation_matrix(self, rvec, tvec):
        rot_mtx = np.zeros(shape=(3, 3))
        cv2.Rodrigues(rvec, rot_mtx)

        transformation = np.concatenate(
            (rot_mtx, np.transpose(tvec)), axis=1)
        transformation = np.concatenate(
            (transformation, np.array([[0, 0, 0, 1]])))

        return transformation

    def __mean_transformation(self, transformations):
        result = np.zeros(shape=(4, 4))
        rows_count, cols_count = result.shape

        for transformation in transformations:
            for row in range(0, rows_count):
                for col in range(0, cols_count):
                    result[row][col] += transformation[row][col]

        for row in range(0, rows_count):
            for col in range(0, cols_count):
                result[row][col] /= self.__acquire_min_count

        return result
