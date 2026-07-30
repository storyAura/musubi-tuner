<script setup>
// 产物库:样图画廊 + 检查点/缓存/日志索引表;训练产生的 artifact 实时插入最前。
import { computed } from 'vue'
import { store, demo } from '../store.js'

// 演示模式的种子数据(默认真实模式不显示任何编造产物)
const SEED_ARTIFACTS = [
  { name: 'character-v1-000002.safetensors', kind: 'epoch checkpoint', size: '152.4 MB', created: '13:58', job: 'job_38f7b0', remote: '—' },
  { name: 'img_0184_1328x1328_qwen-image.safetensors', kind: 'latent cache', size: '2.1 MB', created: '13:43', job: 'job_5b12c4', remote: '—' },
  { name: 'img_0184_qwen-image_te.safetensors', kind: 'text cache', size: '0.4 MB', created: '13:44', job: 'job_5b12c4', remote: '—' },
  { name: 'sample_e01_0001.png', kind: 'sample', size: '1.8 MB', created: '13:52', job: 'job_38f7b0', remote: '—' },
  { name: 'train_20260730-1341.log', kind: 'log', size: '86 KB', created: '13:41', job: 'job_5b12c4', remote: '—' },
]

const PLACEHOLDER_GALLERY = [
  { id: 'p1', label: 'epoch 12', reso: '1328×1328' }, { id: 'p2', label: 'epoch 11', reso: '1328×1328' },
  { id: 'p3', label: 'epoch 10', reso: '1328×1328' }, { id: 'p4', label: 'epoch 09', reso: '1328×1328' },
]

const gallery = computed(() => demo.demoMode ? store.samples.concat(PLACEHOLDER_GALLERY).slice(0, 8) : store.samples)
const artifactRows = computed(() => demo.demoMode ? store.extraArtifacts.concat(SEED_ARTIFACTS).slice(0, 12) : store.extraArtifacts)
</script>

<template>
  <div data-screen-label="产物库" style="animation:pageIn .24s cubic-bezier(.2,.8,.2,1) both;max-width:1280px;margin:0 auto">
    <h1 style="margin:0;font-size:20px;line-height:28px;font-weight:600;color:var(--ink)">产物库</h1>
    <p style="margin:4px 0 24px;font-size:14px;line-height:20px;color:var(--body)">检查点、样图与缓存都登记在产物索引里,下载只接受索引内路径。</p>

    <section style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);padding:16px;margin-bottom:32px">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:12px">
        <div style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">SAMPLE GALLERY</div>
        <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute)">{{ store.samples.length }} 张</span>
      </div>
      <div v-if="!store.samples.length"
        style="height:140px;display:flex;align-items:center;justify-content:center;font-family:var(--font-mono);font-size:12px;color:var(--mute);border:1px dashed var(--hairline);border-radius:8px">还没有样图 · 开始训练后按 epoch 生成</div>
      <div v-else style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
        <div v-for="s in gallery" :key="s.id"
          style="position:relative;aspect-ratio:1/1;border:1px solid var(--hairline);border-radius:8px;background:var(--surface-2);overflow:hidden;animation:tileIn .32s cubic-bezier(.2,.8,.2,1) both">
          <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-family:var(--font-mono);font-size:11px;color:var(--mute)">{{ s.reso }}</div>
          <div style="position:absolute;top:6px;left:6px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;padding:1px 6px;font-family:var(--font-mono);font-size:11px;color:var(--body);white-space:nowrap">{{ s.label }}</div>
        </div>
      </div>
    </section>

    <section style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);overflow-x:auto;overflow-y:hidden">
      <div style="display:grid;grid-template-columns:1fr 132px 88px 96px 116px 104px;gap:12px;padding:0 16px;height:36px;align-items:center;background:var(--surface-2);border-bottom:1px solid var(--hairline)">
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">NAME</span>
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">KIND</span>
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute);text-align:right">SIZE</span>
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute);text-align:right">CREATED</span>
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">JOB</span>
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">REMOTE</span>
      </div>
      <div v-if="!artifactRows.length"
        style="height:96px;display:flex;align-items:center;justify-content:center;font-family:var(--font-mono);font-size:12px;color:var(--mute)">还没有产物 · 训练或缓存完成后登记到这里</div>
      <div v-for="a in artifactRows" :key="a.name + a.created" class="hv-row"
        style="display:grid;grid-template-columns:1fr 132px 88px 96px 116px 104px;gap:12px;padding:0 16px;min-height:44px;align-items:center;border-bottom:1px solid var(--hairline);transition:background .12s ease">
        <span style="font-family:var(--font-mono);font-size:13px;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ a.name }}</span>
        <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute)">{{ a.kind }}</span>
        <span style="font-family:var(--font-mono);font-size:13px;color:var(--body);text-align:right;font-variant-numeric:tabular-nums">{{ a.size }}</span>
        <span style="font-family:var(--font-mono);font-size:13px;color:var(--body);text-align:right;font-variant-numeric:tabular-nums">{{ a.created }}</span>
        <span style="font-family:var(--font-mono);font-size:13px;color:var(--body)">{{ a.job }}</span>
        <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute)">{{ a.remote }}</span>
      </div>
    </section>
  </div>
</template>
