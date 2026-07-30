// 全局状态与动作 — 自设计原型 LoRA训练器.dc.html 的 DCLogic 直译(React class → Vue reactive)。
// 训练流程当前为假数据模拟;交互语义(作业状态机、缓存删除确认、argv 脱敏)
// 按 MUSUBI_TUNER_UI_ADAPTATION_HANDOFF.md 的 API 契约设计,后续替换为真实后端调用。
import { reactive } from 'vue'
import { getJson, modelsQuery, postJson, subscribeJobEvents, trainPayloadValues } from './api.js'

// ---- 运行配置(URL query) ----
// 默认为真实模式:无假数据、无模拟训练,未实现的提交动作明确提示「后端未连接」。
// ?demo=1 进入演示模式(种子数据 + 模拟训练引擎),其余演示参数仅在 demo 下生效:
// ?demo=1&theme=dark&simSpeed=4&demoOutcome=failure&seedErrors=false&showAdvanced=true
const q = new URLSearchParams(location.search)
export const demo = {
  demoMode: q.get('demo') === '1',
  initialTheme: q.get('theme') === 'dark' ? 'dark' : 'light',
  accent: q.get('accent') || '', // 留空则由 CSS 按主题取规范色(亮 #0070f3 / 暗 #3291ff)
  simSpeed: parseFloat(q.get('simSpeed')) || 2,
  demoOutcome: q.get('demoOutcome') || 'success', // failure 时在 62% 处模拟 OOM
  seedErrors: q.get('seedErrors') !== 'false', // demo 下默认预置 2 个真实校验错误
  showAdvanced: q.get('showAdvanced') === 'true',
}

// 演示模式的种子表单值(原型的假数据,仅 ?demo=1 时灌入)
const DEMO_VALUES = {
  project_dir: 'D:/lora/character-v1/training',
  output_dir: 'D:/lora/character-v1/output',
  output_name: 'character-v1',
  dit: 'D:/ComfyUI/models/diffusion_models/qwen_image_bf16.safetensors',
  vae: 'D:/ComfyUI/models/vae/qwen_image_vae.safetensor', // 故意缺 s,演示校验
  text_encoder: 'D:/ComfyUI/models/text_encoders/qwen_2.5_vl_7b.safetensors',
  dataset_config: 'D:/lora/character-v1/dataset_config.toml',
  cache_directory: 'D:/lora/character-v1/cache',
  logging_dir: 'D:/lora/character-v1/logs',
  attn_mode: 'sage_attn', // 演示「不支持训练」校验
  sample_prompt: '1girl, silver hair, studio portrait, soft rim light',
  sample_negative_prompt: 'lowres, worst quality, jpeg artifacts',
}

export const store = reactive({
  theme: 'light',
  page: 'train',
  status: 'idle', // idle|queued|validating|running|cancelling|cancelled|succeeded|failed
  step: 0, totalSteps: 4000, epoch: 0, totalEpochs: 10,
  loss: 0, avg: 0, series: [], simTime: 0, itps: 1.98,
  vram: 8.2, logs: [], seq: 0, samples: [], extraArtifacts: [],
  doneJobs: [], toasts: [], modal: null, exit: null,
  autoScroll: true, atBottom: true, errors: {}, banner: null,
  adv: {}, collapsed: {}, railTab: 'progress', narrow: false, keepCache: false, tSeq: 0,
  termPinned: false, termOrient: 'h', termFull: false, termOp: 0.92,
  jobId: '', pending: [], pSeq: 0, editingId: null, startedAt: '',
  // 当前机器与后端的真实信息;source: nvidia(后端环境 API)| webgl(仅 GPU 名)| none
  env: {
    gpuName: '', vramTotalGb: 0, vramUsedGb: 0, driver: '', computeCap: '', gpuCount: 0, source: 'none',
    backend: false, python: '', torch: null, accelerate: null,
  },
  // 训练器模型库(models/ 目录):当前架构+变体的推荐清单与目录内现有文件
  modelLib: { dir: '', catalog: [], files: {}, checked: false },
  // 全部 12 架构的完整模型清单(模型页「全部模型」区)
  modelLibAll: { architectures: [], checked: false },
  values: {
    project_dir: '',
    model_arch: 'qwen-image',
    model_version: 'edit-2511', task: '', model_type: '',
    workflow: 'train_network',
    output_dir: '',
    output_name: 'my-lora',
    dit: '',
    vae: '',
    text_encoder: '',
    vae_dtype: 'bfloat16',
    dit_dtype: 'bfloat16',
    network_weights: '',
    dataset_config: '',
    resolution_w: '1328', resolution_h: '1328',
    batch_size: '1', num_repeats: '1',
    enable_bucket: true, bucket_no_upscale: false,
    caption_extension: '.txt',
    cache_directory: '',
    network_module: 'standard_lora',
    network_dim: '16', network_alpha: '16', network_dropout: '0',
    network_args: 'loraplus_lr_ratio=4',
    dim_from_weights: false, scale_weight_norms: '0',
    optimizer_type: 'AdamW8bit',
    learning_rate: '1e-4', max_grad_norm: '1.0',
    optimizer_args: 'weight_decay=0.01',
    lr_scheduler: 'constant_with_warmup',
    lr_warmup_steps: '100', lr_scheduler_num_cycles: '1', lr_scheduler_min_lr_ratio: '0',
    max_train_epochs: '10', max_train_steps: '4000', seed: '42',
    gradient_accumulation_steps: '1',
    mixed_precision: 'bf16', save_precision: 'bf16',
    timestep_sampling: 'shift', discrete_flow_shift: '2.2',
    weighting_scheme: 'none', min_timestep: '0', max_timestep: '1000',
    attn_mode: 'sdpa',
    fp8_base: true, fp8_scaled: true, fp8_llm: false,
    gradient_checkpointing: true, blocks_to_swap: '0',
    use_pinned_memory_for_block_swap: false,
    split_attn: false, img_in_txt_in_offloading: false,
    sample_at_first: true, sample_every_n_epochs: '1', sample_every_n_steps: '0',
    sample_prompt: '',
    sample_negative_prompt: '',
    sample_w: '1328', sample_h: '1328', sample_steps: '20', sample_seed: '1234',
    save_every_n_epochs: '1', save_every_n_steps: '0', save_last_n_epochs: '4',
    save_state: false, save_state_on_train_end: false, resume: '',
    log_with: 'tensorboard', logging_dir: '',
    wandb_api_key: '', huggingface_repo_id: '', huggingface_token: '', async_upload: false,
  },
})

