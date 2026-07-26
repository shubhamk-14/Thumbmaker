// const API_BASE = '/api'
const API_BASE = import.meta.env.VITE_API_URL || '/api'

async function parseJsonResponse(response, fallbackMessage) {
  if (response.ok) return response.json()

  let detail = fallbackMessage
  try {
    const body = await response.json()
    detail = body.detail || body.details || detail
  } catch {
    detail = fallbackMessage
  }

  throw new Error(detail)
}

export async function uploadHeadshot(file) {
  const form = new FormData()
  form.append('file', file)

  const response = await fetch(`${API_BASE}/upload-headshot`, {
    method: 'POST',
    body: form,
  })

  return parseJsonResponse(response, 'Failed to upload headshot')
}

export async function createJob({ prompt, numThumbnails, headshotUrl }) {
  const response = await fetch(`${API_BASE}/jobs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt,
      num_thumbnails: numThumbnails,
      headshot_url: headshotUrl,
    }),
  })

  return parseJsonResponse(response, 'Failed to create job')
}

export function subscribeToJob(
  jobId,
  { onThumbnailReady, onThumbnailFailed, onJobComplete, onError },
) {
  const eventSource = new EventSource(`${API_BASE}/jobs/${jobId}/stream`)

  const parse = (event) => {
    try {
      return JSON.parse(event.data)
    } catch {
      return {}
    }
  }

  const ready = (event) => onThumbnailReady(parse(event))
  const failed = (event) => onThumbnailFailed(parse(event))
  const complete = (event) => {
    onJobComplete(parse(event))
    eventSource.close()
  }

  eventSource.addEventListener('thumbnail_ready', ready)
  eventSource.addEventListener('thumbnail ready', ready)
  eventSource.addEventListener('thumbnail_failed', failed)
  eventSource.addEventListener('thumbnail failed', failed)
  eventSource.addEventListener('job_complete', complete)
  eventSource.addEventListener('job completed', complete)
  eventSource.addEventListener('error', (event) => {
    onError(event)
    eventSource.close()
  })

  return eventSource
}
