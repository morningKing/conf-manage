# 颜色预设选择器实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建 Material Design 预设色板选择器组件，支持50种精选颜色和 RGB/HEX 自定义输入，替换现有 el-color-picker。

**Architecture:** 新建 ColorPicker.vue 组件，包含预设色板网格和自定义输入区域。预设颜色按色系分类展示，支持快速选择和精确调整。组件兼容 v-model 双向绑定。

**Tech Stack:** Vue 3, Element Plus, SCSS

---

## 文件结构

```
frontend/src/
├── components/
│   └── ColorPicker.vue         # 新建：颜色预设选择器组件
├── views/
│   ├── Categories.vue          # 修改：替换颜色选择器
│   └── Tags.vue                # 修改：替换颜色选择器
```

---

### Task 1: 创建 ColorPicker 组件

**Files:**
- Create: `frontend/src/components/ColorPicker.vue`

- [ ] **Step 1: 创建 ColorPicker.vue 组件**

创建 `frontend/src/components/ColorPicker.vue`：

```vue
<template>
  <div class="color-picker-panel">
    <!-- 预设色板区 -->
    <div class="preset-section">
      <div class="section-title">预设颜色</div>
      <div class="color-grid">
        <div
          v-for="color in materialColors"
          :key="color.hex"
          class="color-item"
          :class="{ selected: selectedColor === color.hex }"
          :style="{ backgroundColor: color.hex }"
          :title="color.name"
          @click="selectPreset(color.hex)"
        >
          <el-icon v-if="selectedColor === color.hex" class="check-icon">
            <Check />
          </el-icon>
        </div>
      </div>
    </div>

    <!-- 分隔线 -->
    <el-divider content-position="left">自定义颜色</el-divider>

    <!-- 自定义区 -->
    <div class="custom-section">
      <!-- 颜色选择器 -->
      <el-color-picker
        v-model="customColor"
        :show-alpha="showAlpha"
        @change="handleCustomChange"
      />

      <!-- HEX输入 -->
      <el-input
        v-model="hexInput"
        placeholder="409EFF"
        class="hex-input"
        @change="handleHexChange"
      >
        <template #prefix>#</template>
      </el-input>

      <!-- RGB输入 -->
      <div class="rgb-inputs">
        <el-input-number
          v-model="rgb.r"
          :min="0"
          :max="255"
          size="small"
          controls-position="right"
          @change="handleRgbChange"
        />
        <el-input-number
          v-model="rgb.g"
          :min="0"
          :max="255"
          size="small"
          controls-position="right"
          @change="handleRgbChange"
        />
        <el-input-number
          v-model="rgb.b"
          :min="0"
          :max="255"
          size="small"
          controls-position="right"
          @change="handleRgbChange"
        />
      </div>
    </div>

    <!-- 预览 -->
    <div class="preview-section">
      <span class="preview-label">预览效果：</span>
      <el-tag :color="selectedColor" effect="plain" class="preview-tag">
        {{ previewText || '示例标签' }}
      </el-tag>
      <span class="preview-hex">{{ selectedColor }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Check } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: String, default: '#409EFF' },
  showAlpha: { type: Boolean, default: false },
  previewText: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue', 'change'])

// Material Design 预设颜色（50种）
const materialColors = [
  // 红色系（6种）
  { name: '红色', hex: '#F44336' },
  { name: '深红', hex: '#D32F2F' },
  { name: '玫红', hex: '#E91E63' },
  { name: '粉红', hex: '#EC407A' },
  { name: '紫红', hex: '#C2185B' },
  { name: '浅红', hex: '#FFCDD2' },

  // 紫色系（4种）
  { name: '紫色', hex: '#9C27B0' },
  { name: '深紫', hex: '#7B1FA2' },
  { name: '浅紫', hex: '#BA68C8' },
  { name: '淡紫', hex: '#E1BEE7' },

  // 蓝色系（8种）
  { name: '靛蓝', hex: '#3F51B5' },
  { name: '蓝色', hex: '#2196F3' },
  { name: '深蓝', hex: '#1976D2' },
  { name: '天蓝', hex: '#03A9F4' },
  { name: '亮蓝', hex: '#00BCD4' },
  { name: '青色', hex: '#0097A7' },
  { name: 'Teal', hex: '#009688' },
  { name: '蓝灰', hex: '#607D8B' },

  // 绿色系（6种）
  { name: '绿色', hex: '#4CAF50' },
  { name: '深绿', hex: '#388E3C' },
  { name: '亮绿', hex: '#8BC34A' },
  { name: '柠檬', hex: '#CDDC39' },
  { name: '黄绿', hex: '#AEEA00' },
  { name: '淡绿', hex: '#C8E6C9' },

  // 黄/橙色系（6种）
  { name: '黄色', hex: '#FFEB3B' },
  { name: '琥珀', hex: '#FFC107' },
  { name: '橙色', hex: '#FF9800' },
  { name: '深橙', hex: '#FF5722' },
  { name: '金橙', hex: '#FF6F00' },
  { name: '浅黄', hex: '#FFF9C4' },

  // 棕/灰色系（8种）
  { name: '棕色', hex: '#795548' },
  { name: '深棕', hex: '#5D4037' },
  { name: '灰色', hex: '#9E9E9E' },
  { name: '深灰', hex: '#616161' },
  { name: '浅灰', hex: '#BDBDBD' },
  { name: '白色', hex: '#FFFFFF' },
  { name: '黑色', hex: '#000000' },
  { name: '炭灰', hex: '#424242' },

  // Element UI常用色（6种）
  { name: '主色蓝', hex: '#409EFF' },
  { name: '成功绿', hex: '#67C23A' },
  { name: '警告橙', hex: '#E6A23C' },
  { name: '危险红', hex: '#F56C6C' },
  { name: '信息灰', hex: '#909399' },
  { name: '链接蓝', hex: '#1890ff' },

  // 补充色（6种）
  { name: '青绿', hex: '#00BFA5' },
  { name: '藏青', hex: '#304FFE' },
  { name: '珊瑚', hex: '#FF7043' },
  { name: '薰衣草', hex: '#B388FF' },
  { name: '薄荷', hex: '#69F0AE' },
  { name: '奶油', hex: '#FFF8E1' }
]

const selectedColor = ref(props.modelValue)
const customColor = ref(props.modelValue)
const hexInput = ref(props.modelValue.replace('#', ''))

const rgb = ref({ r: 64, g: 158, b: 255 })

// HEX转RGB
const hexToRgb = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : { r: 64, g: 158, b: 255 }
}

// RGB转HEX
const rgbToHex = (r, g, b) => {
  return '#' + [r, g, b].map(x => {
    const hex = x.toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }).join('').toUpperCase()
}

// 初始化RGB值
rgb.value = hexToRgb(selectedColor.value)

// 选择预设色
const selectPreset = (hex) => {
  selectedColor.value = hex
  customColor.value = hex
  hexInput.value = hex.replace('#', '')
  rgb.value = hexToRgb(hex)
  emit('update:modelValue', hex)
  emit('change', hex)
}

// 自定义颜色变化
const handleCustomChange = (hex) => {
  if (hex) {
    selectedColor.value = hex
    hexInput.value = hex.replace('#', '')
    rgb.value = hexToRgb(hex)
    emit('update:modelValue', hex)
    emit('change', hex)
  }
}

// HEX输入变化
const handleHexChange = (val) => {
  const hex = '#' + val.replace('#', '')
  if (/^#[0-9A-Fa-f]{6}$/.test(hex)) {
    selectedColor.value = hex.toUpperCase()
    customColor.value = hex.toUpperCase()
    rgb.value = hexToRgb(hex)
    emit('update:modelValue', hex.toUpperCase())
    emit('change', hex.toUpperCase())
  } else {
    hexInput.value = selectedColor.value.replace('#', '')
  }
}

// RGB输入变化
const handleRgbChange = () => {
  const hex = rgbToHex(rgb.value.r, rgb.value.g, rgb.value.b)
  selectedColor.value = hex
  customColor.value = hex
  hexInput.value = hex.replace('#', '')
  emit('update:modelValue', hex)
  emit('change', hex)
}

// 监听外部值变化
watch(() => props.modelValue, (newVal) => {
  if (newVal !== selectedColor.value) {
    selectedColor.value = newVal
    customColor.value = newVal
    hexInput.value = newVal.replace('#', '')
    rgb.value = hexToRgb(newVal)
  }
})
</script>

<style scoped lang="scss">
.color-picker-panel {
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

  .preset-section {
    .section-title {
      font-size: 13px;
      color: #606266;
      margin-bottom: 10px;
    }

    .color-grid {
      display: grid;
      grid-template-columns: repeat(10, 1fr);
      gap: 6px;

      .color-item {
        width: 28px;
        height: 28px;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 2px solid transparent;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;

        &:hover {
          transform: scale(1.15);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
          z-index: 1;
        }

        &.selected {
          border-color: #409EFF;
          box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
        }

        .check-icon {
          color: #fff;
          font-size: 14px;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
        }
      }
    }
  }

  .custom-section {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 12px;
    flex-wrap: wrap;

    .hex-input {
      width: 120px;
    }

    .rgb-inputs {
      display: flex;
      gap: 6px;

      .el-input-number {
        width: 70px;
      }
    }
  }

  .preview-section {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #E4E7ED;
    display: flex;
    align-items: center;
    gap: 10px;

    .preview-label {
      font-size: 13px;
      color: #606266;
    }

    .preview-tag {
      padding: 4px 12px;
    }

    .preview-hex {
      font-size: 12px;
      color: #909399;
      font-family: monospace;
    }
  }
}
</style>
```

