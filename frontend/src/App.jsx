import { useMemo, useState } from 'react'
import './App.css'
import { createJob, subscribeToJob, uploadHeadshot } from './api'

// Convert any static URL to a path that works through the Vite dev proxy
function normalizeImageUrl(url) {
  if (!url) return url
  // Convert full local URL to relative path so Vite proxy handles it
  if (url.startsWith('http://127.0.0.1:8000/static/')) {
    return url.replace('http://127.0.0.1:8000', '')
  }
  return url
}

const styles = [
  {
    id: 'bold_dramatic',
    label: 'Dramatic',
    tone: 'High contrast, cinematic shadows, punchy face crop',
  },
  {
    id: 'clean_minimal',
    label: 'Clean',
    tone: 'Bright studio look, simple layout, sharp professional polish',
  },
  {
    id: 'vibrant_energetic',
    label: 'Vibrant',
    tone: 'Colorful, energetic, scroll-stopping YouTube energy',
  },
]

const starterPrompts = [
  'I built a FastAPI project from scratch',
  'AI tools that save hours every week',
  'How to make thumbnails people actually click',
]

function App() {
  const [prompt, setPrompt] = useState(starterPrompts[0])
  const [numThumbnails, setNumThumbnails] = useState(3)
  const [headshotFile, setHeadshotFile] = useState(null)
  const [headshotUrl, setHeadshotUrl] = useState('')
  const [jobId, setJobId] = useState('')
  const [status, setStatus] = useState('idle')
  const [message, setMessage] = useState('Ready to build a thumbnail set.')
  const [results, setResults] = useState([])

  const activeStyles = useMemo(
    () => styles.slice(0, Number(numThumbnails)),
    [numThumbnails],
  )

  const previewUrl = useMemo(() => {
    if (!headshotFile) return ''
    return URL.createObjectURL(headshotFile)
  }, [headshotFile])

  async function handleGenerate(event) {
    event.preventDefault()
    setStatus('uploading')
    setMessage('Preparing your headshot and creative brief...')
    setResults([])

    try {
      let uploadedUrl = headshotUrl.trim()
      if (headshotFile) {
        const upload = await uploadHeadshot(headshotFile)
        uploadedUrl = upload.url
        setHeadshotUrl(uploadedUrl)
      }

      if (!uploadedUrl) {
        throw new Error('Add a headshot file or paste an image URL.')
      }

      setStatus('generating')
      setMessage('Generating thumbnail concepts...')

      const job = await createJob({
        prompt: prompt.trim(),
        numThumbnails: Number(numThumbnails),
        headshotUrl: uploadedUrl,
      })

      setJobId(job.job_id)
      setMessage(`Job ${job.job_id} started. Waiting for thumbnails...`)

      subscribeToJob(job.job_id, {
        onThumbnailReady: (thumbnail) => {
          setResults((current) => {
            const next = current.filter(
              (item) => item.thumbnail_id !== thumbnail.thumbnail_id,
            )
            return [...next, thumbnail]
          })
        },
        onThumbnailFailed: (thumbnail) => {
          setResults((current) => {
            const next = current.filter(
              (item) => item.thumbnail_id !== thumbnail.thumbnail_id,
            )
            return [...next, { ...thumbnail, failed: true }]
          })
        },
        onJobComplete: () => {
          setStatus('complete')
          setMessage('Thumbnail set complete.')
        },
        onError: () => {
          setStatus('error')
          setMessage('The live job stream stopped. Check the backend logs.')
        },
      })
    } catch (error) {
      setStatus('error')
      setMessage(error.message || 'Something went wrong while starting the job.')
    }
  }

  async function downloadImage(url, filename) {
    try {
      const response = await fetch(url)
      const blob = await response.blob()
      const blobUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(blobUrl)
    } catch (err) {
      // Fallback: open in new tab if CORS prevents fetching directly
      window.open(url, '_blank')
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <aside className="control-panel">
          <div className="brand-row">
            <div className="brand-mark">TM</div>
            <div>
              <p className="eyebrow">Thumbmaker Studio</p>
              <h1>Design a click-worthy thumbnail pack.</h1>
            </div>
          </div>

          <form className="creator-form" onSubmit={handleGenerate}>
            <label className="field-block">
              <span>Video idea</span>
              <textarea
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder="Describe your video topic, promise, and audience"
                rows="5"
                required
              />
            </label>

            <div className="prompt-pills" aria-label="Prompt examples">
              {starterPrompts.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setPrompt(item)}
                  title="Use this prompt"
                >
                  {item}
                </button>
              ))}
            </div>

            <label className="field-block">
              <span>Headshot</span>
              <input
                type="file"
                accept="image/*"
                onChange={(event) => {
                  setHeadshotFile(event.target.files?.[0] || null)
                  setHeadshotUrl('')
                }}
              />
            </label>

            <label className="field-block compact">
              <span>Or image URL</span>
              <input
                type="url"
                value={headshotUrl}
                onChange={(event) => {
                  setHeadshotUrl(event.target.value)
                  setHeadshotFile(null)
                }}
                placeholder="https://example.com/headshot.png"
              />
            </label>

            <div className="count-row">
              <span>Variations</span>
              <div className="segmented">
                {[1, 2, 3].map((count) => (
                  <button
                    key={count}
                    type="button"
                    className={numThumbnails === count ? 'active' : ''}
                    onClick={() => setNumThumbnails(count)}
                    title={`${count} thumbnail variation${count > 1 ? 's' : ''}`}
                  >
                    {count}
                  </button>
                ))}
              </div>
            </div>

            <button className="generate-button" type="submit">
              <span className="button-glyph" aria-hidden="true">+</span>
              Generate pack
            </button>
          </form>
        </aside>

        <section className="preview-stage" aria-live="polite">
          <div className="stage-header">
            <div>
              <p className="eyebrow">Live preview</p>
              <h2>{status === 'complete' ? 'Ready thumbnails' : 'Creative board'}</h2>
            </div>
            <span className={`status-chip ${status}`}>{status}</span>
          </div>

          <div className="thumbnail-canvas">
            <div className="thumb-background">
              <div className="thumb-copy">
                <span>NEW VIDEO</span>
                <strong>{prompt || 'Your video title'}</strong>
              </div>
              <div className="headshot-preview">
                {previewUrl || headshotUrl ? (
                  <img src={previewUrl || headshotUrl} alt="Selected headshot preview" />
                ) : (
                  <span>Add headshot</span>
                )}
              </div>
            </div>
          </div>

          <div className="message-bar">
            <span>{message}</span>
            {jobId ? <code>{jobId}</code> : null}
          </div>

          <div className="style-grid">
            {activeStyles.map((style, index) => {
              const result = results.find((item) => item.style_name === style.id)
              return (
                <article className="style-card" key={style.id}>
                  <div className={`style-swatch swatch-${index + 1}`}>
                    {result?.imagekit_url ? (
                      <img src={normalizeImageUrl(result.imagekit_url)} alt={`${style.label} thumbnail`} />
                    ) : (
                      <span>{index + 1}</span>
                    )}
                  </div>
                  <div className="style-info">
                    <h3>{style.label}</h3>
                    <p>{result?.failed ? result.error : style.tone}</p>
                    {result?.imagekit_url && !result.failed && (
                      <button
                        type="button"
                        className="download-link-btn"
                        onClick={() => downloadImage(normalizeImageUrl(result.imagekit_url), `${style.id}.png`)}
                        title="Download this thumbnail"
                      >
                        Download Image
                      </button>
                    )}
                  </div>
                </article>
              )
            })}
          </div>
        </section>
      </section>
    </main>
  )
}

export default App
