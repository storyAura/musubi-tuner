<script setup>
// 应用壳:顶栏(项目/GPU/主题/训练控制)、侧栏导航、页面切换、Toast 栈、
// 置顶悬浮终端(跨页面常驻)、确认弹窗宿主。
import { computed, onMounted, onUnmounted } from 'vue'
import {
  store, init, destroy, toggleTheme, start, enqueue, askCancel, dismissToast, togglePin,
  ARCH_VARIANTS, demo, clock,
} from './store.js'
import StatusBadge from './components/StatusBadge.vue'
import TerminalPanel from './components/TerminalPanel.vue'
import ModalsHost from './components/ModalsHost.vue'
import TrainPage from './pages/TrainPage.vue'
import ModelsPage from './pages/ModelsPage.vue'
import QueuePage from './pages/QueuePage.vue'
import ArtifactsPage from './pages/ArtifactsPage.vue'
import EnvironmentPage from './pages/EnvironmentPage.vue'
import PresetsPage from './pages/PresetsPage.vue'
import SettingsPage from './pages/SettingsPage.vue'

onMounted(init)
onUnmounted(destroy)

const st = computed(() => store.status)
// 顶栏 GPU 徽章:演示模式是自洽沙盘(模拟 4090);真实模式只显示当前机器数据(nvidia-smi → WebGL 型号)
const vramWarn = computed(() => {
  if (demo.demoMode) return store.vram / 24 * 100 > 90
  const e = store.env
  return e.source === 'nvidia' && e.vramTotalGb > 0 && e.vramUsedGb / e.vramTotalGb > 0.9
})
const gpuLabel = computed(() => {
  if (demo.demoMode) return 'RTX 4090 · ' + store.vram.toFixed(1) + '/24 GB (demo)'
  const e = store.env
  if (e.source === 'nvidia') return e.gpuName + ' · ' + e.vramUsedGb.toFixed(1) + '/' + e.vramTotalGb.toFixed(1) + ' GB'
  if (e.backend) return 'GPU 未检测' // 训练机无 GPU / 无卡模式;不显示浏览器显卡
  if (e.source === 'webgl') return e.gpuName + '(浏览器)'
  return 'GPU —'
})

// 置顶悬浮终端占位:竖排让出右侧、横排让出底部,避免遮挡内容
const mainPad = computed(() => {
  if (!store.termPinned || store.termFull) return {}
  return store.termOrient === 'v' ? { paddingRight: '472px' } : { paddingBottom: '268px' }
})
const themeLabel = computed(() => store.theme === 'dark' ? '暗色' : '亮色')
const projectLabel = computed(() =>
  store.datasets[0]?.image_directory || store.values.output_dir || 'workspace')

const archLabel = computed(() => {
  const arch = store.values.model_arch
  const variants = (ARCH_VARIANTS[arch] || []).map(d => store.values[d.flag]).filter(Boolean)
  return [arch, ...variants].join(' · ')
})

const canStart = computed(() => ['idle', 'succeeded', 'failed', 'cancelled'].includes(st.value))
const canStop = computed(() => ['running', 'queued', 'validating'].includes(st.value))
// 排队接续目前是演示能力;真实模式的多任务队列由后端排程,待队列页接入 /api/v1/jobs
const canEnqueue = computed(() => demo.demoMode && ['running', 'queued', 'validating'].includes(st.value))
const isCancelling = computed(() => st.value === 'cancelling')
const pendingLabel = computed(() => store.pending.length ? '已排 ' + store.pending.length + ' 个' : '加入队列')

const jobIdLabel = computed(() => {
  if (!store.jobId) return '—'
  return st.value === 'idle' ? store.jobId + ' (未提交)' : store.jobId
})
const hasPending = computed(() => store.pending.length > 0 || !!store.editingId)
const pendingNote = computed(() =>
  store.editingId ? '队列已暂停 · 编辑中' : (store.pending.length ? '跑完自动接下一个' : ''))

// 侧栏下载进度(任何页面可见;点击跳转模型页)
const activeDownloads = computed(() => Object.entries(store.downloads)
  .filter(([, d]) => ['queued', 'running', 'cancelling'].includes(d.status))
  .map(([filename, d]) => {
    const pct = d.total_bytes ? Math.min(100, d.bytes / d.total_bytes * 100) : 0
    const spd = (d.speed_bps || 0) >= 1048576
      ? (d.speed_bps / 1048576).toFixed(1) + ' MB/s'
      : Math.round((d.speed_bps || 0) / 1024) + ' KB/s'
    const line = d.bytes
      ? Math.round(pct) + '% · ' + spd + (d.eta_s > 0 ? ' · 剩 ' + clock(d.eta_s) : '')
      : '排队中…'
    return { filename, pct, line }
  }))

const modelsCount = computed(() => {
  const c = store.modelLib.catalog
  return c.length ? c.filter(x => x.exists).length + '/' + c.length : ''
})

