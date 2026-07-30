// 跨组件共享的派生数据 — 原型 renderVals()/buildGroups() 的直译。
// 字段定义当前只按 Qwen-Image 写实;12 架构的变体/扩展参数将来由后端 Capability Registry 生成。
import { computed, reactive } from 'vue'
import {
  store, demo, setV, toast, autoFix, askCancel, editPending, clock,
  ARCH_VARIANTS, FULL_FINETUNE_ARCHS,
} from './store.js'

// 各架构的入口脚本与 LoRA 模块(交接文档 §7.3/§7.4/§7.5;由后端 adapter 权威决定,此处仅供命令预览)
const TRAIN_ENTRY = {
  'hunyuan-video': 'hv_train_network', 'wan2.1/2.2': 'wan_train_network', 'framepack': 'fpack_train_network',
  'hunyuan-video-1.5': 'hv_1_5_train_network', 'flux.1-kontext': 'flux_kontext_train_network',
  'flux.2': 'flux_2_train_network', 'qwen-image': 'qwen_image_train_network', 'z-image': 'zimage_train_network',
  'hidream-o1': 'hidream_o1_train_network', 'ideogram4': 'ideogram4_train_network',
  'kandinsky5': 'kandinsky5_train_network', 'krea2': 'krea2_train_network',
}
const FT_ENTRY = {
  'hunyuan-video': 'hv_train', 'qwen-image': 'qwen_image_train',
  'z-image': 'zimage_train', 'hidream-o1': 'hidream_o1_train',
}
const LORA_MODULE = {
  'hunyuan-video': 'networks.lora', 'wan2.1/2.2': 'networks.lora_wan', 'framepack': 'networks.lora_framepack',
  'hunyuan-video-1.5': 'networks.lora_hv_1_5', 'flux.1-kontext': 'networks.lora_flux',
  'flux.2': 'networks.lora_flux_2', 'qwen-image': 'networks.lora_qwen_image', 'z-image': 'networks.lora_zimage',
  'hidream-o1': 'networks.lora_hidream_o1', 'ideogram4': 'networks.lora_ideogram4',
  'kandinsky5': 'networks.lora_kandinsky', 'krea2': 'networks.lora_krea2',
}

// ---- 表单字段工厂 ----

function mkField(label, flag, type, extra) {
  const e = extra || {}
  const v = store.values[flag]
  const isTog = type === 'toggle'
  return {
    label, flag, hint: e.hint || '', ph: e.ph || '',
    value: v === undefined || v === null ? '' : v,
    error: store.errors[flag] || '',
    options: (e.options || []).map(o => ({ v: o })),
    min: e.min || 0, max: e.max || 100,
    isPath: type === 'path', isText: type === 'text', isNum: type === 'num',
    isSelect: type === 'select', isArea: type === 'area', isSlider: type === 'slider',
    isSecret: type === 'secret', isSeg: type === 'seg',
    segs: (type === 'seg' ? (e.options || []) : []).map(o => ({
      label: o.label, active: v === o.v, idle: v !== o.v, go: () => setV(flag, o.v),
    })),
    isOn: isTog && v === true, isOff: isTog && v !== true,
    onInput: ev => setV(flag, ev.target.value),
    onToggle: () => setV(flag, !v),
  }
}

// ---- 参数分组(10 张卡;高级参数二级折叠) ----

