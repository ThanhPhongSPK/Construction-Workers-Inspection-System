import sys
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QTimer, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, \
    QFileDialog, QLabel, QStackedWidget, QGroupBox
from PyQt5.QtGui import QPixmap, QImage, QFont
from ultralytics import YOLO
from Detection import detect_video, detect_image


class FinalTermProjectApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.title = "Final Term Project"
        self.left = 10
        self.top = 10
        self.width = 1920
        self.height = 1080
        self.initUI()

        font = QFont('San Francisco', 12)
        self.setFont(font)

        #
        self.model = YOLO('runs/detect/yolov8m.pt_train_120_epochs/weights/best.pt')
        self.image_path = None
        self.video_path = None
        self.mode = 'Normal'

        # Timer for video processing
        self.timer = QTimer(self)
        self.cap = None

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setStyleSheet("background-color: #f0f0f0;")

        # Central widget
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: white;")
        self.setCentralWidget(self.central_widget)

        # Horizontal layout for the whole area
        h_layout = QHBoxLayout()
        self.central_widget.setLayout(h_layout)

        # stacked widget to switch between image and video displays
        self.stacked_widget = QStackedWidget()
        h_layout.addWidget(self.stacked_widget)

        # image area label
        self.image_area = QLabel()
        self.image_area.setMinimumSize(1280, 720)
        self.image_area.setStyleSheet(
            "background-color: white; color: black; border: 2px solid lightgray; border-radius: 6px; padding: 10px;")
        self.image_area.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(self.image_area)

        # Video display area using QLabel
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(1280, 720)
        self.video_widget.setStyleSheet(
            "background-color: white; color: black; border: 2px solid lightgray; border-radius: 6px; padding: 10px;")
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)
        self.stacked_widget.addWidget(self.video_widget)

        # Setup QLabel for video output
        self.video_output_label = QLabel()  # Initialize QLabel
        self.video_output_label.setMinimumSize(1280, 720)  # Set a minimum size
        self.video_output_label.setStyleSheet(
            "background-color: black; color: black; border: 2px solid lightgray; border-radius: 6px; padding: 10px;")
        self.video_output_label.setAlignment(Qt.AlignCenter)  # Center alignment for the image
        self.stacked_widget.addWidget(self.video_output_label)  # Add QLabel to the stacked widget


        # Control panel with vertical layout
        self.control_panel = QVBoxLayout()
        h_layout.addLayout(self.control_panel)

        # Create buttons
        self.browse_button = QPushButton('🗂️ Browse')
        self.refresh_button = QPushButton('🔄 Refresh')
        self.start_detect_button = QPushButton('▶️ Start Detect')
        self.stop_detect_button = QPushButton('⏹️ Stop Detect')
        self.play_video_button = QPushButton('▶️ Play Video')
        self.pause_video_button = QPushButton('⏸️ Pause Video')

        control_panel_group = QGroupBox("Control Panel")  # Create a group box with title "Control Panel"
        control_panel_group.setStyleSheet(
            "QGroupBox { border: 2px solid lightgray; border-radius: 5px; margin-top: 20px; font-size: 16px; font-weight: bold } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; }")  # Style the group box

        control_panel_group.setFixedSize(610, 300)
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(1, 1, 1, 1)  # Set margins to be closer
        group_layout.setSpacing(1)  # Set spacing to be closer
        control_panel_group.setLayout(group_layout)
        self.control_panel.addWidget(control_panel_group)

        # Set styles and sizes for buttons
        for button in [self.browse_button, self.refresh_button, self.start_detect_button, self.stop_detect_button,
                       self.play_video_button, self.pause_video_button]:
            button.setFixedSize(150, 80)

            if button in [self.start_detect_button]:
                # green for Start Detect
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #19692c); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #19692c, stop:1 #0f421a);}")
            elif button in [self.stop_detect_button]:
                # red for Stop Detect
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #7c1c21); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7c1c21, stop:1 #4e0e12);}")
            elif button in [self.browse_button]:
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #003865);}")
            elif button in [self.refresh_button]:
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6c757d, stop:1 #343a40); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #343a40, stop:1 #1b1e21);}")
            elif button in [self.play_video_button]:
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #17a2b8, stop:1 #0f5969); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0f5969, stop:1 #073536);}")
            else:
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6c757d, stop:1 #343a40); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #343a40, stop:1 #1b1e21);}")
        # Connect buttons to functions
        self.browse_button.clicked.connect(self.browse_files)
        self.refresh_button.clicked.connect(self.refresh_ui)
        self.start_detect_button.clicked.connect(self.start_detect)
        self.stop_detect_button.clicked.connect(self.stop_detect)
        self.play_video_button.clicked.connect(lambda: self.player.play())
        self.pause_video_button.clicked.connect(lambda: self.player.pause())

        # Assign buttons to layouts and add to control panel
        top_buttons = QHBoxLayout()
        top_buttons.addWidget(self.browse_button)
        top_buttons.addWidget(self.refresh_button)
        bottom_buttons = QHBoxLayout()
        bottom_buttons.addWidget(self.start_detect_button)
        bottom_buttons.addWidget(self.stop_detect_button)
        media_buttons = QHBoxLayout()
        media_buttons.addWidget(self.play_video_button)
        media_buttons.addWidget(self.pause_video_button)

        # Add button layouts to the group layout
        group_layout.addLayout(top_buttons)
        group_layout.addLayout(bottom_buttons)
        group_layout.addLayout(media_buttons)

        # Mode panel with vertical layout
        mode_panel_group = QGroupBox("Mode")
        mode_panel_group.setStyleSheet(
            "QGroupBox { border: 2px solid lightgray; border-radius: 5px; margin-top: 20px; font-size: 16px; font-weight: bold } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; }")

        mode_panel_group.setFixedSize(610, 200)
        mode_layout = QVBoxLayout()
        mode_layout.setContentsMargins(1, 1, 1, 1)
        mode_layout.setSpacing(1)
        mode_panel_group.setLayout(mode_layout)
        self.control_panel.addWidget(mode_panel_group)

        # Create mode buttons
        self.normal_button = QPushButton('Normal')
        self.inspection_button = QPushButton('Inspection')
        self.tracking_button = QPushButton('Tracking')
        self.detect_button = QPushButton('Detect')

        # Set styles and sizes for mode buttons
        for button in [self.normal_button, self.inspection_button, self.tracking_button, self.detect_button]:
            button.setFixedSize(150, 80)
      
            if button in [self.normal_button]:
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34568B, stop:1 #1C3A59); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1C3A59, stop:1 #34568B);}")
            elif button in [self.inspection_button]:
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0F4C5C, stop:1 #052C34); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #052C34, stop:1 #0F4C5C);}")
            elif button in [self.tracking_button]:
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4169E1, stop:1 #27408B); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #27408B, stop:1 #4169E1);}")
            elif button in [self.detect_button]:
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a6073, stop:1 #3a7bd5); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a7bd5, stop:1 #3a6073);}")

        # Connect mode buttons to mode selection function
        self.normal_button.clicked.connect(lambda: self.select_mode(self.normal_button, "Normal"))
        self.inspection_button.clicked.connect(lambda: self.select_mode(self.inspection_button, "Inspection"))
        self.tracking_button.clicked.connect(lambda: self.select_mode(self.tracking_button, "Tracking"))
        self.detect_button.clicked.connect(lambda: self.select_mode(self.detect_button, "Detect"))

        # Assign mode buttons to mode layout
        mode_buttons_top = QHBoxLayout()
        mode_buttons_top.addWidget(self.normal_button)
        mode_buttons_top.addWidget(self.inspection_button)

        mode_buttons_bottom = QHBoxLayout()
        mode_buttons_bottom.addWidget(self.tracking_button)
        mode_buttons_bottom.addWidget(self.detect_button)

        mode_layout.addLayout(mode_buttons_top)
        mode_layout.addLayout(mode_buttons_bottom)

        # Result text area
        result_group = QGroupBox("Result")
        result_group.setStyleSheet(
            "QGroupBox { border: 2px solid lightgray; border-radius: 5px; margin-top: 20px; font-size: 16px; font-weight: bold} QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; }")

        result_layout = QVBoxLayout()
        result_layout.setContentsMargins(1, 1, 1, 1)
        result_layout.setSpacing(1)
        result_group.setLayout(result_layout)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumSize(200, 200)
        # self.result_text.setStyleSheet(
        #     "background-color: white; color: black; border: none; border-radius: 5px;")
        self.result_text.setStyleSheet(
            "QTextEdit {"
            "background-color: #f2f2f2;"  # Light grey background
            "color: black;"  # Ensuring the text color is black for better readability
            "border-radius: 5px;"  # Optional: rounding the corners
            "padding: 8px;"  # Padding inside the text area
            "}"
        )
        result_layout.addWidget(self.result_text)

        self.control_panel.addWidget(result_group)

    def browse_files(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "",
                                                   "Image Files (*.png *.jpg *.jpeg *.bmp);;Video Files (*.mp4 *.avi *.mov);;All Files (*)")

        if file_path:  # Check if a file was selected
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):  # If the file is an image
                self.result_text.clear()
                self.result_text.append(f'Completed import image')
                try:
                    pixmap = QPixmap(file_path)
                    self.image_area.setPixmap(
                        pixmap.scaled(self.image_area.width(), self.image_area.height(), Qt.KeepAspectRatio)
                    )
                    self.stacked_widget.setCurrentWidget(self.image_area)
                    self.image_path = file_path
                    self.video_path = None  # Ensure not have any video in UI
                except:
                    self.result_text.append(f'Image at path {file_path} can not be displayed')

            elif file_path.lower().endswith(('.mp4', '.avi', '.mov')):  # If the file is a video
                self.result_text.clear()
                self.result_text.append('Complete import video')
                self.player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
                self.player.pause()
                self.stacked_widget.setCurrentWidget(self.video_widget)
                self.video_path = file_path
                self.image_path = None  # Ensure not have any image in UI

            else:
                self.result_text.append("Unsupported file format.")
        else:
            self.result_text.append("No file selected.")

    def refresh_ui(self):
        self.result_text.clear()  # clear result text
        self.image_area.clear()  # clear image 
        self.video_output_label.clear()  # clear video

        if self.player.state() == QMediaPlayer.PlayingState:  # check if video is playing
            self.player.stop()  # stop video

        self.player.setMedia(QMediaContent())  # delete media

        self.reset_modes()  # reset all mode
        self.result_text.append("UI has been refreshed.")


    def start_detect(self):
        self.result_text.append("Starting detect...")
        #self.select_mode(self.normal_button, "Normal")  # Activate Normal mode by default
        if self.image_path is not None:
            detect_image(self.model, self.image_path, self.image_area, self.result_text)
        elif self.video_path is not None:
            detect_video(self.model,self.video_path, self.mode, self.timer, self.result_text, self.video_output_label, self.stacked_widget)

    def stop_detect(self):
        self.result_text.append("Stopping detect...")
        # Dừng timer hoặc thread đang chạy phát hiện
        if self.timer.isActive():
            self.timer.stop()  # Giả sử đang dùng QTimer để handle loop
        elif hasattr(self, 'detection_thread') and self.detection_thread.is_alive():
            self.detection_thread.stop()  # Giả sử có thread chạy phát hiện

        self.result_text.append("Detection has been paused.")


    def select_mode(self, button, mode):
        for btn in [self.normal_button, self.inspection_button, self.tracking_button, self.detect_button]:
            btn.setStyleSheet(
                "QPushButton {background-color: #6c757d; color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: #007BFF;}")
        button.setStyleSheet(
            "QPushButton {background-color: #0056b3; color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 16px; font-style: italic}")
        self.result_text.append(f"Mode {mode} is turned on.")
        self.mode = mode

        # Disconnect and reconnect the timer
        self.timer.stop()
        self.timer.timeout.disconnect()
        print('Mode: ', self.mode)

    def play_video(self):
        self.result_text.append("Playing video...")

    def pause_video(self):
        self.result_text.append("Pausing video...")

    def reset_modes(self):
        # This function resets all mode buttons to their default state
        for button in [self.normal_button, self.inspection_button, self.tracking_button, self.detect_button]:
            if button in [self.normal_button]:
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34568B, stop:1 #1C3A59); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1C3A59, stop:1 #34568B);}")
            elif button in [self.inspection_button]:
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0F4C5C, stop:1 #052C34); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #052C34, stop:1 #0F4C5C);}")
            elif button in [self.tracking_button]:
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4169E1, stop:1 #27408B); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #27408B, stop:1 #4169E1);}")
            elif button in [self.detect_button]:
                button.setStyleSheet(
                    "QPushButton {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a6073, stop:1 #3a7bd5); color: white; border: 2px solid lightgray; padding: 5px; margin: 5px; border-radius: 7px; font-size: 14px; font-weight: bold} QPushButton:hover {background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a7bd5, stop:1 #3a6073);}")
        self.result_text.append("All modes have been reset.")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FinalTermProjectApp()
    ex.show()
    sys.exit(app.exec_())
