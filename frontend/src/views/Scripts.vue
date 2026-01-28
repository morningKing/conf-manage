<template>
  <div class="scripts-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>脚本列表</span>
          <div class="header-actions">
            <el-button @click="guideVisible = true">
              <el-icon><Document /></el-icon>
              使用指南
            </el-button>
            <el-button type="primary" @click="handleCreate">
              <el-icon><Plus /></el-icon>
              新建脚本
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选和搜索区域 -->
      <div class="filter-bar">
        <el-input
          v-model="searchText"
          placeholder="搜索脚本名称或描述"
          style="width: 300px;"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="filterCategory"
          placeholder="选择分类"
          clearable
          style="width: 200px;"
          @change="handleFilter"
        >
          <el-option label="全部分类" :value="null" />
          <el-option
            v-for="category in categories"
            :key="category.id"
            :label="category.name"
            :value="category.id"
          >
            <span :style="{ color: category.color }">{{ category.name }}</span>
          </el-option>
        </el-select>

        <el-select
          v-model="filterTags"
          placeholder="选择标签"
          multiple
          clearable
          collapse-tags
          collapse-tags-tooltip
          style="width: 250px;"
          @change="handleFilter"
        >
          <el-option
            v-for="tag in tags"
            :key="tag.id"
            :label="tag.name"
            :value="tag.id"
          >
            <el-tag :color="tag.color" size="small" effect="plain">{{ tag.name }}</el-tag>
          </el-option>
        </el-select>

        <el-button
          :type="filterFavorite ? 'warning' : ''"
          @click="toggleFavorite"
          style="margin-left: 10px;"
        >
          <el-icon><Star /></el-icon>
          {{ filterFavorite ? '仅收藏' : '全部' }}
        </el-button>
      </div>

      <el-table :data="scripts" stripe>
        <el-table-column prop="name" label="脚本名称" width="200" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.type === 'python' ? 'success' : 'warning'">
              {{ row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="分类" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.category" :color="row.category.color" effect="plain">
              {{ row.category.name }}
            </el-tag>
            <span v-else style="color: #909399;">未分类</span>
          </template>
        </el-table-column>
        <el-table-column label="标签" width="200">
          <template #default="{ row }">
            <el-tag
              v-for="tag in row.tags"
              :key="tag.id"
              :color="tag.color"
              size="small"
              style="margin-right: 5px;"
              effect="plain"
            >
              {{ tag.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="620" fixed="right">
          <template #default="{ row }">
            <el-button
              :type="row.is_favorite ? 'warning' : ''"
              size="small"
              @click="handleToggleFavorite(row)"
            >
              <el-icon><Star /></el-icon>
            </el-button>
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="success" @click="handleExecute(row)">执行</el-button>
            <el-button size="small" type="info" @click="handleVersions(row)">版本</el-button>
            <el-dropdown trigger="click" @command="(cmd) => cmd === 'versions' ? handleCleanHistory(row, 'versions') : handleCleanHistory(row, 'executions')">
              <el-button size="small" type="warning">
                清理
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="versions">清理版本</el-dropdown-item>
                  <el-dropdown-item command="executions">清理执行</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="80%"
      :close-on-click-modal="false"
      class="script-dialog"
    >
      <el-form :model="form" label-width="100px" class="script-form">
        <el-form-item label="脚本名称">
          <el-input v-model="form.name" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="脚本类型">
          <el-select v-model="form.type" placeholder="请选择脚本类型" @change="handleTypeChange">
            <el-option label="Python" value="python" />
            <el-option label="JavaScript" value="javascript" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category_id" placeholder="选择分类（可选）" clearable>
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            >
              <span :style="{ color: category.color }">{{ category.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="form.tag_ids"
            placeholder="选择标签（可选）"
            multiple
            clearable
            collapse-tags
            collapse-tags-tooltip
          >
            <el-option
              v-for="tag in tags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            >
              <el-tag :color="tag.color" size="small" effect="plain">{{ tag.name }}</el-tag>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="收藏">
          <el-switch v-model="form.is_favorite" />
        </el-form-item>
        <el-form-item label="执行环境">
          <el-select v-model="form.environment_id" placeholder="默认环境（可选）" clearable>
            <el-option
              v-for="env in filteredEnvironments"
              :key="env.id"
              :label="`${env.name}${env.is_default ? ' (默认)' : ''}`"
              :value="env.id"
            >
              <span>{{ env.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px; margin-left: 10px;">{{ env.version }}</span>
            </el-option>
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            {{ form.environment_id ? '将使用指定环境的解释器执行' : '将使用系统默认解释器或环境类型的默认环境' }}
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item label="依赖配置">
          <el-input
            v-model="form.dependencies"
            type="textarea"
            rows="2"
            placeholder="多个依赖用逗号分隔,例如: requests,pandas"
          />
        </el-form-item>
        <el-form-item label="参数配置">
          <ParameterConfig v-model="form.parameters" />
        </el-form-item>
        <el-form-item label="脚本代码">
          <CodeEditor
            v-model="form.code"
            :language="form.type"
            height="400px"
            theme="dark"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 执行对话框 -->
    <el-dialog v-model="executeVisible" title="执行脚本" width="700px">
      <el-form :model="executeForm" label-width="100px">
        <el-form-item label="脚本名称">
          <el-input :value="currentScript?.name" disabled />
        </el-form-item>

        <el-form-item label="脚本参数" v-if="currentScript?.parameters">
          <ExecutionParams
            :key="`exec-params-${currentScript.id}-${executeVisible}`"
            :parameters="currentScript.parameters"
            v-model="executeParamsObj"
          />
        </el-form-item>

        <el-form-item label="执行环境">
          <el-select v-model="executeForm.environment_id" placeholder="默认环境（可选）" clearable style="width: 100%;">
            <el-option
              v-for="env in executeEnvironments"
              :key="env.id"
              :label="`${env.name}${env.is_default ? ' (默认)' : ''}`"
              :value="env.id"
            >
              <span>{{ env.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px; margin-left: 10px;">{{ env.version }}</span>
            </el-option>
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            {{ executeForm.environment_id
              ? '将使用指定环境的解释器执行'
              : currentScript?.environment_id
                ? '将使用脚本预设的环境'
                : '将使用系统默认解释器'
            }}
          </div>
        </el-form-item>

        <el-form-item label="上传文件">
          <FileUpload v-model="uploadFiles" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="executeVisible = false">取消</el-button>
        <el-button type="primary" @click="handleExecuteConfirm">执行</el-button>
      </template>
    </el-dialog>

    <!-- 实时日志对话框 -->
    <el-dialog
      v-model="logVisible"
      title="执行日志（实时）"
      width="80%"
      :close-on-click-modal="false"
      @close="closeLogStream"
    >
      <div class="log-header">
        <el-tag :type="getStatusType(logStatus)" size="large">
          {{ getStatusText(logStatus) }}
        </el-tag>
        <div class="log-actions">
          <el-button
            v-if="logStatus === 'running'"
            type="danger"
            size="small"
            @click="handleCancelExecution"
          >
            中断执行
          </el-button>
          <el-button
            v-if="logStatus === 'running'"
            type="info"
            size="small"
            @click="closeLogStream"
          >
            停止监听
          </el-button>
        </div>
      </div>

      <el-divider />

      <!-- 进度显示 -->
      <div class="progress-section">
        <ExecutionProgress
          :progress="logProgress"
          :stage="logStage"
          :status="logStatus"
          :show-detail="true"
        />
      </div>

      <el-divider />

      <div class="log-container" ref="logContainer">
        <pre v-if="realTimeLogs">{{ realTimeLogs }}</pre>
        <div v-else class="log-empty">等待日志输出...</div>
      </div>

      <div v-if="logError" class="error-container">
        <el-divider>错误信息</el-divider>
        <pre>{{ logError }}</pre>
      </div>

      <!-- 执行空间文件列表 -->
      <div v-if="logStatus === 'success' || logStatus === 'failed'" class="files-section">
        <el-divider>执行空间文件</el-divider>
        <div v-if="filesLoading" style="text-align: center; padding: 20px;">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span style="margin-left: 8px;">加载文件列表中...</span>
        </div>
        <div v-else-if="executionFiles.length === 0" class="files-empty">
          执行空间中没有文件
        </div>
        <el-table v-else :data="executionFiles" stripe max-height="300">
          <el-table-column prop="name" label="文件名" min-width="200" />
          <el-table-column prop="path" label="路径" min-width="200" show-overflow-tooltip />
          <el-table-column label="大小" width="120">
            <template #default="{ row }">
              {{ formatFileSize(row.size) }}
            </template>
          </el-table-column>
          <el-table-column prop="modified_time" label="修改时间" width="180">
            <template #default="{ row }">
              {{ new Date(row.modified_time).toLocaleString('zh-CN') }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="handleFilePreview(row)" v-if="row.is_text">
                预览
              </el-button>
              <el-button size="small" type="primary" @click="handleFileDownload(row)">
                下载
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="closeLogStream">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 文件预览对话框 -->
    <el-dialog
      v-model="filePreviewVisible"
      :title="`预览: ${selectedFile?.name || ''}`"
      width="80%"
    >
      <div class="file-preview-container">
        <pre v-if="filePreviewType === 'text'">{{ filePreviewContent }}</pre>
        <div v-else style="color: #909399; text-align: center; padding: 40px;">
          {{ filePreviewContent }}
        </div>
      </div>
      <template #footer>
        <el-button @click="filePreviewVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleFileDownload(selectedFile)">下载</el-button>
      </template>
    </el-dialog>

    <!-- 版本历史对话框 -->
    <el-dialog v-model="versionVisible" title="版本历史" width="80%">
      <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
        <el-alert
          v-if="compareVersions.length > 0"
          type="info"
          :closable="false"
          style="flex: 1; margin-right: 16px;"
        >
          已选择 {{ compareVersions.length }} 个版本用于对比
          <el-button
            v-if="compareVersions.length === 2"
            type="primary"
            size="small"
            @click="showVersionDiff"
            style="margin-left: 10px;"
          >
            开始对比
          </el-button>
          <el-button
            size="small"
            @click="compareVersions = []"
            style="margin-left: 10px;"
          >
            清空选择
          </el-button>
        </el-alert>
        <el-button type="warning" size="small" @click="handleCleanHistory(currentScript, 'versions')">
          <el-icon><Delete /></el-icon>
          清理版本历史
        </el-button>
      </div>

      <el-table
        :data="versions"
        stripe
        @selection-change="handleVersionSelection"
      >
        <el-table-column type="selection" width="55" :selectable="() => compareVersions.length < 2" />
        <el-table-column prop="version" label="版本号" width="100" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="handleViewVersion(row)">查看</el-button>
            <el-button
              size="small"
              type="warning"
              @click="handleRollback(row)"
              v-if="row.version !== currentScript?.version"
            >
              回滚
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 版本代码查看对话框 -->
    <el-dialog
      v-model="versionCodeVisible"
      :title="`版本 ${currentVersion?.version} 代码`"
      width="80%"
    >
      <CodeEditor
        v-if="currentVersion"
        :model-value="currentVersion.code"
        :language="currentScript?.type || 'python'"
        height="600px"
        theme="dark"
        :readonly="true"
      />
      <template #footer>
        <el-button @click="versionCodeVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 版本对比对话框 -->
    <el-dialog v-model="diffVisible" title="版本对比" width="95%" :close-on-click-modal="false">
      <CodeDiff
        v-if="diffVisible && compareVersions.length === 2"
        :old-code="compareVersions[0].code"
        :new-code="compareVersions[1].code"
        :old-version="`v${compareVersions[0].version}`"
        :new-version="`v${compareVersions[1].version}`"
        :language="currentScript?.type || 'python'"
        height="600px"
        theme="dark"
      />
      <template #footer>
        <el-button @click="diffVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 清理历史记录对话框 -->
    <el-dialog
      v-model="cleanHistoryVisible"
      :title="cleanHistoryType === 'versions' ? '清理版本历史' : '清理执行历史'"
      width="500px"
    >
      <el-form :model="cleanHistoryForm" label-width="120px">
        <el-form-item label="保留最新数量">
          <el-input-number
            v-model="cleanHistoryForm.keep_latest"
            :min="1"
            :max="1000"
            style="width: 100%"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            保留最新的 {{ cleanHistoryForm.keep_latest }} 条记录，删除其余记录
          </div>
        </el-form-item>

        <el-form-item v-if="cleanHistoryType === 'executions'" label="执行状态">
          <el-select v-model="cleanHistoryForm.status" placeholder="全部状态" clearable style="width: 100%">
            <el-option label="全部状态" :value="null" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            仅清理指定状态的执行记录
          </div>
        </el-form-item>

        <el-form-item v-if="cleanHistoryType === 'executions'" label="清理天数">
          <el-input-number
            v-model="cleanHistoryForm.before_days"
            :min="1"
            :max="3650"
            placeholder="可选"
            style="width: 100%"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            清理 {{ cleanHistoryForm.before_days || '所有' }} 天前的记录
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cleanHistoryVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCleanHistoryConfirm">确定清理</el-button>
      </template>
    </el-dialog>

    <!-- 使用指南对话框 -->
    <el-dialog v-model="guideVisible" title="📖 脚本编写使用指南" width="80%">
      <el-tabs v-model="guideActiveTab" type="border-card">
        <!-- Python 指南 -->
        <el-tab-pane label="Python" name="python">
          <div class="script-guide">
            <h4>一、参数传递</h4>
            <p class="guide-desc">所有参数通过环境变量传递，使用 <code>os.environ.get()</code> 获取</p>
            <pre class="code-example">import os

# 获取参数（带默认值）
param1 = os.environ.get('PARAM_NAME', 'default_value')
host = os.environ.get('HOST', 'localhost')
port = int(os.environ.get('PORT', '8080'))</pre>

            <h4>二、文件访问</h4>
            <p class="guide-desc">上传的文件会保存在执行空间（当前目录），通过 FILES 环境变量获取文件列表</p>
            <pre class="code-example">import os
import json

# 获取上传的文件列表
files_json = os.environ.get('FILES', '[]')
files = json.loads(files_json)  # ['file1.txt', 'file2.csv']

# 读取文件（使用文件名即可，无需路径）
for filename in files:
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f'读取文件: {filename}')

# 写入新文件到执行空间
with open('output.txt', 'w') as f:
    f.write('处理结果...')</pre>

            <h4>三、工作流中获取上一步输出</h4>
            <p class="guide-desc">在工作流中，可以通过环境变量访问前置节点的执行结果</p>
            <pre class="code-example">import os
import json

# 假设前置节点ID为 node_1
# 获取节点执行状态
node_1_status = os.environ.get('NODE_node_1_STATUS')

# 获取节点输出（JSON格式）
node_1_output = os.environ.get('NODE_node_1_OUTPUT', '{}')
result = json.loads(node_1_output)

# 使用前置节点的结果
if node_1_status == 'success':
    data = result.get('data')
    print(f'上一步处理了 {data} 条记录')</pre>

            <h4>四、完整示例</h4>
            <p class="guide-desc">CSV文件处理脚本示例</p>
            <pre class="code-example">#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV数据处理脚本
"""
import os
import json
import sys
import csv

def main():
    try:
        # 1. 获取参数
        output_file = os.environ.get('OUTPUT_FILE', 'result.csv')
        delimiter = os.environ.get('DELIMITER', ',')

        # 2. 获取上传的文件
        files_json = os.environ.get('FILES', '[]')
        files = json.loads(files_json)

        if not files:
            print('错误: 未上传文件', file=sys.stderr)
            sys.exit(1)

        # 3. 处理CSV文件
        input_file = files[0]
        print(f'开始处理文件: {input_file}')

        rows = []
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                # 数据处理逻辑
                rows.append(row)

        print(f'共读取 {len(rows)} 行数据')

        # 4. 输出结果
        with open(output_file, 'w', encoding='utf-8') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        print(f'处理完成，结果保存到: {output_file}')

    except Exception as e:
        print(f'错误: {str(e)}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()</pre>

            <div class="guide-tips">
              <h4>💡 重要提示</h4>
              <ul>
                <li>执行空间是<strong>独立的临时目录</strong>，每次执行都会创建新的空间</li>
                <li>上传的文件和生成的文件都在<strong>执行空间</strong>中，执行完成后可在日志弹窗中查看和下载</li>
                <li>参数名和工作流节点ID是<strong>大小写敏感</strong>的</li>
                <li>工作流节点输出格式：<code>NODE_{节点ID}_{属性}</code>，属性包括 STATUS、OUTPUT 等</li>
                <li>建议使用 <code>try-except</code> 进行<strong>错误处理</strong></li>
              </ul>
            </div>
          </div>
        </el-tab-pane>

        <!-- JavaScript 指南 -->
        <el-tab-pane label="JavaScript" name="javascript">
          <div class="script-guide">
            <h4>一、参数传递</h4>
            <p class="guide-desc">所有参数通过环境变量传递，使用 <code>process.env</code> 获取</p>
            <pre class="code-example">// 获取参数（带默认值）
const param1 = process.env.PARAM_NAME || 'default_value';
const host = process.env.HOST || 'localhost';
const port = parseInt(process.env.PORT || '8080');</pre>

            <h4>二、文件访问</h4>
            <p class="guide-desc">上传的文件会保存在执行空间（当前目录），通过 FILES 环境变量获取文件列表</p>
            <pre class="code-example">const fs = require('fs');

// 获取上传的文件列表
const filesJson = process.env.FILES || '[]';
const files = JSON.parse(filesJson);  // ['file1.txt', 'file2.csv']

// 读取文件（使用文件名即可，无需路径）
files.forEach(filename => {
    const content = fs.readFileSync(filename, 'utf8');
    console.log(`读取文件: ${filename}`);
});

// 写入新文件到执行空间
fs.writeFileSync('output.txt', '处理结果...');</pre>

            <h4>三、工作流中获取上一步输出</h4>
            <p class="guide-desc">在工作流中，可以通过环境变量访问前置节点的执行结果</p>
            <pre class="code-example">// 假设前置节点ID为 node_1
// 获取节点执行状态
const node1Status = process.env.NODE_node_1_STATUS;

// 获取节点输出（JSON格式）
const node1Output = process.env.NODE_node_1_OUTPUT || '{}';
const result = JSON.parse(node1Output);

// 使用前置节点的结果
if (node1Status === 'success') {
    const data = result.data;
    console.log(`上一步处理了 ${data} 条记录`);
}</pre>

            <h4>四、完整示例</h4>
            <p class="guide-desc">JSON文件处理脚本示例</p>
            <pre class="code-example">#!/usr/bin/env node
/**
 * JSON数据处理脚本
 */
const fs = require('fs');

function main() {
    try {
        // 1. 获取参数
        const outputFile = process.env.OUTPUT_FILE || 'result.json';

        // 2. 获取上传的文件
        const filesJson = process.env.FILES || '[]';
        const files = JSON.parse(filesJson);

        if (files.length === 0) {
            console.error('错误: 未上传文件');
            process.exit(1);
        }

        // 3. 处理JSON文件
        const inputFile = files[0];
        console.log(`开始处理文件: ${inputFile}`);

        const content = fs.readFileSync(inputFile, 'utf8');
        const data = JSON.parse(content);

        // 数据处理逻辑
        console.log(`共读取 ${data.length} 条数据`);

        // 4. 输出结果
        fs.writeFileSync(outputFile, JSON.stringify(data, null, 2));
        console.log(`处理完成，结果保存到: ${outputFile}`);

    } catch (error) {
        console.error(`错误: ${error.message}`);
        process.exit(1);
    }
}

main();</pre>

            <div class="guide-tips">
              <h4>💡 重要提示</h4>
              <ul>
                <li>执行空间是<strong>独立的临时目录</strong>，每次执行都会创建新的空间</li>
                <li>上传的文件和生成的文件都在<strong>执行空间</strong>中，执行完成后可在日志弹窗中查看和下载</li>
                <li>参数名和工作流节点ID是<strong>大小写敏感</strong>的</li>
                <li>工作流节点输出格式：<code>NODE_{节点ID}_{属性}</code>，属性包括 STATUS、OUTPUT 等</li>
                <li>建议使用 <code>try-catch</code> 进行<strong>错误处理</strong></li>
              </ul>
            </div>
          </div>
        </el-tab-pane>

        <!-- Bash 指南 -->
        <el-tab-pane label="Bash" name="bash">
          <div class="script-guide">
            <h4>一、参数传递</h4>
            <p class="guide-desc">所有参数通过环境变量传递</p>
            <pre class="code-example">#!/bin/bash

# 获取参数（带默认值）
PARAM_NAME=${PARAM_NAME:-"default_value"}
HOST=${HOST:-"localhost"}
PORT=${PORT:-"8080"}</pre>

            <h4>二、文件访问</h4>
            <p class="guide-desc">上传的文件会保存在执行空间（当前目录），通过 FILES 环境变量获取文件列表</p>
            <pre class="code-example">#!/bin/bash

# 获取上传的文件列表（需要 jq 工具解析JSON）
FILES_JSON=${FILES:-"[]"}

# 如果有文件，遍历处理
if [ "$FILES_JSON" != "[]" ]; then
    echo "处理上传的文件..."
    # 示例：读取第一个文件
    # first_file=$(echo $FILES_JSON | jq -r '.[0]')
    # cat "$first_file"
fi</pre>

            <h4>三、完整示例</h4>
            <p class="guide-desc">文本文件处理脚本示例</p>
            <pre class="code-example">#!/bin/bash
set -e

# 获取参数
OUTPUT_FILE=${OUTPUT_FILE:-"output.txt"}

# 获取上传的文件
FILES_JSON=${FILES:-"[]"}

echo "开始处理..."

# 创建输出文件
touch "$OUTPUT_FILE"

# 处理逻辑
echo "处理完成" > "$OUTPUT_FILE"

echo "结果已保存到: $OUTPUT_FILE"</pre>

            <div class="guide-tips">
              <h4>💡 重要提示</h4>
              <ul>
                <li>执行空间是<strong>独立的临时目录</strong>，每次执行都会创建新的空间</li>
                <li>上传的文件和生成的文件都在<strong>执行空间</strong>中，执行完成后可在日志弹窗中查看和下载</li>
                <li>参数名是<strong>大小写敏感</strong>的</li>
                <li>Bash 脚本建议使用 <code>set -e</code> 在遇到错误时自动退出</li>
              </ul>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="guideVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getScripts,
  createScript,
  updateScript,
  deleteScript,
  getScriptVersions,
  rollbackScript,
  executeScriptWithFiles,
  getEnvironments,
  cancelExecution,
  getCategories,
  getTags,
  toggleScriptFavorite,
  getExecutionFiles,
  getExecutionFile,
  previewExecutionFile,
  cleanScriptVersions,
  cleanScriptExecutions
} from '../api'
import FileUpload from '../components/FileUpload.vue'
import CodeEditor from '../components/CodeEditor.vue'
import CodeDiff from '../components/CodeDiff.vue'
import ParameterConfig from '../components/ParameterConfig.vue'
import ExecutionParams from '../components/ExecutionParams.vue'
import ExecutionProgress from '../components/ExecutionProgress.vue'
import { Plus, Search, Star, Loading, Document, ArrowDown, Delete } from '@element-plus/icons-vue'

const scripts = ref([])
const environments = ref([])
const categories = ref([])
const tags = ref([])

// 筛选相关
const searchText = ref('')
const filterCategory = ref(null)
const filterTags = ref([])
const filterFavorite = ref(false)

const dialogVisible = ref(false)
const dialogTitle = ref('新建脚本')
const form = ref({
  name: '',
  type: 'python',
  description: '',
  code: '',
  dependencies: '',
  parameters: '',
  environment_id: null,
  category_id: null,
  tag_ids: [],
  is_favorite: false
})
const currentScript = ref(null)
const executeVisible = ref(false)
const executeForm = ref({})
const executeParams = ref('')
const executeParamsObj = ref({})
const uploadFiles = ref([])
const versionVisible = ref(false)
const versions = ref([])
const versionCodeVisible = ref(false)
const currentVersion = ref(null)
const compareVersions = ref([])  // 用于对比的版本列表
const diffVisible = ref(false)  // 对比对话框显示状态
const guideVisible = ref(false)  // 使用指南对话框显示状态
const guideActiveTab = ref('python')  // 使用指南当前标签页

// 清理历史记录相关
const cleanHistoryVisible = ref(false)  // 清理历史对话框显示状态
const cleanHistoryType = ref('versions')  // 清理类型：versions 或 executions
const cleanHistoryForm = ref({
  keep_latest: 5,  // 保留最新N条
  status: '',  // 执行状态过滤（仅针对执行记录）
  before_days: null  // 清理N天前的记录（仅针对执行记录）
})

// 实时日志相关
const logVisible = ref(false)
const realTimeLogs = ref('')
const logError = ref('')
const logStatus = ref('pending')
const logProgress = ref(0)
const logStage = ref('pending')
const currentExecutionId = ref(null)
const logContainer = ref(null)
let eventSource = null

// 执行文件相关
const executionFiles = ref([])
const filesLoading = ref(false)
const selectedFile = ref(null)
const filePreviewVisible = ref(false)
const filePreviewContent = ref('')
const filePreviewType = ref('text')

// 根据当前脚本类型过滤环境（用于创建/编辑脚本）
const filteredEnvironments = computed(() => {
  return environments.value.filter(env => env.type === form.value.type)
})

// 根据当前执行脚本类型过滤环境（用于执行脚本）
const executeEnvironments = computed(() => {
  if (!currentScript.value) return []
  return environments.value.filter(env => env.type === currentScript.value.type)
})

const loadScripts = async () => {
  try {
    const params = {}
    if (filterCategory.value) params.category_id = filterCategory.value
    if (filterTags.value.length > 0) params.tags = filterTags.value.join(',')
    if (filterFavorite.value) params.is_favorite = 'true'
    if (searchText.value) params.search = searchText.value

    const res = await getScripts(params)
    scripts.value = res.data
  } catch (error) {
    console.error(error)
  }
}

const loadEnvironments = async () => {
  try {
    const res = await getEnvironments()
    environments.value = res.data
  } catch (error) {
    console.error(error)
  }
}

const loadCategories = async () => {
  try {
    const res = await getCategories()
    categories.value = res.data
  } catch (error) {
    console.error(error)
  }
}

const loadTags = async () => {
  try {
    const res = await getTags()
    tags.value = res.data
  } catch (error) {
    console.error(error)
  }
}

const handleFilter = () => {
  loadScripts()
}

const handleSearch = () => {
  loadScripts()
}

const toggleFavorite = () => {
  filterFavorite.value = !filterFavorite.value
  loadScripts()
}

const handleToggleFavorite = async (row) => {
  try {
    await toggleScriptFavorite(row.id)
    ElMessage.success(row.is_favorite ? '已取消收藏' : '已收藏')
    loadScripts()
  } catch (error) {
    console.error(error)
    ElMessage.error('操作失败')
  }
}

const handleTypeChange = () => {
  // 当脚本类型改变时，清空环境选择（如果当前选择的环境类型不匹配）
  if (form.value.environment_id) {
    const selectedEnv = environments.value.find(env => env.id === form.value.environment_id)
    if (selectedEnv && selectedEnv.type !== form.value.type) {
      form.value.environment_id = null
    }
  }
}

const handleCreate = () => {
  dialogTitle.value = '新建脚本'
  form.value = {
    name: '',
    type: 'python',
    description: '',
    code: '',
    dependencies: '',
    parameters: '',
    environment_id: null,
    category_id: null,
    tag_ids: [],
    is_favorite: false
  }
  currentScript.value = null
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑脚本'
  form.value = {
    ...row,
    tag_ids: row.tags ? row.tags.map(t => t.id) : []
  }
  currentScript.value = row
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (currentScript.value) {
      await updateScript(currentScript.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createScript(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadScripts()
  } catch (error) {
    console.error(error)
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除此脚本吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteScript(row.id)
    ElMessage.success('删除成功')
    loadScripts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handleExecute = (row) => {
  currentScript.value = row
  executeParams.value = ''
  executeParamsObj.value = {}
  uploadFiles.value = []
  executeForm.value = {
    environment_id: null  // 初始化为 null，用户可选择
  }
  executeVisible.value = true
}

const handleExecuteConfirm = async () => {
  try {
    const formData = new FormData()

    // 添加文件
    uploadFiles.value.forEach((file, index) => {
      formData.append(`file${index}`, file)
    })

    // 添加参数（使用ExecutionParams组件收集的参数）
    if (executeParamsObj.value && Object.keys(executeParamsObj.value).length > 0) {
      formData.append('params', JSON.stringify(executeParamsObj.value))
    }

    // 添加执行环境ID（如果指定）
    if (executeForm.value.environment_id) {
      formData.append('environment_id', executeForm.value.environment_id)
    }

    const res = await executeScriptWithFiles(currentScript.value.id, formData)
    const executionId = res.data.id

    ElMessage.success('脚本执行已启动')
    executeVisible.value = false

    // 打开实时日志窗口
    openLogStream(executionId)
  } catch (error) {
    ElMessage.error('参数格式错误或执行失败: ' + error.message)
    console.error(error)
  }
}

const openLogStream = (executionId) => {
  // 重置日志状态
  realTimeLogs.value = ''
  logError.value = ''
  logStatus.value = 'pending'
  logProgress.value = 0
  logStage.value = 'pending'
  currentExecutionId.value = executionId
  logVisible.value = true

  // 关闭已有的连接
  if (eventSource) {
    eventSource.close()
  }

  // 创建 SSE 连接
  const apiUrl = import.meta.env.VITE_API_URL || '/api'
  eventSource = new EventSource(`${apiUrl}/executions/${executionId}/logs/stream`)

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === 'log') {
        // 追加日志内容
        realTimeLogs.value += data.content
        // 自动滚动到底部
        nextTick(() => {
          if (logContainer.value) {
            logContainer.value.scrollTop = logContainer.value.scrollHeight
          }
        })
      } else if (data.type === 'progress') {
        // 更新进度信息
        logProgress.value = data.progress || 0
        logStage.value = data.stage || 'pending'
        // 根据阶段更新状态
        if (data.stage === 'running' || data.stage === 'preparing' || data.stage === 'installing_deps' || data.stage === 'finishing') {
          logStatus.value = 'running'
        }
      } else if (data.type === 'status') {
        // 更新状态
        logStatus.value = data.status
        logProgress.value = data.progress || 100
        logStage.value = data.stage || (data.status === 'success' ? 'completed' : 'failed')
        if (data.error) {
          logError.value = data.error
        }
        // 关闭连接
        eventSource.close()
        eventSource = null
        // 加载执行文件列表
        loadExecutionFiles()
      } else if (data.error) {
        ElMessage.error(data.error)
        eventSource.close()
        eventSource = null
      }
    } catch (error) {
      console.error('解析日志数据失败:', error)
    }
  }

  eventSource.onerror = (error) => {
    console.error('日志流连接错误:', error)
    ElMessage.error('日志流连接中断')
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }
}

const loadExecutionFiles = async () => {
  if (!currentExecutionId.value) return

  filesLoading.value = true
  try {
    const res = await getExecutionFiles(currentExecutionId.value)
    executionFiles.value = res.data.files || []
  } catch (error) {
    console.error('加载执行文件失败:', error)
  } finally {
    filesLoading.value = false
  }
}

const formatFileSize = (size) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / (1024 * 1024)).toFixed(2) + ' MB'
}

const handleFilePreview = async (file) => {
  selectedFile.value = file

  if (file.is_text) {
    try {
      const res = await previewExecutionFile(currentExecutionId.value, file.path)
      filePreviewContent.value = res.data.content
      filePreviewType.value = res.data.type
      filePreviewVisible.value = true
    } catch (error) {
      ElMessage.error('预览文件失败: ' + error.message)
    }
  } else {
    // 二进制文件直接下载
    handleFileDownload(file)
  }
}

const handleFileDownload = (file) => {
  const url = getExecutionFile(currentExecutionId.value, file.path, true)
  window.open(url, '_blank')
}

const closeLogStream = () => {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  logVisible.value = false
  // 清空文件列表
  executionFiles.value = []
}

const getStatusType = (status) => {
  const types = {
    pending: 'info',
    running: '',
    success: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    running: '运行中',
    success: '执行成功',
    failed: '执行失败'
  }
  return texts[status] || '未知状态'
}

const handleVersions = async (row) => {
  try {
    currentScript.value = row
    const res = await getScriptVersions(row.id)
    versions.value = res.data
    compareVersions.value = []  // 清空对比选择
    versionVisible.value = true
  } catch (error) {
    console.error(error)
  }
}

const handleVersionSelection = (selection) => {
  compareVersions.value = selection
}

const showVersionDiff = () => {
  if (compareVersions.value.length !== 2) {
    ElMessage.warning('请选择两个版本进行对比')
    return
  }
  diffVisible.value = true
}

const handleViewVersion = (row) => {
  currentVersion.value = row
  versionCodeVisible.value = true
}

const handleRollback = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要回滚到版本 ${row.version} 吗?`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await rollbackScript(currentScript.value.id, row.version)
    ElMessage.success('回滚成功')
    versionVisible.value = false
    loadScripts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handleCleanHistory = (row, type = 'versions') => {
  currentScript.value = row
  cleanHistoryType.value = type
  cleanHistoryForm.value = {
    keep_latest: type === 'versions' ? 5 : 50,
    status: '',
    before_days: null
  }
  cleanHistoryVisible.value = true
}

const handleCleanHistoryConfirm = async () => {
  try {
    const scriptId = currentScript.value.id
    let result

    if (cleanHistoryType.value === 'versions') {
      result = await cleanScriptVersions(scriptId, {
        keep_latest: cleanHistoryForm.value.keep_latest
      })
    } else {
      const data = {
        keep_latest: cleanHistoryForm.value.keep_latest
      }
      if (cleanHistoryForm.value.status) {
        data.status = cleanHistoryForm.value.status
      }
      if (cleanHistoryForm.value.before_days) {
        data.before_days = cleanHistoryForm.value.before_days
      }
      result = await cleanScriptExecutions(scriptId, data)
    }

    ElMessage.success(result.message || '清理成功')
    cleanHistoryVisible.value = false

    // 如果是清理版本历史，重新加载版本列表
    if (cleanHistoryType.value === 'versions') {
      const res = await getScriptVersions(scriptId)
      versions.value = res.data
    }
  } catch (error) {
    ElMessage.error('清理失败: ' + (error.message || error))
    console.error(error)
  }
}

const handleCancelExecution = async () => {
  try {
    await ElMessageBox.confirm('确定要中断当前执行吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await cancelExecution(currentExecutionId.value)
    ElMessage.success('执行已中断')

    // 更新状态
    logStatus.value = 'failed'
    logStage.value = 'cancelled'
    logProgress.value = 100

  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('中断执行失败: ' + (error.message || error))
      console.error(error)
    }
  }
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadScripts()
  loadEnvironments()
  loadCategories()
  loadTags()
})
</script>

<style scoped>
.scripts-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  align-items: center;
}

/* 脚本编辑对话框样式 */
.script-dialog :deep(.el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
  padding: 20px;
}

.script-form {
  padding-right: 10px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.log-actions {
  display: flex;
  gap: 8px;
}

.progress-section {
  margin-bottom: 16px;
}

.log-container {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 4px;
  max-height: 500px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.log-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.log-empty {
  color: #909399;
  text-align: center;
  padding: 40px;
  font-style: italic;
}

.error-container {
  margin-top: 16px;
}

.error-container pre {
  background-color: #fee;
  color: #c00;
  padding: 16px;
  border-radius: 4px;
  border-left: 4px solid #f56c6c;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  margin: 0;
  overflow-x: auto;
}

.files-section {
  margin-top: 16px;
}

.files-empty {
  color: #909399;
  text-align: center;
  padding: 40px;
  font-style: italic;
}

.file-preview-container {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 4px;
  max-height: 600px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.file-preview-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 使用指南样式 */
.script-guide {
  padding: 10px 0;
}

.script-guide h4 {
  color: #409eff;
  font-size: 15px;
  margin: 20px 0 10px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
}

.script-guide h4:first-child {
  margin-top: 0;
}

.guide-desc {
  color: #606266;
  font-size: 13px;
  margin: 8px 0;
  line-height: 1.6;
}

.guide-desc code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  color: #e83e8c;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 12px;
}

.code-example {
  background: #282c34;
  color: #abb2bf;
  padding: 12px 15px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  margin: 10px 0;
  border-left: 3px solid #409eff;
}

.guide-tips {
  background: #fff7e6;
  border: 1px solid #ffd591;
  border-radius: 4px;
  padding: 15px;
  margin-top: 20px;
}

.guide-tips h4 {
  color: #fa8c16;
  font-size: 14px;
  margin: 0 0 10px 0;
  border: none;
  padding: 0;
}

.guide-tips ul {
  margin: 0;
  padding-left: 20px;
}

.guide-tips li {
  color: #595959;
  font-size: 13px;
  line-height: 1.8;
  margin-bottom: 8px;
}

.guide-tips li:last-child {
  margin-bottom: 0;
}

.guide-tips code {
  background: #fffbe6;
  padding: 2px 6px;
  border-radius: 3px;
  color: #d4380d;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 12px;
}

.guide-tips strong {
  color: #262626;
}

/* 深色模式下的使用指南样式 */
.dark-mode .guide-desc {
  color: #b3b3b3;
}

.dark-mode .guide-desc code {
  background: #2a2a2a;
  color: #f78fb3;
}

.dark-mode .guide-tips {
  background: #2c2416;
  border-color: #594214;
}

.dark-mode .guide-tips h4 {
  color: #ffa940;
}

.dark-mode .guide-tips li {
  color: #d9d9d9;
}

.dark-mode .guide-tips code {
  background: #3d2f1f;
  color: #ff7a45;
}

.dark-mode .guide-tips strong {
  color: #f0f0f0;
}
</style>
