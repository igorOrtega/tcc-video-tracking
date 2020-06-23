import os
import glob
import cv2


class CalibrationImageCapture:

    def __init__(self, chessboard_points_per_row, chessboard_points_per_column, image_save_dir):
        self.chessboard_points_per_row = chessboard_points_per_row
        self.chessboard_points_per_column = chessboard_points_per_column
        self.image_save_dir = image_save_dir

        self.criteria = (cv2.TERM_CRITERIA_EPS +
                         cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        self.calibration_image_count = 0
        self.get_saved_image_count()

    def main_loop(self):
        win_name = "Calibration Image Capture"
        cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(
            win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        video = cv2.VideoCapture(0)

        while True:
            _, image = video.read()

            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(image, "calibration image count: {}".format(
                self.calibration_image_count), (0, 32), font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(image, "S - Save Image ", (0, 64),
                        font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(image, "D - Delete All Images ", (0, 96),
                        font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(image, "Q - Quit ", (0, 128), font,
                        0.6, (0, 255, 0), 2, cv2.LINE_AA)

            cv2.imshow(win_name, image)

            key = cv2.waitKey(1)

            if(key == ord('s')):
                self.try_save_image(image)

            elif(key == ord('d')):
                self.delete_images()

            elif(key == ord('q')):
                video.release()
                cv2.destroyAllWindows()
                break

    def get_saved_image_count(self):
        paths = glob.glob(self.image_save_dir + '*.jpg')
        self.calibration_image_count = len(paths)

    def try_save_image(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # only saves images with chessboard
        found, _ = cv2.findChessboardCorners(
            gray, (self.chessboard_points_per_row, self.chessboard_points_per_column), None)

        if found:
            self.calibration_image_count = self.calibration_image_count + 1
            save_path = self.image_save_dir + 'cal_image' + \
                str(self.calibration_image_count) + '.jpg'
            cv2.imwrite(save_path, gray)

    def delete_images(self):
        paths = glob.glob(self.image_save_dir + '*.jpg')
        for image_path in paths:
            os.remove(image_path)
        self.calibration_image_count = 0


if __name__ == "__main__":

    calibration_image_capture = CalibrationImageCapture(
        9, 6, "calibration_images/")

    calibration_image_capture.main_loop()