- [ ] **Step 2: 验证组件语法**

Run: `cd frontend && npm run build 2>&1 | grep -i error || echo "Build OK"`
Expected: Build OK

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ColorPicker.vue
git commit -m "feat: add ColorPicker component with Material Design preset colors"
```

---

### Task 2: 在 Categories.vue 中集成 ColorPicker

**Files:**
- Modify: `frontend/src/views/Categories.vue:62-63`

- [ ] **Step 1: 导入 ColorPicker 组件**

在 Categories.vue 的 `<script setup>` 部分添加导入：

```javascript
import ColorPicker from '../components/ColorPicker.vue'
```

完整导入：
```javascript
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCategories, createCategory, updateCategory, deleteCategory } from '../api'
import { Plus } from '@element-plus/icons-vue'
import ColorPicker from '../components/ColorPicker.vue'
```

- [ ] **Step 2: 替换颜色选择器**

将表单中的颜色选择器替换：

原代码：
```vue
<el-form-item label="颜色">
  <el-color-picker v-model="form.color" show-alpha />
  <span style="margin-left: 10px; color: #909399;">{{ form.color }}</span>
</el-form-item>
```

替换为：
```vue
<el-form-item label="颜色">
  <ColorPicker
    v-model="form.color"
    :preview-text="form.name || '分类'"
    :show-alpha="false"
  />