// 定时器与一次性标记(非响应式)
let timer = null, t1 = null, t2 = null, t3 = null, t4 = null
let warned = false
let mq = null, onKeyFn = null, onMqFn = null

// ---- 架构 capability(前端迷你表) ----
// 变体/任务枚举是「特定架构才有」的字段,依据交接文档 §8.2 逐架构核对;
// 无枚举的架构(hunyuan-video/framepack/flux.1-kontext/z-image/ideogram4/krea2)不渲染该字段。
// FramePack 的 f1/one_frame 与 Krea2 的 turbo_dit 是布尔扩展参数,不属于此下拉。
// 后端 Capability Registry(UI-CAP-001)就绪后,本表由 GET /api/v1/capabilities 取代。
export const ARCH_VARIANTS = {
  'qwen-image': [{ label: '训练类型', flag: 'model_version', options: ['original', 'layered', 'edit', 'edit-2509', 'edit-2511'] }],
  'flux.2': [{ label: '训练类型', flag: 'model_version', options: ['klein-4b', 'klein-base-4b', 'klein-9b', 'klein-base-9b', 'dev'] }],
  'wan2.1/2.2': [{ label: '任务', flag: 'task', options: ['t2v-14B', 't2v-1.3B', 'i2v-14B', 't2i-14B', 'flf2v-14B', 't2v-1.3B-FC', 't2v-14B-FC', 'i2v-14B-FC', 'i2v-A14B', 't2v-A14B'] }],
  'hunyuan-video-1.5': [{ label: '任务', flag: 'task', options: ['t2v', 'i2v'] }],
  'hidream-o1': [
    { label: '模型类型', flag: 'model_type', options: ['full', 'dev'] },
    { label: '任务', flag: 'task', options: ['t2i', 'i2i'] },
  ],
  'kandinsky5': [{
    label: '任务', flag: 'task', options: [
      'k5-lite-t2i-hd', 'k5-lite-i2i-hd', 'k5-lite-t2v-5s-sd', 'k5-lite-t2v-10s-sd', 'k5-lite-i2v-5s-sd',
      'k5-pro-t2v-5s-sd', 'k5-pro-t2v-5s-hd', 'k5-pro-t2v-10s-sd', 'k5-pro-t2v-10s-hd',
      'k5-pro-i2v-5s-sd', 'k5-pro-i2v-5s-hd',
      'k5-lite-t2v-5s-distil-sd', 'k5-lite-t2v-10s-distil-sd', 'k5-lite-t2v-5s-nocfg-sd', 'k5-lite-t2v-10s-nocfg-sd',
      'k5-lite-t2v-5s-pretrain-sd', 'k5-lite-t2v-10s-pretrain-sd',
    ],
  }],
}

// 全量微调只有这四个架构有入口(hv_train / qwen_image_train / zimage_train / hidream_o1_train)
export const FULL_FINETUNE_ARCHS = new Set(['hunyuan-video', 'qwen-image', 'z-image', 'hidream-o1'])

// ---- 基础动作 ----

function applyTheme(t) { document.documentElement.setAttribute('data-theme', t) }

function applyAccent() {
  if (demo.accent) document.documentElement.style.setProperty('--accent', demo.accent)
}

export function toggleTheme() {
  const t = store.theme === 'dark' ? 'light' : 'dark'
  applyTheme(t)
  store.theme = t
}

export function setV(flag, val) {
  delete store.errors[flag]
  store.values[flag] = val
  if (flag === 'model_arch') {
    // 切换架构:清空旧变体字段,按新架构的枚举重置为首项;不支持全量微调的架构强制回 LoRA 训练
    store.values.model_version = ''
    store.values.task = ''
    store.values.model_type = ''
    for (const v of ARCH_VARIANTS[val] || []) store.values[v.flag] = v.options[0]
    if (store.values.workflow === 'full_finetune' && !FULL_FINETUNE_ARCHS.has(val)) {
      store.values.workflow = 'train_network'
    }
  }
  // 架构或变体变化时刷新模型库并自动选择库中已有模型
  if (flag === 'model_arch' || flag === 'model_version') refreshModels()
  store.banner = null
}

// ---- 模型库:清单刷新、自动选择、一键下载 ----

export async function refreshModels(autoFill = true) {
  if (demo.demoMode) return
  try {
    const data = await getJson(modelsQuery(store.values))
    store.modelLib = { dir: data.models_dir, catalog: data.catalog, files: data.files, checked: true }
    if (!autoFill) return
    const filled = []
    for (const c of data.catalog) {
      // role 与表单字段同名(dit / text_encoder / vae);只填空字段,不覆盖手动输入
      if (c.exists && store.values[c.role] === '') {
        store.values[c.role] = c.local_path
        filled.push(c.filename)
      }
    }
    if (filled.length) {
      log('dim', '[models] auto-selected from library · ' + filled.join(', '))
      toast('info', '已自动选择模型库中的 ' + filled.length + ' 个模型')
    }
  } catch {
    store.modelLib = { ...store.modelLib, checked: false }
  }
}

export async function loadAllModels() {
  if (demo.demoMode) return
  try {
    const data = await getJson('/api/v1/models/all')
    store.modelLibAll = { architectures: data.architectures, checked: true }
  } catch {
    store.modelLibAll = { ...store.modelLibAll, checked: false }
  }
}

export async function downloadModel(architecture, filename) {
  try {
    const job = await postJson('/api/v1/models/download', { architecture, filename })
    if (job.status === 'exists') {
      toast('info', '模型已在库中 · ' + job.filename)
      refreshModels()
      return
    }
    store.jobId = job.job_id
    store.status = 'queued'
    store.startedAt = nowHHMM()
    store.exit = null
    log('dim', '[job] accepted ' + job.job_id + ' · ' + job.workflow + ' · ' + job.note)
    toast('info', '下载已开始 · ' + job.note + ' · 进度见终端')
    attachRealJob(job.job_id)
  } catch (err) {
    log('err', 'ERROR: ' + err.message)
    toast('error', '下载提交失败 · ' + err.message)
  }
}

export function pushLogs(pairs) {
  for (const p of pairs) store.logs.push({ id: ++store.seq, kind: p[0], text: p[1] })
  if (store.logs.length > 400) store.logs.splice(0, store.logs.length - 400)
}

export function log(kind, text) { pushLogs([[kind, text]]) }

export function toast(kind, text, action) {
  const id = ++store.tSeq
  store.toasts.push({ id, kind, text, action: action || null })
  if (store.toasts.length > 3) store.toasts.splice(0, store.toasts.length - 3)
  setTimeout(() => dismissToast(id), action ? 9000 : 5200)
}

export function dismissToast(id) {
  store.toasts = store.toasts.filter(t => t.id !== id)
}

// ---- 校验(跨字段规则与真实 musubi-tuner 后端一致,见交接文档 §7.7) ----

export function validate() {
  const v = store.values, e = {}
  if (!(parseFloat(v.learning_rate) > 0)) e.learning_rate = '学习率需为正数,常用 1e-4'
  if (v.vae && !/\.safetensors$/.test(v.vae)) e.vae = '文件不存在:检查扩展名是否为 .safetensors'
  if (v.attn_mode === 'sage_attn') e.attn_mode = 'SageAttention 当前不支持训练,请改用 sdpa 或 flash_attn'
  if (v.fp8_scaled && !v.fp8_base) e.fp8_scaled = '--fp8_scaled 需要同时启用 --fp8_base'
  if (v.log_with === 'tensorboard' && !v.logging_dir) e.logging_dir = 'TensorBoard 需要指定 logging_dir'
  if (String(v.sample_every_n_epochs) === '0') e.sample_every_n_epochs = '不能为 0,关闭采样请取消「首次采样」并留空'
  if (!v.dataset_config) e.dataset_config = '必填:dataset_config'
  return e
}

