// Luckysheet wrapper - 确保 jQuery 全局变量在加载 luckysheet 之前设置好
export async function loadLuckysheet() {
  // 1. 先加载 jQuery 并设置全局变量
  const jqueryModule = await import('jquery')
  const jquery = jqueryModule.default || jqueryModule
  window.$ = window.jQuery = jquery

  // 2. 加载 mousewheel 插件
  await import('jquery-mousewheel')

  // 3. 最后加载 luckysheet
  const luckysheetModule = await import('luckysheet')
  const luckysheet = luckysheetModule.default || luckysheetModule
  window.luckysheet = luckysheet

  return luckysheet
}

// 默认导出加载函数
export default loadLuckysheet