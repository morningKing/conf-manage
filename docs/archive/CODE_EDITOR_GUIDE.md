# 代码编辑器功能说明

## 新增的代码编辑器功能 ✨

系统现在使用 **CodeMirror 6** 作为代码编辑器，提供专业的代码编辑体验。

### 主要特性

#### 🎨 语法高亮
- **Python**: 完整的 Python 语法高亮支持
- **JavaScript**: 完整的 JavaScript 语法高亮支持
- 自动根据脚本类型切换语言模式

#### 🌙 暗色主题
- 专业的 One Dark 主题
- 适合长时间编码，保护眼睛
- 高对比度，易于阅读

#### 💡 智能编辑
- **行号显示**: 每行代码都有行号
- **当前行高亮**: 光标所在行自动高亮
- **自动缩进**: 支持智能缩进
- **括号匹配**: 自动匹配和高亮括号
- **多行编辑**: 支持多光标编辑
- **代码折叠**: 支持代码块折叠（即将支持）

#### ⌨️ 快捷键支持
- `Ctrl/Cmd + Z`: 撤销
- `Ctrl/Cmd + Y`: 重做
- `Ctrl/Cmd + F`: 查找
- `Ctrl/Cmd + H`: 替换
- `Ctrl/Cmd + A`: 全选
- `Tab`: 缩进
- `Shift + Tab`: 取消缩进

#### 📏 可调节高度
- 默认高度 500px
- 支持滚动查看大文件
- 自定义滚动条样式

#### 🔒 只读模式
- 版本查看时自动启用只读模式
- 防止意外修改历史版本代码

## 使用场景

### 1. 创建/编辑脚本
在脚本管理页面，创建或编辑脚本时：
- 自动根据选择的脚本类型（Python/JavaScript）高亮代码
- 切换脚本类型时，编辑器自动切换语法高亮

### 2. 查看版本历史
在版本历史对话框中：
- 点击"查看"按钮
- 在代码查看器中以只读模式查看历史代码
- 完整的语法高亮支持
- 便于对比和回顾代码变更

## 技术实现

### CodeEditor 组件

位置: `frontend/src/components/CodeEditor.vue`

**Props:**
```javascript
{
  modelValue: String,      // 代码内容（v-model）
  language: String,        // 语言类型: 'python' | 'javascript'
  readonly: Boolean,       // 是否只读
  height: String,          // 编辑器高度，默认 '400px'
  theme: String           // 主题: 'light' | 'dark'
}
```

**使用示例:**
```vue
<CodeEditor
  v-model="code"
  language="python"
  height="500px"
  theme="dark"
/>
```

**只读模式:**
```vue
<CodeEditor
  :model-value="code"
  language="javascript"
  :readonly="true"
/>
```

### 集成位置

#### Scripts.vue
- **脚本编辑对话框**: 可编辑模式，自动语法高亮
- **版本查看对话框**: 只读模式，语法高亮

### CodeMirror 扩展

当前启用的扩展：
- `basicSetup`: 基础编辑功能（行号、折叠等）
- `python()`: Python 语法支持
- `javascript()`: JavaScript 语法支持
- `oneDark`: One Dark 主题
- `EditorView.updateListener`: 监听内容变化
- `EditorView.editable`: 可编辑状态控制
- `EditorState.readOnly`: 只读状态控制

## 自定义样式

编辑器支持自定义样式：

```css
/* 编辑器字体 */
.code-editor :deep(.cm-editor) {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
}

/* 行高 */
.code-editor :deep(.cm-line) {
  line-height: 1.6;
}

/* 选中文本颜色 */
.code-editor :deep(.cm-selectionBackground) {
  background-color: rgba(64, 158, 255, 0.3) !important;
}
```

## Python 代码示例

```python
#!/usr/bin/env python3
"""
示例Python脚本
"""

import sys
import json

def main():
    print("Hello, Python!")

    # 列表推导式
    numbers = [x ** 2 for x in range(10)]

    # 字典
    config = {
        "name": "Script Manager",
        "version": "1.0.0"
    }

    return 0

if __name__ == '__main__':
    sys.exit(main())
```

## JavaScript 代码示例

```javascript
#!/usr/bin/env node
/**
 * 示例JavaScript脚本
 */

const fs = require('fs');
const path = require('path');

async function main() {
    console.log("Hello, JavaScript!");

    // 箭头函数
    const square = (x) => x ** 2;

    // 对象
    const config = {
        name: "Script Manager",
        version: "1.0.0"
    };

    return 0;
}

main().catch(console.error);
```

## 依赖包

```json
{
  "dependencies": {
    "codemirror": "^6.0.1",
    "@codemirror/lang-javascript": "^6.2.1",
    "@codemirror/lang-python": "^6.1.3",
    "@codemirror/theme-one-dark": "^6.1.2"
  }
}
```

## 未来计划

- [ ] 添加更多语言支持（JSON, YAML, Shell等）
- [ ] 代码提示和自动补全
- [ ] 代码片段（Snippets）
- [ ] 多主题切换
- [ ] 代码格式化
- [ ] 错误检查和 Linting
- [ ] Vim/Emacs 键位绑定
- [ ] 代码搜索和替换增强

## 相关文件

- 编辑器组件: `frontend/src/components/CodeEditor.vue`
- 使用示例: `frontend/src/views/Scripts.vue`
- 依赖配置: `frontend/package.json`

## 故障排除

**问题1: 语法高亮不显示**
- 检查是否正确设置 `language` 属性
- 确认语言值为 `python` 或 `javascript`
- 刷新页面重新加载编辑器

**问题2: 编辑器高度异常**
- 检查 `height` 属性设置
- 确保父容器有足够空间
- 使用浏览器开发者工具检查 CSS

**问题3: 无法输入内容**
- 确认 `readonly` 属性未设置为 `true`
- 检查是否有其他输入限制
- 查看浏览器控制台错误信息

## 性能优化

- 使用 `v-if` 而非 `v-show` 控制编辑器显示
- 避免频繁创建和销毁编辑器实例
- 大文件（>10000行）考虑使用虚拟滚动
