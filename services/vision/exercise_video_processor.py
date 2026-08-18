from streamlit_webrtc import VideoProcessorBase
import threading
import cv2
import os
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from detectors.Biceps_curl import BicepsCurlDetector
from detectors.Lunges import LungesDetector
from detectors.Pushup import PushUpDetector
from detectors.Shoulder_press import ShoulderPressDetector
from detectors.Squat import SquatDetector
from services.config.workout_config import POSE_CONNECTIONS 


class VideoProcessorClass(VideoProcessorBase):
    def __init__(self):
        self.lock=threading.lock()
        self._latest_metrics=None
        self.exercise_type="Squats"

        model_path=os.path.join(os.getcwd(),"ml_Models","pose_landmarker_full.task")
        base_option=python.BaseOptions(model_path=model_path)

        options=vision.PoseLandmarkerOptions(
            base_option=base_option,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.7,
            min_pose_presence_confidence=0.7,
            min_tracking_confidence=0.7,
            output_segmentation_masks=False
        )

        self._landmarker=vision.PoseLandmarker.create_from_options(options)

        self._detectors={
            "Squats":SquatDetector(),
            "Biceps Curls(Dumbell)":BicepsCurlDetector(),
            "Push-ups":PushUpDetector(),
            "Lunges":LungesDetector(),
            "Shoulder Press":ShoulderPressDetector()
        }

        self._frame_timestamps_ms=0


    def set_latest_metrics(self,metrics):
        with self._lock:
            self._latest_metrics=metrics.copy()

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()

    def set_exercise(self,exercise_type):
        with self._lock:
            self._exercise_type=exercise_type

    def get_exercise(self):
        return self._exercise_type

    def _draw_sekeleton(self,img,landmarks):
        h,w=img.shape[:2]

        for start_idx,end_idx in POSE_CONNECTIONS:
          p1=landmarks[start_idx]
          p2=landmarks[end_idx]

          if p1.visibility >0.7 and p2.visibility>0.7:
              cv2.line(
                  img,
                  ((p1.x*w),int(p1.y*h)),
                  ((p1.x*w),int(p1.y*h)),
                  (0,255,0),
                  8

                  
              )

        for lm in landmarks:
            if lm.visibility>0.7:
                cv2.circle(
                    img,
                    (int(lm.x*w),(lm.y*h)),
                    8,
                    (255,0,0),
                    -1
                )

        return img


    def _draw_no_pose_warnings(self,img):

        cv2.putText(
            img,
            "No Pose Detected",
            (30,50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0,255,0),
            2,
            cv2.LINE_AA

        )

        cv2.putText(
            img,
            "Please Face the Camera",
            (30,100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0,255,0),
            2,
            cv2.LINE_AA
        )


    def _draw_overlays(self,img,metrics,ex_type):
        if ex_type=="Squats":
            self._draw_squats_overlays(img,metrics)

    def _draw_squats_overlays(self,img,metrics):
        h,_=img.shape[:2]

        cv2.putText(
            img,
            f"Dpeth:{metrics['depth-status']}",
            (20,h-20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0,255,0),
            2
        )

    def _draw_pushup_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"BODY: {metrics['body_alignment']} | HIP: {metrics['hip_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_curl_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"SWING: {metrics['swing_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_press_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"EXT: {metrics['extension_status']} | BACK: {metrics['back_arch_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_lunge_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"BALANCE: {metrics['balance_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )


