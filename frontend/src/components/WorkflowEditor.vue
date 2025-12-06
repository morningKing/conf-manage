<template>
  <div class="workflow-editor">
    <div class="editor-toolbar">
      <el-space>
        <el-button :icon="Plus" @click="addScriptNode" type="primary">添加脚本节点</el-button>
        <el-button :icon="Clock" @click="addDelayNode">添加延迟节点</el-button>
        <el-button :icon="Delete" @click="clearAll" :disabled="nodes.length === 0">清空</el-button>
        <el-divider direction="vertical" />
        <span class="tip">提示：拖拽节点移动位置，连接节点创建依赖关系</span>
      </el-space>
    </div>

    <div class="flow-container">
      <VueFlow
        v-model:nodes="flowNodes"
        v-model:edges="flowEdges"
        @connect="onConnect"
        @edge-update="onEdgeUpdate"
        @nodes-change="onNodesChange"
        @edges-change="onEdgesChange"
        :default-viewport="{ zoom: 1 }"
        :min-zoom="0.2"
        :max-zoom="4"
      >
        <Background pattern-color="#aaa" :gap="16" />
        <Controls />

        <template #node-script="nodeProps">
          <ScriptNode
            :data="nodeProps.data"
            :id="nodeProps.id"
            @delete="deleteNode"
            @edit="editNode"
          />
        </template>

        <template #node-delay="nodeProps">
          <DelayNode
            :data="nodeProps.data"
            :id="nodeProps.id"
            @delete="deleteNode"
            @edit="editNode"
          />
        </template>
      </VueFlow>
    </div>

    <!-- 编辑脚本节点对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑节点" width="500px">
      <el-form label-width="100px">
        <el-form-item label="节点名称">
          <el-input v-model="currentNode.label" placeholder="请输入节点名称" />
        </el-form-item>
        <el-form-item v-if="currentNode.type === 'script'" label="选择脚本">
          <el-select v-model="currentNode.scriptId" placeholder="请选择脚本" style="width: 100%">
            <el-option
              v-for="script in scripts"
              :key="script.id"
              :label="script.name"
              :value="script.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="currentNode.type === 'delay'" label="延迟时间(秒)">
          <el-input-number v-model="currentNode.delay" :min="1" :max="3600" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNodeEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 编辑边条件对话框 -->
    <el-dialog v-model="edgeDialogVisible" title="设置连接条件" width="500px">
      <el-form label-width="100px">
        <el-form-item label="条件类型">
          <el-select v-model="currentEdge.conditionType" placeholder="请选择条件类型" style="width: 100%">
            <el-option label="无条件（始终执行）" value="none" />
            <el-option label="前置节点成功" value="success" />
            <el-option label="前置节点失败" value="failed" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="edgeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdgeEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, computed, defineProps, defineEmits } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { Plus, Clock, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import ScriptNode from './workflow-nodes/ScriptNode.vue'
import DelayNode from './workflow-nodes/DelayNode.vue'

// 只导入核心样式，background 和 controls 的样式已经包含在核心包中
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

