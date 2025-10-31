import React from 'react'
import MoodTimeline from './components/MoodTimeline'

const DEMO_VIDEO = 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4'

export default function App(){
  return (
    <div style={{maxWidth: 900, margin: '32px auto', fontFamily: 'system-ui, sans-serif'}}>
      <h2 style={{marginBottom: 12}}>Mood Timeline — Demo</h2>
      <MoodTimeline videoSrc={DEMO_VIDEO} apiUrl={'http://localhost:8000'} />
    </div>
  )
}
