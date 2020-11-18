import os
import glob
import tkinter as tk
from tkinter import ttk
import multiprocessing
from video_source_calibration import VideoSourceCalibration, VideoSourceCalibrationConfig
from tracking import TrackingScheduler, TrackingCofig
from marker_detection_settings import CUBE_DETECTION, SINGLE_DETECTION, SingleMarkerDetectionSettings, MarkersCubeDetectionSettings, MarkerCubeMapping
import video_device_listing


class App():

    def __init__(self, start_tracking, stop_tracking, window):
        self.start_tracking_event = start_tracking
        self.stop_tracking_event = stop_tracking

        window.title("AR Tracking Interface")

        width = 800
        height = 450
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

        self.tracking_button = tk.Button(
            self.tracking_commands_frame, text="Start Tracking", command=self.start_tracking)
        self.tracking_button.grid(row=1, column=1)

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

        self.tracking_config = TrackingCofig.persisted()

        self.show_video_frame = tk.Frame(self.tracking_config_frame)
        self.show_video_frame.grid(row=1, column=1)
        self.show_video = tk.BooleanVar()
        self.show_video.set(self.tracking_config.show_video)
        self.show_video_checkbox = tk.Checkbutton(
            self.show_video_frame, text="Show video", variable=self.show_video)
        self.show_video_checkbox.grid(row=1, column=1, pady=5)

        self.detection_mode_frame = tk.LabelFrame(self.tracking_config_frame, text="Detection Mode")
        self.detection_mode_frame.grid(row=2, column=1, padx=5, pady=5)
        
        self.single_marker_frame = ttk.LabelFrame(
            self.detection_mode_frame, text="Single Marker")
        self.single_marker_frame.grid(
            row=1, column=1, padx=5, pady=5)

        self.single_marker_mode = tk.BooleanVar()
        self.single_marker_mode_checkbox = tk.Checkbutton(
            self.single_marker_frame, variable=self.single_marker_mode,
            command=self.single_marker_settings_selection)
        self.single_marker_mode_checkbox.grid(row=1, column=1, pady=5)

        self.single_marker_settings_frame = tk.Frame(
            self.single_marker_frame)
        self.single_marker_settings_frame.grid(
            row=2, column=1, padx=5, pady=5)

        self.single_marker_id = tk.IntVar()
        self.single_marker_id_label = ttk.Label(
            self.single_marker_settings_frame, text="Marker ID:")
        self.single_marker_id_label.grid(
            row=1, column=1, sticky=tk.W + tk.N)
        self.single_marker_id_entry = ttk.Entry(
            self.single_marker_settings_frame, textvariable=self.single_marker_id, width=5)
        self.single_marker_id_entry.grid(row=1, column=2, sticky=tk.W)

        self.single_marker_length = tk.DoubleVar()
        self.single_marker_length_label = ttk.Label(
            self.single_marker_settings_frame, text="Marker length:")
        self.single_marker_length_label.grid(
            row=2, column=1, sticky=tk.W + tk.N)
        self.single_marker_length_entry = ttk.Entry(
            self.single_marker_settings_frame, textvariable=self.single_marker_length, width=5)
        self.single_marker_length_entry.grid(row=2, column=2, sticky=tk.W)

        self.single_marker_buttons_frame = tk.Frame(
            self.single_marker_frame)
        self.single_marker_buttons_frame.grid(
            row=3, column=1, padx=5, pady=5)

        self.single_marker_save_button = tk.Button(self.single_marker_buttons_frame,text="Save", command=self.single_marker_save)
        self.single_marker_save_button.grid(row=1, column=1)

        self.marker_cube_frame = ttk.LabelFrame(
            self.detection_mode_frame, text="Marker Cube")
        self.marker_cube_frame.grid(
            row=1, column=2, padx=5, pady=5)

        self.marker_cube_mode = tk.BooleanVar()
        # self.single_marker_mode.set(self.tracking_config.show_video)
        self.marker_cube_mode_checkbox = tk.Checkbutton(
            self.marker_cube_frame, variable=self.marker_cube_mode,
            command=self.marker_cube_settings_selection)
        self.marker_cube_mode_checkbox.grid(row=1, column=1, pady=5)

        self.cube_id_frame = tk.Frame(self.marker_cube_frame)
        self.cube_id_frame.grid(row=2, column=1, padx=5, pady=5)

        self.cube_id_selection = ttk.Combobox(
            self.cube_id_frame, state="normal", height=4, width=15)
        self.cube_id_selection.bind('<<ComboboxSelected>>',
                               self.cube_id_selected)
        self.cube_id_selection.grid(row=1, column=1)

        self.new_cube_id_button = tk.Button(self.cube_id_frame,text="New", command=self.add_cube_id)
        self.new_cube_id_button.grid(row=1, column=2, padx=5)

        self.marker_cube_settings_frame = tk.Frame(
            self.marker_cube_frame)
        self.marker_cube_settings_frame.grid(
            row=3, column=1, padx=5, pady=5)

        self.cube_main_marker_id = tk.IntVar()
        self.cube_main_marker_id_label = ttk.Label(
            self.marker_cube_settings_frame, text="Up Marker ID:")
        self.cube_main_marker_id_label.grid(
            row=1, column=1, sticky=tk.W + tk.N)
        self.cube_main_marker_id_entry = ttk.Entry(
            self.marker_cube_settings_frame, textvariable=self.cube_main_marker_id, width=5)
        self.cube_main_marker_id_entry.grid(row=1, column=2, sticky=tk.W)

        self.cube_side_marker_ids_label = ttk.Label(
            self.marker_cube_settings_frame, text="Side Marker IDS:")
        self.cube_side_marker_ids_label.grid(
            row=2, column=1, sticky=tk.W + tk.N)

        self.cube_side_marker_1 = tk.IntVar()
        self.cube_side_marker_1_entry = ttk.Entry(
            self.marker_cube_settings_frame, textvariable=self.cube_side_marker_1, width=5)
        self.cube_side_marker_1_entry.grid(row=2, column=2, sticky=tk.W)
        self.cube_side_marker_2 = tk.IntVar()
        self.cube_side_marker_2_entry = ttk.Entry(
            self.marker_cube_settings_frame, textvariable=self.cube_side_marker_2, width=5)
        self.cube_side_marker_2_entry.grid(row=2, column=3, sticky=tk.W)
        self.cube_side_marker_3 = tk.IntVar()
        self.cube_side_marker_3_entry = ttk.Entry(
            self.marker_cube_settings_frame, textvariable=self.cube_side_marker_3, width=5)
        self.cube_side_marker_3_entry.grid(row=2, column=4, sticky=tk.W)
        self.cube_side_marker_4 = tk.IntVar()
        self.cube_side_marker_4_entry = ttk.Entry(
            self.marker_cube_settings_frame, textvariable=self.cube_side_marker_4, width=5)
        self.cube_side_marker_4_entry.grid(row=2, column=5, sticky=tk.W)

        self.cube_markers_length = tk.DoubleVar()
        self.cube_markers_length_label = ttk.Label(
            self.marker_cube_settings_frame, text="Markers length:")
        self.cube_markers_length_label.grid(
            row=3, column=1, pady=5)
        self.cube_markers_length_entry = ttk.Entry(
            self.marker_cube_settings_frame, textvariable=self.cube_markers_length, width=5)
        self.cube_markers_length_entry.grid(row=3, column=2, sticky=tk.W)

        self.marker_cube_buttons_frame = tk.Frame(
            self.marker_cube_frame)
        self.marker_cube_buttons_frame.grid(
            row=4, column=1, padx=5, pady=5)

        self.marker_cube_id_map_button = tk.Button(self.marker_cube_buttons_frame,text="Map and Save", command=self.marker_cube_map)
        self.marker_cube_id_map_button.grid(row=1, column=1, padx=5)

        self.marker_cube_id_delete_button = tk.Button(self.marker_cube_buttons_frame,text="Delete", command=self.marker_cube_delete)
        self.marker_cube_id_delete_button.grid(row=1, column=2, padx=5)

        self.single_marker_settings = SingleMarkerDetectionSettings.persisted()
        self.single_marker_settings_set()

        self.marker_cube_settings = MarkersCubeDetectionSettings.persisted(self.cube_id_selection.current())
        self.marker_cube_settings_set()

        if self.tracking_config.marker_detection_settings.identifier == SINGLE_DETECTION:
            self.single_marker_mode.set(True)
            self.single_marker_settings_selection()
        elif self.tracking_config.marker_detection_settings.identifier == CUBE_DETECTION:
            self.marker_cube_mode.set(True)
            self.marker_cube_settings_selection()

        self.video_source_frame = ttk.LabelFrame(
            self.configuration_frame, text="Video Source")
        self.video_source_frame.grid(
            row=1, column=2, sticky=tk.E + tk.W + tk.N + tk.S, pady=5, padx=5)
        self.video_source_frame.grid_columnconfigure(1, weight=1)

        self.video_source_selection_frame = tk.Frame(self.video_source_frame)
        self.video_source_selection_frame.grid(row=1, column=1)

        self.video_source = ttk.Combobox(
            self.video_source_selection_frame, state="readonly", height=4, width=25)
        self.video_source.bind('<<ComboboxSelected>>',
                               self.video_source_init)
        self.video_source.grid(row=1, column=1)

        self.refresh_video_sources_button = tk.Button(
            self.video_source_selection_frame, text="Refresh")
        self.refresh_video_sources_button['command'] = self.refresh_video_sources
        self.refresh_video_sources_button.grid(row=1, column=3, padx=5)

        self.calibration_status_frame = tk.Frame(self.video_source_frame)
        self.calibration_status_frame.grid(row=2, column=1)
        self.calibration_status_label = ttk.Label(
            self.calibration_status_frame, text="Status:")
        self.calibration_status_label.grid(row=1, column=1)
        self.calibration_status = ttk.Label(self.calibration_status_frame)
        self.calibration_status.grid(row=1, column=2)

        self.calibration_frame = ttk.LabelFrame(
            self.video_source_frame, text="Calibration")
        self.calibration_frame.grid(
            row=3, column=1, sticky=tk.E + tk.W + tk.N + tk.S, pady=5, padx=5)
        self.calibration_frame.grid_columnconfigure(1, weight=1)

        self.calibration_buttons_frame = tk.Frame(self.calibration_frame)
        self.calibration_buttons_frame.grid(row=1, column=1, pady=5)

        self.calibrate_button = tk.Button(
            self.calibration_buttons_frame, text="Calibrate", command=self.calibrate)
        self.calibrate_button.grid(row=1, column=1, padx=5)

        self.capture_images_button = tk.Button(
            self.calibration_buttons_frame, text="Capture Images", command=self.capture_images)
        self.capture_images_button.grid(row=1, column=2, padx=5)

        self.reset_button = tk.Button(
            self.calibration_buttons_frame, text="Reset", command=self.reset)
        self.reset_button.grid(row=1, column=3, padx=5)

        self.calibration_image_count_label = ttk.Label(self.calibration_frame)
        self.calibration_image_count_label.grid(row=2, column=1)

        self.calibration_chessboard_parameters_frame = tk.Frame(
            self.calibration_frame)
        self.calibration_chessboard_parameters_frame.grid(
            row=3, column=1, pady=5)

        self.calibration_config = VideoSourceCalibrationConfig.persisted()

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

        self.export_coordinates_frame = ttk.LabelFrame(
            window, text="Coordinates Publish Server UDP")
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

        self.utils_frame = tk.Frame(window)
        self.utils_frame.grid(row=4, column=1, sticky=tk.S)

        self.save_button = ttk.Button(
            self.utils_frame, text="Save", command=self.save)
        self.save_button.grid(row=1, column=1)

        self.base_video_source_dir = '../assets/camera_calibration_data'
        self.base_cube_dir = '../assets/configs/marker_cubes'
        self.calibration = None
        self.cube_ids = []
        self.cube_ids_init()
        self.video_source_list = []
        self.refresh_video_sources()
        self.video_source_init()


    def single_marker_settings_selection(self):
        if self.single_marker_mode.get():
            self.marker_cube_mode.set(False)

            for child in self.single_marker_settings_frame.winfo_children():
                child.configure(state=tk.ACTIVE)

            for child in self.single_marker_buttons_frame.winfo_children():
                child.configure(state=tk.ACTIVE)

            for child in self.marker_cube_settings_frame.winfo_children():
                child.configure(state=tk.DISABLED)

            for child in self.cube_id_frame.winfo_children():
                child.configure(state=tk.DISABLED)

            for child in self.marker_cube_buttons_frame.winfo_children():
                child.configure(state=tk.DISABLED)
        else:
            self.single_marker_mode.set(True)

    def single_marker_settings_set(self):
        self.single_marker_length.set(self.single_marker_settings.marker_length)
        self.single_marker_id.set(self.single_marker_settings.marker_id)

    def single_marker_save(self):
        self.single_marker_settings.marker_length = self.single_marker_length.get()
        self.single_marker_settings.marker_id = self.single_marker_id.get()

        self.single_marker_settings.persist()

    def marker_cube_settings_selection(self):
        if self.marker_cube_mode.get():
            self.single_marker_mode.set(False)
            for child in self.marker_cube_settings_frame.winfo_children():
                child.configure(state=tk.ACTIVE)

            for child in self.cube_id_frame.winfo_children():
                child.configure(state=tk.ACTIVE)

            for child in self.marker_cube_buttons_frame.winfo_children():
                child.configure(state=tk.ACTIVE)

            for child in self.single_marker_settings_frame.winfo_children():
                child.configure(state=tk.DISABLED)

            for child in self.single_marker_buttons_frame.winfo_children():
                child.configure(state=tk.DISABLED)
        else:
            self.marker_cube_mode.set(True)

    def cube_ids_init(self):
        for cube_id in os.listdir(self.base_cube_dir):
            self.cube_ids.append(cube_id.split(".")[0])

        self.cube_id_selection['values'] = self.cube_ids
        
        if len(self.cube_ids) > 0:
            self.cube_id_selection.current(0)
            self.marker_cube_settings = MarkersCubeDetectionSettings.persisted(self.cube_id_selection.get())
            self.marker_cube_settings_set()
        else:
            self.cube_id_selection.set("")

    def cube_id_selected(self, _=None):
        self.marker_cube_settings = MarkersCubeDetectionSettings.persisted(self.cube_id_selection.get())
        self.marker_cube_settings_set()
        self.cube_id_selection['state'] = 'readonly'

    def add_cube_id(self):
        if self.cube_ids.__contains__(""):
            self.cube_ids.remove("")

        self.cube_ids.append("")
        self.cube_id_selection['values'] = self.cube_ids
        self.cube_id_selection.current(len(self.cube_ids) - 1)
        self.cube_id_selected()
        self.cube_id_selection['state'] = 'normal'

    def marker_cube_settings_set(self):
        self.cube_main_marker_id.set(self.marker_cube_settings.main_marker_id)
        self.cube_side_marker_1.set(self.marker_cube_settings.other_marker_ids[0])
        self.cube_side_marker_2.set(self.marker_cube_settings.other_marker_ids[1])
        self.cube_side_marker_3.set(self.marker_cube_settings.other_marker_ids[2])
        self.cube_side_marker_4.set(self.marker_cube_settings.other_marker_ids[3])
        self.cube_markers_length.set(self.marker_cube_settings.markers_length)

    def marker_cube_map(self):
        detection = MarkerCubeMapping(self.cube_id_selection.get(),self.get_video_source_dir(),self.video_source.current(),
            self.cube_markers_length.get(), self.cube_main_marker_id.get(),
            [self.cube_side_marker_1.get(), self.cube_side_marker_2.get(), self.cube_side_marker_3.get(), self.cube_side_marker_4.get()])

        detection.map()
        self.marker_cube_settings = MarkersCubeDetectionSettings.persisted(self.cube_id_selection.get())
        self.cube_id_selection['state'] = 'readonly'

        if not self.cube_ids.__contains__(self.cube_id_selection.get()):
            self.cube_ids.append(self.cube_id_selection.get())
            self.cube_ids.remove("")
            self.cube_id_selection['values'] = self.cube_ids

    def marker_cube_delete(self):
        filename = '../assets/configs/marker_cubes/{}.pkl'.format(self.cube_id_selection.get())
        if  os.path.isfile(filename):
            os.remove(filename)

        if self.cube_ids.__contains__(self.cube_id_selection.get()):
            self.cube_ids.remove(self.cube_id_selection.get())
            self.cube_id_selection['values'] = self.cube_ids
        
        if len(self.cube_ids) > 0:
            self.cube_id_selection.current(0)
            self.marker_cube_settings_set()
        else:
            self.cube_id_selection.set("")
        
        self.cube_id_selected()

    def refresh_video_sources(self):
        try:
            self.video_source_list = video_device_listing.get_devices()
            self.video_source['values'] = self.video_source_list
            self.video_source.current(0)
            self.capture_images_button['state'] = tk.ACTIVE
        except SystemError:
            self.capture_images_button['state'] = tk.DISABLED

    def start_tracking(self):
        self.save_tracking_config()
        self.start_tracking_event.set()

        if not self.tracking_config.show_video:
            self.tracking_button['text'] = "Stop Tracking"
            self.tracking_button['command'] = self.stop_tracking

    def stop_tracking(self):
        self.stop_tracking_event.set()
        self.tracking_button['text'] = "Start Tracking"
        self.tracking_button['command'] = self.start_tracking

    def calibrate(self):
        self.save_calibration_config()
        self.calibration.run_calibration()
        self.update_calibration_status()

    def capture_images(self):
        self.calibration.acquire_calibration_images()
        self.update_calibration_images()

    def reset(self):
        self.calibration.delete_images()
        self.calibration.delete_calibration()
        self.update_calibration_status()
        self.update_calibration_images()

    def video_source_init(self, _=None):
        self.update_calibration_status()

        self.calibration = VideoSourceCalibration(
            self.get_video_source_dir(), self.video_source.current(), self.calibration_config)

        self.update_calibration_images()

    def update_calibration_status(self):
        if(self.check_video_source_calibration()):
            self.tracking_button['state'] = tk.ACTIVE
            self.calibration_status['text'] = "Calibrated!"
            self.calibration_status['foreground'] = "green"
        else:
            self.tracking_button['state'] = tk.DISABLED
            self.calibration_status['text'] = "Not calibrated!"
            self.calibration_status['foreground'] = "red"

    def update_calibration_images(self):
        if self.calibration.calibration_image_count < 30:
            self.calibrate_button['state'] = tk.DISABLED
            self.calibration_image_count_label['text'] = "Calibration images count: {}\nMinimum: 30".format(
                self.calibration.calibration_image_count)
            self.calibration_image_count_label['foreground'] = "red"
        else:
            self.calibrate_button['state'] = tk.ACTIVE
            self.calibration_image_count_label['text'] = "Calibration images count: {}".format(
                self.calibration.calibration_image_count)
            self.calibration_image_count_label['foreground'] = "green"

    def check_video_source_calibration(self):
        if not os.path.exists(self.get_video_source_dir()):
            return False

        cam_mtx_exists = os.path.isfile(
            '{}/cam_mtx.npy'.format(self.get_video_source_dir()))
        dist_exists = os.path.isfile(
            '{}/dist.npy'.format(self.get_video_source_dir()))

        return cam_mtx_exists & dist_exists

    def get_video_source_dir(self):
        camera_identification = self.video_source.get().replace(" ", "_")
        return '{}/{}'.format(self.base_video_source_dir, camera_identification)

    def save_tracking_config(self):
        self.tracking_config.device_number = self.video_source.current()
        self.tracking_config.device_parameters_dir = self.get_video_source_dir()
        self.tracking_config.show_video = self.show_video.get()
        self.tracking_config.server_ip = self.server_ip.get()
        self.tracking_config.server_port = self.server_port.get()
        
        marker_detection_settings = None
        if self.single_marker_mode.get():
            marker_detection_settings = self.single_marker_settings
        elif self.marker_cube_mode.get():
            marker_detection_settings = self.marker_cube_settings

        self.tracking_config.marker_detection_settings = marker_detection_settings

        self.tracking_config.persist()

    def save_calibration_config(self):
        self.calibration_config.chessboard_square_size = self.chessboard_square_size.get()

        self.calibration_config.persist()

    def save(self):
        self.save_tracking_config()
        self.save_calibration_config()


if __name__ == "__main__":
    multiprocessing.freeze_support()

    start_tracking_event = multiprocessing.Event()
    stop_tracking_event = multiprocessing.Event()

    tracking_scheduler_process = multiprocessing.Process(
        target=TrackingScheduler(start_tracking_event, stop_tracking_event).main)
    tracking_scheduler_process.start()

    tk_root = tk.Tk()
    App(start_tracking_event, stop_tracking_event, tk_root)
    tk_root.mainloop()

    tracking_scheduler_process.terminate()
