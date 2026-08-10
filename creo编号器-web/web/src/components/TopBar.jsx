import React, { useRef } from 'react'

export function TopBar({
  projects,
  projectId,
  onSelectProject,
  onNewProject,
  onDeleteProject,
  onImport,
}) {
  const fileRef = useRef(null)

  return (
    <div className="topbar">
      <span className="app-title">Creo 模型树自动取号器</span>
      <select
        value={projectId ?? ''}
        onChange={(e) => onSelectProject(e.target.value ? Number(e.target.value) : null)}
        style={{ minWidth: 200 }}
      >
        <option value="">选择项目…</option>
        {projects.map((p) => (
          <option key={p.id} value={p.id}>
            {p.root_number} · {p.name || p.root_number}
          </option>
        ))}
      </select>
      <span className="topbar-spacer" />
      <button onClick={onNewProject}>新建项目</button>
      <button disabled={!projectId} onClick={onDeleteProject}>删除项目</button>
      <button onClick={() => fileRef.current?.click()}>导入数据</button>
      <input
        ref={fileRef}
        type="file"
        accept=".json,application/json"
        style={{ display: 'none' }}
        onChange={(e) => {
          const file = e.target.files && e.target.files[0]
          if (file) onImport(file)
          e.target.value = ''
        }}
      />
    </div>
  )
}
