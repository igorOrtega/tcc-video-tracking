from calibration import CameraCalibration, CalibrationCofig

if __name__ == "__main__":
    config = CalibrationCofig(
        'teste', 'teste', 'teste')

    camera_calibration = CameraCalibration(
        config)

    camera_calibration.acquire_calibration_images(0)
