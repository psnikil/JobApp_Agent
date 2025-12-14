from faster_whisper import WhisperModel
from dotenv import load_dotenv
import whisper
import os
from moviepy.video.io import VideoFileClip
import subprocess

import tempfile

load_dotenv()

model_size = os.getenv('ASR_MODEL_SIZE', 'base')

class Asr:
    def __init__(self):
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_path):
        segments= self.model.transcribe(audio_path, beam_size=5)
        return segments
        

    def get_audio_from_video(self, video_path):


        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
            audio_path = tmpfile.name
        
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(audio_path)
        audio_clip.close()
        video_clip.close()
        return audio_path

    def extract_audio_ffmpeg(self,input_video):

        # with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        #     audio_path = tmpfile.name
        #     print(f"the audio path is : {audio_path}")

        command = ["ffmpeg", "-i", input_video, "-q:a", "0", "-map", "a", "./data/audio.wav"]
        subprocess.run(command, check=True)
        return "./data/audio.wav"



if __name__ == "__main__":
    asr = Asr()
    audio_path  = asr.extract_audio_ffmpeg("./data/video.mp4")
    segments = asr.transcribe(audio_path)
    print(segments)
    

        

