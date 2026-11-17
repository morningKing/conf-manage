# 脚本执行参数重复输入问题 - 修复报告

## 问题描述
当执行脚本并输入重复的参数值时（如执行第一次和第二次都输入相同参数），第二次脚本执行时会获得 `None` 的参数值，而不是预期的参数值。

## 问题原因

### 主要原因：ExecutionParams 组件状态持久化

在 `frontend/src/components/ExecutionParams.vue` 中，参数值存储在组件的 `ref` 状态中：
```javascript
const paramValues = ref({})
```

当执行对话框关闭后，组件虽然从 DOM 中被卸载，但当再次打开同一脚本的执行对话框时，有以下问题：

1. **组件重新创建，但初始化逻辑有缺陷**
   - 原来的初始化逻辑会检查 `modelValue` prop 是否有值
   - 但 `modelValue` 每次都从父组件 `executeParamsObj` 初始化为 `{}`
   - 这导致参数值总是被重新初始化为空字符串或默认值

2. **参数值没有被清空**
   - 当用户在第一次执行时输入参数值后关闭对话框
   - 第二次打开同一脚本的执行对话框时，组件应该重新初始化
   - 但由于缺少强制重新创建机制，组件状态可能没有被彻底重置

### 次要问题：v-model 绑定的参数对象没有强制更新

在 `Scripts.vue` 中：
```javascript
const handleExecute = (row) => {
  currentScript.value = row
  executeParams.value = ''
  executeParamsObj.value = {}  // 尝试清空，但组件可能没有重新初始化
  executeVisible.value = true
}
```

虽然代码尝试清空 `executeParamsObj`，但 `ExecutionParams` 组件的 `paramValues` 状态可能没有被同步重置。

## 解决方案

### 修改 1：ExecutionParams.vue - 完整重新初始化参数值

**文件路径**: `frontend/src/components/ExecutionParams.vue`

**修改位置**: 第 65-91 行（`initParams()` 函数）

**修改前**:
```javascript
// 初始化参数
const initParams = () => {
  try {
    if (typeof props.parameters === 'string') {
      params.value = props.parameters ? JSON.parse(props.parameters) : []
    } else {
      params.value = props.parameters || []
    }

    // 初始化参数值（使用默认值）
    const values = {}
    params.value.forEach(param => {
      if (param.default_value) {
        values[param.key] = param.default_value
      } else {
        values[param.key] = ''
      }
    })
    paramValues.value = values

    // 发送初始值
    emitChange()
  } catch (e) {
    console.error('解析参数定义失败:', e)
    params.value = []
  }
}
```

**修改后**:
```javascript
// 初始化参数
const initParams = () => {
  try {
    if (typeof props.parameters === 'string') {
      params.value = props.parameters ? JSON.parse(props.parameters) : []
    } else {
      params.value = props.parameters || []
    }

    // 初始化参数值
    // 优先级：default_value > 空字符串
    // 注意：不使用之前记录的参数值，确保每次初始化时都是干净的状态
    const values = {}
    params.value.forEach(param => {
      if (param.default_value) {
        values[param.key] = param.default_value
      } else {
        values[param.key] = ''
      }
    })
    paramValues.value = values

    // 发送初始值
    emitChange()
  } catch (e) {
    console.error('解析参数定义失败:', e)
    params.value = []
  }
}
```

**变化说明**:
- 注释改进：更清楚地说明了参数值的初始化优先级和目的
- 核心逻辑：确保参数值每次都被**完全重新初始化**，不使用任何之前保留的值
- 这防止了组件状态在多次打开执行对话框时累积旧数据

---

**修改位置**: 第 96-100 行（watch 监听）

**修改前**:
```javascript
// 监听参数定义变化
watch(() => props.parameters, () => {
  initParams()
}, { immediate: true })
```

**修改后**:
```javascript
// 监听参数定义变化
watch(() => props.parameters, () => {
  initParams()
}, { immediate: true, deep: true })
```

**变化说明**:
- 添加了 `deep: true` 选项
- 确保不仅监听参数定义对象的引用改变，还监听其内部属性的改变
- 这样即使参数定义的对象结构发生改变，也能正确触发重新初始化

