// 后端 API 客户端(/api/v1/*,开发下由 vite proxy 转发到 127.0.0.1:8787)。
// 只做传输,不持有状态;事件通过回调交给 store。

export async function postJson(path, body) {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  })
  if (!r.ok) {
    let detail = ''
    try { detail = (await r.json()).detail || '' } catch { /* 非 JSON 错误体 */ }
    throw new Error(detail || 'HTTP ' + r.status)
  }
  return r.json()
}

export async function getJson(path) {
  const r = await fetch(path)
  if (!r.ok) throw new Error('HTTP ' + r.status)
  return r.json()
}

export async function putJson(path, body) {
  const r = await fetch(path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  })
  if (!r.ok) {
    let detail = ''
    try { detail = (await r.json()).detail || '' } catch { /* 非 JSON 错误体 */ }
    throw new Error(detail || 'HTTP ' + r.status)
  }
  return r.json()
}

export function modelsQuery(values) {
  // 变体标识按架构取自不同字段:qwen/flux.2 用 model_version,hidream 用 model_type,
  // wan/hv1.5/kandinsky 用 task(hidream 的 DiT 由 model_type 决定,优先于 task)
  const variant = values.model_version || values.model_type || values.task || ''
  return '/api/v1/models?' + new URLSearchParams({
    architecture: values.model_arch,
    model_version: variant,
  }).toString()
}

// SSE 订阅;返回带 close() 的句柄。终态后服务端关流,onerror 里静默关闭。
export function subscribeJobEvents(jobId, onEvent) {
  const es = new EventSource('/api/v1/jobs/' + jobId + '/events')
  es.onmessage = e => {
    try { onEvent(JSON.parse(e.data)) } catch { /* 忽略坏帧 */ }
  }
  es.onerror = () => { es.close() }
  return es
}

// 提交训练时剔除秘密与 UI 专属字段;后端另有白名单二次把关。
// enable_bucket / bucket_no_upscale / cache_directory 保留传输:它们用于后端生成数据集 TOML
// (argv 白名单不含它们,不会进入命令行)。
const OMIT_KEYS = new Set([
  'wandb_api_key', 'huggingface_token', 'huggingface_repo_id', 'async_upload',
  'model_arch', 'workflow',
])

export function trainPayloadValues(values) {
  const out = {}
  for (const [k, v] of Object.entries(values)) {
    if (!OMIT_KEYS.has(k)) out[k] = v
  }
  return out
}
