import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import cv2.aruco as aruco
from calibration import CameraCalibration, CalibrationConfig
import video_device_listing
from tracking import SingleMarkerTracking, SingleMarkerTrackingCofig


class App():

    def __init__(self, window=None):
        # config = SingleMarkerTrackingCofig(
        #     2.5, aruco.DICT_6X6_250, 'localhost', 10000)
        # self.tracking = SingleMarkerTracking(config)

        window.title("AR Tracking Interface")

        width = 600
        height = 350
        pos_x = (window.winfo_screenwidth()/2) - (width/2)
        pos_y = (window.winfo_screenheight()/2) - (height/2)
        window.geometry('%dx%d+%d+%d' % (width, height, pos_x, pos_y))
        window.resizable(0, 0)

        # Create some room around all the internal frames
        window['padx'] = 5
        window['pady'] = 5

        window.grid_rowconfigure(1, weight=1)
        window.grid_rowconfigure(2, weight=1)
        window.grid_rowconfigure(3, weight=1)
        window.grid_rowconfigure(4, weight=1)
        window.grid_columnconfigure(1, weight=1)

        self.tracking_commands_frame = tk.Frame(window)
        self.tracking_commands_frame.grid(row=1, column=1)

        self.start_tracking_button = tk.Button(
            self.tracking_commands_frame, text="Start Tracking", command=self.start_tracking)
        self.start_tracking_button.grid(row=1, column=1)

        self.configuration_frame = tk.Frame(window)
        self.configuration_frame.grid(
            row=2, column=1, sticky=tk.E + tk.W + tk.N + tk.S)

        self.configuration_frame.grid_columnconfigure(1, weight=1)
        self.configuration_frame.grid_columnconfigure(2, weight=1)

        self.tracking_config_frame = ttk.LabelFrame(
            self.configuration_frame, text="Tracking Configuration")
        self.tracking_config_frame.grid(
            row=1, column=1, sticky=tk.E + tk.W + tk.N + tk.S, pady=5, padx=5)

        self.tracking_config_frame.grid_columnconfigure(1, weight=1)
        self.tracking_config_frame.grid_rowconfigure(1, weight=1)
        self.tracking_config_frame.grid_rowconfigure(2, weight=1)
        self.tracking_config_frame.grid_rowconfigure(3, weight=1)

        self.tracking_config = SingleMarkerTrackingCofig.persisted()

        self.show_video_frame = tk.Frame(self.tracking_config_frame)
        self.show_video_frame.grid(row=1, column=1)
        self.show_video = tk.BooleanVar()
        self.show_video.set(self.tracking_config.show_video)
        self.show_video_checkbox = tk.Checkbutton(
            self.show_video_frame, text="Show video", variable=self.show_video)
        self.show_video_checkbox.grid(row=1, column=1, pady=5)

        self.marker_parameters_frame = tk.Frame(self.tracking_config_frame)
        self.marker_parameters_frame.grid(row=2, column=1, pady=5)

        self.marker_lenght = tk.StringVar()
        self.marker_lenght.set(self.tracking_config.marker_lenght)
        self.marker_lenght_label = ttk.Label(
            self.marker_parameters_frame, text="Marker side lenght (cm):")
        self.marker_lenght_label.grid(
            row=1, column=1, sticky=tk.W + tk.N)
        self.marker_lenght_entry = ttk.Entry(
            self.marker_parameters_frame, textvariable=self.marker_lenght, width=10)
        self.marker_lenght_entry.grid(row=1, column=2, sticky=tk.W)

        self.export_coordinates_frame = ttk.LabelFrame(
            self.tracking_config_frame, text="Coordinates Publish Server")
        self.export_coordinates_frame.grid(row=3, column=1, pady=5)

        self.export_coordinates_input_frame = tk.Frame(
            self.export_coordinates_frame)
        self.export_coordinates_input_frame.grid(
            row=1, column=1, padx=5, pady=5)

        self.server_ip = tk.StringVar()
        self.server_ip.set(self.tracking_config.server_ip)
        self.server_ip_label = ttk.Label(
            self.export_coordinates_input_frame, text="IP Address:")
        self.server_ip_label.grid(row=1, column=1)
        self.server_ip_entry = ttk.Entry(
            self.export_coordinates_input_frame, textvariable=self.server_ip, width=15)
        self.server_ip_entry.grid(row=1, column=2)

        self.server_port = tk.StringVar()
        self.server_port.set(self.tracking_config.server_port)
        self.server_port_label = ttk.Label(
            self.export_coordinates_input_frame, text="Port:")
        self.server_port_label.grid(row=1, column=3)
        self.server_port_entry = ttk.Entry(
            self.export_coordinates_input_frame, textvariable=self.server_port, width=7)
        self.server_port_entry.grid(row=1, column=4)

        self.video_source_frame = ttk.LabelFrame(
            self.configuration_frame, text="Video Source")
        self.video_source_frame.grid(
            row=1, column=2, sticky=tk.E + tk.W + tk.N + tk.S, pady=5, padx=5)
        self.video_source_frame.grid_columnconfigure(1, weight=1)

        self.video_source_selection_frame = tk.Frame(self.video_source_frame)
        self.video_source_selection_frame.grid(row=1, column=1)

        self.video_source_list = video_device_listing.get_devices()
        self.video_source = ttk.Combobox(
            self.video_source_selection_frame, state="readonly", height=4, width=25)
        self.video_source.grid(row=1, column=1)
        self.video_source['values'] = self.video_source_list
        self.video_source.current(0)

        self.refresh_video_sources_button = tk.Button(
            self.video_source_selection_frame, text="Refresh")
        self.refresh_video_sources_button['command'] = self.refresh_video_sources
        self.refresh_video_sources_button.grid(row=1, column=3, padx=5)

        self.calibration_status_frame = tk.Frame(self.video_source_frame)
        self.calibration_status_frame.grid(row=2, column=1)
        self.calibration_status_label = ttk.Label(
            self.calibration_status_frame, text="Status:")
        self.calibration_status_label.grid(row=1, column=1)
        self.calibration_status = ttk.Label(
            self.calibration_status_frame, text="Not calibrated!", foreground="red")
        self.calibration_status.grid(row=1, column=2)

        self.calibration_frame = ttk.LabelFrame(
            self.video_source_frame, text="Calibration")
        self.calibration_frame.grid(
            row=3, column=1, sticky=tk.E + tk.W + tk.N + tk.S, pady=5, padx=5)
        self.calibration_frame.grid_columnconfigure(1, weight=1)

        self.calibration_buttons_frame = tk.Frame(self.calibration_frame)
        self.calibration_buttons_frame.grid(row=1, column=1, pady=5)

        self.calibrate_button = tk.Button(
            self.calibration_buttons_frame, text="Calibrate", state=tk.DISABLED)
        # self.calibrate_button['command'] = lambda: self.Calibrate()
        self.calibrate_button.grid(row=1, column=1, padx=5)
        self.capture_images_button = tk.Button(
            self.calibration_buttons_frame, text="Capture Images")
        # self.capture_images_button['command'] = lambda: self.Capture()
        self.capture_images_button.grid(row=1, column=2, padx=5)

        self.calibration_image_count_label = ttk.Label(
            self.calibration_frame, text="Calibration images count: 0\nMinimum: 30", foreground="red")
        self.calibration_image_count_label.grid(row=2, column=1)

        self.calibration_chessboard_parameters_frame = tk.Frame(
            self.calibration_frame)
        self.calibration_chessboard_parameters_frame.grid(
            row=3, column=1, pady=5)

        self.calibration_config = CalibrationConfig.persisted()

        self.chessboard_square_size = tk.StringVar()
        self.chessboard_square_size.set(
            self.calibration_config.chessboard_square_size)
        self.chessboard_square_size_label = ttk.Label(
            self.calibration_chessboard_parameters_frame, text="Chessboard square size (cm):")
        self.chessboard_square_size_label.grid(
            row=1, column=1)
        self.chessboard_square_size_entry = ttk.Entry(
            self.calibration_chessboard_parameters_frame, width=5,
            textvariable=self.chessboard_square_size)
        self.chessboard_square_size_entry.grid(row=1, column=2)

        self.utils_frame = tk.Frame(window)
        self.utils_frame.grid(row=3, column=1, sticky=tk.S)

        self.save_button = ttk.Button(
            self.utils_frame, text="Save", command=self.save)
        self.save_button.grid(row=1, column=1)

    def refresh_video_sources(self):
        self.video_source_list = video_device_listing.get_devices()
        self.video_source['values'] = self.video_source_list

    def start_tracking(self):
        tracking = SingleMarkerTracking(self.tracking_config)
        tracking.single_marker_tracking(self.video_source.current())

    def stop_tracking(self):
        pass

    # def Calibrate(self):
    #     config = CalibrationConfig(5, 10, 2.5)
    #     cam_calib = CameraCalibration(config)
    #     cam_calib.run_calibration()
    #     return "calibrou"

    # def Capture(self):
    #     config = CalibrationConfig(5, 10, 2.5)
    #     cam_capture = CameraCalibration(config)
    #     cam_capture.acquire_calibration_images(self.webcam_selection.current())
    #     return "tirou foto"

    def save(self):
        self.tracking_config.show_video = self.show_video.get()
        self.tracking_config.marker_lenght = self.marker_lenght.get()
        self.tracking_config.server_ip = self.server_ip.get()
        self.tracking_config.server_port = self.server_port.get()
        self.tracking_config.persist()

        self.calibration_config.chessboard_square_size = self.chessboard_square_size.get()
        self.calibration_config.persist()


if __name__ == "__main__":
    tk_root = tk.Tk()
    App(tk_root)
    tk_root.mainloop()