function buildGroups() {
  const F = mkField
  const arch = store.values.model_arch
  // 变体/任务字段按架构条件渲染:该架构没有的字段不出现
  const variantFields = (ARCH_VARIANTS[arch] || []).map(vd =>
    F(vd.label, vd.flag, 'select', { options: vd.options, hint: '由架构决定 · 后端 capability 就绪后从 API 生成' }))
  const workflowField = FULL_FINETUNE_ARCHS.has(arch)
    ? F('训练方式', 'workflow', 'seg', { options: [{ v: 'train_network', label: 'LoRA 训练' }, { v: 'full_finetune', label: '全量微调' }], hint: '两者是独立 capability:全量微调没有 network_dim,内存与保存语义也不同' })
    : F('训练方式', 'workflow', 'seg', { options: [{ v: 'train_network', label: 'LoRA 训练' }], hint: '该架构仅支持 LoRA 训练' })
  const defs = [
    {
      key: 'basic', eyebrow: 'BASIC', title: '基础', desc: '训练模型 + 变体/任务 + 训练方式决定后端选用哪个入口脚本。',
      fields: [
        F('训练集目录', 'project_dir', 'path', { hint: '图片与同名 .txt 标注放在这里' }),
        F('训练模型', 'model_arch', 'select', { options: ['qwen-image', 'z-image', 'hunyuan-video', 'hunyuan-video-1.5', 'wan2.1/2.2', 'framepack', 'flux.1-kontext', 'flux.2', 'hidream-o1', 'ideogram4', 'kandinsky5', 'krea2'] }),
        ...variantFields,
        workflowField,
        F('输出目录', 'output_dir', 'path'),
        F('输出名', 'output_name', 'text'),
      ], adv: [],
    },
    {
      key: 'model', eyebrow: 'MODEL', title: '模型与权重', desc: '可在「模型」页一键下载;模型库中已有时,切换架构/变体会自动选择。',
      fields: [
        F('DiT', 'dit', 'path'),
        F('VAE', 'vae', 'path'),
        F('Text Encoder', 'text_encoder', 'path'),
        F('VAE 精度', 'vae_dtype', 'select', { options: ['bfloat16', 'float16', 'float32'] }),
      ],
      adv: [
        F('DiT 精度', 'dit_dtype', 'select', { options: ['bfloat16', 'float16'] }),
        F('续训权重', 'network_weights', 'path', { ph: '留空表示从零开始' }),
      ],
    },
    {
      key: 'dataset', eyebrow: 'DATASET', title: '数据集', desc: '支持多个 [[datasets]];此处是当前激活的那一组。', cache: true,
      fields: [
        F('数据集配置', 'dataset_config', 'path'),
        F('分辨率 宽', 'resolution_w', 'num'),
        F('分辨率 高', 'resolution_h', 'num'),
        F('批大小', 'batch_size', 'num'),
        F('重复次数', 'num_repeats', 'num'),
        F('启用分桶', 'enable_bucket', 'toggle'),
        F('禁止放大', 'bucket_no_upscale', 'toggle'),
        F('caption 扩展名', 'caption_extension', 'text'),
      ],
      adv: [F('缓存目录', 'cache_directory', 'path', { hint: '每个 dataset 的最终缓存目录必须唯一' })],
    },
    {
      key: 'network', eyebrow: 'NETWORK', title: '网络', desc: '只提交稳定名称,由 adapter 映射到 network_module 路径。',
      fields: [
        F('网络类型', 'network_module', 'select', { options: ['standard_lora', 'loha', 'lokr'] }),
        F('维度', 'network_dim', 'num'),
        F('Alpha', 'network_alpha', 'num'),
        F('Dropout', 'network_dropout', 'num'),
        F('网络参数', 'network_args', 'text', { hint: 'key=value 列表,类型化编辑' }),
      ],
      adv: [
        F('从权重推断维度', 'dim_from_weights', 'toggle'),
        F('权重范数缩放', 'scale_weight_norms', 'num'),
      ],
    },
    {
      key: 'optimizer', eyebrow: 'OPTIMIZER', title: '优化器与学习率', desc: '默认只开放已验证的内建项;自定义 module 视为执行本机代码。',
      fields: [
        F('优化器', 'optimizer_type', 'select', { options: ['AdamW8bit', 'AdamW', 'Adafactor', 'Lion8bit', 'Prodigy'] }),
        F('学习率', 'learning_rate', 'num'),
        F('梯度裁剪', 'max_grad_norm', 'num'),
        F('调度器', 'lr_scheduler', 'select', { options: ['constant', 'constant_with_warmup', 'cosine', 'cosine_with_restarts', 'polynomial', 'linear'] }),
        F('预热步数', 'lr_warmup_steps', 'num'),
      ],
      adv: [
        F('优化器参数', 'optimizer_args', 'text'),
        F('重启周期数', 'lr_scheduler_num_cycles', 'num'),
        F('最小 LR 比例', 'lr_scheduler_min_lr_ratio', 'num'),
      ],
    },
    {
      key: 'training', eyebrow: 'TRAINING', title: '训练参数', desc: 'epoch 与 step 同时给出时,先到者停止。',
      fields: [
        F('最大 epoch', 'max_train_epochs', 'num'),
        F('最大 step', 'max_train_steps', 'num'),
        F('随机种子', 'seed', 'num'),
        F('梯度累积', 'gradient_accumulation_steps', 'num'),
        F('混合精度', 'mixed_precision', 'select', { options: ['bf16', 'fp16', 'no'] }),
        F('保存精度', 'save_precision', 'select', { options: ['bf16', 'fp16', 'float32'] }),
        F('时间步采样', 'timestep_sampling', 'select', { options: ['shift', 'uniform', 'sigmoid', 'flux_shift', 'logsnr'] }),
        F('Flow Shift', 'discrete_flow_shift', 'num'),
      ],
      adv: [
        F('加权方案', 'weighting_scheme', 'select', { options: ['none', 'sigma_sqrt', 'logit_normal', 'mode', 'cosmap'] }),
        F('最小时间步', 'min_timestep', 'num'),
        F('最大时间步', 'max_timestep', 'num'),
      ],
    },
    {
      key: 'memory', eyebrow: 'MEMORY', title: '内存与注意力', desc: 'blocks_to_swap 直接影响下方显存曲线,调高可消除显存警告。',
      fields: [
        F('注意力实现', 'attn_mode', 'select', { options: ['sdpa', 'flash_attn', 'flash3', 'xformers', 'sage_attn'] }),
        F('FP8 base', 'fp8_base', 'toggle'),
        F('FP8 scaled', 'fp8_scaled', 'toggle', { hint: '要求同时启用 fp8_base' }),
        F('FP8 文本编码器', 'fp8_llm', 'toggle'),
        F('梯度检查点', 'gradient_checkpointing', 'toggle'),
        F('Block Swap', 'blocks_to_swap', 'slider', { min: 0, max: 58 }),
        F('Block Swap 锁页内存', 'use_pinned_memory_for_block_swap', 'toggle', { hint: '建议 64GB+ 系统内存' }),
      ],
      adv: [
        F('Split Attention', 'split_attn', 'toggle'),
        F('img/txt in 卸载', 'img_in_txt_in_offloading', 'toggle'),
      ],
    },
    {
      key: 'sampling', eyebrow: 'SAMPLING', title: '训练中采样', desc: '按 SamplePrompt[] 维护,导出时再序列化成 prompt 文件。',
      fields: [
        F('首次采样', 'sample_at_first', 'toggle'),
        F('每 N epoch', 'sample_every_n_epochs', 'num'),
        F('每 N step', 'sample_every_n_steps', 'num', { hint: '0 表示不按 step 触发' }),
        F('提示词', 'sample_prompt', 'area'),
        F('负面提示词', 'sample_negative_prompt', 'area'),
        F('宽', 'sample_w', 'num'),
        F('高', 'sample_h', 'num'),
      ],
      adv: [
        F('采样步数', 'sample_steps', 'num'),
        F('采样种子', 'sample_seed', 'num'),
      ],
    },
    {
      key: 'save', eyebrow: 'SAVE', title: '保存与恢复', desc: '保留策略会删除旧检查点,提交前给出最终解释。',
      fields: [
        F('每 N epoch 保存', 'save_every_n_epochs', 'num'),
        F('每 N step 保存', 'save_every_n_steps', 'num'),
        F('保留最近 N epoch', 'save_last_n_epochs', 'num'),
        F('保存优化器状态', 'save_state', 'toggle'),
        F('结束时保存状态', 'save_state_on_train_end', 'toggle'),
      ],
      adv: [F('从状态恢复', 'resume', 'path', { ph: 'output/state 目录' })],
    },
    {
      key: 'logging', eyebrow: 'LOGGING', title: '日志与发布', desc: '秘密只提交 secret_ref,命令预览与日志一律脱敏。',
      fields: [
        F('追踪器', 'log_with', 'select', { options: ['tensorboard', 'wandb', 'all', 'none'] }),
        F('日志目录', 'logging_dir', 'path'),
        F('W&B API Key', 'wandb_api_key', 'secret'),
        F('HF 仓库', 'huggingface_repo_id', 'text', { ph: 'user/repo' }),
        F('HF Token', 'huggingface_token', 'secret'),
      ],
      adv: [F('异步上传', 'async_upload', 'toggle', { hint: '异步上传注册为独立子任务' })],
    },
  ]
  const showAll = demo.showAdvanced
  return defs.map(d => {
    const open = showAll || !!store.adv[d.key]
    const col = !!store.collapsed[d.key]
    return {
      key: d.key,
      toggleCollapse: () => { store.collapsed[d.key] = !store.collapsed[d.key] },
      caretStyle: { flexShrink: 0, marginTop: '4px', fontSize: '12px', lineHeight: '16px', color: 'var(--mute)', display: 'inline-block', transform: col ? 'rotate(-90deg)' : 'none', transition: 'transform .26s cubic-bezier(.2,.8,.2,1)' },
      bodyWrapStyle: { display: 'grid', gridTemplateRows: col ? '0fr' : '1fr', margin: '0 -24px', transition: 'grid-template-rows .3s cubic-bezier(.2,.8,.2,1)' },
      eyebrow: d.eyebrow, title: d.title, desc: d.desc,
      fields: d.fields, advFields: d.adv,
      hasAdv: d.adv.length > 0, advOpen: open && d.adv.length > 0,
      advCaret: open ? '▾' : '▸',
      advLabel: (open ? '收起高级参数' : '高级参数') + ' (' + d.adv.length + ')',
      toggleAdv: () => { store.adv[d.key] = !store.adv[d.key] },
      hasCache: !!d.cache,
    }
  })
}

// ---- 队列行(live + 排队 + 已完成;种子历史仅演示模式) ----

const DEMO_SEED_JOBS = [
  { id: 'job_5b12c4', workflow: 'cache_latents · qwen-image', note: '184 items · keep_cache=False', status: 'succeeded', progress: '184/184', started: '13:41', duration: '02:18' },
  { id: 'job_4a09e1', workflow: 'train_network · wan2.2', note: 'wan-i2v-a14b · dim 32', status: 'failed', progress: '620/3000', started: '11:02', duration: '18:44' },
  { id: 'job_38f7b0', workflow: 'train_network · z-image', note: 'style-anime · dim 8', status: 'cancelled', progress: '1240/2000', started: '09:27', duration: '11:03' },
  { id: 'job_2c55da', workflow: 'convert · lora→comfy', note: 'character-v0.safetensors', status: 'succeeded', progress: '1/1', started: '08:58', duration: '00:04' },
]

function buildJobRows() {
  const s = store, v = s.values, st = s.status
  const active = st === 'queued' || st === 'validating' || st === 'running' || st === 'cancelling'
  const live = !active ? [] : [{
    id: s.jobId, workflow: 'train_network · qwen-image', note: v.output_name + ' · dim ' + v.network_dim,
    status: st, progress: s.step + '/' + s.totalSteps, started: s.startedAt || '—', duration: clock(s.simTime),
  }]
  const waiting = s.pending.map(p => ({
    id: p.id, workflow: (p.workflow === 'full_finetune' ? 'full_finetune · ' : 'train_network · ') + p.arch,
    note: p.name + ' · waiting_for_gpu:0' + (s.editingId === p.id ? ' · 编辑中' : ''), status: 'queued',
    progress: '0/' + s.totalSteps, started: '—', duration: '—', pjob: p,
  }))
  const seed = demo.demoMode ? DEMO_SEED_JOBS : []
  return live.concat(waiting, s.doneJobs, seed).slice(0, 10).map(j => ({
    id: j.id, workflow: j.workflow, note: j.note, status: j.status,
    progress: j.progress, started: j.started, duration: j.duration,
    actLabel: j.pjob ? '编辑' : ((j.status === 'running' || j.status === 'queued' || j.status === 'validating') ? '停止' : '详情'),
    act: j.pjob
      ? (() => editPending(j.pjob))
      : (j.status === 'running' ? askCancel : () => toast('info', j.id + ' · 请求快照与退出信息已打开')),
  }))
}

