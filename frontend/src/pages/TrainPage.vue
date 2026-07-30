<script setup>
// 训练页:左侧 10 张分组参数卡,右侧 sticky 监控栏(进度/显存、loss 曲线、样图、终端)。
// <1200px 时监控栏折叠为 PROGRESS / LOSS / SAMPLES / TERMINAL 标签页。
import { computed } from 'vue'
import { store, demo, clock, autoFix, showCommand, savePreset, togglePin } from '../store.js'
import { ui } from '../derived.js'
import ParamCard from '../components/ParamCard.vue'
import StatusBadge from '../components/StatusBadge.vue'
import LossChart from '../components/LossChart.vue'
import TerminalPanel from '../components/TerminalPanel.vue'

const running = computed(() => store.status === 'running')
const pct = computed(() => store.totalSteps ? store.step / store.totalSteps * 100 : 0)
const eta = computed(() => (running.value && store.totalSteps && store.itps)
  ? clock((store.totalSteps - store.step) / store.itps) : '--:--')
// 总量:演示模式用模拟配置;真实模式运行中用后端事件里的真实总量,空闲时显示表单计划值
const shownTotals = computed(() => {
  if (demo.demoMode) return { epochs: store.totalEpochs, steps: store.totalSteps }
  const active = store.status === 'running' || store.status === 'cancelling'
  return {
    epochs: (active && store.totalEpochs) || parseInt(store.values.max_train_epochs, 10) || 0,
    steps: (active && store.totalSteps) || parseInt(store.values.max_train_steps, 10) || 0,
  }
})
const progressLine = computed(() =>
  'Epoch ' + Math.max(0, store.epoch) + '/' + shownTotals.value.epochs +
  ' · Step ' + store.step + '/' + shownTotals.value.steps + ' · ETA ' + eta.value)

