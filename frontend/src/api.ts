const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
export const tokenStore = {
  get: () => localStorage.getItem('papertrail_token'),
  set: (value: string) => { localStorage.setItem('papertrail_token', value); window.dispatchEvent(new Event('papertrail-auth')) },
  clear: () => { localStorage.removeItem('papertrail_token'); window.dispatchEvent(new Event('papertrail-auth')) },
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = tokenStore.get()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const response = await fetch(`${API}${path}`, { ...init, headers })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = typeof body.detail === 'string' ? body.detail : 'Something went wrong. Please try again.'
    if (response.status === 401) tokenStore.clear()
    throw new Error(detail)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function documentBlob(path: string): Promise<string> {
  const token = tokenStore.get()
  const response = await fetch(`${API}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (!response.ok) throw new Error('Could not open this PDF')
  return URL.createObjectURL(await response.blob())
}

export type User = { id: string; name: string; email: string; role?: 'user'|'admin' }
export type FeedbackEntry = { id: string; document_id: string; question: string; original_answer: string; feedback_type: string; correction?: string; comment?: string; status: string; created_at: string; reviewed_at?: string; submitted_by?: string }
export type Doc = { id: string; original_filename: string; file_size: number; status: 'uploaded'|'processing'|'ready'|'failed'; page_count?: number; chunk_count?: number; processing_error?: string; created_at: string }
export type Conversation = { id: string; document_id: string; title: string; created_at: string; updated_at: string }
export type Source = { document_id: string; filename: string; page?: number|string; chunk_id?: string; excerpt: string }
export type Message = { id?: string; role: 'user'|'assistant'; content: string; confidence?: { level: string; score: number; signals?: Record<string, number> }; sources?: Source[]; created_at?: string }
export type Answer = { status: string; conversation_id: string; message_id?: string; question: string; answer: string; confidence: Message['confidence']; sources: Source[]; related_questions: string[] }
