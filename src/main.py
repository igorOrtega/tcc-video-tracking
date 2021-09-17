import os
import tkinter as tk
from tkinter import ttk
import multiprocessing
import time
from PIL import ImageTk, Image
import socket
import numpy as np
from video_source_calibration import VideoSourceCalibration, VideoSourceCalibrationConfig
from tracking import TrackingScheduler, TrackingCofig
from marker_detection_settings import CUBE_DETECTION, SINGLE_DETECTION, SingleMarkerDetectionSettings, MarkersCubeDetectionSettings, MarkerCubeMapping
import video_device_listing


class App():

    def __init__(self, start_tracking, stop_tracking, window):
        self.start_tracking_event = start_tracking
        self.stop_tracking_event = stop_tracking
        self.saving_error = False

        window.title("AR Tracking Interface")

        width = 500
        height = 360
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

        tabControl = ttk.Notebook(window)
        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)
        tab3 = ttk.Frame(tabControl)

        tabControl.add(tab1, text="Camera")
        tabControl.add(tab2, text="Tracking Configuration")
        tabControl.add(tab3, text="Tracking")
        tabControl.pack(fill="both")

        self.video_source_frame = ttk.LabelFrame(
            tab1, text="Video Source")
        self.video_source_frame.place(relx=0.5, rely=0.5, anchor='center')
        self.video_source_frame.grid_columnconfigure(1, weight=1)

        self.refresh_video_sources_button = tk.Button(
            self.video_source_frame, text="Refresh Devices")
        self.refresh_video_sources_button['command'] = self.refresh_video_sources
        self.refresh_video_sources_button.grid(row=1, column=1, pady=5)

        self.video_source = ttk.Combobox(
            self.video_source_frame, state="readonly", height=4, width=25)
        self.video_source.bind('<<ComboboxSelected>>',
                               self.video_source_init)
        self.video_source.grid(row=2, column=1, padx=5, pady=5)

        self.video_source_calibration_frame = ttk.LabelFrame(
            self.video_source_frame, text="Calibration")
        self.video_source_calibration_frame.grid(
            row=3, column=1, padx=5, pady=5)

        self.video_source_calibration_status_frame = tk.Frame(
            self.video_source_calibration_frame)
        self.video_source_calibration_status_frame.grid(
            row=1, column=1, padx=5, pady=5)

        self.calibration_status_label = ttk.Label(
            self.video_source_calibration_status_frame, text="Status:")
        self.calibration_status_label.grid(row=1, column=1)
        self.calibration_status = ttk.Label(
            self.video_source_calibration_status_frame)
        self.calibration_status.grid(row=1, column=2)

        self.calibration_chessboard_parameters_frame = tk.Frame(
            self.video_source_calibration_frame)
        self.calibration_chessboard_parameters_frame.grid(
            row=2, column=1, padx=5)

        self.calibration_config = VideoSourceCalibrationConfig.persisted()

        self.chessboard_square_size = tk.DoubleVar()
        self.chessboard_square_size.set(
            self.calibration_config.chessboard_square_size)
        self.chessboard_square_size_label = ttk.Label(
            self.calibration_chessboard_parameters_frame, text="Chessboard square size:")
        self.chessboard_square_size_label.grid(
            row=1, column=1)
        self.chessboard_square_size_entry = ttk.Entry(
            self.calibration_chessboard_parameters_frame, width=5,
            textvariable=self.chessboard_square_size)
        self.chessboard_square_size_entry.grid(row=1, column=2)

        self.calibration_buttons_frame = tk.Frame(
            self.video_source_calibration_frame)
        self.calibration_buttons_frame.grid(row=3, column=1, pady=5)

        self.calibrate_button = tk.Button(
            self.calibration_buttons_frame, text="Calibrate", command=self.calibrate)
        self.calibrate_button.grid(row=1, column=1, padx=5)

        self.calibrate_button = tk.Button(
            self.calibration_buttons_frame, text="Reset", command=self.reset_calibration)
        self.calibrate_button.grid(row=1, column=2, padx=5)

        self.configuration_frame = tk.Frame(tab2)
        self.configuration_frame.pack()

        self.configuration_frame.grid_columnconfigure(1, weight=1)
        self.configuration_frame.grid_columnconfigure(2, weight=1)

        self.tracking_config_frame = tk.Frame(
            self.configuration_frame)
        self.tracking_config_frame.grid(
            row=1, column=1, padx=5)

        self.tracking_config_frame.grid_columnconfigure(1, weight=1)
        self.tracking_config_frame.grid_rowconfigure(1, weight=1)
        self.tracking_config_frame.grid_rowconfigure(2, weight=1)
        self.tracking_config_frame.grid_rowconfigure(3, weight=1)

        self.tracking_config = TrackingCofig.persisted()

        self.detection_mode_frame = tk.LabelFrame(
            self.tracking_config_frame, text="Detection Mode")
        self.detection_mode_frame.grid(row=1, column=1, padx=5, pady=2)

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

        self.single_marker_save_button = tk.Button(
            self.single_marker_buttons_frame, text="Save", command=self.single_marker_save)
        self.single_marker_save_button.grid(row=1, column=1)

        self.marker_cube_frame = ttk.LabelFrame(
            self.detection_mode_frame, text="Marker Cube")
        self.marker_cube_frame.grid(
            row=1, column=2, padx=5, pady=5)

        self.marker_cube_mode = tk.BooleanVar()
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

        self.new_cube_id_button = tk.Button(
            self.cube_id_frame, text="New", command=self.add_cube_id)
        self.new_cube_id_button.grid(row=1, column=2, padx=5)

        self.marker_cube_settings_frame = tk.Frame(
            self.marker_cube_frame)
        self.marker_cube_settings_frame.grid(
            row=3, column=1, padx=5, pady=5)

        self.cube_up_marker_id = tk.IntVar()
        self.cube_up_marker_id_label = ttk.Label(
            self.marker_cube_settings_frame, text="Up Marker ID:")
        self.cube_up_marker_id_label.grid(
            row=1, column=1, sticky=tk.W + tk.N)
        self.cube_up_marker_id_entry = ttk.Entry(
            self.marker_cube_settings_frame, textvariable=self.cube_up_marker_id, width=5)
        self.cube_up_marker_id_entry.grid(row=1, column=2, sticky=tk.W)

        self.cube_side_marker_ids_label = ttk.Label(
            self.marker_cube_settings_frame, text="Side Marker IDS:")
        self.cube_side_marker_ids_label.grid(
            row=2, column=1, sticky=tk.W + tk.N)

        self.cube_side_marker_1 = tk.IntVar()
        self.cube_side_marker_1_entry = ttk.Entry(
            self.marker_cube_settings_frame, textvariable=self.cube_side_marker_1, width=5)
        self.cube_side_marker_1_entry.grid(row=2, column=2, sticky=tk.W)
        self.cube_side_marker_2 = tk.StringVar()
        self.cube_side_marker_2_entry = ttk.Entry(
            self.marker_cube_settings_frame, textvariable=self.cube_side_marker_2, width=5)
        self.cube_side_marker_2_entry.grid(row=2, column=3, sticky=tk.W)
        self.cube_side_marker_3 = tk.StringVar()
        self.cube_side_marker_3_entry = ttk.Entry(
            self.marker_cube_settings_frame, textvariable=self.cube_side_marker_3, width=5)
        self.cube_side_marker_3_entry.grid(row=2, column=4, sticky=tk.W)
        self.cube_side_marker_4 = tk.StringVar()
        self.cube_side_marker_4_entry = ttk.Entry(
            self.marker_cube_settings_frame, textvariable=self.cube_side_marker_4, width=5)
        self.cube_side_marker_4_entry.grid(row=2, column=5, sticky=tk.W)

        self.cube_down_marker_id = tk.StringVar()
        self.cube_down_marker_id_label = ttk.Label(
            self.marker_cube_settings_frame, text="Down Marker ID:")
        self.cube_down_marker_id_label.grid(
            row=3, column=1, sticky=tk.W + tk.N)
        self.cube_down_marker_id_entry = ttk.Entry(
            self.marker_cube_settings_frame, textvariable=self.cube_down_marker_id, width=5)
        self.cube_down_marker_id_entry.grid(row=3, column=2, sticky=tk.W)

        self.cube_markers_length = tk.DoubleVar()
        self.cube_markers_length_label = ttk.Label(
            self.marker_cube_settings_frame, text="Markers length:")
        self.cube_markers_length_label.grid(
            row=4, column=1, pady=5)
        self.cube_markers_length_entry = ttk.Entry(
            self.marker_cube_settings_frame, textvariable=self.cube_markers_length, width=5)
        self.cube_markers_length_entry.grid(row=4, column=2, sticky=tk.W)

        self.marker_cube_buttons_frame = tk.Frame(
            self.marker_cube_frame)
        self.marker_cube_buttons_frame.grid(
            row=4, column=1, padx=5, pady=5)

        self.marker_cube_id_map_button = tk.Button(
            self.marker_cube_buttons_frame, text="Map and Save", command=self.marker_cube_map)
        self.marker_cube_id_map_button.grid(row=1, column=1, padx=5)

        self.marker_cube_id_delete_button = tk.Button(
            self.marker_cube_buttons_frame, text="Delete", command=self.marker_cube_delete)
        self.marker_cube_id_delete_button.grid(row=1, column=2, padx=5)

        self.single_marker_settings = SingleMarkerDetectionSettings.persisted()
        self.single_marker_settings_set()

        self.marker_cube_settings = MarkersCubeDetectionSettings.persisted(
            self.cube_id_selection.current())
        self.marker_cube_settings_set()

        if self.tracking_config.marker_detection_settings is None or self.tracking_config.marker_detection_settings.identifier == SINGLE_DETECTION:
            self.single_marker_mode.set(True)
            self.single_marker_settings_selection()
        elif self.tracking_config.marker_detection_settings.identifier == CUBE_DETECTION:
            self.marker_cube_mode.set(True)
            self.marker_cube_settings_selection()

        self.translation_offset_frame = ttk.LabelFrame(
            self.tracking_config_frame, text="Translation Offset")
        self.translation_offset_frame.grid(row=2, column=1, pady=5)

        self.translation_offset_x = tk.DoubleVar()
        self.translation_offset_x.set(
            self.tracking_config.translation_offset[0][3])
        self.translation_offset_x_label = ttk.Label(
            self.translation_offset_frame, text="X", foreground="red")
        self.translation_offset_x_label.grid(row=1, column=1, pady=5)
        self.translation_offset_x_entry = ttk.Entry(
            self.translation_offset_frame, textvariable=self.translation_offset_x, width=5)
        self.translation_offset_x_entry.grid(
            row=1, column=2, sticky=tk.W, padx=5)

        self.translation_offset_y = tk.DoubleVar()
        self.translation_offset_y.set(
            self.tracking_config.translation_offset[1][3])
        self.translation_offset_y_label = ttk.Label(
            self.translation_offset_frame, text="Y", foreground="green")
        self.translation_offset_y_label.grid(row=1, column=3, pady=5)
        self.translation_offset_y_entry = ttk.Entry(
            self.translation_offset_frame, textvariable=self.translation_offset_y, width=5)
        self.translation_offset_y_entry.grid(
            row=1, column=4, sticky=tk.W, padx=5)

        self.translation_offset_z = tk.DoubleVar()
        self.translation_offset_z.set(
            self.tracking_config.translation_offset[2][3])
        self.translation_offset_z_label = ttk.Label(
            self.translation_offset_frame, text="Z", foreground="blue")
        self.translation_offset_z_label.grid(row=1, column=5, pady=5)
        self.translation_offset_z_entry = ttk.Entry(
            self.translation_offset_frame, textvariable=self.translation_offset_z, width=5)
        self.translation_offset_z_entry.grid(
            row=1, column=6, sticky=tk.W, padx=5)

        self.publishing_config_frame = tk.Frame(tab3)
        self.publishing_config_frame.place(relx=0.5, rely=0.5, anchor='center')

        self.export_coordinates_frame = ttk.LabelFrame(
            self.publishing_config_frame, text="Coordinates Publish Server UDP")
        self.export_coordinates_frame.grid(row=0, column=1, pady=5)

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

        self.export_video_frame = ttk.LabelFrame(
            self.publishing_config_frame, text="Video Publish Server UDP")
        self.export_video_frame.grid(row=1, column=1, pady=5)

        self.export_video_input_frame = tk.Frame(
            self.export_video_frame)
        self.export_video_input_frame.grid(
            row=1, column=1, padx=5, pady=5)

        self.video_server_ip = tk.StringVar()
        self.video_server_ip.set(self.tracking_config.video_server_ip)
        self.video_server_ip_label = ttk.Label(
            self.export_video_input_frame, text="IP Address:")
        self.video_server_ip_label.grid(row=1, column=1)
        self.video_server_ip_entry = ttk.Entry(
            self.export_video_input_frame, textvariable=self.video_server_ip, width=15)
        self.video_server_ip_entry.grid(row=1, column=2)

        self.video_server_port = tk.StringVar()
        self.video_server_port.set(self.tracking_config.video_server_port)
        self.video_server_port_label = ttk.Label(
            self.export_video_input_frame, text="Port:")
        self.video_server_port_label.grid(row=1, column=3)
        self.video_server_port_entry = ttk.Entry(
            self.export_video_input_frame, textvariable=self.video_server_port, width=7)
        self.video_server_port_entry.grid(row=1, column=4)

        self.export_coordinates_websocket_frame = ttk.LabelFrame(
            self.publishing_config_frame, text="Coordinates Publish Server Web")
        self.export_coordinates_websocket_frame.grid(row=2, column=1, pady=5)

        self.export_coordinates_input_websocket_frame = tk.Frame(
            self.export_coordinates_websocket_frame)
        self.export_coordinates_input_websocket_frame.grid(
            row=1, column=1, padx=5, pady=5)

        self.websocket_server_ip = tk.StringVar()
        self.websocket_server_ip.set(self.tracking_config.websocket_server_ip)
        self.websocket_server_ip_label = ttk.Label(
            self.export_coordinates_input_websocket_frame, text="IP Address:")
        self.websocket_server_ip_label.grid(row=1, column=1)
        self.websocket_server_ip_entry = ttk.Entry(
            self.export_coordinates_input_websocket_frame, textvariable=self.websocket_server_ip, width=15)
        self.websocket_server_ip_entry.grid(row=1, column=2)

        self.websocket_server_port = tk.StringVar()
        self.websocket_server_port.set(self.tracking_config.websocket_server_port)
        self.websocket_server_port_label = ttk.Label(
            self.export_coordinates_input_websocket_frame, text="Port:")
        self.websocket_server_port_label.grid(row=1, column=3)
        self.websocket_server_port_entry = ttk.Entry(
            self.export_coordinates_input_websocket_frame, textvariable=self.websocket_server_port, width=7)
        self.websocket_server_port_entry.grid(row=1, column=4)

        self.export_video_websocket_frame = ttk.LabelFrame(
            self.publishing_config_frame, text="Video Publish Server Web")
        self.export_video_websocket_frame.grid(row=3, column=1, pady=5)

        self.export_video_input_websocket_frame = tk.Frame(
            self.export_video_websocket_frame)
        self.export_video_input_websocket_frame.grid(
            row=1, column=1, padx=5, pady=5)

        self.websocket_video_server_ip = tk.StringVar()
        self.websocket_video_server_ip.set(self.tracking_config.websocket_video_server_ip)
        self.websocket_video_server_ip_label = ttk.Label(
            self.export_video_input_websocket_frame, text="IP Address:")
        self.websocket_video_server_ip_label.grid(row=1, column=1)
        self.websocket_video_server_ip_entry = ttk.Entry(
            self.export_video_input_websocket_frame, textvariable=self.websocket_video_server_ip, width=15)
        self.websocket_video_server_ip_entry.grid(row=1, column=2)

        self.websocket_video_server_port = tk.StringVar()
        self.websocket_video_server_port.set(self.tracking_config.websocket_video_server_port)
        self.websocket_video_server_port_label = ttk.Label(
            self.export_video_input_websocket_frame, text="Port:")
        self.websocket_video_server_port_label.grid(row=1, column=3)
        self.websocket_video_server_port_entry = ttk.Entry(
            self.export_video_input_websocket_frame, textvariable=self.websocket_video_server_port, width=7)
        self.websocket_video_server_port_entry.grid(row=1, column=4)

        self.show_video = tk.BooleanVar()
        self.show_video.set(self.tracking_config.show_video)
        self.show_video_checkbox = tk.Checkbutton(
            self.publishing_config_frame, text="Show video", variable=self.show_video)
        self.show_video_checkbox.grid(row=4, column=1, pady=5)

        self.tracking_button = tk.Button(
            self.publishing_config_frame, text="Start Tracking", command=self.start_tracking)
        self.tracking_button.grid(row=5, column=1, sticky=tk.N)

        self.menu_bar = tk.Menu(window)
        self.menu_help = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_help.add_command(label="About", command=self.create_about_window)
        self.menu_bar.add_cascade(label="Help", menu=self.menu_help)

        window.config(menu=self.menu_bar)

        self.base_video_source_dir = '../assets/camera_calibration_data'
        self.base_cube_dir = '../assets/configs/marker_cubes'
        self.base_img_dir = '../images'
        self.calibration = None
        self.cube_ids = []
        self.cube_ids_init()
        self.video_source_list = []
        self.refresh_video_sources()
        self.video_source_init()
        self.icon_img = ImageTk.PhotoImage(Image.open("{}/error_icon.png".format(self.base_img_dir)))

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
        self.single_marker_length.set(
            self.single_marker_settings.marker_length)
        self.single_marker_id.set(self.single_marker_settings.marker_id)

    def single_marker_save(self):
        try:
            self.single_marker_settings.marker_length = self.single_marker_length.get()
            self.single_marker_settings.marker_id = self.single_marker_id.get()

            self.single_marker_settings.persist()
            self.saving_error = False
        except tk.TclError:
            self.saving_error = True
            error_window = tk.Toplevel()
            error_window.title("Saving Error")
            error_window.grab_set()
            error_window.resizable(0, 0)

            error_window.columnconfigure([0, 1], minsize=50, weight=1)
            error_window.rowconfigure([0, 1], minsize=50, weight=1)
            
            error_title = tk.Label(master=error_window, text="Insufficient data to save marker ID and length", fg="blue", font=("Arial", 18))
            error_title.grid(row=0, column=1, sticky="w")

            icon_label = tk.Label(master=error_window, image=self.icon_img, width=80, height=80)
            icon_label.grid(row=0, column=0)

            self.example_img = ImageTk.PhotoImage(Image.open("{}/saving_marker_example.png".format(self.base_img_dir)))
            example_label = tk.Label(master=error_window, image=self.example_img, width=170, height=170)
            example_label.grid(row=2, column=1)
            
            error_message = tk.Label(master=error_window, text="To save the marker it is necessary to fill in both Marker ID and Marker length slots. \nIn order to solve this problem, fill in the Marker ID slot with the marker ID and fill in the Marker length slot with the marker side length like in the example bellow.",
                                    justify="left", font=("Arial", 11),)
            error_message.grid(row=1, column=1)

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
            self.marker_cube_settings = MarkersCubeDetectionSettings.persisted(
                self.cube_id_selection.get())
            self.marker_cube_settings_set()
        else:
            self.cube_id_selection.set("")

    def cube_id_selected(self, _=None):
        self.marker_cube_settings = MarkersCubeDetectionSettings.persisted(
            self.cube_id_selection.get())
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
        self.cube_up_marker_id.set(self.marker_cube_settings.up_marker_id)
        self.cube_side_marker_1.set(
            self.marker_cube_settings.side_marker_ids[0])
        self.cube_side_marker_2.set(
            self.marker_cube_settings.side_marker_ids[1])
        self.cube_side_marker_3.set(
            self.marker_cube_settings.side_marker_ids[2])
        self.cube_side_marker_4.set(
            self.marker_cube_settings.side_marker_ids[3])
        self.cube_down_marker_id.set(self.marker_cube_settings.down_marker_id)
        self.cube_markers_length.set(self.marker_cube_settings.markers_length)

    def marker_cube_map(self):
        try:
            detection = MarkerCubeMapping(self.cube_id_selection.get(), self.get_video_source_dir(), self.video_source.current(),
                                        self.cube_markers_length.get(), self.cube_up_marker_id.get(),
                                        [self.cube_side_marker_1.get(), self.cube_side_marker_2.get(
                                        ), self.cube_side_marker_3.get(), self.cube_side_marker_4.get()],
                                        self.cube_down_marker_id.get())

            detection.map()
            self.marker_cube_settings = MarkersCubeDetectionSettings.persisted(
                self.cube_id_selection.get())
            self.cube_id_selection['state'] = 'readonly'

            if not self.cube_ids.__contains__(self.cube_id_selection.get()):
                self.cube_ids.append(self.cube_id_selection.get())

                if self.cube_ids.__contains__(""):
                    self.cube_ids.remove("")

                self.cube_id_selection['values'] = self.cube_ids
        except tk.TclError:
            error_window = tk.Toplevel()
            error_window.title("Mapping Error")
            error_window.grab_set()
            error_window.resizable(0, 0)

            error_window.columnconfigure([0, 1], minsize=50, weight=1)
            error_window.rowconfigure([0, 1], minsize=50, weight=1)
            
            error_title = tk.Label(master=error_window, text="Insufficient data to start cube mapping", fg="blue", font=("Arial", 18))
            error_title.grid(row=0, column=1, sticky="w")
            
            icon_label = tk.Label(master=error_window, image=self.icon_img, width=80, height=80)
            icon_label.grid(row=0, column=0)
            
            self.example_img = ImageTk.PhotoImage(Image.open("{}/mapping_example.png".format(self.base_img_dir)))
            example_label = tk.Label(master=error_window, image=self.example_img)
            example_label.grid(row=2, column=1)
            
            error_message = tk.Label(master=error_window, text="This problem occurred because it is necessary to fill in at least the Up Marker ID slot, the first Side Marker ID slot and the Markers length slot. \nTo solve the problem, fill in at least these three slots. The first two with markers IDs and the last one with the markers length like in the example bellow.",
                                    justify="left", font=("Arial", 11),)
            error_message.grid(row=1, column=1)

    def marker_cube_delete(self):
        filename = '../assets/configs/marker_cubes/{}.pkl'.format(
            self.cube_id_selection.get())
        if os.path.isfile(filename):
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
        except SystemError:
            pass

    def start_tracking(self):
        try:
            self.save_tracking_config()
            self.single_marker_save()
            if not self.saving_error:
                self.start_tracking_event.set()

                if not self.tracking_config.show_video:
                    self.tracking_button['text'] = "Stop Tracking"
                    self.tracking_button['command'] = self.stop_tracking
        except socket.error:
            error_window = tk.Toplevel()
            error_window.title("IP Error")
            error_window.grab_set()
            error_window.resizable(0, 0)

            error_window.columnconfigure([0, 1], minsize=50, weight=1)
            error_window.rowconfigure([0, 1], minsize=50, weight=1)
            
            error_title = tk.Label(master=error_window, text="IP Address is incorrect", fg="blue", font=("Arial", 18))
            error_title.grid(row=0, column=1, sticky="w")

            icon_label = tk.Label(master=error_window, image=self.icon_img, width=80, height=80)
            icon_label.grid(row=0, column=0)
            
            self.example_img = ImageTk.PhotoImage(Image.open("{}/IP_address_example.png".format(self.base_img_dir)))
            example_label = tk.Label(master=error_window, image=self.example_img, width=200, height=70)
            example_label.grid(row=2, column=1)
            
            error_message = tk.Label(master=error_window, text="This problem occurred because the IP Address slot is blank or contains an address that does not exist. \nIf the slot is empty, fill it in with an existing IP address to solve the problem. \nIf the slot is not blank, AR Tracking was not able to connect to the address you filled in because the address is not available. Check for any spelling mistakes. \nAn example of IP address is given below.",
                                     justify="left", font=("Arial", 11),)
            error_message.grid(row=1, column=1)
        except ValueError:
            error_window = tk.Toplevel()
            error_window.title("Port Error")
            error_window.grab_set()
            error_window.resizable(0, 0)

            error_window.columnconfigure([0, 1], minsize=50, weight=1)
            error_window.rowconfigure([0, 1], minsize=50, weight=1)
            
            error_title = tk.Label(master=error_window, text="Port is incorrect", fg="blue", font=("Arial", 18))
            error_title.grid(row=0, column=1, sticky="w")

            icon_label = tk.Label(master=error_window, image=self.icon_img, width=80, height=80)
            icon_label.grid(row=0, column=0)
            
            self.example_img = ImageTk.PhotoImage(Image.open("{}/port_example.png".format(self.base_img_dir)))
            example_label = tk.Label(master=error_window, image=self.example_img, width=270, height=80)
            example_label.grid(row=2, column=1)

            error_message = tk.Label(master=error_window, text="This problem occurred because the Port slot is blank or contains letters instead of numbers. \nTo solve this problem, fill in the Port slot with a valid port number like in the example below.",
                                     justify="left", font=("Arial", 11),)
            error_message.grid(row=1, column=1)
        except tk.TclError:
            error_window = tk.Toplevel()
            error_window.title("Tracking Error")
            error_window.grab_set()
            error_window.resizable(0, 0)

            error_window.columnconfigure([0, 1], minsize=50, weight=1)
            error_window.rowconfigure([0, 1], minsize=50, weight=1)

            error_title = tk.Label(master=error_window, text="Translation Offset slots are blank", fg="blue", font=("Arial", 18))
            error_title.grid(row=0, column=1, sticky="w")

            icon_label = tk.Label(master=error_window, image=self.icon_img, width=80, height=80)
            icon_label.grid(row=0, column=0)
            
            self.example_img = ImageTk.PhotoImage(Image.open("{}/translation_offset_example.png".format(self.base_img_dir)))
            example_label = tk.Label(master=error_window, image=self.example_img, width=200, height=70)
            example_label.grid(row=2, column=1)

            error_message = tk.Label(master=error_window, text="To solve this problem fill in the three slots inside the Translation Offset section with the desired distance offset. \nAn example is given bellow.",
                                     justify="left", font=("Arial", 11),)
            error_message.grid(row=1, column=1)

    def stop_tracking(self):
        self.stop_tracking_event.set()
        self.tracking_button['text'] = "Start Tracking"
        self.tracking_button['command'] = self.start_tracking

    def calibrate(self):
        try:    
            self.save_calibration_config()
            self.calibration.calibrate()
            self.update_calibration_status()
        except tk.TclError:
            error_window = tk.Toplevel()
            error_window.title("Calibration Error")
            error_window.grab_set()
            error_window.resizable(0, 0)
            error_window.columnconfigure([0, 1], minsize=50, weight=1)
            error_window.rowconfigure([0, 1], minsize=50, weight=1)

            error_title = tk.Label(master=error_window, text="Chessboard square size is incorrect", fg="blue", font=("Arial", 18))
            error_title.grid(row=0, column=1, sticky="w")

            icon_label = tk.Label(master=error_window, image=self.icon_img, width=80, height=80)
            icon_label.grid(row=0, column=0)
            
            self.example_img = ImageTk.PhotoImage(Image.open("{}/calibration_example.png".format(self.base_img_dir)))
            example_label = tk.Label(master=error_window, image=self.example_img, width=200, height=130)
            example_label.grid(row=2, column=1)

            error_message = tk.Label(master=error_window, text="This problem occurred because the Cheesboard Square size slot is blank or contains letters instead of numbers. \nIn order to start the calibration, it is necessary to fill in the Chessboard Square size slot with the chessboard square side length like in the example below.",
                                     justify="left", font=("Arial", 11))
            error_message.grid(row=1, column=1)

    def reset_calibration(self):
        self.calibration.delete_calibration()
        self.update_calibration_status()

    def video_source_init(self, _=None):
        self.update_calibration_status()

        self.calibration = VideoSourceCalibration(
            self.get_video_source_dir(), self.video_source.current(), self.calibration_config)

    def update_calibration_status(self):
        if(self.check_video_source_calibration()):
            self.tracking_button['state'] = tk.ACTIVE
            self.calibration_status['text'] = "Calibrated!"
            self.calibration_status['foreground'] = "green"
        elif(self.check_default_calibration()):
            self.tracking_button['state'] = tk.ACTIVE
            self.calibration_status['text'] = "Default Calibration"
            self.calibration_status['foreground'] = "green"
        else:
            self.tracking_button['state'] = tk.DISABLED
            self.calibration_status['text'] = "Not calibrated!"
            self.calibration_status['foreground'] = "red"

    def check_video_source_calibration(self):
        if os.path.exists(self.get_video_source_dir()):
            cam_mtx_exists = os.path.isfile(
                '{}/cam_mtx.npy'.format(self.get_video_source_dir()))
            dist_exists = os.path.isfile(
                '{}/dist.npy'.format(self.get_video_source_dir()))
        else:
            return False

        return cam_mtx_exists & dist_exists
    
    def check_default_calibration(self):
        if os.path.exists('../assets/camera_calibration_data/Default_calibration'):
            cam_mtx_exists = os.path.isfile(
                '../assets/camera_calibration_data/Default_calibration/cam_mtx.npy')
            dist_exists = os.path.isfile(
                '../assets/camera_calibration_data/Default_calibration/dist.npy')
        else:
            return False

        return cam_mtx_exists & dist_exists 

    def get_video_source_dir(self):
        camera_identification = self.video_source.get().replace(" ", "_")
        return '{}/{}'.format(self.base_video_source_dir, camera_identification)

    def save_tracking_config(self):
        self.tracking_config.device_number = self.video_source.current()
        self.tracking_config.device_parameters_dir = self.get_video_source_dir()
        self.tracking_config.show_video = self.show_video.get()
        if self.server_ip.get() != "localhost":
            socket.inet_aton(self.server_ip.get())
        self.tracking_config.server_ip = self.server_ip.get()
        int(self.server_port.get())
        self.tracking_config.server_port = self.server_port.get()
        if self.video_server_ip.get() != "localhost":
            socket.inet_aton(self.video_server_ip.get())
        self.tracking_config.video_server_ip = self.video_server_ip.get()
        int(self.video_server_port.get())
        self.tracking_config.video_server_port = self.video_server_port.get()
        if self.websocket_server_ip.get() != "localhost":
            socket.inet_aton(self.websocket_server_ip.get())
        self.tracking_config.websocket_server_ip = self.websocket_server_ip.get()
        int(self.websocket_server_port.get())
        self.tracking_config.websocket_server_port = self.websocket_server_port.get()
        if self.websocket_video_server_ip.get() != "localhost":
            socket.inet_aton(self.websocket_video_server_ip.get())
        self.tracking_config.websocket_video_server_ip = self.websocket_video_server_ip.get()
        int(self.websocket_video_server_port.get())
        self.tracking_config.websocket_video_server_port = self.websocket_video_server_port.get()

        marker_detection_settings = None
        if self.single_marker_mode.get():
            marker_detection_settings = self.single_marker_settings
        elif self.marker_cube_mode.get():
            marker_detection_settings = self.marker_cube_settings

        self.tracking_config.marker_detection_settings = marker_detection_settings

        offset_matrix = np.zeros(shape=(4, 4))
        offset_matrix[0][0] = 1
        offset_matrix[1][1] = 1
        offset_matrix[2][2] = 1
        offset_matrix[0][3] = self.translation_offset_x.get()
        offset_matrix[1][3] = self.translation_offset_y.get()
        offset_matrix[2][3] = self.translation_offset_z.get()
        offset_matrix[3][3] = 1
        self.tracking_config.translation_offset = offset_matrix

        self.tracking_config.persist()

    def save_calibration_config(self):
        self.calibration_config.chessboard_square_size = self.chessboard_square_size.get()
        self.calibration_config.persist()

    def create_about_window(self):
        about_window = tk.Toplevel()
        about_window.title("About")
        about_window.grab_set()
        about_window.resizable(0, 0)
        version_label = tk.Label(master=about_window, text='Version: 0.00.0')
        version_label.grid(sticky='nw')
        credits_label = tk.Label(master=about_window, text='Credits: Igor Ortega\n              Lucca Catalan de Freitas Reis Viana\n              Vitor Santos', justify='left')
        credits_label.grid(sticky='nw')

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

    stop_tracking_event.set()
    time.sleep(1)
    tracking_scheduler_process.terminate()
