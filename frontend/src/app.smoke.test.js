// 冒烟测试:应用能完整挂载、五页可切换、训练状态机能从提交走到 running 并产生日志/曲线。
// 运行:npx vitest run
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import App from './App.vue'
import { store, start, setV, mkDataset, ARCH_VARIANTS, demo } from './store.js'

function resetStore() {
  demo.demoMode = false
  Object.assign(store, {
    page: 'train', status: 'idle', step: 0, epoch: 0, loss: 0, avg: 0,
    series: [], simTime: 0, vram: 8.2, logs: [], samples: [], extraArtifacts: [],
    doneJobs: [], toasts: [], modal: null, exit: null, errors: {}, banner: null,
    pending: [], editingId: null, jobId: '',
  })
  Object.assign(store.values, {
    model_arch: 'qwen-image', model_version: 'edit-2511', task: '', model_type: '',
    workflow: 'train_network',
    dataset_config: '', logging_dir: '', vae: '', attn_mode: 'sdpa', learning_rate: '1e-4',
  })
  store.datasets = [mkDataset()]
}

describe('musubi tuner frontend', () => {
  beforeEach(resetStore)

  it('挂载后渲染顶栏、侧栏与训练页参数卡,真实模式不出现模拟硬件数据', () => {
    const w = mount(App, { attachTo: document.body })
    const text = w.text()
    expect(text).toContain('musubi')
    expect(text).toContain('开始训练')
    for (const nav of ['训练', '队列', '产物', '环境', '预设']) expect(text).toContain(nav)
    for (const eyebrow of ['BASIC', 'MODEL', 'DATASET', 'NETWORK', 'OPTIMIZER', 'TRAINING', 'MEMORY', 'SAMPLING', 'SAVE', 'LOGGING']) {
      expect(text).toContain(eyebrow)
    }
    // 真实模式:不显示演示用的假 GPU/显存,也没有演示路径值
    expect(text).not.toContain('RTX 4090')
    expect(text).not.toContain('24.0 GB')
    expect(text).not.toContain('character-v1')
    w.unmount()
  })

  it('五个页面都能切换渲染', async () => {
    const w = mount(App, { attachTo: document.body })
    const cases = [
      ['models', '模型库'], ['queue', '作业队列'], ['artifacts', '产物库'],
      ['env', '环境与设备'], ['presets', '预设与 TOML'], ['settings', 'Token 明文只保存在训练机本地'],
      ['train', '训练配置'],
    ]
    for (const [page, title] of cases) {
      store.page = page
      await w.vm.$nextTick()
      expect(w.text()).toContain(title)
    }
    w.unmount()
  })

  it('校验拦截无效表单;真实模式提交失败如实报错;演示模式完整状态机到 running', async () => {
    const w = mount(App, { attachTo: document.body })

    // 空表单提交 → dataset_config 必填、tensorboard 需 logging_dir → 同步拦下,停在 idle
    start()
    expect(store.status).toBe('idle')
    expect(store.banner).toBeTruthy()
    expect(Object.keys(store.errors).length).toBeGreaterThan(0)

    // 补齐必填后提交:进入 queued 并真实 POST 后端;测试环境无后端 → 如实回落 idle 并报错
    store.values.dataset_config = 'D:/data/dataset_config.toml'
    store.values.logging_dir = 'D:/data/logs'
    store.errors = {}
    store.banner = null
    start()
    expect(store.status).toBe('queued')
    await vi.waitUntil(() => store.status === 'idle', { timeout: 5000 })
    expect(store.logs.some(l => l.text.includes('backend not connected'))).toBe(true)

    // 演示模式(?demo=1):同一表单 → queued → validating → running,模拟引擎推进
    demo.demoMode = true
    vi.useFakeTimers()
    start()
    await vi.advanceTimersByTimeAsync(700 + 850 + 50)
    expect(store.status).toBe('running')
    await vi.advanceTimersByTimeAsync(3000)
    expect(store.step).toBeGreaterThan(0)
    expect(store.series.length).toBeGreaterThan(0)
    expect(store.logs.some(l => l.text.includes('running training'))).toBe(true)
    vi.useRealTimers()

    w.unmount()
  })

  it('变体/任务字段与全量微调选项按架构条件显示(capability 语义)', async () => {
    const w = mount(App, { attachTo: document.body })
    const hasFtButton = () => w.findAll('button').some(b => b.text().trim() === '全量微调')

    // qwen-image:有「训练类型」且支持全量微调
    expect(w.text()).toContain('训练类型')
    expect(hasFtButton()).toBe(true)

    // krea2:没有任何变体枚举,也没有全量微调入口 → 都不该出现
    setV('model_arch', 'krea2')
    await w.vm.$nextTick()
    expect(w.text()).not.toContain('训练类型')
    expect(w.text()).not.toContain('任务 task')
    expect(hasFtButton()).toBe(false)
    expect(store.values.model_version).toBe('')

    // wan:显示「任务」,并重置为首个真实 task;全量微调不可用
    setV('model_arch', 'wan2.1/2.2')
    await w.vm.$nextTick()
    expect(w.text()).toContain('任务')
    expect(store.values.task).toBe('t2v-14B')
    expect(hasFtButton()).toBe(false)

    // 在不支持的架构上选中全量微调是不可能的;若切换前处于全量微调,须被强制回 LoRA 训练
    setV('model_arch', 'hidream-o1')
    setV('workflow', 'full_finetune')
    setV('model_arch', 'framepack')
    expect(store.values.workflow).toBe('train_network')

    // hidream-o1:模型类型 + 任务 两个字段都要出现
    setV('model_arch', 'hidream-o1')
    await w.vm.$nextTick()
    expect(w.text()).toContain('模型类型')
    expect(store.values.model_type).toBe('full')
    expect(store.values.task).toBe('t2i')

    // 每个架构的枚举表自检:有表的架构 options 非空且无重复
    for (const [arch, defs] of Object.entries(ARCH_VARIANTS)) {
      for (const d of defs) {
        expect(d.options.length, arch + '.' + d.flag).toBeGreaterThan(0)
        expect(new Set(d.options).size, arch + '.' + d.flag).toBe(d.options.length)
      }
    }
    w.unmount()
  })
})
