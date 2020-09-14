import os
from tkinter import *
import cv2.aruco as aruco
from tracking import ArucoTracking, ArucoTrackingCofig


class Application:
    def __init__(self, master=None):
        self.traking_container = Frame(master)
        self.traking_container["pady"] = 10
        self.traking_container.pack()

        self.title = Label(self.traking_container, text="AR Tracking - TCC")
        self.title.pack()

        self.tracking_button = Button(self.traking_container)
        self.tracking_button["text"] = "Start tracking"
        self.tracking_button["width"] = 12
        self.tracking_button["command"] = self.start_tracking
        self.tracking_button.pack()

    def start_tracking(self):
        config = ArucoTrackingCofig(
            2.5, aruco.DICT_6X6_250, 'localhost', 10000)
        tracking = ArucoTracking(config)
        tracking.single_marker_tracking(0, True)


if __name__ == "__main__":
    root = Tk()

    WIDTH = 400
    HEIGHT = 400

    # centers window
    pos_x = (root.winfo_screenwidth()/2) - (WIDTH/2)
    pos_y = (root.winfo_screenheight()/2) - (HEIGHT/2)
    root.geometry('%dx%d+%d+%d' % (WIDTH, HEIGHT, pos_x, pos_y))

    Application(root)
    root.mainloop()
