import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import cv2.aruco as aruco
from calibration import CameraCalibration, CalibrationCofig
import video_device_listing
from tracking import SingleMarkerTracking, SingleMarkerTrackingCofig


class App():

    def __init__(self, window=None):
        # config = SingleMarkerTrackingCofig(
        #     2.5, aruco.DICT_6X6_250, 'localhost', 10000)
        # self.tracking = SingleMarkerTracking(config)

        window.title("AR Tracking Interface")

        width = 600
        height = 300
        pos_x = (window.winfo_screenwidth()/2) - (width/2)
        pos_y = (window.winfo_screenheight()/2) - (height/2)
        window.geometry('%dx%d+%d+%d' % (width, height, pos_x, pos_y))

        # Create some room around all the internal frames
        window['padx'] = 5
        window['pady'] = 5

        window.grid_rowconfigure(0, weight=0)
        window.grid_columnconfigure(1, weight=1)

        self.video_source_frame = tk.Frame(window)
        self.video_source_frame.grid(row=1, column=1)

        self.video_source_label = tk.Label(
            self.video_source_frame, text="Video Source")
        self.video_source_label.grid(row=1, column=1)

        self.video_source_list = video_device_listing.get_devices()
        self.video_source = ttk.Combobox(
            self.video_source_frame, state="readonly", height=4, width=25)
        self.video_source.grid(row=1, column=2)
        self.video_source['values'] = self.video_source_list
        self.video_source.current(0)

        self.refresh_video_sources_button = tk.Button(
            self.video_source_frame, text="Refresh")
        self.refresh_video_sources_button['command'] = self.refresh_video_sources
        self.refresh_video_sources_button.grid(row=1, column=3)

        self.tracking_commands_frame = tk.Frame(window)
        self.tracking_commands_frame.grid(row=2, column=1)

        self.start_tracking_button = tk.Button(
            self.tracking_commands_frame, text="Start Tracking")
        # self.start_tracking_button['command'] = lambda: self.tracking.single_marker_tracking(
        #     self.webcam_selection.current(), self.show_video.get())
        self.start_tracking_button.grid(row=1, column=1)

    #     tracking_frame = ttk.LabelFrame(
    #         window, text="AR Tracking", relief=tk.RIDGE)
    #     tracking_frame.grid(row=1, column=1, sticky="nsew", columnspan=2)
    #     window.grid_rowconfigure(2, weight=1)

    #     self.show_video = tk.BooleanVar()
    #     self.show_video.set(True)
    #     show_video_checkbox = tk.Checkbutton(
    #         tracking_frame, text="Enable video", variable=self.show_video)
    #     show_video_checkbox.grid(row=1, column=1)

    #     # The tracking config entry frame
    #     entry_frame = ttk.LabelFrame(window, text="Tracking Configuration",
    #                                  relief=tk.RIDGE)
    #     entry_frame.grid(row=2, column=1, sticky=tk.E + tk.W + tk.N + tk.S)

    #     marker_size_label = ttk.Label(entry_frame, text="Marker size (cm):")
    #     marker_size_label.grid(row=4, column=1, sticky=tk.W + tk.N)
    #     my_marker_size = ttk.Entry(entry_frame, width=10)
    #     my_marker_size.grid(row=4, column=2, sticky=tk.W, pady=3)

    #     export_add_label = ttk.Label(entry_frame, text="Export address:")
    #     export_add_label.grid(row=7, column=1, sticky=tk.W + tk.N)

    #     export_add = ttk.Entry(entry_frame, width=15)
    #     export_add.grid(row=7, column=2, sticky=tk.W + tk.N)

    #     port_label = ttk.Label(entry_frame, text="Port:")
    #     port_label.grid(row=7, column=3, sticky=tk.W + tk.N)

    #     port_label_add = ttk.Entry(entry_frame, width=7)
    #     port_label_add.grid(row=7, column=4, sticky=tk.W + tk.N)

    # # - - - - - - - - - - - - - - - - - - - - -
    #     # The calibration config frame
    #     calib_config_frame = ttk.LabelFrame(
    #         window, text="Calibration Configuration", relief=tk.RIDGE, padding=6)
    #     calib_config_frame.grid(row=2, column=3, padx=6,
    #                             sticky=tk.E + tk.W + tk.N + tk.S, columnspan=2)

    #     chess_label = ttk.Label(
    #         calib_config_frame, text="Chessboard square size (cm):")
    #     chess_label.grid(row=1, rowspan=2, column=1, sticky=tk.W + tk.N)
    #     chess_label_add = ttk.Entry(calib_config_frame, width=5)
    #     chess_label_add.grid(row=1, column=3)

    #     chess_column_label = ttk.Label(
    #         calib_config_frame, text="Chessboard column count:")
    #     chess_column_label.grid(row=3, rowspan=2, column=1, sticky=tk.W + tk.N)
    #     chess_column_add = ttk.Entry(calib_config_frame, width=5)
    #     chess_column_add.grid(row=3, column=3)

    #     chess_row_label = ttk.Label(
    #         calib_config_frame, text="Chessboard row count:")
    #     chess_row_label.grid(row=5, rowspan=2, column=1, sticky=tk.W + tk.N)
    #     chess_row_add = ttk.Entry(calib_config_frame, width=5)
    #     chess_row_add.grid(row=5, column=3)

    #     calib_img_count = ttk.Label(
    #         calib_config_frame, text="Calibration image count:")
    #     calib_img_count.grid(row=8, column=1, rowspan=3,  sticky=tk.W)

    #     cam = CameraCalibration(CalibrationCofig)
    #     img_count = ttk.Label(calib_config_frame,
    #                           text=cam.calibration_image_count)
    #     img_count.grid(row=8, column=2)

    #     calibrate_b = tk.Button(calib_config_frame, text="Calibrate")
    #     calibrate_b['command'] = lambda: self.Calibrate()
    #     calibrate_b.grid(row=11, column=1)

    #     capture_img_b = tk.Button(calib_config_frame, text="Capture Images")
    #     capture_img_b['command'] = lambda: self.Capture()
    #     capture_img_b.grid(row=12, column=1)

    #     # - - - - - - - - - - - - - - - - - - - - -
    #     save_button = ttk.Button(
    #         window, text="Salvar", command=filedialog.asksaveasfilename)
    #     save_button.grid(row=1, column=3)
    #     # Quit button in the lower right corner
    #     quit_button = ttk.Button(
    #         window, text="Sair", command=window.destroy)
    #     quit_button.grid(row=2, column=5)

    # def Calibrate(self):
    #     config = CalibrationCofig(5, 10, 2.5)
    #     cam_calib = CameraCalibration(config)
    #     cam_calib.run_calibration()
    #     return "calibrou"

    # def Capture(self):
    #     config = CalibrationCofig(5, 10, 2.5)
    #     cam_capture = CameraCalibration(config)
    #     cam_capture.acquire_calibration_images(self.webcam_selection.current())
    #     return "tirou foto"

    def refresh_video_sources(self):
        self.video_source_list = video_device_listing.get_devices()


if __name__ == "__main__":
    tk_root = tk.Tk()
    App(tk_root)
    tk_root.mainloop()
