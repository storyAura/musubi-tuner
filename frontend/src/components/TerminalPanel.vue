<script setup>
// kohya 原样日志终端:自动吸底、回到底部浮钮、双击全屏(Esc 退出)、
// 「置顶」后变成跨页面常驻的半透明悬浮控制台(横排贴底 / 竖排靠右,透明度可调)。
// 同一组件同时服务训练页停靠形态与全局悬浮形态,形态由 store 的 termPinned/termFull 决定。
import { computed, nextTick, ref, watch } from 'vue'
import {
  store, onLogScroll, termDbl, togglePin, toggleOrient, setTermOp,
  copyLogs, clearLogs, toggleScroll,
} from '../store.js'

const bodyEl = ref(null)

const KIND_COLOR = { ink: '#ededed', dim: '#8f8f8f', warn: '#ffb224', err: '#ff6166' }

const floatingCtl = computed(() => store.termPinned && !store.termFull)
const pinLabel = computed(() => store.termPinned ? '收回' : '置顶')
const scrollLabel = computed(() => store.autoScroll ? '自动滚动 开' : '自动滚动 关')
const termHint = computed(() => store.termFull ? '双击或 Esc 退出全屏' : '双击日志区全屏')
const orientLabel = computed(() => store.termOrient === 'h' ? '竖排' : '横排')
const termOpPct = computed(() => Math.round(store.termOp * 100))

const wrapStyle = computed(() => {
  if (store.termFull) {
    return { position: 'fixed', inset: '0', zIndex: 90, background: 'var(--terminal-bg)', display: 'flex', flexDirection: 'column' }
  }
  if (store.termPinned) {
    // 透明度完全由滑杆控制(不做 hover 强制不透明——那会让拖动滑杆时看不到实时效果)
    const base = {
      position: 'fixed', zIndex: 65, background: 'var(--surface)', borderRadius: '8px',
      boxShadow: 'var(--shadow-modal)', overflow: 'hidden', display: 'flex', flexDirection: 'column',
      opacity: store.termOp, transition: 'opacity .15s ease',
    }
    return store.termOrient === 'h'
      ? { ...base, left: '240px', right: '16px', bottom: '16px', height: '236px' }
      : { ...base, top: '72px', right: '16px', bottom: '16px', width: '440px' }
  }
  return { background: 'var(--surface)', borderRadius: '8px', boxShadow: 'var(--shadow-card)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }
})

const bodyStyle = computed(() => ({
  overflowY: 'auto', overflowX: 'hidden', background: 'var(--terminal-bg)',
  padding: '12px 14px', borderTop: '1px solid var(--hairline)', cursor: 'default',
  ...(store.termFull || (store.termPinned && store.termOrient === 'v')
    ? { height: '100%' }
    : (store.termPinned ? { height: '188px' } : { height: '280px' })),
}))

function scrollToBottom() {
  if (bodyEl.value) bodyEl.value.scrollTop = bodyEl.value.scrollHeight
}

function jumpBottom() {
  store.autoScroll = true
  store.atBottom = true
  scrollToBottom()
}

watch(() => [store.logs.length, store.autoScroll], async () => {
  if (!store.autoScroll) return
  await nextTick()
  scrollToBottom()
})
</script>

<template>
  <section :style="wrapStyle">
    <div style="display:flex;align-items:center;gap:6px;padding:8px 10px;background:var(--surface)">
      <div style="display:flex;align-items:baseline;gap:8px;flex:1;min-width:0">
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">TERMINAL</span>
        <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute);opacity:.7;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ termHint }}</span>
      </div>
      <div v-if="floatingCtl" style="display:flex;align-items:center;gap:6px;animation:rowIn .18s ease both">
        <input type="range" min="35" max="100" :value="termOpPct" @input="setTermOp" title="透明度"
          style="width:64px;accent-color:var(--ink);height:4px" />
        <button @click="toggleOrient" class="hv-line"
          style="height:28px;padding:0 8px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:11px;color:var(--body);white-space:nowrap;cursor:pointer">{{ orientLabel }}</button>
      </div>
      <button @click="togglePin" class="hv-line"
        style="height:28px;padding:0 8px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:11px;color:var(--body);white-space:nowrap;cursor:pointer">{{ pinLabel }}</button>
      <button @click="copyLogs" class="hv-line"
        style="height:28px;padding:0 8px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:11px;color:var(--body);cursor:pointer">复制</button>
      <button @click="clearLogs" class="hv-line"
        style="height:28px;padding:0 8px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:11px;color:var(--body);cursor:pointer">清空</button>
      <button @click="toggleScroll" class="hv-line"
        style="height:28px;padding:0 8px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:11px;color:var(--body);cursor:pointer">{{ scrollLabel }}</button>
    </div>
    <div style="position:relative;flex:1 1 auto;min-height:0">
      <div ref="bodyEl" @scroll="onLogScroll" @dblclick="termDbl" title="双击切换全屏" :style="bodyStyle">
        <div v-for="l in store.logs" :key="l.id"
          :style="{ fontFamily: 'var(--font-mono)', fontSize: '13px', lineHeight: '20px', color: KIND_COLOR[l.kind] || '#ededed', whiteSpace: 'pre-wrap', wordBreak: 'break-all', animation: 'lineIn .18s ease-out both' }">
          {{ l.text }}</div>
      </div>
      <button v-if="!store.atBottom" @click="jumpBottom"
        style="position:absolute;right:12px;bottom:12px;height:28px;padding:0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;box-shadow:var(--shadow-float);font-family:var(--font-mono);font-size:11px;color:var(--ink);cursor:pointer;animation:toastIn .18s ease both">回到底部 ↓</button>
    </div>
  </section>
</template>
