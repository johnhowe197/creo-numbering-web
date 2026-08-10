/* 后端 API 封装 */

async function request(url, options = {}) {
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await resp.json().catch(() => null)
  if (!resp.ok) {
    const detail = data && data.detail ? data.detail : `请求失败 (${resp.status})`
    throw new Error(detail)
  }
  return data
}

export const api = {
  listProjects: () => request('/api/projects'),

  createProject: (rootNumber, name) =>
    request('/api/projects', {
      method: 'POST',
      body: JSON.stringify({ root_number: rootNumber, name }),
    }),

  getProject: (id) => request(`/api/projects/${id}`),

  deleteProject: (id) => request(`/api/projects/${id}`, { method: 'DELETE' }),

  updateProject: (id, payload) =>
    request(`/api/projects/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  addNode: (projectId, type, payload) =>
    request(
      `/api/projects/${projectId}/${type === 'component' ? 'components' : 'parts'}`,
      { method: 'POST', body: JSON.stringify(payload) },
    ),

  updateNode: (projectId, number, payload) =>
    request(
      `/api/projects/${projectId}/nodes/${encodeURIComponent(number)}`,
      { method: 'PATCH', body: JSON.stringify(payload) },
    ),

  deleteNode: (projectId, number) =>
    request(
      `/api/projects/${projectId}/nodes/${encodeURIComponent(number)}`,
      { method: 'DELETE' },
    ),

  importProject: (data) =>
    request('/api/import', { method: 'POST', body: JSON.stringify(data) }),
}
