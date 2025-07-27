import cv2
import numpy as np
from deepface import DeepFace
from django.conf import settings
import os
import json
from datetime import datetime

class VideoProcessor:
    def __init__(self):
        self.emotion_history = []
        self.cap = None
        self.is_processing = False

    def start_capture(self):
        """Start video capture from default camera"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("Could not open video device")
        self.is_processing = True

    def stop_capture(self):
        """Stop video capture and release resources"""
        if self.cap:
            self.cap.release()
        self.is_processing = False
        self.emotion_history = []

    def process_frame(self):
        """Process a single frame and detect emotions"""
        if not self.cap or not self.is_processing:
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        try:
            # Analyze frame for emotions
            result = DeepFace.analyze(
                frame,
                actions=['emotion'],
                enforce_detection=False,
                detector_backend='opencv'
            )

            if result and len(result) > 0:
                emotions = result[0]['emotion']
                timestamp = datetime.now().isoformat()
                
                # Add to emotion history
                self.emotion_history.append({
                    'timestamp': timestamp,
                    'emotions': emotions
                })

                return emotions
        except Exception as e:
            print(f"Error processing frame: {str(e)}")
            return None

        return None

    def get_emotion_summary(self):
        """Get summary of emotions detected during the session"""
        if not self.emotion_history:
            return None

        # Calculate average emotions
        total_emotions = {
            'angry': 0,
            'disgust': 0,
            'fear': 0,
            'happy': 0,
            'sad': 0,
            'surprise': 0,
            'neutral': 0
        }

        for entry in self.emotion_history:
            for emotion, value in entry['emotions'].items():
                total_emotions[emotion] += value

        # Calculate averages
        num_frames = len(self.emotion_history)
        avg_emotions = {
            emotion: value / num_frames
            for emotion, value in total_emotions.items()
        }

        return {
            'average_emotions': avg_emotions,
            'emotion_history': self.emotion_history,
            'total_frames_analyzed': num_frames
        }

    def save_emotion_data(self, attempt_id):
        """Save emotion data to a file"""
        summary = self.get_emotion_summary()
        if not summary:
            return None

        # Create directory if it doesn't exist
        emotion_dir = os.path.join(settings.MEDIA_ROOT, 'emotion_data')
        os.makedirs(emotion_dir, exist_ok=True)

        # Save to file
        filename = f'emotion_data_{attempt_id}.json'
        filepath = os.path.join(emotion_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(summary, f)

        return filepath 