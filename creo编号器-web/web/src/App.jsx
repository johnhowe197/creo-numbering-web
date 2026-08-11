import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from './api'
import { TopBar } from './components/TopBar'
import { TreeView } from './components/TreeView'
import { PropertyPanel } from './components/PropertyPanel'
import { NodeDialog } from './components/NodeDialog'

const COLOR_KEYS = ['', 'red', 'yellow', 'green', 'blue']

export default function App() {
  const [projects, setProjects] = useState([])
  const [projectId, setProjectId] = useState(null)
  const [project, setProject] = useState(null)
  const [selected, setSelected] = useState(null)
  const [multiSelected, setMultiSelected] = useState(() => new Set())
  const [expanded, setExpanded] = useState(() => new Set())
  const [dialog, setDialog] = useState(null) // { type, parent }
  const [status, setStatus] = useState('就绪')

  const loadProjects = useCallback(async () => {
    const list = await api.listProjects()
    setProjects(list)
    return list
  }, [])

  const loadProject = useCallback(async (id) => {
    const data = await api.getProject(id)
    setProject(data)
    return data
  }, [])

  useEffect(() => {
    loadProjects().catch((e) => setStatus(`加载项目失败: ${e.message}`))
  }, [loadProjects])

  useEffect(() => {
    if (projectId == null) {
      setProject(null)
      setSelected(null)
      setMultiSelected(new Set())
      return
    }
    loadProject(projectId).catch((e) => setStatus(`加载失败: ${e.message}`))
  }, [projectId, loadProject])

  const nodes = project ? project.nodes : []
  const nodeMap = useMemo(() => {
    const m = {}
    for (const n of nodes) m[n.number] = n
    return m
  }, [nodes])

  const rootNode = useMemo(
    () => nodes.find((n) => n.node_type === 'root') || nodes.find((n) => !n.parent),
    [nodes],
  )

  const selectedNode = selected ? nodeMap[selected] : null

  const stats = useMemo(() => {
    let components = 0
    let parts = 0
    for (const n of nodes) {
      if (n.node_type === 'component') components += 1
      else if (n.node_type === 'part') parts += 1
    }
    return { total: nodes.length, components, parts }
  }, [nodes])

  const refresh = useCallback(async () => {
    if (projectId == null) return
    const data = await loadProject(projectId)
    if (selected && !data.nodes.some((n) => n.number === selected)) {
      setSelected(null)
      setMultiSelected(new Set())
    }
  }, [projectId, loadProject, selected])

  const selectedCount = multiSelected.size

  async function run(action) {
    try {
      await action()
    } catch (e) {
      setStatus(e.message)
    }
  }

  const handleNewProject = () =>
    run(async () => {
      const rootInput = window.prompt('请输入根图号（如 05S01101）：')
      const root = (rootInput || '').trim()
      if (!root) return
      const nameInput = window.prompt('请输入项目中文名称（可留空，如：标准化中部槽）：', root)
      const name = (nameInput || '').trim() || root
      const created = await api.createProject(root, name)
      setProjectId(created.id)
      setExpanded(new Set([root]))
      await loadProjects()
      setStatus(`已创建项目: ${root}${name !== root ? `（${name}）` : ''}`)
    })

  const handleRenameProject = () =>
    run(async () => {
      if (!project) return
      const input = window.prompt('请输入项目名称（如：标准化中部槽）：', project.name)
      const name = (input || '').trim()
      if (!name || name === project.name) return
      const result = await api.updateProject(project.id, { name })
      await loadProjects()
      if (projectId != null) await loadProject(projectId)
      setStatus(`项目名称已更新: ${result.name}`)
    })

  const handleDeleteProject = () =>
    run(async () => {
      if (!project) return
      if (!window.confirm(`确定删除项目 ${project.root_number} 及其全部数据？此操作不可恢复。`)) return
      await api.deleteProject(project.id)
      setProjectId(null)
      setSelected(null)
      await loadProjects()
      setStatus(`已删除项目: ${project.root_number}`)
    })

  const handleImport = (file) =>
    run(async () => {
      const text = await file.text()
      const data = JSON.parse(text)
      const result = await api.importProject(data)
      setProjectId(result.id)
      await loadProjects()
      setStatus(`已导入项目 ${result.root_number}（${result.node_count} 个节点）`)
    })

  const handleAdd = (parent, type) => {
    if (!parent) {
      setStatus('请先选择父节点')
      return
    }
    if (parent.node_type === 'part') {
      setStatus('零件不能作为父级')
      return
    }
    setDialog({ type, parent })
  }

  const handleRename = (node) =>
    run(async () => {
      const input = window.prompt('请输入新的图号：', node.number)
      const newNumber = (input || '').trim()
      if (!newNumber || newNumber === node.number) return
      const result = await api.updateNode(project.id, node.number, { new_number: newNumber })
      await refresh()
      setSelected(result.number)
      setStatus(`已重命名: ${node.number} -> ${result.number}`)
    })

  const handleDelete = (node) =>
    run(async () => {
      if (node.node_type === 'root') {
        setStatus('不能删除根节点')
        return
      }
      if (!window.confirm(`确定删除节点 ${node.number} 及其所有子节点？`)) return
      await api.deleteNode(project.id, node.number)
      await refresh()
      setStatus(`已删除节点: ${node.number}`)
    })

  const handleDeleteSelected = () =>
    run(async () => {
      const list = [...multiSelected]
      if (list.length === 0) return
      if (!window.confirm(`确定删除选中的 ${list.length} 个节点及其所有子节点？`)) return
      for (const num of list) {
        try {
          await api.deleteNode(project.id, num)
        } catch {
          // 节点可能已随祖先一并删除，忽略
        }
      }
      await refresh()
      setSelected(null)
      setMultiSelected(new Set())
      setStatus(`已删除 ${list.length} 个节点`)
    })

  const handleColor = (node, color) =>
    run(async () => {
      await api.updateNode(project.id, node.number, { status_color: color })
      await refresh()
    })

  const handleBulkColor = (color) =>
    run(async () => {
      const list = [...multiSelected]
      if (list.length === 0) return
      for (const num of list) {
        await api.updateNode(project.id, num, { status_color: color })
      }
      await refresh()
      setStatus(`已为 ${list.length} 个节点设置颜色`)
    })

  const handleSelect = (node, additive) => {
    setSelected(node.number)
    setMultiSelected((prev) => {
      const next = new Set(prev)
      if (additive) {
        if (next.has(node.number)) next.delete(node.number)
        else next.add(node.number)
        return next
      }
      next.clear()
      next.add(node.number)
      return next
    })
  }

  const handleEditField = (number, field, value) =>
    run(async () => {
      const payload = field === 'name' ? { name: value } : { memo: value }
      await api.updateNode(project.id, number, payload)
      await refresh()
    })

  const handleToggle = (number) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(number)) next.delete(number)
      else next.add(number)
      return next
    })
  }

  const handleCopy = (number) => {
    setStatus(`已复制图号: ${number}`)
  }

  const handleExpandAll = () => {
    setExpanded(new Set(nodes.filter((n) => n.node_type !== 'part').map((n) => n.number)))
  }

  const handleCollapseAll = () => setExpanded(new Set())

  const handleDialogDone = async (createdList) => {
    setDialog(null)
    await refresh()
    const list = Array.isArray(createdList) ? createdList : []
    if (list.length > 0) {
      const first = list[0]
      setExpanded((prev) => new Set(prev).add(first.parent))
      setSelected(first.number)
    }
    const kind = dialog ? (dialog.type === 'part' ? '零件' : '组件') : '节点'
    setStatus(
      list.length > 1
        ? `已批量添加 ${list.length} 个${kind}（${list[0].number} … ${list[list.length - 1].number}）`
        : `已添加${kind}: ${list[0] ? list[0].number : ''}`,
    )
  }

  return (
    <div className="app">
      <TopBar
        projects={projects}
        projectId={projectId}
        onSelectProject={setProjectId}
        onNewProject={handleNewProject}
        onRenameProject={handleRenameProject}
        onDeleteProject={handleDeleteProject}
        onImport={handleImport}
      />

      <div className="toolbar">
        <div className="group">
          <button onClick={() => handleAdd(selectedNode || rootNode, 'component')}>添加组件</button>
          <button onClick={() => handleAdd(selectedNode || rootNode, 'part')}>添加零件</button>
        </div>
        <div className="divider" />
        <div className="group">
          <button disabled={selectedCount !== 1} onClick={() => selectedNode && handleRename(selectedNode)}>重命名</button>
          <button disabled={selectedCount === 0} onClick={handleDeleteSelected}>
            {selectedCount > 1 ? `删除(${selectedCount})` : '删除'}
          </button>
        </div>
        <div className="divider" />
        <div className="group">
          <button onClick={handleExpandAll}>展开全部</button>
          <button onClick={handleCollapseAll}>折叠全部</button>
        </div>
        <div className="divider" />
        <div className="group">
          <button
            disabled={selectedCount === 0}
            onClick={() => handleBulkColor('')}
            title="清除颜色"
          >
            无色
          </button>
          {COLOR_KEYS.slice(1).map((c) => (
            <button
              key={c}
              disabled={selectedCount === 0}
              onClick={() => handleBulkColor(c)}
              title={`设置颜色：${c}`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <div className="main">
        <TreeView
          nodes={nodes}
          selected={selected}
          multiSelected={multiSelected}
          onSelect={handleSelect}
          expanded={expanded}
          onToggle={handleToggle}
          onAdd={handleAdd}
          onRename={handleRename}
          onDelete={handleDelete}
          onColor={handleColor}
          onEditField={handleEditField}
          onCopy={handleCopy}
        />
        <PropertyPanel
          node={selectedNode}
          children={selectedNode ? (nodes.filter((n) => n.parent === selectedNode.number)) : []}
        />
      </div>

      <div className="statusbar">
        <span>
          {status}
          {selectedCount > 0 && `（已选 ${selectedCount} 个节点）`}
        </span>
        <span style={{ marginLeft: 'auto' }}>
          节点数: {stats.total} | 组件: {stats.components} | 零件: {stats.parts}
        </span>
      </div>

      {dialog && (
        <NodeDialog
          project={project}
          parentNode={dialog.parent}
          type={dialog.type}
          onClose={() => setDialog(null)}
          onDone={handleDialogDone}
        />
      )}
    </div>
  )
}
