import React, { useEffect, useMemo, useState } from 'react'

const COLOR_OPTIONS = [
  { key: '', label: '无色' },
  { key: 'red', label: '红色' },
  { key: 'yellow', label: '黄色' },
  { key: 'green', label: '绿色' },
  { key: 'blue', label: '蓝色' },
]

export function TreeView({
  nodes,
  selected,
  multiSelected,
  onSelect,
  expanded,
  onToggle,
  onAdd,
  onRename,
  onDelete,
  onColor,
  onEditField,
  onCopy,
}) {
  const [menu, setMenu] = useState(null)
  const [editing, setEditing] = useState(null) // { number, field, value }

  const childrenMap = useMemo(() => {
    const m = {}
    for (const n of nodes) {
      const key = n.parent ?? '__root__'
      ;(m[key] ||= []).push(n)
    }
    return m
  }, [nodes])

  useEffect(() => {
    const close = () => setMenu(null)
    window.addEventListener('click', close)
    window.addEventListener('contextmenu', close)
    return () => {
      window.removeEventListener('click', close)
      window.removeEventListener('contextmenu', close)
    }
  }, [])

  if (nodes.length === 0) {
    return (
      <div className="tree-pane">
        <div className="tree-placeholder">暂无节点，点击「添加组件」创建</div>
      </div>
    )
  }

  function openMenu(e, node) {
    e.preventDefault()
    e.stopPropagation()
    setMenu({ x: e.clientX, y: e.clientY, node })
  }

  function startEdit(node, field) {
    setEditing({ number: node.number, field, value: node[field] })
  }

  function commitEdit() {
    if (!editing) return
    onEditField(editing.number, editing.field, editing.value)
    setEditing(null)
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
  }

  function renderNode(node, depth) {
    const isLeaf = node.node_type === 'part'
    const isExpanded = expanded.has(node.number)
    const kids = isLeaf ? [] : childrenMap[node.number] || []
    const editingThis = editing && editing.number === node.number

    return (
      <React.Fragment key={node.number}>
        <div
          className={`tree-row${multiSelected && multiSelected.has(node.number) ? ' selected' : ''}`}
          style={{ paddingLeft: 6 + depth * 18 }}
          onClick={(e) => onSelect(node, e.ctrlKey || e.metaKey, e.shiftKey)}
          onContextMenu={(e) => openMenu(e, node)}
        >
          {isLeaf ? (
            <span className="expand-btn placeholder" />
          ) : (
            <button
              className="expand-btn"
              onClick={(e) => { e.stopPropagation(); onToggle(node.number) }}
              title={isExpanded ? '折叠' : '展开'}
            >
              {isExpanded ? '▾' : '▸'}
            </button>
          )}
          <span className={`status-dot ${node.status_color || 'empty'}`} />
          <span
            className="row-number"
            onClick={(e) => {
              if (e.ctrlKey || e.metaKey) {
                e.stopPropagation()
                copyText(node.number)
                onCopy(node.number)
              }
            }}
            title="Ctrl+点击复制图号"
          >
            {node.number}
          </span>
          {editingThis && editing.field === 'name' ? (
            <input
              className="inline-edit"
              value={editing.value}
              autoFocus
              onChange={(e) => setEditing({ ...editing, value: e.target.value })}
              onBlur={commitEdit}
              onKeyDown={(e) => { if (e.key === 'Enter') commitEdit(); if (e.key === 'Escape') setEditing(null) }}
            />
          ) : (
            <span
              className="row-name"
              onDoubleClick={(e) => { e.stopPropagation(); startEdit(node, 'name') }}
              title="双击编辑名称"
            >
              {node.name || '\u00A0'}
            </span>
          )}
          {editingThis && editing.field === 'memo' ? (
            <input
              className="inline-edit"
              style={{ flex: 1 }}
              value={editing.value}
              autoFocus
              onChange={(e) => setEditing({ ...editing, value: e.target.value })}
              onBlur={commitEdit}
              onKeyDown={(e) => { if (e.key === 'Enter') commitEdit(); if (e.key === 'Escape') setEditing(null) }}
            />
          ) : (
            <span
              className="row-memo"
              onDoubleClick={(e) => { e.stopPropagation(); startEdit(node, 'memo') }}
              title="双击编辑备注"
            >
              {node.memo || '\u00A0'}
            </span>
          )}
          {!isLeaf && (
            <span className="row-actions">
              <button title="添加组件" onClick={(e) => { e.stopPropagation(); onAdd(node, 'component') }}>+组件</button>
              <button title="添加零件" onClick={(e) => { e.stopPropagation(); onAdd(node, 'part') }}>+零件</button>
              <button title="重命名" onClick={(e) => { e.stopPropagation(); onRename(node) }}>✎</button>
              {node.node_type !== 'root' && (
                <button title="删除" onClick={(e) => { e.stopPropagation(); onDelete(node) }}>🗑</button>
              )}
            </span>
          )}
        </div>
        {isExpanded && kids.map((k) => renderNode(k, depth + 1))}
      </React.Fragment>
    )
  }

  const roots = childrenMap.__root__ || nodes.filter((n) => !n.parent)

  return (
    <div className="tree-pane">
      {roots.map((r) => renderNode(r, 0))}
      {menu && (
        <div className="context-menu" style={{ left: menu.x, top: menu.y }}>
          <button onClick={() => { onAdd(menu.node, 'component'); setMenu(null) }}>添加组件</button>
          <button onClick={() => { onAdd(menu.node, 'part'); setMenu(null) }}>添加零件</button>
          <div className="sep" />
          <button onClick={() => { onRename(menu.node); setMenu(null) }}>重命名</button>
          {menu.node.node_type !== 'root' && (
            <button onClick={() => { onDelete(menu.node); setMenu(null) }}>删除</button>
          )}
          <div className="sep" />
          {COLOR_OPTIONS.map((c) => (
            <button key={c.key} onClick={() => { onColor(menu.node, c.key); setMenu(null) }}>
              设置颜色：{c.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
