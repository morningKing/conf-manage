<template>
  <div class="code-editor-wrapper">
    <div ref="editorRef" class="code-editor"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { EditorView, basicSetup } from 'codemirror'
import { EditorState } from '@codemirror/state'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { oneDark } from '@codemirror/theme-one-dark'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  language: {
    type: String,
    default: 'python',
    validator: (value) => ['python', 'javascript'].includes(value)
  },
  readonly: {
    type: Boolean,
    default: false
  },
  height: {
    type: String,
    default: '400px'
  },
  theme: {
    type: String,
    default: 'dark',
    validator: (value) => ['light', 'dark'].includes(value)
  }
})

const emit = defineEmits(['update:modelValue'])

const editorRef = ref(null)
let editorView = null

// 获取语言扩展
const getLanguageExtension = (lang) => {
  switch (lang) {
    case 'python':
      return python()
    case 'javascript':
      return javascript()
    default:
      return python()
  }
}

// 创建编辑器
const createEditor = () => {
  if (!editorRef.value) return

  // 构建扩展列表
  const extensions = [
    basicSetup,
    getLanguageExtension(props.language),
    EditorView.updateListener.of((update) => {
      if (update.docChanged) {
        emit('update:modelValue', update.state.doc.toString())
      }
    }),
    EditorView.editable.of(!props.readonly),
    EditorState.readOnly.of(props.readonly)
  ]

  // 添加主题
  if (props.theme === 'dark') {
    extensions.push(oneDark)
  }

  // 创建状态
  const state = EditorState.create({
    doc: props.modelValue || '',
    extensions
  })

  // 创建视图
  editorView = new EditorView({
    state,
    parent: editorRef.value
  })
}

// 更新编辑器内容
const updateEditorContent = (newValue) => {
  if (!editorView) return

  const currentValue = editorView.state.doc.toString()
  if (currentValue !== newValue) {
    editorView.dispatch({
      changes: {
        from: 0,
        to: currentValue.length,
        insert: newValue || ''
      }
    })
  }
}

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  updateEditorContent(newValue)
})

// 监听语言变化
watch(() => props.language, () => {
  if (editorView) {
    editorView.destroy()
    createEditor()
  }
})

// 监听主题变化
watch(() => props.theme, () => {
  if (editorView) {
    editorView.destroy()
    createEditor()
  }
})

onMounted(() => {
  createEditor()
})

onBeforeUnmount(() => {
  if (editorView) {
    editorView.destroy()
  }
})

// 暴露方法给父组件
defineExpose({
  focus: () => editorView?.focus(),
  getValue: () => editorView?.state.doc.toString() || '',
  setValue: (value) => updateEditorContent(value)
})
</script>

<style scoped>
.code-editor-wrapper {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.code-editor {
  width: 100%;
  height: v-bind(height);
  overflow: auto;
}

/* CodeMirror 样式调整 */
.code-editor :deep(.cm-editor) {
  width: 100%;
  height: 100%;
  font-size: 14px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.code-editor :deep(.cm-scroller) {
  overflow: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.code-editor :deep(.cm-content) {
  padding: 10px 0;
}

.code-editor :deep(.cm-line) {
  padding: 0 4px;
  line-height: 1.6;
}

/* 光标样式 */
.code-editor :deep(.cm-cursor) {
  border-left-width: 2px;
}

/* 选中文本样式 */
.code-editor :deep(.cm-selectionBackground) {
  background-color: rgba(64, 158, 255, 0.3) !important;
}

/* 行号样式 */
.code-editor :deep(.cm-gutters) {
  background-color: #f5f7fa;
  border-right: 1px solid #dcdfe6;
  color: #909399;
  padding-right: 8px;
}

/* 暗色主题下的行号 */
.code-editor :deep(.cm-theme-dark .cm-gutters) {
  background-color: #1e1e1e;
  border-right: 1px solid #333;
}

/* 活动行高亮 */
.code-editor :deep(.cm-activeLine) {
  background-color: rgba(64, 158, 255, 0.05);
}

/* 暗色主题下的活动行 */
.code-editor :deep(.cm-theme-dark .cm-activeLine) {
  background-color: rgba(255, 255, 255, 0.05);
}

/* 滚动条样式 */
.code-editor :deep(.cm-scroller::-webkit-scrollbar) {
  width: 10px;
  height: 10px;
}

.code-editor :deep(.cm-scroller::-webkit-scrollbar-track) {
  background: #f1f1f1;
}

.code-editor :deep(.cm-scroller::-webkit-scrollbar-thumb) {
  background: #888;
  border-radius: 5px;
}

.code-editor :deep(.cm-scroller::-webkit-scrollbar-thumb:hover) {
  background: #555;
}

/* 暗色主题滚动条 */
.code-editor :deep(.cm-theme-dark .cm-scroller::-webkit-scrollbar-track) {
  background: #1e1e1e;
}

.code-editor :deep(.cm-theme-dark .cm-scroller::-webkit-scrollbar-thumb) {
  background: #555;
}

.code-editor :deep(.cm-theme-dark .cm-scroller::-webkit-scrollbar-thumb:hover) {
  background: #777;
}
</style>
