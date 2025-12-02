<template>
  <div class="code-editor-container">
    <!-- 工具栏 -->
    <div class="editor-toolbar" v-if="!readonly">
      <el-button-group>
        <el-button size="small" @click="formatCode" :loading="formatting">
          <el-icon><Document /></el-icon>
          格式化
        </el-button>
        <el-button size="small" @click="triggerSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button size="small" @click="triggerFileImport">
          <el-icon><Upload /></el-icon>
          导入文件
        </el-button>
        <el-button size="small" @click="showTemplateDialog = true">
          <el-icon><Collection /></el-icon>
          模板
        </el-button>
      </el-button-group>

      <div class="toolbar-info">
        <el-tag size="small" type="info">{{ language }}</el-tag>
        <span class="line-col-info">行: {{ cursorLine }} | 列: {{ cursorCol }}</span>
      </div>
    </div>

    <!-- 编辑器 -->
    <div class="code-editor-wrapper">
      <div ref="editorRef" class="code-editor"></div>
    </div>

    <!-- 隐藏的文件输入 -->
    <input
      ref="fileInputRef"
      type="file"
      style="display: none"
      @change="handleFileImport"
      accept=".py,.js,.txt"
    />

    <!-- 模板选择对话框 -->
    <el-dialog v-model="showTemplateDialog" title="代码模板" width="600px">
      <el-tabs v-model="activeTemplateTab">
        <el-tab-pane :label="`${language} 模板`" :name="language">
          <div class="template-list">
            <div
              v-for="template in currentTemplates"
              :key="template.name"
              class="template-item"
              @click="insertTemplate(template)"
            >
              <div class="template-header">
                <span class="template-name">{{ template.name }}</span>
                <el-tag size="small">{{ template.category }}</el-tag>
              </div>
              <div class="template-desc">{{ template.description }}</div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Search, Upload, Collection } from '@element-plus/icons-vue'
import { EditorView, basicSetup } from 'codemirror'
import { EditorState } from '@codemirror/state'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { oneDark } from '@codemirror/theme-one-dark'
import { search, highlightSelectionMatches } from '@codemirror/search'
import { autocompletion } from '@codemirror/autocomplete'
import prettier from 'prettier'
import parserBabel from 'prettier/parser-babel'

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
const fileInputRef = ref(null)
let editorView = null

// UI 状态
const formatting = ref(false)
const showTemplateDialog = ref(false)
const activeTemplateTab = ref(props.language)
const cursorLine = ref(1)
const cursorCol = ref(1)

// 触发搜索功能（使用 CodeMirror 内置搜索）
const triggerSearch = () => {
  if (!editorView) return
  // 触发搜索面板（使用 Mod-f 命令）
  const searchKeymap = editorView.state.facet(EditorView.editorAttributes)
  editorView.focus()
  // 手动触发搜索面板打开
  import('@codemirror/search').then(({ openSearchPanel }) => {
    openSearchPanel(editorView)
  })
}

