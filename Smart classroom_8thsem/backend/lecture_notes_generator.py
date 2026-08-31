import boto3
import pyaudio
import wave
import threading
from datetime import datetime
from transformers import pipeline
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os

class LectureNotesGenerator:
    def __init__(self):
        self.transcribe_client = boto3.client('transcribe', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.bucket_name = os.getenv('S3_BUCKET', 'classroom-lectures')
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        
        self.is_recording = False
        self.audio_frames = []
        self.audio_params = {
            'format': pyaudio.paInt16,
            'channels': 1,
            'rate': 16000,
            'chunk': 1024
        }
    
    def start_recording(self, lecture_id):
        """Start recording classroom audio"""
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
        """Stop recording and save audio file"""
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
        """Convert speech to text using AWS Transcribe"""
        s3_key = f"lectures/{os.path.basename(audio_filepath)}"
        
        # Upload to S3
        self.s3_client.upload_file(audio_filepath, self.bucket_name, s3_key)
        
        job_name = f"transcribe_{lecture_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        job_uri = f"s3://{self.bucket_name}/{s3_key}"
        
        # Start transcription job
        self.transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': job_uri},
            MediaFormat='wav',
            LanguageCode='en-US'
        )
        
        # Wait for completion
        while True:
            status = self.transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                break
        
        if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
            transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
            import requests
            transcript_data = requests.get(transcript_uri).json()
            transcript_text = transcript_data['results']['transcripts'][0]['transcript']
            return transcript_text
        
        return None
    
    def summarize_lecture(self, transcript):
        """Generate summary from transcript"""
        max_chunk = 1024
        chunks = [transcript[i:i+max_chunk] for i in range(0, len(transcript), max_chunk)]
        
        summaries = []
        for chunk in chunks:
            if len(chunk) > 50:
                summary = self.summarizer(chunk, max_length=130, min_length=30, do_sample=False)
                summaries.append(summary[0]['summary_text'])
        
        return ' '.join(summaries)
    
    def generate_pdf(self, lecture_data, output_path):
        """Generate PDF lecture notes"""
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=12)
        story.append(Paragraph(lecture_data['title'], title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Metadata
        meta_style = styles['Normal']
        story.append(Paragraph(f"<b>Date:</b> {lecture_data['date']}", meta_style))
        story.append(Paragraph(f"<b>Faculty:</b> {lecture_data['faculty']}", meta_style))
        story.append(Paragraph(f"<b>Subject:</b> {lecture_data['subject']}", meta_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Summary
        story.append(Paragraph("<b>Lecture Summary</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(lecture_data['summary'], styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Full Transcript
        story.append(Paragraph("<b>Full Transcript</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(lecture_data['transcript'], styles['Normal']))
        
        doc.build(story)
        return output_path