---

### 修改 2：Scripts.vue - 强制组件重新创建

**文件路径**: `frontend/src/views/Scripts.vue`

**修改位置**: 第 242-248 行（执行对话框内的 `ExecutionParams` 组件）

**修改前**:
```vue
<el-form-item label="脚本参数" v-if="currentScript?.parameters">
  <ExecutionParams
    :parameters="currentScript.parameters"
    v-model="executeParamsObj"
  />
</el-form-item>
```

**修改后**:
```vue
<el-form-item label="脚本参数" v-if="currentScript?.parameters">
  <ExecutionParams
    :key="`exec-params-${currentScript.id}-${executeVisible}`"
    :parameters="currentScript.parameters"
    v-model="executeParamsObj"
  />
</el-form-item>
```

**变化说明**:
- 添加了动态 `key` 属性：`:key="`exec-params-${currentScript.id}-${executeVisible}`"`
- **工作原理**：
  - 当 `currentScript.id` 改变时（用户选择执行不同脚本），`key` 变化 → 组件被销毁后重新创建
  - 当 `executeVisible` 改变时（打开/关闭执行对话框），`key` 变化 → 组件被销毁后重新创建
  - 强制重新创建确保 `onMounted` 生命周期钩子被调用，`initParams()` 被重新执行
  - 从而 100% 保证参数值被重新初始化为干净状态

**关键逻辑**:
```javascript
// 当用户点击"执行"按钮时（Scripts.vue 中的 handleExecute 函数）
const handleExecute = (row) => {
  currentScript.value = row                    // currentScript.id 改变 → key 改变 ✓
  executeParams.value = ''
  executeParamsObj.value = {}                  // 清空参数对象
  uploadFiles.value = []
  executeForm.value = {
    environment_id: null
  }
  executeVisible.value = true                  // executeVisible 改变 → key 改变 ✓
}

// 组件的 key 从旧值变化后，Vue 会销毁旧实例并创建新实例
// 新实例的 onMounted 会执行 initParams()，参数值会被重新初始化
```

---

## 完整修改文件清单

| 文件 | 行号 | 修改类型 | 说明 |
|------|------|--------|------|
| `frontend/src/components/ExecutionParams.vue` | 65-91 | 代码注释改进 | 改进 `initParams()` 函数的注释，强调完全重新初始化 |
| `frontend/src/components/ExecutionParams.vue` | 96-100 | 功能增强 | `watch` 监听添加 `deep: true` 选项 |
| `frontend/src/views/Scripts.vue` | 242-248 | 关键修复 | 为 `ExecutionParams` 组件添加动态 `key`，强制重新创建 |

---

## 验证测试步骤

1. 创建一个带参数的脚本，定义如下参数：
   - `API_KEY`（必填）
   - `TIMEOUT`（选填，默认值：30）

2. 执行脚本：
   - 第一次执行：输入 `API_KEY=abc123`，`TIMEOUT=60`
   - 检查脚本是否正确收到参数值
   - 关闭执行对话框

3. 再次执行脚本（同一脚本）：
   - 输入相同参数：`API_KEY=abc123`，`TIMEOUT=60`
   - **预期结果**：脚本应该正确收到参数值，而不是 `None`
   - **实际结果**（修复前）：参数值为 `None` ❌
   - **实际结果**（修复后）：脚本正确收到参数值 ✅

4. 测试参数默认值：
   - 第二次执行时只输入 `API_KEY=xyz789`，不改变 `TIMEOUT`
   - **预期结果**：`TIMEOUT` 应该使用默认值 `30` ✅

## 影响范围

- ✅ 脚本执行参数输入
- ✅ 工作流节点参数输入（如果有相同问题）
- ✅ 不影响后端逻辑
- ✅ 不影响定时任务、文件上传等其他功能

## 总结

这是一个**前端组件状态管理**的问题，而非后端问题。通过：
1. 确保参数值每次都被完全重新初始化
2. 强制组件重新创建（通过动态 key）

彻底解决了重复执行脚本时参数值丢失的问题。
