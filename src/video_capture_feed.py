import cv2


class VideoCaptureFeed:

    def __init__(self, video_source):
        self.set_video_source(video_source)

    def next_frame(self):
        return self.video_capture.read()

    def set_video_source(self, new_source):
        self.video_source = new_source
        self.video_capture = cv2.VideoCapture(self.video_source)

    def release_camera(self):
        self.video_capture.release()