export function autoFix() {
  const v = store.values
  if (!/\.safetensors$/.test(v.vae)) v.vae = v.vae.replace(/\.safetensor$/, '.safetensors')
  if (v.attn_mode === 'sage_attn') v.attn_mode = 'sdpa'
  if (v.fp8_scaled && !v.fp8_base) v.fp8_base = true
  if (!(parseFloat(v.learning_rate) > 0)) v.learning_rate = '1e-4'
  store.errors = {}
  store.banner = null
  log('dim', '[form] 2 fields auto-corrected · vae, attn_mode')
  toast('info', '已修正 2 个字段 · 可以重新提交')
}

// ---- 作业生命周期(排队 → 校验 → 训练;模拟) ----

export function start() {
  const st = store.status
  if (st === 'queued' || st === 'validating' || st === 'running' || st === 'cancelling') return
  if (!demo.demoMode) { startReal(); return }
  const ed = store.editingId ? store.pending.find(p => p.id === store.editingId) : null
  const jid = ed ? ed.id : store.jobId
  store.status = 'queued'
  store.errors = {}
  store.banner = null
  store.exit = null
  store.jobId = jid
  store.startedAt = nowHHMM()
  if (ed) store.pending = store.pending.filter(p => p.id !== ed.id)
  store.editingId = null
  log('dim', '[job] accepted ' + jid + ' · client_request_id=8c1d…e42')
  toast('info', '已加入队列 · 等待 GPU 0 资源租约')
  t1 = setTimeout(() => {
    store.status = 'validating'
    pushLogs([['dim', '[stage] validating · dataset_config, dit, network_module, optimizer']])
    t2 = setTimeout(() => {
      const e = validate()
      const n = Object.keys(e).length
      if (n) {
        store.status = 'idle'
        store.errors = e
        store.banner = { count: n, detail: Object.keys(e).map(k => '--' + k).join('  ') }
        log('err', 'ERROR: validation failed · ' + n + ' invalid field(s) · nothing was executed')
        toast('error', '校验未通过 · ' + n + ' 个字段需要修正', { label: '自动修正', fn: autoFix })
        return
      }
      beginRun()
    }, 850)
  }, 700)
}

// ---- 真实模式:提交后端并订阅 SSE 事件 ----

let esHandle = null
let realT0 = 0

function startReal() {
  const e = validate()
  const n = Object.keys(e).length
  if (n) {
    store.errors = e
    store.banner = { count: n, detail: Object.keys(e).map(k => '--' + k).join('  ') }
    log('err', 'ERROR: validation failed · ' + n + ' invalid field(s) · nothing was submitted')
    toast('error', '校验未通过 · ' + n + ' 个字段需要修正', { label: '自动修正', fn: autoFix })
    return
  }
  store.errors = {}
  store.banner = null
  store.exit = null
  store.status = 'queued'
  store.startedAt = nowHHMM()
  submitTrain()
}

async function submitTrain() {
  try {
    const job = await postJson('/api/v1/jobs/train', {
      architecture: store.values.model_arch,
      workflow: store.values.workflow,
      values: trainPayloadValues(store.values),
    })
    store.jobId = job.job_id
    log('dim', '[job] accepted ' + job.job_id + ' · ' + job.workflow)
    attachRealJob(job.job_id)
  } catch (err) {
    store.status = 'idle'
    log('err', 'ERROR: backend not connected or rejected · ' + err.message)
    toast('error', '后端未连接或已拒绝 · ' + err.message)
  }
}

async function submitCache(kind, keep) {
  try {
    const job = await postJson('/api/v1/jobs/cache-' + (kind === 'latents' ? 'latents' : 'text'), {
      architecture: store.values.model_arch,
      keep_cache: !!keep,
      values: {
        dataset_config: store.values.dataset_config,
        vae: store.values.vae,
        text_encoder: store.values.text_encoder,
        model_version: store.values.model_version,
      },
    })
    store.jobId = job.job_id
    store.status = 'queued'
    store.startedAt = nowHHMM()
    store.exit = null
    log('dim', '[job] accepted ' + job.job_id + ' · ' + job.workflow)
    toast('info', '缓存作业已提交 · ' + job.job_id)
    attachRealJob(job.job_id)
  } catch (err) {
    log('err', 'ERROR: backend not connected or rejected · ' + err.message)
    toast('error', '后端未连接或已拒绝 · ' + err.message)
  }
}

