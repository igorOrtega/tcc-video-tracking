import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import cv2.aruco as aruco
from tracking import ArucoTracking, ArucoTrackingCofig

class Counter_program():
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("AR Tracking Interface")
        self.create_widgets()
        self.window.geometry("{}x{}+{}+{}".format(600, 300, 300, 80))            
        self.combobox_value = tk.StringVar()

    def start_tracking(self):
        config = ArucoTrackingCofig(
            2.5, aruco.DICT_6X6_250, 'localhost', 10000)
        tracking = ArucoTracking(config)
        tracking.single_marker_tracking(0, True)

#_-----------------------------------------------
    def Calibrate(self):
        return 0
   
    def Capture(self):
        return 0
# -----------------------------------------------
    def create_widgets(self):
        # Create some room around all the internal frames
        self.window['padx'] = 5
        self.window['pady'] = 5

        # - - - - - - - - - - - - - - - - - - - - -
        # The Commands frame
        # cmd_frame = ttk.LabelFrame(self.window, text="Commands", padx=5, pady=5, relief=tk.RIDGE)
        cmd_frame = ttk.LabelFrame(self.window, text="AR Tracking - TCC", relief=tk.RIDGE)
        cmd_frame.grid(row=1,column = 1, sticky = "nsew", columnspan = 2)
        self.window.grid_rowconfigure(2, weight = 1)


        my_button = tk.Button(cmd_frame, text="Start Tracking")
        my_button['command']=self.start_tracking
        my_button.grid(row=1, column=2)

        combobox_label = tk.Label(cmd_frame, text="Webcams")
        combobox_label.grid(row=2, column=1, sticky=tk.W + tk.N)
        self.combobox_value = tk.StringVar()
        my_combobox = ttk.Combobox(cmd_frame, height=4, textvariable=self.combobox_value)
        my_combobox.grid(row=2, column=2)
        my_combobox['values'] = ("web1", "web2", "web3", "web4")
        my_combobox.current(0)

        # - - - - - - - - - - - - - - - - - - - - -
        # The tracking config entry frame
        entry_frame = ttk.LabelFrame(self.window, text="Tracking Configuration",
                                     relief=tk.RIDGE)
        entry_frame.grid(row=2, column=1, sticky=tk.E + tk.W + tk.N + tk.S)

        marker_type_label = ttk.Label(entry_frame, text = "Marker Type:")
        marker_type_label.grid(row = 1, column =1, sticky = tk.W + tk.N)
        my_marker_type = ttk.Entry(entry_frame, width=10)
        my_marker_type.grid(row=2, column=2, sticky=tk.W, pady=3, rowspan = 2)

        marker_size_label = ttk.Label(entry_frame, text="Marker size (cm):")
        marker_size_label.grid(row=4, column=1, sticky=tk.W + tk.N)
        my_marker_size = ttk.Entry(entry_frame, width=10)
        my_marker_size.grid(row=1, column=2, sticky=tk.W, pady=3)
        
        export_add_label = ttk.Label(entry_frame, text="Export address:")
        export_add_label.grid(row=7, column=1, sticky=tk.W + tk.N)

        port_label = ttk.Label(entry_frame, text = "Port:")
        port_label.grid(row=7, column=3, sticky=tk.W + tk.N)

        port_label_add = ttk.Entry(entry_frame, width = 5)
        port_label_add.grid(row=7, column = 4, sticky = tk.W + tk.N)



        #my_text = tk.Text(entry_frame, height=5, width=30)
        #my_text.grid(row=2, column=2)
        #my_text.insert(tk.END, "An example of multi-line\ninput")

    # - - - - - - - - - - - - - - - - - - - - -
        # The calibration config frame
        calib_config_frame = ttk.LabelFrame(self.window, text="Calibration Configuration", relief=tk.RIDGE, padding=6)
        calib_config_frame.grid(row=2, column=3, padx=6, sticky=tk.E + tk.W + tk.N + tk.S, columnspan = 2)

        chess_label = ttk.Label(calib_config_frame, text="Chessboard square size (cm):")
        chess_label.grid(row=1, rowspan=2, column=1, sticky=tk.W + tk.N)
        chess_label_add = ttk.Entry(calib_config_frame, width = 5)
        chess_label_add.grid(row=1, column = 3)

        chess_column_label = ttk.Label(calib_config_frame, text="Chessboard column count:")
        chess_column_label.grid(row=3, rowspan=2, column=1, sticky=tk.W + tk.N)
        chess_column_add = ttk.Entry(calib_config_frame, width = 5)
        chess_column_add.grid(row=3, column = 3)

        chess_row_label = ttk.Label(calib_config_frame, text="Chessboard row count:")
        chess_row_label.grid(row=5, rowspan=2, column=1, sticky=tk.W + tk.N)
        chess_row_add = ttk.Entry(calib_config_frame, width = 5)
        chess_row_add.grid(row=5, column = 3)

        calib_img_count = ttk.Label(calib_config_frame, text = "Calibration image count:")
        calib_img_count.grid(row = 8, column = 1, rowspan = 3,  sticky=tk.W)



        #aqui
        calibrate_b = tk.Button(calib_config_frame, text="Calibrate")
        calibrate_b['command'] = self.Calibrate
        calibrate_b.grid(row=11, column=1)

        #aqui 2
        capture_img_b = tk.Button(calib_config_frame, text= "Capture Images")
        capture_img_b['command'] = self.Capture
        capture_img_b.grid(row = 12, column = 1)

        menubar = tk.Menu(self.window)

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open", command=filedialog.askopenfilename)
        filemenu.add_command(label="Save", command=filedialog.asksaveasfilename)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.window.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        self.window.config(menu=menubar)

        # - - - - - - - - - - - - - - - - - - - - -
        save_button = ttk.Button(self.window, text ="Salvar", command = filedialog.asksaveasfilename)
        save_button.grid(row = 1, column = 3)
        # Quit button in the lower right corner
        quit_button = ttk.Button(self.window, text="Sair", command=self.window.destroy)
        quit_button.grid(row=2, column=5)
        
# Create the entire GUI program
program = Counter_program()

# Start the GUI event loop
program.window.mainloop()
