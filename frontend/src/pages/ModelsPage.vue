<script setup>
// 模型库:当前架构+变体的官方推荐模型清单(一键下载到训练器 models/ 目录)
// 与目录内现有文件。库中已有的模型在训练页切换架构时自动选入表单。
import { computed } from 'vue'
import { store, demo, downloadModel, refreshModels } from '../store.js'

const busy = computed(() => ['queued', 'validating', 'running', 'cancelling'].includes(store.status))
const archLabel = computed(() => {
  const v = store.values
  return v.model_arch + (v.model_version ? ' · ' + v.model_version : '')
})
const ROLE_LABEL = { dit: 'DiT', text_encoder: 'Text Encoder', vae: 'VAE' }
const ROLE_SUBDIR = { dit: 'diffusion_models', text_encoder: 'text_encoders', vae: 'vae' }

function sizeLabel(mb) {
  return mb >= 1024 ? (mb / 1024).toFixed(1) + ' GB' : mb + ' MB'
}
</script>

<template>
  <div data-screen-label="模型库" style="animation:pageIn .24s cubic-bezier(.2,.8,.2,1) both;max-width:1280px;margin:0 auto">
    <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:24px;margin-bottom:24px">
      <div>
        <h1 style="margin:0;font-size:20px;line-height:28px;font-weight:600;color:var(--ink)">模型库</h1>
        <p style="margin:4px 0 0;font-size:14px;line-height:20px;color:var(--body)">一键下载到训练器目录;库中已有的模型在选择架构时自动填入训练表单。</p>
      </div>
      <button @click="refreshModels()" class="hv-border"
        style="height:36px;padding:0 14px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;color:var(--ink);font-size:14px;font-weight:500;white-space:nowrap;cursor:pointer;flex-shrink:0;transition:border-color .14s ease">刷新</button>
    </div>

    <section v-if="!demo.demoMode && !store.modelLib.checked"
      style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);padding:24px;margin-bottom:32px;text-align:center;font-family:var(--font-mono);font-size:12px;color:var(--mute)">
      后端未连接 · 启动后端后点「刷新」读取模型库
    </section>

    <template v-else>
      <section style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);overflow-x:auto;overflow-y:hidden;margin-bottom:32px">
        <div style="display:flex;align-items:center;gap:8px;padding:12px 16px;border-bottom:1px solid var(--hairline)">
          <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">RECOMMENDED</span>
          <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute);border:1px solid var(--hairline);border-radius:6px;padding:1px 6px">{{ archLabel }}</span>
          <span style="flex:1"></span>
          <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute)">bf16 官方权重 · fp8 量化版不可训练</span>
        </div>
        <div style="display:grid;grid-template-columns:120px 1fr 88px 120px 96px;gap:12px;padding:0 16px;height:36px;align-items:center;background:var(--surface-2);border-bottom:1px solid var(--hairline)">
          <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">ROLE</span>
          <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">FILE / SOURCE</span>
          <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute);text-align:right">SIZE</span>
          <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">STATUS</span>
          <span></span>
        </div>
        <div v-if="!store.modelLib.catalog.length"
          style="height:96px;display:flex;align-items:center;justify-content:center;font-family:var(--font-mono);font-size:12px;color:var(--mute)">该架构的一键下载清单待补充 · 可手动导入到模型库目录</div>
        <div v-for="c in store.modelLib.catalog" :key="c.role" class="hv-row"
          style="display:grid;grid-template-columns:120px 1fr 88px 120px 96px;gap:12px;padding:0 16px;min-height:52px;align-items:center;border-bottom:1px solid var(--hairline);transition:background .12s ease">
          <span style="font-size:14px;font-weight:500;color:var(--ink)">{{ ROLE_LABEL[c.role] || c.role }}</span>
          <div style="min-width:0">
            <div style="font-family:var(--font-mono);font-size:13px;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ c.filename }}</div>
            <div style="font-family:var(--font-mono);font-size:11px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ c.repo }}</div>
          </div>
          <span style="font-family:var(--font-mono);font-size:13px;color:var(--body);text-align:right;font-variant-numeric:tabular-nums">{{ sizeLabel(c.size_mb) }}</span>
          <span v-if="c.exists" style="display:inline-flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:12px;color:var(--accent)">
            <span style="width:6px;height:6px;border-radius:50%;background:var(--accent)"></span>已就绪
          </span>
          <span v-else style="display:inline-flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:12px;color:var(--mute)">
            <span style="width:6px;height:6px;border-radius:50%;background:var(--hairline-strong)"></span>未下载
          </span>
          <button v-if="!c.exists" @click="downloadModel(c.role)" :disabled="busy"
            :style="busy ? 'opacity:.4;cursor:not-allowed' : 'cursor:pointer'"
            class="hv-fade"
            style="height:32px;padding:0 12px;background:var(--primary);color:var(--on-primary);border:none;border-radius:6px;font-size:13px;font-weight:500;white-space:nowrap;transition:opacity .14s ease">下载</button>
          <span v-else></span>
        </div>
      </section>

      <section style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);padding:16px 20px">
        <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:4px">
          <div style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">LIBRARY</div>
          <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ store.modelLib.dir }}</span>
        </div>
        <p style="margin:0 0 12px;font-size:12px;line-height:16px;color:var(--mute)">手动导入:把 .safetensors 文件放进对应子目录,点「刷新」即可被识别与自动选择。</p>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px">
          <div v-for="(label, role) in ROLE_LABEL" :key="role">
            <div style="font-family:var(--font-mono);font-size:12px;color:var(--mute);border-bottom:1px solid var(--hairline);padding-bottom:6px;margin-bottom:6px">{{ ROLE_SUBDIR[role] }}/</div>
            <div v-if="!(store.modelLib.files[role] || []).length"
              style="font-family:var(--font-mono);font-size:12px;color:var(--mute);opacity:.6">(空)</div>
            <div v-for="f in store.modelLib.files[role] || []" :key="f"
              style="font-family:var(--font-mono);font-size:12px;line-height:20px;color:var(--body);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ f }}</div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
