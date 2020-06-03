import numpy as np
import cv2
import cv2.aruco as aruco

# SAVE_DIR = "camera_calibration_data/"
# MARKER_LENGHT = 6.3

class ArTagTrack:

    def __init__(self, camera_parameters_save_dir, marker_lenght):
        self.camera_parameters_save_dir = camera_parameters_save_dir
        self.marker_lenght = marker_lenght
    
    def main_loop(self):
        cam_mtx = np.load(self.camera_parameters_save_dir + 'cam_mtx.npy')
        dist = np.load(self.camera_parameters_save_dir + 'dist.npy')

        video = cv2.VideoCapture(0)

        while True:

            _, frame = video.read()

            # operations on the frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # set dictionary size depending on the aruco marker selected
            aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)

            # detector parameters can be set here (List of detection parameters[3])
            parameters = aruco.DetectorParameters_create()
            parameters.adaptiveThreshConstant = 10

            # lists of ids and the corners belonging to each id
            corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

            # font for displaying text (below)
            font = cv2.FONT_HERSHEY_SIMPLEX

            win_name = "Tracking"
            cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

            # check if the ids list is not empty
            # if no check is added the code will crash
            if np.all(ids != None):

                # estimate pose of each marker and return the values
                # rvet and tvec-different from camera coefficients
                rvec, tvec , _ = aruco.estimatePoseSingleMarkers(corners, self.marker_lenght, cam_mtx, dist)
                
                #(rvec-tvec).any() # get rid of that nasty numpy value array error
                for i in range(0, ids.size):
                    # draw axis for the aruco markers
                    aruco.drawAxis(frame, cam_mtx, dist, rvec[i], tvec[i], 5)

                # draw a square around the markers
                aruco.drawDetectedMarkers(frame, corners)


                # code to show ids of the marker found
                strg = ''
                for i in range(0, ids.size):
                    strg += str(ids[i][0])+', '

                cv2.putText(frame, "Id: " + strg, (0, 32), font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)

                x = str(tvec.item(0))
                cv2.putText(frame, "X: " + x, (0, 64), font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
                y = str(tvec.item(1))
                cv2.putText(frame, "Y: " + y, (0, 96), font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
                z = str(tvec.item(2))
                cv2.putText(frame, "Z: " + z, (0, 128), font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)



            else:
                # code to show 'No Ids' when no markers are found
                cv2.putText(frame, "No Ids", (0, 32), font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)

            # display the resulting frame
            cv2.imshow(win_name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    

        # When everything done, release the capture
        video.release()
        cv2.destroyAllWindows()
    
    