import React, { useEffect, useMemo, useState } from 'react'
import { api } from '../api'

const TYPE_LABEL = { component: '组件', part: '零件' }

/* 判断父级类型：字母组件 / 主机层（根的直接子级两位数字） */
function parentKind(node, rootNumber) {
  const segs = node.number.split('-')
  const level = segs.length > 1 ? segs.slice(1).join('-') : ''
  const isRoot = segs.length === 1
  const alpha = /[A-Za-z]/.test(level)
  const isHostLevel =
    !isRoot && node.node_type !== 'part' &&
    node.parent === rootNumber && /^\d{2}$/.test(level)
  return { alpha, isHostLevel }
}

export function NodeDialog({ project, parentNode, type, onClose, onDone }) {
  const [mode, setMode] = useState('auto')
  const [manualNumber, setManualNumber] = useState('')
  const [error, setError] = useState('')

  const kind = useMemo(
    () => (parentNode ? parentKind(parentNode, project.root_number) : {}),
    [parentNode, project.root_number],
  )

  const isPartBlocked = kind.isHostLevel && type === 'part'
  const forceManual = kind.isHostLevel && type === 'component'

  useEffect(() => {
    if (forceManual) setMode('manual')
  }, [forceManual])

  if (!parentNode) return null

  const hint = (() => {
    if (kind.isHostLevel && type === 'part') {
      return {
        warn: true,
        text: `${parentNode.number} 为主机层，不创建零件。零件请添加到其下的字母组件（如 -ZBC）中。`,
      }
    }
    if (kind.isHostLevel && type === 'component') {
      return {
        text: `${parentNode.number} 为主机层，请输入字母组件图号（如 ${project.root_number}-ZBC、-KTC）。`,
      }
    }
    if (kind.alpha && type === 'component') {
      return {
        text: `字母组件 ${parentNode.number} 下创建组件：自动生成「根前缀 + 两位数字」的全局编号（如 ${project.root_number}-01）。`,
      }
    }
    if (kind.alpha && type === 'part') {
      return {
        text: `字母组件 ${parentNode.number} 下创建零件：使用宿主（${parentNode.parent}）的共享零件序列（如 ${parentNode.parent}-1）。`,
      }
    }
    if (parentNode.node_type === 'root') {
      return {
        text: `根图号 ${parentNode.number} 下创建组件：自动生成两位数字（${parentNode.number}-00、-01…）。`,
      }
    }
    if (type === 'component') {
      return { text: '普通数字组件下创建组件：追加两位数字（追加法）。' }
    }
    return { text: '创建零件：父级图号 + 顺序数字（分叉法）。' }
  })()

  async function submit() {
    setError('')
    try {
      const result = await api.addNode(project.id, type, {
        parent_number: parentNode.number,
        mode,
        number: manualNumber.trim(),
      })
      onDone(result)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="modal-mask" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>添加{TYPE_LABEL[type]} — 父级：{parentNode.number}</h2>
        {!isPartBlocked && (
          <div className={`hint${hint.warn ? ' warn' : ''}`}>{hint.text}</div>
        )}

        {!isPartBlocked && !forceManual && (
          <div className="radio-row">
            <label>
              <input type="radio" checked={mode === 'auto'} onChange={() => setMode('auto')} />
              自动生成
            </label>
            <label>
              <input type="radio" checked={mode === 'manual'} onChange={() => setMode('manual')} />
              手动输入
            </label>
          </div>
        )}

        {(mode === 'manual' || forceManual) && !isPartBlocked && (
          <div className="field">
            <label>图号</label>
            <input
              style={{ width: '100%' }}
              value={manualNumber}
              onChange={(e) => setManualNumber(e.target.value)}
              placeholder={type === 'part' ? '如 05S01101-10-1' : '如 05S01101-ZBC'}
              autoFocus
            />
          </div>
        )}

        {isPartBlocked && (
          <p className="error">{hint.text}</p>
        )}

        <p className="error">{error}</p>

        <div className="actions">
          <button onClick={onClose}>取消</button>
          <button className="primary" disabled={isPartBlocked} onClick={submit}>
            确定
          </button>
        </div>
      </div>
    </div>
  )
}
