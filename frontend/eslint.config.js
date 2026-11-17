import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'

export default [
  { ignores: ['dist/**', 'node_modules/**'] },
  js.configs.recommended,
  ...pluginVue.configs['flat/essential'],
  {
    rules: {
      // 阶段 4 统一清理 console 后再收紧为 error
      'no-console': 'off',
      // catch 子句的未用错误对象是合法习惯；下划线前缀表示有意忽略
      'no-unused-vars': ['error', { caughtErrors: 'none', argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      // 模板作用域变量以 _ 开头表示有意忽略
      'vue/no-unused-vars': ['error', { ignorePattern: '^_' }],
      // 单词组件名（ExcelEditor 等）暂不强制
      'vue/multi-word-component-names': 'off',
    },
  },
]