// ---- TOML 与 argv 预览(秘密脱敏) ----

function buildToml() {
  const v = store.values
  const variantLines = (ARCH_VARIANTS[v.model_arch] || []).map(d => d.flag + ' = "' + v[d.flag] + '"')
  return [
    '# exported by musubi tuner ui',
    '[general]',
    'dataset_config = "' + v.dataset_config + '"',
    'output_dir = "' + v.output_dir + '"',
    'output_name = "' + v.output_name + '"',
    '',
    '[model]',
    'dit = "' + v.dit + '"',
    'vae = "' + v.vae + '"',
    'text_encoder = "' + v.text_encoder + '"',
    ...variantLines,
    '',
    '[network]',
    'network_module = "' + (LORA_MODULE[v.model_arch] || 'networks.lora') + '"',
    'network_dim = ' + v.network_dim,
    'network_alpha = ' + v.network_alpha,
    'network_args = ["' + v.network_args + '"]',
    '',
    '[optimizer]',
    'optimizer_type = "' + v.optimizer_type + '"',
    'learning_rate = ' + v.learning_rate,
    'lr_scheduler = "' + v.lr_scheduler + '"',
    'lr_warmup_steps = ' + v.lr_warmup_steps,
    '',
    '[training]',
    'max_train_epochs = ' + v.max_train_epochs,
    'mixed_precision = "' + v.mixed_precision + '"',
    'timestep_sampling = "' + v.timestep_sampling + '"',
    'discrete_flow_shift = ' + v.discrete_flow_shift,
    'gradient_checkpointing = ' + (v.gradient_checkpointing ? 'true' : 'false'),
    'fp8_base = ' + (v.fp8_base ? 'true' : 'false'),
    'fp8_scaled = ' + (v.fp8_scaled ? 'true' : 'false'),
    'blocks_to_swap = ' + v.blocks_to_swap,
    '',
    '[sampling]',
    'sample_every_n_epochs = ' + v.sample_every_n_epochs,
    'sample_prompts = "prompts.toml"',
  ].join('\n')
}

