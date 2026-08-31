import pyaudio
import wave
import threading
from datetime import datetime
from transformers import pipeline
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os
import speech_recognition as sr

class LectureNotesGeneratorLocal:
    def __init__(self):
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        self.recognizer = sr.Recognizer()
        self.is_recording = False
        self.audio_frames = []
        self.audio_params = {
            'format': pyaudio.paInt16,
            'channels': 1,
            'rate': 16000,
            'chunk': 1024
        }
    
    def start_recording(self, lecture_id):
        self.is_recording = True
        self.audio_frames = []
        
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=self.audio_params['format'],
            channels=self.audio_params['channels'],
            rate=self.audio_params['rate'],
            input=True,
            frames_per_buffer=self.audio_params['chunk']
        )
        
        def record():
            while self.is_recording:
                data = stream.read(self.audio_params['chunk'])
                self.audio_frames.append(data)
        
        self.recording_thread = threading.Thread(target=record)
        self.recording_thread.start()
        
        return {'status': 'recording', 'lecture_id': lecture_id}
    
    def stop_recording(self, lecture_id):
        self.is_recording = False
        self.recording_thread.join()
        
        filename = f"lecture_{lecture_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        filepath = os.path.join('uploads', 'lectures', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        audio = pyaudio.PyAudio()
        wf = wave.open(filepath, 'wb')
        wf.setnchannels(self.audio_params['channels'])
        wf.setsampwidth(audio.get_sample_size(self.audio_params['format']))
        wf.setframerate(self.audio_params['rate'])
        wf.writeframes(b''.join(self.audio_frames))
        wf.close()
        
        return filepath
    
    def transcribe_audio(self, audio_filepath, lecture_id):
        """Convert speech to text using local speech recognition"""
        with sr.AudioFile(audio_filepath) as source:
            audio_data = self.recognizer.record(source)
            try:
                transcript = self.recognizer.recognize_google(audio_data)
                return transcript
            except:
                return "Transcription failed. Please check audio quality."
    
    def summarize_lecture(self, transcript):
        if len(transcript) < 50:
            return transcript
        
        max_chunk = 1024
        chunks = [transcript[i:i+max_chunk] for i in range(0, len(transcript), max_chunk)]
        
        summaries = []
        for chunk in chunks:
            if len(chunk) > 50:
                summary = self.summarizer(chunk, max_length=130, min_length=30, do_sample=False)
                summaries.append(summary[0]['summary_text'])
        
        return ' '.join(summaries)
    
    def generate_pdf(self, lecture_data, output_path):
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph(lecture_data['title'], styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph(f"<b>Date:</b> {lecture_data['date']}", styles['Normal']))
        story.append(Paragraph(f"<b>Faculty:</b> {lecture_data['faculty']}", styles['Normal']))
        story.append(Paragraph(f"<b>Subject:</b> {lecture_data['subject']}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("<b>Lecture Summary</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(lecture_data['summary'], styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("<b>Full Transcript</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(lecture_data['transcript'], styles['Normal']))
        
        doc.build(story)
        return output_path