const nav = computed(() => [
  ['train', '训练', ''],
  ['models', '模型', modelsCount.value],
  ['queue', '队列', String(store.doneJobs.length + store.pending.length + (st.value !== 'idle' ? 1 : 0))],
  ['artifacts', '产物', String(store.extraArtifacts.length + (demo.demoMode ? 5 : 0))],
  ['env', '环境', ''],
  ['presets', '预设', demo.demoMode ? '4' : '0'],
  ['settings', '设置', ''],
].map(n => ({ key: n[0], label: n[1], count: n[2], active: store.page === n[0] })))

const PAGES = {
  train: TrainPage, models: ModelsPage, queue: QueuePage,
  artifacts: ArtifactsPage, env: EnvironmentPage, presets: PresetsPage, settings: SettingsPage,
}
const page = computed(() => PAGES[store.page] || TrainPage)
</script>

<template>
  <div style="min-height:100vh;background:var(--canvas);color:var(--ink);font-family:var(--font-sans)">

    <header style="position:sticky;top:0;z-index:40;height:56px;display:flex;align-items:center;gap:16px;padding:0 24px;background:var(--surface);border-bottom:1px solid var(--hairline)">
      <div style="display:flex;align-items:baseline;gap:6px">
        <span style="font-size:15px;font-weight:600;letter-spacing:-0.2px;color:var(--ink)">musubi</span>
        <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute)">tuner</span>
      </div>
      <div style="width:1px;height:20px;background:var(--hairline)"></div>
      <div style="display:flex;align-items:center;gap:8px;min-width:0">
        <span style="font-family:var(--font-mono);font-size:12px;color:var(--body);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ projectLabel }}</span>
        <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute);border:1px solid var(--hairline);border-radius:6px;padding:1px 6px;white-space:nowrap">{{ archLabel }}</span>
      </div>
      <div style="flex:1"></div>
      <div style="display:flex;align-items:center;gap:12px">
        <div v-if="vramWarn"
          style="display:flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:12px;color:var(--warning);background:var(--warning-soft);border-radius:6px;padding:3px 8px">
          <span>▲</span><span style="font-variant-numeric:tabular-nums;white-space:nowrap">{{ gpuLabel }}</span>
        </div>
        <div v-else
          style="display:flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:12px;color:var(--body);border:1px solid var(--hairline);border-radius:6px;padding:3px 8px">
          <span style="font-variant-numeric:tabular-nums;white-space:nowrap">{{ gpuLabel }}</span>
        </div>
        <button @click="toggleTheme" class="hv-line"
          style="height:32px;padding:0 10px;display:flex;align-items:center;gap:6px;background:transparent;border:1px solid var(--hairline);border-radius:6px;cursor:pointer;font-family:var(--font-mono);font-size:12px;color:var(--body)">{{ themeLabel }}</button>
        <button v-if="canStart" @click="start" class="hv-fade"
          style="height:36px;padding:0 16px;background:var(--primary);color:var(--on-primary);border:none;border-radius:6px;font-size:14px;font-weight:500;white-space:nowrap;cursor:pointer;transition:opacity .14s ease,transform .14s ease">开始训练</button>
        <button v-if="canEnqueue" @click="enqueue" class="hv-border"
          style="height:36px;padding:0 14px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:14px;font-weight:500;color:var(--ink);white-space:nowrap;cursor:pointer;transition:border-color .14s ease">{{ pendingLabel }}</button>
        <button v-if="canStop" @click="askCancel" class="hv-danger"
          style="height:36px;padding:0 16px;background:var(--surface);color:var(--error);border:1px solid var(--error);border-radius:6px;font-size:14px;font-weight:500;white-space:nowrap;cursor:pointer;transition:background .14s ease,color .14s ease">停止训练</button>
        <button v-if="isCancelling" disabled
          style="height:36px;padding:0 16px;background:var(--surface);color:var(--body);border:1px solid var(--hairline);border-radius:6px;font-size:14px;font-weight:500;opacity:.4;cursor:not-allowed;display:flex;align-items:center;gap:8px">
          <span style="width:12px;height:12px;border:1.5px solid var(--body);border-top-color:transparent;border-radius:50%;animation:spin .7s linear infinite;display:inline-block"></span>正在停止
        </button>
      </div>
    </header>

    <div style="display:flex;align-items:stretch;min-height:calc(100vh - 56px)">
      <aside style="flex:0 0 224px;border-right:1px solid var(--hairline);background:var(--canvas);padding:24px 0;position:sticky;top:56px;align-self:flex-start;height:calc(100vh - 56px)">
        <div style="font-family:var(--font-mono);font-size:12px;line-height:16px;letter-spacing:.5px;color:var(--mute);padding:0 24px 12px">WORKSPACE</div>
        <nav style="display:flex;flex-direction:column">
          <template v-for="n in nav" :key="n.key">
            <button v-if="n.active" @click="store.page = n.key"
              style="display:flex;align-items:center;justify-content:space-between;gap:8px;height:36px;padding:0 24px;background:var(--surface-2);border:none;border-left:2px solid var(--ink);cursor:pointer;text-align:left;color:var(--ink);font-size:14px;font-weight:500;transition:background .14s ease">
              <span>{{ n.label }}</span>
              <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute);font-variant-numeric:tabular-nums">{{ n.count }}</span>
            </button>
            <button v-else @click="store.page = n.key" class="hv-nav"
              style="display:flex;align-items:center;justify-content:space-between;gap:8px;height:36px;padding:0 24px;background:transparent;border:none;border-left:2px solid transparent;cursor:pointer;text-align:left;color:var(--body);font-size:14px;font-weight:400;transition:background .14s ease,color .14s ease">
              <span>{{ n.label }}</span>
              <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute);font-variant-numeric:tabular-nums">{{ n.count }}</span>
            </button>
          </template>
        </nav>
        <div style="margin-top:32px;padding:0 24px">
          <div style="font-family:var(--font-mono);font-size:12px;line-height:16px;letter-spacing:.5px;color:var(--mute);padding-bottom:12px">CURRENT JOB</div>
          <div style="display:flex;flex-direction:column;gap:8px">
            <span style="font-family:var(--font-mono);font-size:12px;color:var(--body)">{{ jobIdLabel }}</span>
            <div><StatusBadge :status="store.status" /></div>
            <div v-if="hasPending"
              style="display:flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:11px;line-height:16px;color:var(--mute);animation:rowIn .2s ease both">
              <span>↳</span><span>{{ pendingNote }}</span>
            </div>
          </div>
        </div>

        <div v-if="activeDownloads.length" style="margin-top:32px;padding:0 24px">
          <div style="font-family:var(--font-mono);font-size:12px;line-height:16px;letter-spacing:.5px;color:var(--mute);padding-bottom:12px">DOWNLOADS</div>
          <div v-for="d in activeDownloads" :key="d.filename" @click="store.page = 'models'" title="点击查看模型页"
            style="margin-bottom:12px;cursor:pointer;animation:rowIn .2s ease both">
            <div style="font-family:var(--font-mono);font-size:11px;line-height:16px;color:var(--body);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ d.filename }}</div>
            <div style="position:relative;height:4px;background:var(--hairline);border-radius:6px;margin-top:5px;overflow:visible">
              <div :style="{ width: d.pct + '%', height: '4px', background: 'var(--ink)', borderRadius: '6px', transition: 'width .5s linear' }"></div>
              <div :style="{ position: 'absolute', top: '-2px', left: 'calc(' + d.pct + '% - 4px)', width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent)', transition: 'left .5s linear', animation: 'tailPulse 1.6s ease-out infinite' }"></div>
            </div>
            <div style="font-family:var(--font-mono);font-size:10px;line-height:14px;color:var(--mute);font-variant-numeric:tabular-nums;margin-top:4px">{{ d.line }}</div>
          </div>
        </div>
      </aside>

      <main style="flex:1;min-width:0;padding:32px 32px 64px;transition:padding .2s ease" :style="mainPad">
        <component :is="page" />
      </main>
    </div>

    <div v-if="store.toasts.length"
      style="position:fixed;right:24px;bottom:24px;z-index:95;display:flex;flex-direction:column;gap:8px;align-items:flex-end">
      <div v-for="t in store.toasts" :key="t.id"
        style="min-width:280px;max-width:400px;display:flex;align-items:flex-start;gap:10px;background:var(--surface);border-radius:8px;box-shadow:var(--shadow-float);padding:12px 14px;animation:toastIn .22s cubic-bezier(.2,.8,.2,1) both">
        <span v-if="t.kind === 'error'" style="width:6px;height:6px;border-radius:50%;background:var(--error);margin-top:7px;flex-shrink:0"></span>
        <span v-else-if="t.kind === 'warn'" style="width:6px;height:6px;border-radius:50%;background:var(--warning);margin-top:7px;flex-shrink:0"></span>
        <span v-else style="width:6px;height:6px;border-radius:50%;background:var(--accent);margin-top:7px;flex-shrink:0"></span>
        <div style="flex:1;min-width:0;font-size:14px;line-height:20px;color:var(--ink)">{{ t.text }}</div>
        <button v-if="t.action" @click="t.action.fn(); dismissToast(t.id)" class="hv-border"
          style="height:28px;padding:0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:12px;font-weight:500;color:var(--ink);white-space:nowrap;cursor:pointer;flex-shrink:0">{{ t.action.label }}</button>
        <button @click="dismissToast(t.id)"
          style="width:20px;height:20px;padding:0;background:transparent;border:none;color:var(--mute);cursor:pointer;font-size:14px;line-height:20px;flex-shrink:0">×</button>
      </div>
    </div>

    <TerminalPanel v-if="store.termPinned || store.termFull" />
    <ModalsHost />
  </div>
</template>
