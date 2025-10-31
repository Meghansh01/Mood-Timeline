from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from utils import segment_from_transcript, analyze_prosody_from_audio, analyze_visuals_from_video, predict_moods

app = FastAPI()

class Segment(BaseModel):
    t0: float
    t1: float
    mood: str
    confidence: float

class MoodResponse(BaseModel):
    segments: List[Segment]

@app.post('/mood/{videoId}', response_model=MoodResponse)
async def mood_endpoint(videoId: str,
                        transcript: str = Form(...),
                        audio: Optional[UploadFile] = File(None),
                        video_file: Optional[UploadFile] = File(None)):
    # 1) Segment using transcript
    segments = segment_from_transcript(transcript)

    # 2) Prosody (if audio provided)
    prosody_features = None
    if audio is not None:
        contents = await audio.read()
        with open('tmp_audio.wav', 'wb') as f:
            f.write(contents)
        prosody_features = analyze_prosody_from_audio('tmp_audio.wav', segments)

    # 3) Visual features (if video provided)
    visual_features = None
    if video_file is not None:
        contents = await video_file.read()
        with open('tmp_video.mp4', 'wb') as f:
            f.write(contents)
        visual_features = analyze_visuals_from_video('tmp_video.mp4', segments)

    # 4) Predict moods
    predicted = predict_moods(segments, prosody_features, visual_features)

    response = {'segments': predicted}
    return response

if __name__ == '__main__':
    uvicorn.run('app:app', host='0.0.0.0', port=8000, reload=True)