// 代码模板库
const pythonTemplates = [
  {
    name: '基础脚本模板',
    category: '基础',
    description: 'Python 脚本基础模板，包含参数读取',
    code: `#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本描述
"""
import os
import sys
import json

def main():
    """主函数"""
    # 读取环境变量参数
    param1 = os.getenv('param1', '默认值')

    # 读取上传的文件
    files_json = os.getenv('FILES', '[]')
    files = json.loads(files_json)

    # 你的代码逻辑
    print(f"参数: {param1}")
    print(f"文件: {files}")

if __name__ == '__main__':
    main()
`
  },
  {
    name: '文件处理模板',
    category: '文件操作',
    description: '处理上传文件的模板',
    code: `import os
import json

# 读取上传的文件列表
files_json = os.getenv('FILES', '[]')
files = json.loads(files_json)

for filename in files:
    filepath = os.path.join(os.getcwd(), filename)
    print(f"处理文件: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        # 处理文件内容
        print(f"文件内容长度: {len(content)}")
`
  },
  {
    name: 'API 请求模板',
    category: '网络请求',
    description: '发起 HTTP 请求的模板',
    code: `import requests
import json

def fetch_api():
    """API 请求示例"""
    url = "https://api.example.com/data"
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

if __name__ == '__main__':
    fetch_api()
`
  },
  {
    name: '数据处理模板',
    category: '数据处理',
    description: 'Pandas 数据处理模板',
    code: `import pandas as pd
import os
import json

# 读取上传的文件
files_json = os.getenv('FILES', '[]')
files = json.loads(files_json)

if files:
    # 读取 CSV 文件
    filepath = os.path.join(os.getcwd(), files[0])
    df = pd.read_csv(filepath)

    # 数据处理
    print("数据形状:", df.shape)
    print("\\n数据预览:")
    print(df.head())

    # 数据统计
    print("\\n数据统计:")
    print(df.describe())

    # 保存处理结果
    output_file = "output.csv"
    df.to_csv(output_file, index=False)
    print(f"\\n结果已保存到: {output_file}")
`
  }
]

const javascriptTemplates = [
  {
    name: '基础脚本模板',
    category: '基础',
    description: 'Node.js 脚本基础模板',
    code: `#!/usr/bin/env node
/**
 * 脚本描述
 */
const fs = require('fs');
const path = require('path');

function main() {
    // 读取环境变量参数
    const param1 = process.env.param1 || '默认值';

    // 读取上传的文件
    const filesJson = process.env.FILES || '[]';
    const files = JSON.parse(filesJson);

    // 你的代码逻辑
    console.log(\`参数: \${param1}\`);
    console.log(\`文件: \${files}\`);
}

main();
`
  },
  {
    name: '文件处理模板',
    category: '文件操作',
    description: '处理上传文件的模板',
    code: `const fs = require('fs');
const path = require('path');

// 读取上传的文件列表
const filesJson = process.env.FILES || '[]';
const files = JSON.parse(filesJson);

files.forEach(filename => {
    const filepath = path.join(process.cwd(), filename);
    console.log(\`处理文件: \${filepath}\`);

    const content = fs.readFileSync(filepath, 'utf-8');
    // 处理文件内容
    console.log(\`文件内容长度: \${content.length}\`);
});
`
  },
  {
    name: 'API 请求模板',
    category: '网络请求',
    description: '发起 HTTP 请求的模板',
    code: `const https = require('https');

function fetchAPI() {
    const options = {
        hostname: 'api.example.com',
        path: '/data',
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    };

    return new Promise((resolve, reject) => {
        const req = https.request(options, (res) => {
            let data = '';

            res.on('data', (chunk) => {
                data += chunk;
            });

            res.on('end', () => {
                try {
                    const jsonData = JSON.parse(data);
                    console.log(JSON.stringify(jsonData, null, 2));
                    resolve(jsonData);
                } catch (error) {
                    reject(error);
                }
            });
        });

        req.on('error', (error) => {
            console.error(\`请求失败: \${error.message}\`);
            reject(error);
        });

        req.end();
    });
}

fetchAPI().catch(console.error);
`
  }
]