</el-form-item>
```

- [ ] **Step 3: 扩大对话框宽度**

将对话框宽度从 `width="600px"` 保持不变（已足够）。

- [ ] **Step 4: 验证构建**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/Categories.vue
git commit -m "feat: integrate ColorPicker in Categories page"
```

---

### Task 3: 在 Tags.vue 中集成 ColorPicker

**Files:**
- Modify: `frontend/src/views/Tags.vue:60-66, 76-80`

- [ ] **Step 1: 导入 ColorPicker 组件**

在 Tags.vue 的 `<script setup>` 部分添加导入：

```javascript
import ColorPicker from '../components/ColorPicker.vue'
```

完整导入：
```javascript
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTags, createTag, updateTag, deleteTag } from '../api'
import { Plus } from '@element-plus/icons-vue'
import ColorPicker from '../components/ColorPicker.vue'
```

- [ ] **Step 2: 替换颜色选择器和预览**

将颜色表单项替换：

原代码：
```vue
<el-form-item label="颜色">
  <el-color-picker v-model="form.color" show-alpha />
  <span style="margin-left: 10px; color: #909399;">{{ form.color }}</span>
</el-form-item>
<el-form-item label="预览">
  <el-tag :color="form.color" effect="plain">{{ form.name || '标签预览' }}</el-tag>
</el-form-item>
```

替换为：
```vue
<el-form-item label="颜色">
  <ColorPicker
    v-model="form.color"
    :preview-text="form.name || '标签'"
    :show-alpha="false"
  />
</el-form-item>
```

- [ ] **Step 3: 扩大对话框宽度**

将对话框宽度从 `width="500px"` 改为 `width="600px"`。

- [ ] **Step 4: 验证构建**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/Tags.vue
git commit -m "feat: integrate ColorPicker in Tags page"
```

---

### Task 4: 集成测试

**Files:**
- 无文件修改，测试验证

- [ ] **Step 1: 启动前端开发服务**

Run: `cd frontend && npm run dev`
Expected: Vite 在 port 5173 启动

- [ ] **Step 2: 测试分类页面颜色选择器**

在浏览器中：
1. 打开分类管理页面
2. 点击"新建分类"
3. 验证颜色选择器面板显示50种预设颜色
4. 点击预设颜色快速选择
5. 测试 HEX 输入框
6. 测试 RGB 输入框
7. 验证预览标签实时更新
8. 保存分类，验证颜色值正确存储

- [ ] **Step 3: 测试标签页面颜色选择器**

在浏览器中：
1. 打开标签管理页面
2. 点击"新建标签"
3. 重复 Step 2 的测试步骤
4. 验证标签颜色正确显示在列表中

- [ ] **Step 4: 测试边界情况**

测试场景：
1. 输入无效 HEX 值（如 "abc"）→ 应恢复上一个有效值
2. 输入 RGB 边界值（0, 255）→ 应正确转换
3. 选择白色预设 → 检查图标显示

- [ ] **Step 5: Commit 测试通过**

```bash
git add -A
git commit -m "test: ColorPicker integration test passed"
```

---

## 自检清单

**1. Spec覆盖检查:**
- ✓ 50种Material Design预设颜色 - Task 1
- ✓ RGB三值输入 - Task 1
- ✓ HEX输入 - Task 1
- ✓ 预览展示 - Task 1
- ✓ Categories.vue集成 - Task 2
- ✓ Tags.vue集成 - Task 3

**2. Placeholder扫描:**
- 无 TBD、TODO
- 所有颜色值完整定义
- 所有代码完整提供

**3. 类型一致性:**
- ColorPicker 使用 v-model 绑定 HEX 字符串
- RGB 值使用数字类型（0-255）
- 预览使用 el-tag :color 属性

---

## 完成标记

颜色预设选择器功能已完成，支持：
- 50种Material Design精选预设颜色
- RGB和HEX自定义输入
- 实时预览效果
- Categories和Tags页面集成