function attachRealJob(id) {
  if (esHandle) { esHandle.close(); esHandle = null }
  Object.assign(store, {
    step: 0, epoch: 0, avg: 0, loss: 0, series: [], samples: [], simTime: 0,
    totalSteps: 0, totalEpochs: 0,
  })
  realT0 = Date.now()
  esHandle = subscribeJobEvents(id, ev => {
    if (ev.type === 'log') {
      log(ev.kind || 'ink', ev.text)
    } else if (ev.type === 'progress') {
      if (ev.total) store.totalSteps = ev.total
      if (typeof ev.step === 'number') store.step = ev.step
      if (ev.total_epochs) store.totalEpochs = ev.total_epochs
      if (ev.epoch) store.epoch = ev.epoch
      if (ev.itps) store.itps = ev.itps
      store.simTime = (Date.now() - realT0) / 1000
      if (typeof ev.avr_loss === 'number') {
        store.avg = ev.avr_loss
        store.loss = ev.avr_loss
        // 后端只解析 avr_loss:raw 与 smooth 同值,不编造原始损失
        store.series.push({ x: store.step, raw: ev.avr_loss, s: ev.avr_loss })
        if (store.series.length > 2000) store.series.splice(0, store.series.length - 2000)
      }
    } else if (ev.type === 'status') {
      handleRealStatus(ev)
    }
  })
}

function handleRealStatus(ev) {
  const st = ev.status
  store.status = st
  if (st === 'running') {
    store.startedAt = store.startedAt || nowHHMM()
    return
  }
  if (st !== 'succeeded' && st !== 'failed' && st !== 'cancelled') return
  store.simTime = (Date.now() - realT0) / 1000
  if (st === 'failed') {
    store.exit = {
      line: 'exit_code ' + (ev.exit_code ?? '?') + ' · ' + store.jobId,
      tail: (ev.stderr_tail || []).map(t => ({ text: t })),
    }
    toast('error', '作业失败 · 退出码 ' + (ev.exit_code ?? '?'))
  } else if (st === 'succeeded') {
    toast('info', '作业完成 · ' + (store.values.output_name || store.jobId))
  } else {
    toast('warn', '已取消 · ' + store.jobId)
  }
  finishJob(st, store.step)
  if (esHandle) { esHandle.close(); esHandle = null }
  refreshModels() // 下载/训练结束后刷新模型库(下载完成的模型自动选入表单)
  loadAllModels()
}

function beginRun() {
  const v = store.values
  Object.assign(store, {
    status: 'running', step: 0, epoch: 1, series: [], loss: 0, avg: 0,
    simTime: 0, samples: [], exit: null, vram: 8.2,
  })
  warned = false
  pushLogs([
    ['dim', '[stage] loading DiT · qwen_image_bf16.safetensors · fp8_scaled=True'],
    ['dim', '[stage] applying network · standard_lora dim=' + v.network_dim + ' alpha=' + v.network_alpha],
    ['dim', '[stage] optimizer AdamW8bit · lr=' + v.learning_rate + ' scheduler=' + v.lr_scheduler],
    ['ink', 'running training / 4000 steps / 10 epochs · session 20260730-1402'],
  ])
  toast('info', '训练已开始 · GPU 0 · RTX 4090')
  const period = Math.max(28, Math.round(90 / (demo.simSpeed || 2)))
  clearInterval(timer)
  timer = setInterval(tick, period)
}

