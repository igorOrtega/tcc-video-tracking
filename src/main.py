import os
import cv2.aruco as aruco
from tracking import ArucoTracking, ArucoTrackingCofig


if __name__ == "__main__":
    # config1 = CoordinatesExportCofig('localhost', 10000)

    # exporter = CoordinatesExport(config1)

    _exit = False
    while(_exit == False):
        os.system('cls' if os.name == 'nt' else 'clear')
        option = input("1 - Run Tracking\n2 - Exit\n\n")

        if option == "1":
            config = ArucoTrackingCofig(
                2.5, aruco.DICT_6X6_250, 'localhost', 10000)

            tracking = ArucoTracking(config)

            tracking.single_marker_tracking(0, True)
        elif option == "2":
            _exit = True
