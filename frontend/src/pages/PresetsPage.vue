<script setup>
// 预设列表 + 随表单实时生成的 config.toml(导入/导出/复制)。
import { computed } from 'vue'
import { demo, toast, importToml, exportToml } from '../store.js'
import { ui, copyToml } from '../derived.js'

// 演示模式的种子预设(默认真实模式不显示编造预设)
const DEMO_PRESETS = [
  { name: 'character-v1', note: 'standard_lora · dim 16 · 1328', arch: 'qwen-image', updated: '13:58' },
  { name: 'style-anime', note: 'loha · dim 8 · 1024', arch: 'z-image', updated: '昨天' },
  { name: 'product-shot', note: 'lokr · factor 8 · 1024', arch: 'flux.2', updated: '7/28' },
  { name: 'wan-i2v-a14b', note: 'standard_lora · dim 32 · 视频', arch: 'wan2.2', updated: '7/26' },
]

const presets = computed(() => demo.demoMode ? DEMO_PRESETS : [])

function loadPreset(p) { toast('info', '已载入预设 ' + p.name + ' · 3 个字段被覆盖') }
function exportPreset(p) { toast('info', p.name + '.toml 已导出') }
</script>

<template>
  <div data-screen-label="预设与 TOML" style="animation:pageIn .24s cubic-bezier(.2,.8,.2,1) both;max-width:1280px;margin:0 auto">
    <h1 style="margin:0;font-size:20px;line-height:28px;font-weight:600;color:var(--ink)">预设与 TOML</h1>
    <p style="margin:4px 0 24px;font-size:14px;line-height:20px;color:var(--body)">导入时显示未知字段与最终覆盖值;导出后有效 namespace 必须一致。</p>
    <div style="display:flex;flex-wrap:wrap;gap:32px;align-items:flex-start">
      <section style="flex:1 1 420px;min-width:0;background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);overflow-x:auto;overflow-y:hidden">
        <div style="display:grid;grid-template-columns:1fr 120px 96px 116px;gap:12px;padding:0 16px;height:36px;align-items:center;background:var(--surface-2);border-bottom:1px solid var(--hairline)">
          <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">PRESET</span>
          <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">ARCH</span>
          <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute);text-align:right">UPDATED</span>
          <span></span>
        </div>
        <div v-if="!presets.length"
          style="height:96px;display:flex;align-items:center;justify-content:center;font-family:var(--font-mono);font-size:12px;color:var(--mute)">还没有预设 · 在训练页点「保存预设」创建</div>
        <div v-for="p in presets" :key="p.name" class="hv-row"
          style="display:grid;grid-template-columns:1fr 120px 96px 116px;gap:12px;padding:0 16px;min-height:44px;align-items:center;border-bottom:1px solid var(--hairline);transition:background .12s ease">
          <div style="min-width:0">
            <div style="font-family:var(--font-mono);font-size:13px;color:var(--ink)">{{ p.name }}</div>
            <div style="font-size:12px;line-height:16px;color:var(--mute)">{{ p.note }}</div>
          </div>
          <span style="font-family:var(--font-mono);font-size:12px;color:var(--body)">{{ p.arch }}</span>
          <span style="font-family:var(--font-mono);font-size:13px;color:var(--body);text-align:right;font-variant-numeric:tabular-nums">{{ p.updated }}</span>
          <div style="display:flex;gap:6px;justify-content:flex-end">
            <button @click="loadPreset(p)" class="hv-border"
              style="height:28px;padding:0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:12px;color:var(--ink);white-space:nowrap;cursor:pointer">载入</button>
            <button @click="exportPreset(p)" class="hv-line"
              style="height:28px;padding:0 10px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-size:12px;color:var(--body);white-space:nowrap;cursor:pointer">导出</button>
          </div>
        </div>
      </section>
      <section style="flex:1 1 420px;min-width:0;background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);overflow-x:auto;overflow-y:hidden">
        <div style="display:flex;align-items:center;gap:6px;padding:10px 16px;border-bottom:1px solid var(--hairline)">
          <div style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute);flex:1">config.toml</div>
          <button @click="importToml" class="hv-line"
            style="height:28px;padding:0 10px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:11px;color:var(--body);cursor:pointer">导入</button>
          <button @click="exportToml" class="hv-line"
            style="height:28px;padding:0 10px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:11px;color:var(--body);cursor:pointer">导出</button>
          <button @click="copyToml" class="hv-line"
            style="height:28px;padding:0 10px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:11px;color:var(--body);cursor:pointer">复制</button>
        </div>
        <pre style="margin:0;padding:16px;background:var(--surface-2);font-family:var(--font-mono);font-size:12px;line-height:20px;color:var(--ink);overflow-x:auto;max-height:520px">{{ ui.tomlText }}</pre>
      </section>
    </div>
  </div>
</template>
