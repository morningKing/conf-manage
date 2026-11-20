/**
 * 管道（线性工作流）与后端 nodes/edges 契约之间的转换层
 *
 * 后端模型是通用 DAG（WorkflowNode/WorkflowEdge）；管道是"每步只依赖上一步"
 * 的退化形态。前端以有序 steps 为唯一编辑形态，保存时转换回 nodes+链式边。
 */

/** 按 node_id 尾部数字排序（node_1, node_2, ...；非数字 id 排最后） */
export function sortNodes(nodes) {
  return [...(nodes || [])].sort((a, b) => nodeOrder(a.node_id) - nodeOrder(b.node_id))
}

function nodeOrder(id) {
  const m = String(id ?? '').match(/(\d+)$/)
  return m ? parseInt(m[1], 10) : Number.MAX_SAFE_INTEGER
}

function safeParse(text) {
  try {
    return JSON.parse(text)
  } catch {
    return {}
  }
}

function parseParamsText(paramsText) {
  if (!paramsText || !paramsText.trim()) return {}
  const parsed = JSON.parse(paramsText) // 语法错误向上抛给调用方提示
  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
    throw new Error('步骤参数必须是 JSON 对象（键值对）')
  }
  return parsed
}

/**
 * steps -> {nodes, edges}
 * steps: [{type:'script', script_id, params_text}, {type:'delay', delay_seconds}]
 */
export function toGraph(steps) {
  const list = steps || []
  const nodes = list.map((step, i) => {
    const nodeId = `node_${i + 1}`
    if (step.type === 'delay') {
      return {
        node_id: nodeId,
        node_type: 'delay',
        script_id: null,
        config: { delay: Number(step.delay_seconds) || 0 },
        position: { x: 100, y: 100 + i * 40 },
      }
    }
    return {
      node_id: nodeId,
      node_type: 'script',
      script_id: step.script_id,
      config: { params: parseParamsText(step.params_text) },
      position: { x: 100, y: 100 + i * 40 },
    }
  })

  const edges = []
  for (let i = 0; i < nodes.length - 1; i++) {
    edges.push({
      edge_id: `edge_${i + 1}`,
      source: nodes[i].node_id,
      target: nodes[i + 1].node_id,
      condition: null,
    })
  }

  return { nodes, edges }
}

/**
 * nodes/edges -> {steps, droppedConditions}
 * 旧 DAG 拍平为线性：按 node_id 序排列，条件边丢弃（返回数量供提示）
 */
export function fromGraph(nodes, edges) {
  const sorted = sortNodes(nodes)
  const steps = sorted.map(n => {
    const config = typeof n.config === 'string' ? safeParse(n.config) : (n.config || {})
    if (n.node_type === 'delay') {
      return { type: 'delay', delay_seconds: Number(config.delay) || 0, script_id: null, params_text: '' }
    }
    return {
      type: 'script',
      script_id: n.script_id,
      params_text: config.params ? JSON.stringify(config.params, null, 2) : '',
      delay_seconds: 0,
    }
  })
  const droppedConditions = (edges || []).filter(e => e.condition).length
  return { steps, droppedConditions }
}

/** 保存前校验：返回错误信息，无问题时返回 null */
export function validateSteps(steps, scripts = []) {
  const list = steps || []
  if (list.length === 0) {
    return '管道至少需要一个步骤'
  }
  const validScriptIds = new Set(scripts.map(s => s.id))
  for (let i = 0; i < list.length; i++) {
    const step = list[i]
    if (step.type === 'script') {
      if (!step.script_id) return `步骤 ${i + 1} 未选择脚本`
      if (!validScriptIds.has(step.script_id)) return `步骤 ${i + 1} 的脚本不存在（请重新选择）`
      if (step.params_text && step.params_text.trim()) {
        try {
          parseParamsText(step.params_text)
        } catch (e) {
          if (e instanceof SyntaxError) return `步骤 ${i + 1} 参数不是合法 JSON：${e.message}`
          return `步骤 ${i + 1}：${e.message}`
        }
      }
    } else if (step.type === 'delay') {
      if (!(Number(step.delay_seconds) > 0)) return `步骤 ${i + 1} 延时秒数必须大于 0`
    } else {
      return `步骤 ${i + 1} 类型未知: ${step.type}`
    }
  }
  return null
}
