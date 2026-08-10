import React from 'react'

const TYPE_LABEL = { root: '根节点', component: '组件', part: '零件' }

export function PropertyPanel({ node, children }) {
  if (!node) {
    return (
      <aside className="property-pane">
        <h3>节点属性</h3>
        <div className="empty-state">点击左侧节点查看详情</div>
      </aside>
    )
  }

  const componentCount = children.filter((c) => c.node_type === 'component').length
  const partCount = children.filter((c) => c.node_type === 'part').length

  return (
    <aside className="property-pane">
      <h3>节点属性</h3>
      <div className="prop-item"><span className="k">图号</span><span className="v">{node.number}</span></div>
      <div className="prop-item"><span className="k">名称</span><span className="v plain">{node.name || '—'}</span></div>
      <div className="prop-item"><span className="k">类型</span><span className="v plain">{TYPE_LABEL[node.node_type] || node.node_type}</span></div>
      <div className="prop-item"><span className="k">父级</span><span className="v">{node.parent || '—'}</span></div>
      <div className="prop-item"><span className="k">子组件数</span><span className="v plain">{componentCount}</span></div>
      <div className="prop-item"><span className="k">子零件数</span><span className="v plain">{partCount}</span></div>
      <div className="prop-item"><span className="k">备注</span><span className="v plain">{node.memo || '—'}</span></div>
      <div className="prop-item"><span className="k">创建时间</span><span className="v plain">{node.created_at}</span></div>
    </aside>
  )
}