// 当前模板列表
const currentTemplates = computed(() => {
  return props.language === 'python' ? pythonTemplates : javascriptTemplates
})

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
    search({ top: true }),  // 启用搜索功能
    highlightSelectionMatches(),  // 高亮选中的匹配项
    autocompletion(),  // 启用自动补全
    EditorView.updateListener.of((update) => {
      if (update.docChanged) {
        emit('update:modelValue', update.state.doc.toString())
      }
      // 更新光标位置
      if (update.selectionSet) {
        const pos = update.state.selection.main.head
        const line = update.state.doc.lineAt(pos)
        cursorLine.value = line.number
        cursorCol.value = pos - line.from + 1
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

// 代码格式化
const formatCode = async () => {
  if (!editorView || formatting.value) return

  try {
    formatting.value = true
    const code = editorView.state.doc.toString()

    let formatted
    if (props.language === 'javascript') {
      // 使用 Prettier 格式化 JavaScript
      formatted = await prettier.format(code, {
        parser: 'babel',
        plugins: [parserBabel],
        semi: true,
        singleQuote: true,
        tabWidth: 2
      })
    } else if (props.language === 'python') {
      // Python 格式化（简单版本，仅处理缩进）
      // 注：完整的 Python 格式化需要后端 Black 支持
      formatted = formatPythonCode(code)
    }

    if (formatted && formatted !== code) {
      updateEditorContent(formatted)
      ElMessage.success('代码格式化成功')
    }
  } catch (error) {
    ElMessage.error('格式化失败: ' + error.message)
    console.error('格式化错误:', error)
  } finally {
    formatting.value = false
  }
}

// 简单的 Python 代码格式化（规范化缩进）
const formatPythonCode = (code) => {
  // 简单处理：统一缩进为 4 空格
  const lines = code.split('\n')
  const formatted = lines.map(line => {
    const leadingSpaces = line.match(/^\s*/)[0].length
    const tabCount = Math.floor(leadingSpaces / 4)
    const content = line.trim()
    if (content) {
      return '    '.repeat(tabCount) + content
    }
    return ''
  })
  return formatted.join('\n')
}

// 触发文件导入
const triggerFileImport = () => {
  fileInputRef.value?.click()
}

// 处理文件导入
const handleFileImport = (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    const content = e.target?.result
    if (typeof content === 'string') {
      updateEditorContent(content)
      ElMessage.success(`已导入文件: ${file.name}`)
    }
  }
  reader.onerror = () => {
    ElMessage.error('文件读取失败')
  }
  reader.readAsText(file)

  // 清空 input，以便可以重复选择同一文件
  event.target.value = ''
}

// 插入模板
const insertTemplate = (template) => {
  if (!editorView) return

  const currentCode = editorView.state.doc.toString()
  if (currentCode.trim() && !confirm('当前编辑器有内容，是否替换为模板？')) {
    return
  }

  updateEditorContent(template.code)
  showTemplateDialog.value = false
  ElMessage.success(`已插入模板: ${template.name}`)
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
.code-editor-container {
  width: 100%;
  display: flex;
  flex-direction: column;
}

/* 工具栏样式 */
.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-bottom: none;
  border-radius: 4px 4px 0 0;
}

.toolbar-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.line-col-info {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
}

/* 编辑器包装器 */
.code-editor-wrapper {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 0 0 4px 4px;
  overflow: hidden;
}

/* 当编辑器为只读模式时，不显示工具栏，添加顶部圆角 */
.code-editor-container:has(.editor-toolbar:not(:empty)) .code-editor-wrapper {
  border-radius: 0 0 4px 4px;
}

.code-editor-container:not(:has(.editor-toolbar)) .code-editor-wrapper {
  border-radius: 4px;
}

.code-editor {
  width: 100%;
  height: v-bind(height);
  overflow: auto;
}

/* CodeMirror 样式��整 */
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

/* 搜索匹配高亮 */
.code-editor :deep(.cm-searchMatch) {
  background-color: rgba(255, 213, 79, 0.4);
  outline: 1px solid rgba(255, 213, 79, 0.8);
}

.code-editor :deep(.cm-searchMatch-selected) {
  background-color: rgba(255, 160, 0, 0.5);
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

/* 模板列表样式 */
.template-list {
  max-height: 400px;
  overflow-y: auto;
}

.template-item {
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.template-item:hover {
  border-color: #409eff;
  background-color: #ecf5ff;
  transform: translateX(4px);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.template-name {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
}

.template-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

/* 搜索面板样式 */
.code-editor :deep(.cm-panel.cm-search) {
  background-color: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  padding: 8px;
}

.code-editor :deep(.cm-theme-dark .cm-panel.cm-search) {
  background-color: #2b2b2b;
  border-bottom: 1px solid #444;
}
</style>
