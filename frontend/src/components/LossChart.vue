<script setup>
// loss 双线图:平滑线(accent 蓝)+ 原始线(浅灰退后),单 y 轴,悬浮 crosshair tooltip。
import { computed, ref } from 'vue'
import { store } from '../store.js'

const W = 360, H = 168, L = 38, R = 8, T = 10, B = 22
const hover = ref(null)

const scale = computed(() => {
  const pts = store.series
  if (!pts.length) return null
  let lo = Infinity, hi = -Infinity
  for (const p of pts) { lo = Math.min(lo, p.raw, p.s); hi = Math.max(hi, p.raw, p.s) }
  const pad = (hi - lo) * 0.15 || 0.02
  return { lo: Math.max(0, lo - pad), hi: hi + pad }
})

const xs = x => L + (x / store.totalSteps) * (W - L - R)
const ys = y => T + (1 - (y - scale.value.lo) / (scale.value.hi - scale.value.lo)) * (H - T - B)
const pathOf = key => store.series.map((p, i) => (i ? 'L' : 'M') + xs(p.x).toFixed(1) + ' ' + ys(p[key]).toFixed(1)).join(' ')

const rawPath = computed(() => scale.value ? pathOf('raw') : '')
const smoothPath = computed(() => scale.value ? pathOf('s') : '')
const gridLines = computed(() => {
  if (!scale.value) return []
  const { lo, hi } = scale.value
  return [0, 1, 2, 3].map(i => { const g = lo + (hi - lo) * i / 3; return { y: ys(g), label: g.toFixed(3) } })
})
const last = computed(() => store.series[store.series.length - 1])
const tipLeft = computed(() => hover.value ? (xs(hover.value.x) / W) * 100 : 0)

function onMove(e) {
  const pts = store.series
  if (!pts.length) return
  const r = e.currentTarget.getBoundingClientRect()
  const rel = (e.clientX - r.left) / r.width * W
  const stepAt = Math.max(0, Math.min(store.totalSteps, (rel - L) / (W - L - R) * store.totalSteps))
  let best = pts[0]
  for (const p of pts) if (Math.abs(p.x - stepAt) < Math.abs(best.x - stepAt)) best = p
  hover.value = best
}
</script>

<template>
  <div v-if="!store.series.length"
    :style="{ height: H + 'px' }"
    style="display:flex;align-items:center;justify-content:center;font-family:var(--font-mono);font-size:12px;color:var(--mute);border:1px dashed var(--hairline);border-radius:8px">
    等待第一个 step…
  </div>
  <div v-else style="position:relative">
    <svg :viewBox="'0 0 ' + W + ' ' + H" width="100%" :height="H" style="display:block;overflow:visible"
      @mousemove="onMove" @mouseleave="hover = null">
      <template v-for="(g, i) in gridLines" :key="'g' + i">
        <line :x1="L" :x2="W - R" :y1="g.y" :y2="g.y" stroke="var(--hairline)" stroke-width="1" />
        <text :x="L - 6" :y="g.y + 3.5" text-anchor="end"
          style="font-family:var(--font-mono);font-size:10px;fill:var(--mute)">{{ g.label }}</text>
      </template>
      <path :d="rawPath" fill="none" stroke="var(--chart-raw)" stroke-width="1.5" stroke-linejoin="round" />
      <path :d="smoothPath" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
      <circle v-if="last" :cx="xs(last.x)" :cy="ys(last.s)" r="3" fill="var(--accent)" />
      <text :x="L" :y="H - 6" style="font-family:var(--font-mono);font-size:10px;fill:var(--mute)">0</text>
      <text :x="W - R" :y="H - 6" text-anchor="end"
        style="font-family:var(--font-mono);font-size:10px;fill:var(--mute)">{{ store.totalSteps }}</text>
      <template v-if="hover">
        <line :x1="xs(hover.x)" :x2="xs(hover.x)" :y1="T" :y2="H - B" stroke="var(--hairline-strong)" stroke-width="1" />
        <circle :cx="xs(hover.x)" :cy="ys(hover.s)" r="3.5" fill="var(--surface)" stroke="var(--accent)" stroke-width="2" />
      </template>
    </svg>
    <div v-if="hover" :style="{
      position: 'absolute', top: '4px',
      left: tipLeft > 60 ? 'auto' : tipLeft + '%',
      right: tipLeft > 60 ? (100 - tipLeft) + '%' : 'auto',
      transform: tipLeft > 60 ? 'translateX(-8px)' : 'translateX(8px)',
      background: 'var(--surface)', boxShadow: 'var(--shadow-float)', borderRadius: '6px',
      padding: '6px 8px', pointerEvents: 'none', whiteSpace: 'nowrap',
    }">
      <div style="font-family:var(--font-mono);font-size:11px;color:var(--mute)">step {{ hover.x }}</div>
      <div style="font-family:var(--font-mono);font-size:12px;color:var(--ink)">smooth {{ hover.s.toFixed(4) }}</div>
      <div style="font-family:var(--font-mono);font-size:12px;color:var(--body)">raw&nbsp;&nbsp;&nbsp;&nbsp;{{ hover.raw.toFixed(4) }}</div>
    </div>
  </div>
</template>