const props = defineProps({
  nodes: {
    type: Array,
    default: () => []
  },
  edges: {
    type: Array,
    default: () => []
  },
  scripts: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:nodes', 'update:edges'])

// Vue Flow 实例
const { addNodes, addEdges, removeNodes, removeEdges, updateNode, updateEdge } = useVueFlow()

// 内部状态
const flowNodes = ref([])
const flowEdges = ref([])
const editDialogVisible = ref(false)
const edgeDialogVisible = ref(false)
const currentNode = ref({})
const currentEdge = ref({})
const nodeIdCounter = ref(1)
const edgeIdCounter = ref(1)

// 将外部 nodes 转换为 VueFlow 格式
const convertToFlowNodes = (nodes) => {
  return nodes.map(node => ({
    id: node.node_id,
    type: node.node_type,
    position: node.position || { x: 100, y: 100 },
    data: {
      label: node.config?.label || `节点 ${node.node_id}`,
      scriptId: node.script_id,
      script: node.script,
      config: node.config || {},
      nodeType: node.node_type
    }
  }))
}

// 将外部 edges 转换为 VueFlow 格式
const convertToFlowEdges = (edges) => {
  return edges.map(edge => ({
    id: edge.edge_id,
    source: edge.source,
    target: edge.target,
    type: 'smoothstep',
    animated: true,
    data: {
      condition: edge.condition
    }
  }))
}

// 将 VueFlow 格式转换回外部格式
const convertFromFlowNodes = (nodes) => {
  return nodes.map(node => ({
    node_id: node.id,
    node_type: node.type,
    script_id: node.data.scriptId,
    config: {
      ...node.data.config,
      label: node.data.label,
      delay: node.data.delay
    },
    position: node.position
  }))
}

const convertFromFlowEdges = (edges) => {
  return edges.map(edge => ({
    edge_id: edge.id,
    source: edge.source,
    target: edge.target,
    condition: edge.data?.condition
  }))
}

// 监听外部数据变化
watch(() => props.nodes, (newNodes) => {
  if (newNodes && newNodes.length > 0) {
    flowNodes.value = convertToFlowNodes(newNodes)
  }
}, { immediate: true, deep: true })

watch(() => props.edges, (newEdges) => {
  if (newEdges && newEdges.length > 0) {
    flowEdges.value = convertToFlowEdges(newEdges)
  }
}, { immediate: true, deep: true })

// 监听内部变化并同步到外部
watch(flowNodes, (newNodes) => {
  emit('update:nodes', convertFromFlowNodes(newNodes))
}, { deep: true })

watch(flowEdges, (newEdges) => {
  emit('update:edges', convertFromFlowEdges(newEdges))
}, { deep: true })

// 添加脚本节点
const addScriptNode = () => {
  const nodeId = `node_${nodeIdCounter.value++}`
  const newNode = {
    id: nodeId,
    type: 'script',
    position: { x: Math.random() * 300 + 100, y: Math.random() * 300 + 100 },
    data: {
      label: `脚本节点 ${nodeId}`,
      scriptId: null,
      nodeType: 'script',
      config: {}
    }
  }
  flowNodes.value.push(newNode)
}

// 添加延迟节点
const addDelayNode = () => {
  const nodeId = `node_${nodeIdCounter.value++}`
  const newNode = {
    id: nodeId,
    type: 'delay',
    position: { x: Math.random() * 300 + 100, y: Math.random() * 300 + 100 },
    data: {
      label: `延迟节点 ${nodeId}`,
      delay: 5,
      nodeType: 'delay',
      config: {}
    }
  }
  flowNodes.value.push(newNode)
}

// 删除节点
const deleteNode = (nodeId) => {
  flowNodes.value = flowNodes.value.filter(n => n.id !== nodeId)
  flowEdges.value = flowEdges.value.filter(e => e.source !== nodeId && e.target !== nodeId)
}

// 编辑节点
const editNode = (nodeId) => {
  const node = flowNodes.value.find(n => n.id === nodeId)
  if (node) {
    currentNode.value = {
      id: node.id,
      type: node.type,
      label: node.data.label,
      scriptId: node.data.scriptId,
      delay: node.data.delay || 5
    }
    editDialogVisible.value = true
  }
}

// 保存节点编辑
const saveNodeEdit = () => {
  const nodeIndex = flowNodes.value.findIndex(n => n.id === currentNode.value.id)
  if (nodeIndex !== -1) {
    flowNodes.value[nodeIndex].data = {
      ...flowNodes.value[nodeIndex].data,
      label: currentNode.value.label,
      scriptId: currentNode.value.scriptId,
      delay: currentNode.value.delay
    }

    // 更新脚本信息
    if (currentNode.value.type === 'script' && currentNode.value.scriptId) {
      const script = props.scripts.find(s => s.id === currentNode.value.scriptId)
      if (script) {
        flowNodes.value[nodeIndex].data.script = script
      }
    }
  }
  editDialogVisible.value = false
}

// 连接节点
const onConnect = (params) => {
  const edgeId = `edge_${edgeIdCounter.value++}`
  const newEdge = {
    id: edgeId,
    source: params.source,
    target: params.target,
    type: 'smoothstep',
    animated: true,
    data: {
      condition: null
    }
  }

  flowEdges.value.push(newEdge)

  // 打开条件设置对话框
  currentEdge.value = {
    id: edgeId,
    conditionType: 'none'
  }
  edgeDialogVisible.value = true
}

// 保存边编辑
const saveEdgeEdit = () => {
  const edgeIndex = flowEdges.value.findIndex(e => e.id === currentEdge.value.id)
  if (edgeIndex !== -1) {
    let condition = null
    if (currentEdge.value.conditionType === 'success') {
      condition = {
        type: 'success',
        node_id: flowEdges.value[edgeIndex].source
      }
    } else if (currentEdge.value.conditionType === 'failed') {
      condition = {
        type: 'failed',
        node_id: flowEdges.value[edgeIndex].source
      }
    }

    flowEdges.value[edgeIndex].data = {
      condition
    }
  }
  edgeDialogVisible.value = false
}

// 更新边
const onEdgeUpdate = ({ edge, connection }) => {
  const edgeIndex = flowEdges.value.findIndex(e => e.id === edge.id)
  if (edgeIndex !== -1) {
    flowEdges.value[edgeIndex] = {
      ...flowEdges.value[edgeIndex],
      source: connection.source,
      target: connection.target
    }
  }
}

// 节点变化
const onNodesChange = (changes) => {
  changes.forEach(change => {
    if (change.type === 'position' && change.position) {
      const node = flowNodes.value.find(n => n.id === change.id)
      if (node) {
        node.position = change.position
      }
    } else if (change.type === 'remove') {
      deleteNode(change.id)
    }
  })
}

// 边变化
const onEdgesChange = (changes) => {
  changes.forEach(change => {
    if (change.type === 'remove') {
      flowEdges.value = flowEdges.value.filter(e => e.id !== change.id)
    }
  })
}

// 清空所有节点和边
const clearAll = () => {
  flowNodes.value = []
  flowEdges.value = []
  nodeIdCounter.value = 1
  edgeIdCounter.value = 1
}
</script>

<style scoped>
.workflow-editor {
  height: 600px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.editor-toolbar {
  padding: 12px 16px;
  border-bottom: 1px solid #dcdfe6;
  background: #f5f7fa;
}

.tip {
  font-size: 12px;
  color: #909399;
}

.flow-container {
  flex: 1;
  position: relative;
  background: #fafafa;
}

:deep(.vue-flow__node) {
  cursor: move;
}

:deep(.vue-flow__edge-path) {
  stroke: #409eff;
  stroke-width: 2;
}

:deep(.vue-flow__edge.selected .vue-flow__edge-path) {
  stroke: #67c23a;
}
</style>
