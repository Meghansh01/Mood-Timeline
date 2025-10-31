import React, {useEffect, useRef, useState} from 'react'

export default function MoodTimeline({videoSrc, apiUrl}){
  const videoRef = useRef(null)
  const [segments, setSegments] = useState([])
  const [filter, setFilter] = useState('all')

  useEffect(()=>{
    async function fetchMood(){
      // demo transcript included in repo; in production, send real transcript
      const demoTranscript = window.demoTranscript || `
[00:00:00] This is a calm introduction. Welcome to the demo video.
[00:00:06] Now things get a bit more exciting! Wow, amazing scene!
[00:00:12] Back to neutral explanation and calm voice.
[00:00:18] Finale: intense, epic, what a banger!
`
      const form = new FormData()
      form.append('transcript', demoTranscript)
      try{
        const resp = await fetch(apiUrl + '/mood/demo-video', {method:'POST', body: form})
        const data = await resp.json()
        setSegments(data.segments)
      }catch(e){
        // fallback: local segmentation (mimic)
        setSegments([
          {t0:0, t1:6, mood:'calm', confidence:0.8},
          {t0:6, t1:12, mood:'hype', confidence:0.9},
          {t0:12, t1:18, mood:'neutral', confidence:0.6},
          {t0:18, t1:24, mood:'hype', confidence:0.85},
        ])
      }
    }
    fetchMood()
  },[apiUrl])

  function seek(t){
    if(videoRef.current){
      videoRef.current.currentTime = t
      videoRef.current.play()
    }
  }

  function renderSegmentBar(){
    const dur = videoRef.current ? (videoRef.current.duration || 24) : 24
    return (
      <div style={{width:'100%', height:12, background:'#e5e7eb', borderRadius:6, position:'relative', overflow:'hidden'}}>
        {segments.filter(s=> filter==='all' || s.mood===filter).map((s,i)=>{
          const left = (s.t0/dur)*100
          const width = ((s.t1-s.t0)/dur)*100
          const color = s.mood==='hype' ? '#ef4444' : (s.mood==='calm' ? '#60a5fa' : '#fbbf24')
          return (
            <div key={i} onClick={()=>seek(s.t0)} title={`${s.mood} (${s.confidence})`}
              style={{position:'absolute', left:`${left}%`, width:`${width}%`, top:0, bottom:0, background:color, cursor:'pointer'}} />
          )
        })}
      </div>
    )
  }

  return (
    <div>
      <div style={{marginBottom:8}}>
        <video ref={videoRef} src={videoSrc} controls style={{width:'100%', borderRadius:8}} />
      </div>
      <div style={{display:'flex', alignItems:'center', gap:8, marginBottom:8}}>
        <label style={{fontSize:13}}>Show:</label>
        <select value={filter} onChange={e=>setFilter(e.target.value)} style={{padding:6, borderRadius:6}}>
          <option value="all">All</option>
          <option value="calm">Calm</option>
          <option value="neutral">Neutral</option>
          <option value="hype">Hype</option>
        </select>
      </div>
      {renderSegmentBar()}
      <div style={{marginTop:8, fontSize:12, color:'#374151'}}>Click colored segments to jump. Colors: <span style={{color:'#ef4444'}}>Hype</span>, <span style={{color:'#fbbf24'}}>Neutral</span>, <span style={{color:'#60a5fa'}}>Calm</span>.</div>
    </div>
  )
}