function buildArgv() {
  const v = store.values
  const isFT = v.workflow === 'full_finetune'
  const entry = (isFT ? FT_ENTRY[v.model_arch] : TRAIN_ENTRY[v.model_arch]) || TRAIN_ENTRY['qwen-image']
  const variantArgs = (ARCH_VARIANTS[v.model_arch] || []).map(d => '--' + d.flag + ' ' + v[d.flag]).join(' ')
  return [
    'accelerate launch --num_processes 1 --mixed_precision ' + v.mixed_precision + ' \\',
    '  src/musubi_tuner/' + entry + '.py \\',
    ...(variantArgs ? ['  ' + variantArgs + ' \\'] : []),
    '  --dataset_config ' + v.dataset_config + ' \\',
    '  --dit ' + v.dit + ' \\',
    '  --vae ' + v.vae + ' \\',
    '  --text_encoder ' + v.text_encoder + ' \\',
    // 全量微调没有 network_* 字段(独立 capability)
    ...(isFT ? [] : [
      '  --network_module ' + (LORA_MODULE[v.model_arch] || 'networks.lora') + ' \\',
      '  --network_dim ' + v.network_dim + ' --network_alpha ' + v.network_alpha + ' \\',
    ]),
    '  --optimizer_type ' + v.optimizer_type + ' --learning_rate ' + v.learning_rate + ' \\',
    '  --lr_scheduler ' + v.lr_scheduler + ' --lr_warmup_steps ' + v.lr_warmup_steps + ' \\',
    '  --max_train_epochs ' + v.max_train_epochs + ' --mixed_precision ' + v.mixed_precision + ' \\',
    '  --timestep_sampling ' + v.timestep_sampling + ' --discrete_flow_shift ' + v.discrete_flow_shift + ' \\',
    '  --blocks_to_swap ' + v.blocks_to_swap + (v.fp8_base ? ' --fp8_base' : '') + (v.fp8_scaled ? ' --fp8_scaled' : '') + ' \\',
    '  --output_dir ' + v.output_dir + ' --output_name ' + v.output_name + ' \\',
    '  --huggingface_token <redacted> --wandb_api_key <redacted>',
  ].map(t => ({ text: t }))
}

export function copyToml() {
  navigator.clipboard?.writeText(buildToml())
  toast('info', 'TOML 已复制')
}

export function copyArgv() {
  navigator.clipboard?.writeText(buildArgv().map(l => l.text).join('\n'))
  store.modal = null
  toast('info', 'argv 已复制 · 秘密已脱敏')
}

// reactive 容器内的 computed 会自动解包,模板里直接用 ui.groups / ui.jobRows / …
export const ui = reactive({
  groups: computed(buildGroups),
  jobRows: computed(buildJobRows),
  tomlText: computed(buildToml),
  argvLines: computed(buildArgv),
})
