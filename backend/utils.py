# utils.py - helpers for simple prototype
import math
from typing import List, Dict
import numpy as np

def parse_timestamp(ts: str) -> float:
    parts = ts.split(':')
    parts = [float(p) for p in parts]
    if len(parts) == 3:
        return parts[0]*3600 + parts[1]*60 + parts[2]
    elif len(parts) == 2:
        return parts[0]*60 + parts[1]
    else:
        return float(parts[0])

def segment_from_transcript(transcript: str) -> List[Dict]:
    lines = [l.strip() for l in transcript.splitlines() if l.strip()]
    segments = []
    if any(l.startswith('[') and ']' in l for l in lines):
        for i, l in enumerate(lines):
            if l.startswith('[') and ']' in l:
                ts = l[1:l.index(']')]
                text = l[l.index(']')+1:].strip()
                t0 = parse_timestamp(ts)
                t1 = None
                for j in range(i+1, len(lines)):
                    lj = lines[j]
                    if lj.startswith('[') and ']' in lj:
                        tsj = lj[1:lj.index(']')]
                        t1 = parse_timestamp(tsj)
                        break
                if t1 is None:
                    t1 = t0 + max(3, len(text.split())/2)
                segments.append({'t0': t0, 't1': t1, 'text': text})
    else:
        # fallback: split into sentences evenly spaced
        try:
            import nltk
            nltk.data.find('tokenizers/punkt')
        except Exception:
            import nltk
            nltk.download('punkt')
        from nltk.tokenize import sent_tokenize
        text = '\\n'.join(lines)
        sents = sent_tokenize(text)
        words = sum(len(s.split()) for s in sents)
        est_total_secs = max(10, math.ceil(words / 2.5))
        t = 0.0
        for s in sents:
            w = len(s.split())
            dur = max(1.0, w / 2.5)
            segments.append({'t0': t, 't1': t+dur, 'text': s})
            t += dur
    return segments

def analyze_prosody_from_audio(audio_path: str, segments: List[Dict]):
    try:
        import librosa
    except Exception:
        raise RuntimeError('librosa required for prosody analysis')
    y, sr = librosa.load(audio_path, sr=None)
    features = []
    for seg in segments:
        s = int(max(0, seg['t0'] * sr))
        e = int(min(len(y), seg['t1'] * sr))
        chunk = y[s:e]
        if len(chunk) < 20:
            features.append({'energy': 0.0, 'pitch_var': 0.0})
            continue
        rms = float(np.mean(librosa.feature.rms(y=chunk)))
        try:
            f0, voiced_flag, voiced_probs = librosa.pyin(chunk, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
            pitch_var = float(np.nanvar(f0)) if f0 is not None else 0.0
        except Exception:
            pitch_var = 0.0
        features.append({'energy': rms, 'pitch_var': pitch_var})
    return features

def analyze_visuals_from_video(video_path: str, segments: List[Dict], frame_every=5):
    try:
        import cv2
    except Exception:
        raise RuntimeError('opencv-python required for visuals analysis')
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    features = []
    for seg in segments:
        s_frame = int(seg['t0'] * fps)
        e_frame = int(seg['t1'] * fps)
        frame_idxs = list(range(s_frame, e_frame, int(frame_every*fps))) if e_frame>s_frame else [s_frame]
        brs = []
        edges = []
        for fi in frame_idxs:
            cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brs.append(float(gray.mean()))
            edge = cv2.Canny(gray, 100, 200)
            edges.append(float(edge.mean()))
        if len(brs)==0:
            features.append({'brightness':0.0, 'edge_density':0.0})
        else:
            features.append({'brightness': float(np.mean(brs)), 'edge_density': float(np.mean(edges))})
    cap.release()
    return features

def predict_moods(segments: List[Dict], prosody_features=None, visual_features=None):
    results = []
    excited_keywords = ['wow','amazing','insane','incredible','hype','excited','epic','banger','!','🔥','exciting']
    calm_keywords = ['relax','calm','chill','soft','gentle','quiet','peace']
    for idx, seg in enumerate(segments):
        text = seg.get('text','')
        score = 0.0
        tlower = text.lower()
        kw_exc = sum(1 for k in excited_keywords if k in tlower)
        kw_calm = sum(1 for k in calm_keywords if k in tlower)
        score += 0.6 * (kw_exc - kw_calm)
        score += 0.2 * text.count('!')
        if sum(1 for c in text if c.isupper()) > max(5, 0.2*len(text)):
            score += 0.5
        if prosody_features is not None and idx < len(prosody_features):
            pf = prosody_features[idx]
            score += 0.004 * (pf.get('energy',0)*1000) + 0.3*(pf.get('pitch_var',0))
        if visual_features is not None and idx < len(visual_features):
            vf = visual_features[idx]
            score += 0.002*(vf.get('brightness',0)) + 0.0005*(vf.get('edge_density',0))
        if score > 1.0:
            mood = 'hype'
            conf = min(0.99, 0.5 + (score-1)/4)
        elif score < -0.5:
            mood = 'calm'
            conf = min(0.99, 0.5 + (-score)/4)
        else:
            mood = 'neutral'
            conf = 0.6
        results.append({'t0': float(seg['t0']), 't1': float(seg['t1']), 'mood': mood, 'confidence': float(round(conf,2))})
    return results