function tick() {
  const s = store
  if (s.status !== 'running') return
  const inc = 8
  const total = s.totalSteps
  const failAt = demo.demoOutcome === 'failure' ? Math.round(total * 0.62) : Infinity
  const step = Math.min(total, s.step + inc)
  const raw = 0.30 * Math.exp(-step / 1050) + 0.058 + (Math.random() - 0.5) * 0.035
  const avg = s.avg === 0 ? raw : s.avg * 0.94 + raw * 0.06
  const simTime = s.simTime + inc / s.itps
  const epoch = Math.max(1, Math.ceil(step / (total / s.totalEpochs)))
  const swap = parseInt(s.values.blocks_to_swap || '0', 10)
  const peak = swap >= 30 ? 15.4 : (swap > 0 ? 19.6 : 23.4)
  const vram = 8.2 + (peak - 8.2) * Math.min(1, step / 320)

  const prevEpoch = s.epoch
  s.series.push({ x: step, raw: Math.max(0.02, raw), s: avg })
  Object.assign(s, { step, loss: raw, avg, simTime, vram, epoch })

  if (epoch !== prevEpoch) {
    const name = s.values.output_name + '-' + String(epoch - 1).padStart(6, '0') + '.safetensors'
    pushLogs([
      ['ink', 'saving checkpoint: ' + name],
      ['dim', 'generating sample images at epoch ' + (epoch - 1) + ' · 1 prompt'],
    ])
    s.samples = [{ id: 'e' + (epoch - 1) + 'a', label: 'epoch ' + (epoch - 1), reso: s.values.sample_w + '×' + s.values.sample_h }]
      .concat(s.samples).slice(0, 6)
    s.extraArtifacts = [
      { name, kind: 'epoch checkpoint', size: '152.4 MB', created: clock(simTime), job: s.jobId, remote: '—' },
    ].concat(s.extraArtifacts)
    if (epoch === 2) toast('info', '已保存 epoch 1 检查点 · ' + name)
  }

  if (step % 320 === 0) {
    const pct = Math.round(step / total * 100)
    const filled = Math.round(pct / 10)
    const bar = '█'.repeat(filled) + '▏'.repeat(filled < 10 ? 1 : 0) + ' '.repeat(Math.max(0, 10 - filled - 1))
    log('ink', 'steps: ' + String(pct).padStart(3, ' ') + '%|' + bar + '| ' + step + '/' + total +
      ' [' + clock(simTime) + '<' + clock((total - step) / s.itps) + ', ' + s.itps.toFixed(2) + 'it/s, avr_loss=' + avg.toFixed(4) + ']')
  }

  if (vram / 24 > 0.9 && !warned) {
    warned = true
    log('warn', 'WARNING: VRAM usage ' + Math.round(vram / 24 * 100) + '% (' + vram.toFixed(1) + '/24.0 GB) — consider --blocks_to_swap or --fp8_llm')
    toast('warn', '显存吃紧 ' + Math.round(vram / 24 * 100) + '% · 建议提高 blocks_to_swap')
  }

  if (step >= failAt) {
    clearInterval(timer)
    pushLogs([
      ['err', 'Traceback (most recent call last):'],
      ['err', '  File "src/musubi_tuner/qwen_image_train_network.py", line 616, in <module>'],
      ['err', 'torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 1.62 GiB'],
      ['err', 'ERROR: process exited with code 1 during stage=training'],
    ])
    warned = false
    Object.assign(s, {
      status: 'failed', vram: 8.2,
      exit: {
        line: 'exit_code 1 · stage training · step ' + step + '/' + total,
        tail: [
          { text: 'torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 1.62 GiB' },
          { text: 'GPU 0 has a total capacity of 24.00 GiB of which 0.41 GiB is free.' },
          { text: 'argv: python qwen_image_train_network.py … --huggingface_token <redacted>' },
        ],
      },
    })
    finishJob('failed', step)
    toast('error', '训练失败 · CUDA out of memory,退出码 1')
    if (s.pending.length) {
      log('warn', '[queue] paused · ' + s.pending.length + ' job(s) waiting · 上一个作业非零退出')
      toast('warn', '队列已暂停 · ' + s.pending.length + ' 个任务等待,修正后可继续')
    }
    return
  }

  if (step >= total) {
    clearInterval(timer)
    const name = s.values.output_name + '.safetensors'
    pushLogs([
      ['ink', 'saving checkpoint: ' + name],
      ['dim', '[job] succeeded · 4000/4000 steps · ' + clock(simTime)],
    ])
    warned = false
    s.status = 'succeeded'
    s.vram = 8.2
    s.extraArtifacts = [
      { name, kind: 'final checkpoint', size: '152.4 MB', created: clock(simTime), job: s.jobId, remote: 'uploaded' },
    ].concat(s.extraArtifacts)
    finishJob('succeeded', step)
    toast('info', '训练完成 · ' + name + ' 已保存')
    if (s.pending.length) {
      if (s.editingId) {
        log('warn', '[queue] paused · 排队任务正在编辑,请手动开始')
        toast('warn', '队列已暂停 · 排队任务正在编辑,改完后手动点「开始训练」')
      } else {
        t4 = setTimeout(startNext, 1500)
      }
    }
  }
}

// ---- 队列 ----

export function enqueue() {
  const s = store
  const base = s.values.output_name.replace(/-v\d+$/, '')
  const n = ++s.pSeq
  const job = {
    id: 'job_' + (n * 13 + 3) + 'c' + (n * 37 % 90 + 10) + 'e' + n,
    name: base + '-v' + (n + 1), dim: s.values.network_dim,
    arch: s.values.model_arch, workflow: s.values.workflow,
  }
  s.pending.push(job)
  log('dim', '[queue] enqueued ' + job.name + ' · ' + job.id + ' · 当前作业结束后自动开始')
  toast('info', '已加入队列 · ' + job.name + ' 会在当前训练结束后自动开始')
}

export function editPending(p) {
  store.page = 'train'
  store.editingId = p.id
  Object.assign(store.values, { output_name: p.name, network_dim: p.dim, model_arch: p.arch, workflow: p.workflow })
  log('dim', '[queue] editing ' + p.id + ' · 队列自动接续已暂停')
  toast('warn', '已载入 ' + p.name + ' 配置 · 编辑期间队列暂停,改完手动点「开始训练」')
}