const barStyle = computed(() => ({ width: pct.value + '%', height: '6px', background: 'var(--ink)', borderRadius: '6px', transition: 'width .22s linear' }))
const tailStyle = computed(() => ({ position: 'absolute', top: '-2px', left: 'calc(' + pct.value + '% - 5px)', width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent)', transition: 'left .22s linear', animation: 'tailPulse 1.6s ease-out infinite' }))
// VRAM:演示模式是自洽沙盘(24GB 模拟曲线);真实模式只用当前机器数据,读不到就如实标未知
const vramInfo = computed(() => {
  if (demo.demoMode) {
    const p = store.vram / 24 * 100
    return { pct: p, warn: p > 90, label: store.vram.toFixed(1) + ' / 24.0 GB · ' + Math.round(p) + '% (demo)' }
  }
  const e = store.env
  if (e.source === 'nvidia' && e.vramTotalGb > 0) {
    const p = e.vramUsedGb / e.vramTotalGb * 100
    return { pct: p, warn: p > 90, label: e.vramUsedGb.toFixed(1) + ' / ' + e.vramTotalGb.toFixed(1) + ' GB · ' + Math.round(p) + '%' }
  }
  return { pct: 0, warn: false, label: '未知 · 需本地环境 API' }
})
const vramBarStyle = computed(() => ({ width: Math.min(100, vramInfo.value.pct) + '%', height: '6px', background: vramInfo.value.warn ? 'var(--warning)' : 'var(--ink)', borderRadius: '6px', transition: 'width .3s linear,background .2s ease' }))

const lossBig = computed(() => store.avg ? store.avg.toFixed(4) : '—')
const itpsLabel = computed(() => running.value ? store.itps.toFixed(2) : '—')
const elapsedLabel = computed(() => store.simTime ? clock(store.simTime) : '00:00')

const railTabs = computed(() => [['progress', 'PROGRESS'], ['chart', 'LOSS'], ['samples', 'SAMPLES'], ['logs', 'TERMINAL']].map(t => ({
  key: t[0], label: t[1], active: store.railTab === t[0],
})))
const showProgress = computed(() => !store.narrow || store.railTab === 'progress')
const showChart = computed(() => !store.narrow || store.railTab === 'chart')
const showSamples = computed(() => !store.narrow || store.railTab === 'samples')
const showLogs = computed(() => !store.narrow || store.railTab === 'logs' || store.termPinned || store.termFull)
const termAway = computed(() => store.termPinned || store.termFull)
</script>

<template>
  <div data-screen-label="训练配置与监控" style="animation:pageFade .24s ease none;max-width:1280px;margin:0 auto">
    <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:24px;margin-bottom:24px">
      <div>
        <h1 style="margin:0;font-size:20px;line-height:28px;font-weight:600;color:var(--ink)">训练配置</h1>
        <p style="margin:4px 0 0;font-size:14px;line-height:20px;color:var(--body)">配置提交后由后端渲染 argv 执行,表单分组只是显示层,最终字段仍是扁平 CLI 名称。</p>
      </div>
      <div style="display:flex;gap:8px;flex-shrink:0">
        <button @click="showCommand" class="hv-border"
          style="height:36px;padding:0 14px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;color:var(--ink);font-size:14px;font-weight:500;white-space:nowrap;cursor:pointer;transition:border-color .14s ease">查看命令</button>
        <button @click="savePreset" class="hv-border"
          style="height:36px;padding:0 14px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;color:var(--ink);font-size:14px;font-weight:500;white-space:nowrap;cursor:pointer;transition:border-color .14s ease">保存预设</button>
      </div>
    </div>

    <div v-if="store.banner"
      style="display:flex;align-items:flex-start;gap:12px;background:var(--error-soft);border:1px solid var(--error);border-radius:8px;padding:12px 16px;margin-bottom:24px;animation:cardIn .2s ease both">
      <span style="width:6px;height:6px;border-radius:50%;background:var(--error);margin-top:7px;flex-shrink:0"></span>
      <div style="flex:1;min-width:0">
        <div style="font-size:14px;font-weight:500;color:var(--ink)">校验未通过 · {{ store.banner.count }} 个字段需要修正</div>
        <div style="font-family:var(--font-mono);font-size:12px;line-height:18px;color:var(--body);margin-top:4px">{{ store.banner.detail }}</div>
      </div>
      <button @click="autoFix"
        style="height:28px;padding:0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:12px;font-weight:500;color:var(--ink);white-space:nowrap;cursor:pointer;flex-shrink:0">自动修正</button>
    </div>

    <div v-if="store.exit" style="border:1px solid var(--error);border-radius:8px;overflow:hidden;margin-bottom:24px;animation:cardIn .2s ease both">
      <div style="display:flex;align-items:center;gap:8px;background:var(--error-soft);padding:10px 16px">
        <span style="width:6px;height:6px;border-radius:50%;background:var(--error)"></span>
        <span style="font-size:14px;font-weight:500;color:var(--ink)">作业失败</span>
        <span style="font-family:var(--font-mono);font-size:12px;color:var(--body)">{{ store.exit.line }}</span>
      </div>
      <div style="background:var(--terminal-bg);padding:12px 16px">
        <div v-for="(l, i) in store.exit.tail" :key="i"
          style="font-family:var(--font-mono);font-size:13px;line-height:20px;color:#ff6166;white-space:pre-wrap;word-break:break-all">{{ l.text }}</div>
      </div>
    </div>

    <div style="display:flex;flex-wrap:wrap;align-items:flex-start;gap:32px">
      <div style="flex:1 1 620px;min-width:0;max-width:760px;display:flex;flex-direction:column;gap:32px">
        <ParamCard v-for="g in ui.groups" :key="g.key" :g="g" />
      </div>

      <div style="flex:1 1 340px;min-width:320px;max-width:480px;position:sticky;top:88px;display:flex;flex-direction:column;gap:16px">
        <div v-if="store.narrow" style="display:flex;gap:4px;padding:4px;background:var(--surface-2);border-radius:6px">
          <button v-for="t in railTabs" :key="t.key" @click="store.railTab = t.key"
            :style="t.active
              ? 'flex:1;height:28px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:12px;color:var(--ink);cursor:pointer'
              : 'flex:1;height:28px;background:transparent;border:1px solid transparent;border-radius:6px;font-family:var(--font-mono);font-size:12px;color:var(--body);cursor:pointer'">{{ t.label }}</button>
        </div>

        <section v-if="showProgress" style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);padding:16px">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
            <div style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">PROGRESS</div>
            <StatusBadge :status="store.status" />
          </div>
          <div style="font-family:var(--font-mono);font-size:12px;line-height:16px;color:var(--body);font-variant-numeric:tabular-nums;margin-top:12px">{{ progressLine }}</div>
          <div style="position:relative;height:6px;background:var(--hairline);border-radius:6px;margin-top:10px;overflow:visible">
            <div :style="barStyle"></div>
            <div v-if="running" :style="tailStyle"></div>
          </div>
          <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin-top:16px">
            <div>
              <div style="font-family:var(--font-mono);font-size:28px;line-height:32px;font-weight:600;color:var(--ink);font-variant-numeric:tabular-nums">{{ lossBig }}</div>
              <div style="font-family:var(--font-mono);font-size:12px;color:var(--mute);margin-top:2px">avr_loss</div>
            </div>
            <div style="display:grid;grid-template-columns:auto auto;gap:2px 16px;text-align:right">
              <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute)">lr</span>
              <span style="font-family:var(--font-mono);font-size:12px;color:var(--ink);font-variant-numeric:tabular-nums">{{ store.values.learning_rate }}</span>
              <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute)">it/s</span>
              <span style="font-family:var(--font-mono);font-size:12px;color:var(--ink);font-variant-numeric:tabular-nums">{{ itpsLabel }}</span>
              <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute)">elapsed</span>
              <span style="font-family:var(--font-mono);font-size:12px;color:var(--ink);font-variant-numeric:tabular-nums">{{ elapsedLabel }}</span>
            </div>
          </div>
          <div style="height:1px;background:var(--hairline);margin:16px -16px"></div>
          <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
            <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute)">VRAM</span>
            <span style="font-family:var(--font-mono);font-size:12px;color:var(--ink);font-variant-numeric:tabular-nums">{{ vramInfo.label }}</span>
          </div>
          <div style="height:6px;background:var(--hairline);border-radius:6px;margin-top:8px">
            <div :style="vramBarStyle"></div>
          </div>
          <div v-if="vramInfo.warn"
            style="display:flex;align-items:flex-start;gap:6px;margin-top:10px;background:var(--warning-soft);border-radius:6px;padding:6px 8px;animation:rowIn .2s ease both">
            <span style="color:var(--warning);font-size:11px;line-height:16px">▲</span>
            <span style="font-size:12px;line-height:16px;color:var(--body)">显存吃紧,建议提高 <span style="font-family:var(--font-mono)">--blocks_to_swap</span> 或启用 fp8。</span>
          </div>
        </section>

        <section v-if="showChart" style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);padding:16px">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
            <div style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">LOSS</div>
            <div style="display:flex;gap:6px">
              <span style="display:inline-flex;align-items:center;gap:5px;border:1px solid var(--hairline);border-radius:6px;padding:2px 8px;font-family:var(--font-mono);font-size:11px;color:var(--body)">
                <span style="width:6px;height:6px;border-radius:50%;background:var(--accent)"></span>smooth
              </span>
              <span style="display:inline-flex;align-items:center;gap:5px;border:1px solid var(--hairline);border-radius:6px;padding:2px 8px;font-family:var(--font-mono);font-size:11px;color:var(--body)">
                <span style="width:6px;height:6px;border-radius:50%;background:var(--chart-raw)"></span>raw
              </span>
            </div>
          </div>
          <div style="margin-top:12px"><LossChart /></div>
        </section>

        <section v-if="showSamples" style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);padding:16px">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
            <div style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">SAMPLES</div>
            <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute);font-variant-numeric:tabular-nums">{{ store.samples.length }} 张</span>
          </div>
          <div v-if="!store.samples.length"
            style="height:96px;display:flex;align-items:center;justify-content:center;font-family:var(--font-mono);font-size:12px;color:var(--mute);margin-top:12px;border:1px dashed var(--hairline);border-radius:8px">等待第一次采样…</div>
          <div v-else style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px">
            <div v-for="s in store.samples" :key="s.id"
              style="position:relative;aspect-ratio:1/1;border:1px solid var(--hairline);border-radius:8px;background:var(--surface-2);overflow:hidden;animation:tileIn .32s cubic-bezier(.2,.8,.2,1) both;cursor:pointer">
              <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-family:var(--font-mono);font-size:11px;color:var(--mute)">{{ s.reso }}</div>
              <div style="position:absolute;top:6px;left:6px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;padding:1px 6px;font-family:var(--font-mono);font-size:11px;color:var(--body);white-space:nowrap">{{ s.label }}</div>
            </div>
          </div>
        </section>

        <template v-if="showLogs">
          <section v-if="termAway"
            style="border:1px dashed var(--hairline);border-radius:8px;padding:12px 16px;display:flex;align-items:center;justify-content:space-between;gap:8px;animation:rowIn .2s ease both">
            <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">TERMINAL 已置顶 · 双击日志区全屏</span>
            <button @click="togglePin" class="hv-line"
              style="height:28px;padding:0 8px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:11px;color:var(--body);white-space:nowrap;cursor:pointer">收回</button>
          </section>
          <TerminalPanel v-else />
        </template>
      </div>
    </div>
  </div>
</template>