function startNext() {
  const next = store.pending[0]
  if (!next) return
  store.pending = store.pending.slice(1)
  store.jobId = next.id
  Object.assign(store.values, { output_name: next.name, network_dim: next.dim })
  log('ink', '[queue] starting next job ' + next.id + ' · ' + next.name)
  toast('info', '队列继续 · ' + next.name)
  setTimeout(start, 150)
}

function finishJob(status, step) {
  store.doneJobs = [{
    id: store.jobId, workflow: store.values.workflow + ' · ' + store.values.model_arch,
    note: store.values.output_name + ' · dim ' + store.values.network_dim,
    status, progress: step + '/' + store.totalSteps, started: store.startedAt || '—', duration: clock(store.simTime),
  }].concat(store.doneJobs)
}

// ---- 取消 ----

export function askCancel() { store.modal = 'cancel' }
export function closeModal() { store.modal = null }

export function confirmCancel() {
  store.modal = null
  if (!demo.demoMode) {
    store.status = 'cancelling'
    postJson('/api/v1/jobs/' + store.jobId + '/cancel').catch(err => {
      log('err', 'ERROR: cancel failed · ' + err.message)
      toast('error', '取消请求失败 · ' + err.message)
    })
    return // 后续状态由 SSE 事件驱动
  }
  clearInterval(timer)
  store.status = 'cancelling'
  log('warn', '[job] cancel_requested · sending graceful terminate, waiting for safe step boundary')
  t3 = setTimeout(() => {
    store.status = 'cancelled'
    pushLogs([
      ['dim', '[job] process group terminated · cancelled at step ' + store.step],
      ['dim', '[job] last artifact kept: ' + store.values.output_name + '-000002.safetensors'],
    ])
    finishJob('cancelled', store.step)
    toast('warn', '已取消 · 检查点保留至 epoch ' + Math.max(1, store.epoch - 1))
  }, 1700)
}

// ---- 缓存(清理计划确认 → 执行) ----

export function planCleanup() { store.modal = 'cleanup' }
export function toggleKeep() { store.keepCache = !store.keepCache }

export function confirmCleanup() {
  const keep = store.keepCache
  store.modal = null
  if (!demo.demoMode) { submitCache('latents', keep); return }
  pushLogs(keep
    ? [['dim', '[cache] latents · keep_cache=True · 0 files removed · 184 items to encode']]
    : [['warn', '[cache] cleanup executed · 3 stale files removed (412.6 MB)'], ['dim', '[cache] latents · 184 items to encode · batch_size=1']])
  toast('info', keep ? '已加入队列 · 保留旧缓存' : '已加入队列 · 将删除 3 个旧缓存')
}

export function cacheText() {
  if (!demo.demoMode) { submitCache('text', store.keepCache); return }
  log('dim', '[cache] text encoder outputs queued · qwen_2.5_vl_7b · fp8_vl=False')
  toast('info', '文本编码器缓存已加入队列')
}

// ---- 弹窗与杂项 ----

export function showCommand() { store.modal = 'command' }
export function savePreset() {
  if (!demo.demoMode) { toast('error', '后端未连接 · 预设保存尚未实现'); return }
  toast('info', '预设已保存 · character-v1 · 原子写入')
}

export function copyLogs() {
  const text = store.logs.map(l => l.text).join('\n')
  navigator.clipboard?.writeText(text)
  toast('info', '日志已复制到剪贴板')
}

export function clearLogs() { store.logs = [] }
export function toggleScroll() { store.autoScroll = !store.autoScroll }

export function onLogScroll(e) {
  const el = e.target
  const at = el.scrollHeight - el.scrollTop - el.clientHeight < 24
  if (at !== store.atBottom) store.atBottom = at
}

export function termDbl() { store.termFull = !store.termFull }
export function togglePin() { store.termPinned = !store.termPinned; store.termFull = false }
export function toggleOrient() { store.termOrient = store.termOrient === 'h' ? 'v' : 'h' }
export function setTermOp(ev) { store.termOp = Math.max(0.35, Math.min(1, parseInt(ev.target.value, 10) / 100)) }

export function importToml() {
  if (!demo.demoMode) { toast('error', '后端未连接 · TOML 导入尚未实现'); return }
  toast('warn', '导入完成 · 2 个未知字段被忽略:legacy_control_resize')
}
export function exportToml() {
  if (!demo.demoMode) { toast('error', '后端未连接 · TOML 导出尚未实现,可先用「复制」'); return }
  toast('info', 'config.toml 已导出到 output/')
}

// ---- 真实硬件探测 ----
// 首选本地环境 API(vite 插件跑 nvidia-smi,路径与未来后端 /api/v1/environment 对齐),
// 拿不到时回退 WebGL 读 GPU 型号(浏览器拿不到显存,只显示名称)。

let envTimer = null

function shortGpuName(name) {
  return (name || '').replace(/NVIDIA\s*/i, '').replace(/GeForce\s*/i, '').trim()
}

async function fetchEnv() {
  const r = await fetch('/api/v1/environment')
  if (!r.ok) throw new Error('env http ' + r.status)
  const data = await r.json()
  const g = data.gpus && data.gpus[0]
  store.env = {
    ...store.env,
    backend: true,
    python: data.python || '',
    torch: data.torch || null,
    accelerate: data.accelerate || null,
    ...(g ? {
      gpuName: shortGpuName(g.name),
      vramTotalGb: (g.memory_total_mb || 0) / 1024,
      vramUsedGb: (g.memory_used_mb || 0) / 1024,
      driver: g.driver || '',
      computeCap: g.compute_cap || '',
      gpuCount: data.gpus.length,
      source: 'nvidia',
    } : {}),
  }
}

function webglGpuName() {
  try {
    const gl = document.createElement('canvas').getContext('webgl')
    if (!gl) return ''
    const ext = gl.getExtension('WEBGL_debug_renderer_info')
    const raw = String((ext && gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) || gl.getParameter(gl.RENDERER) || '')
    const m = /ANGLE \([^,]+,\s*([^,(]+)/.exec(raw)
    const name = (m ? m[1] : raw).replace(/\s*\(0x[0-9A-Fa-f]+\)/, '').replace(/Direct3D.*$/i, '').trim()
    return shortGpuName(name)
  } catch { return '' }
}

async function probeEnv() {
  try {
    await fetchEnv()
    clearInterval(envTimer)
    envTimer = setInterval(() => fetchEnv().catch(() => { store.env.backend = false }), 5000) // 5s 一刷
    // 后端已连接时以后端报告为准:无 GPU 就如实显示未检测,
    // 绝不用 WebGL 补——那读到的是访问者浏览器的显卡,不是训练机的
    log('ink', 'backend connected · python ' + (store.env.python || '?') +
      ' · torch ' + (store.env.torch || '未安装') + ' · accelerate ' + (store.env.accelerate || '未安装'))
  } catch {
    store.env.backend = false
    const name = webglGpuName()
    if (name) store.env = { ...store.env, gpuName: name, source: 'webgl' }
    log('warn', 'backend not connected · 启动:python -m uvicorn backend.main:app --port 8787')
  }
}

// ---- 工具 ----

export function nowHHMM() {
  const d = new Date()
  const p = n => String(n).padStart(2, '0')
  return p(d.getHours()) + ':' + p(d.getMinutes())
}

export function clock(sec) {
  sec = Math.max(0, Math.round(sec))
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60
  const p = n => String(n).padStart(2, '0')
  return h ? h + ':' + p(m) + ':' + p(s) : p(m) + ':' + p(s)
}

// ---- 生命周期(App.vue 挂载/卸载时调用) ----

export function init() {
  applyTheme(demo.initialTheme)
  store.theme = demo.initialTheme
  applyAccent()
  if (demo.demoMode) {
    Object.assign(store.values, DEMO_VALUES)
    store.jobId = 'job_7f3a91'
    if (!demo.seedErrors) {
      store.values.attn_mode = 'sdpa'
      store.values.vae = store.values.vae + 's'
    }
  }
  onKeyFn = e => { if (e.key === 'Escape' && store.termFull) store.termFull = false }
  window.addEventListener('keydown', onKeyFn)
  mq = window.matchMedia('(max-width: 1199px)')
  onMqFn = e => { store.narrow = e.matches }
  mq.addEventListener('change', onMqFn)
  store.narrow = mq.matches
  if (demo.demoMode) {
    pushLogs([
      ['dim', 'musubi tuner 0.3.4 · torch 2.5.1+cu124 · CUDA 12.4 (demo)'],
      ['dim', 'capability registry loaded · 12 architectures · 925 cli arguments (demo)'],
      ['ink', 'project D:/lora/character-v1 ready · workflow=train_network arch=qwen-image (demo)'],
      ['dim', 'waiting for job submission…'],
    ])
  } else {
    pushLogs([
      ['dim', 'musubi tuner ui · 前端就绪'],
      ['dim', 'probing backend · GET /api/v1/environment'],
      ['dim', 'waiting for job submission…'],
    ])
  }
  probeEnv()
  refreshModels()
}

export function destroy() {
  clearInterval(timer)
  clearInterval(envTimer)
  clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4)
  if (esHandle) { esHandle.close(); esHandle = null }
  if (mq && onMqFn) mq.removeEventListener('change', onMqFn)
  if (onKeyFn) window.removeEventListener('keydown', onKeyFn)
}
