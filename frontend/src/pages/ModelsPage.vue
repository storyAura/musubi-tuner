<script setup>
// 模型库:上半部分是当前架构+变体的推荐清单(自动选择联动);
// 下半部分是全部 12 个架构的完整可训练模型清单(按架构分组,均为实测核对的官方权重)。
import { computed, onMounted } from 'vue'
import { store, demo, clock, downloadModel, cancelDownload, refreshModels, loadAllModels } from '../store.js'

// 下载状态独立于训练状态机;每个条目按自身 filename 查询下载进度
function dlStatus(filename) {
  return store.downloads[filename]?.status || ''
}

function dlInfo(filename) {
  const d = store.downloads[filename]
  return d && d.bytes ? d : null
}

function dlPct(filename) {
  const d = dlInfo(filename)
  return d && d.total_bytes ? Math.min(100, d.bytes / d.total_bytes * 100) : 0
}

function dlLine(filename) {
  const d = dlInfo(filename)
  if (!d) return ''
  const gb = x => (x / 1024 ** 3).toFixed(2)
  const spd = (d.speed_bps || 0) >= 1048576
    ? (d.speed_bps / 1048576).toFixed(1) + ' MB/s'
    : Math.round((d.speed_bps || 0) / 1024) + ' KB/s'
  const eta = d.eta_s > 0 ? clock(d.eta_s) : '--:--'
  return gb(d.bytes) + ' / ' + gb(d.total_bytes) + ' GB · ' + spd + ' · ETA ' + eta + ' · ' + Math.round(dlPct(filename)) + '%'
}
const archLabel = computed(() => {
  const v = store.values
  const variant = v.model_version || v.model_type || v.task || ''
  return v.model_arch + (variant ? ' · ' + variant : '')
})
const ROLE_LABEL = {
  dit: 'DiT', dit_high_noise: 'DiT (high noise)', unconditional_dit: 'DiT (uncond)',
  text_encoder: 'Text Encoder', text_encoder2: 'Text Encoder 2', byt5: 'BYT5',
  clip: 'CLIP', vae: 'VAE', image_encoder: 'Image Encoder',
}
const LIB_SUBDIRS = ['diffusion_models', 'text_encoders', 'vae', 'clip_vision']

function sizeLabel(mb) {
  return mb >= 1024 ? (mb / 1024).toFixed(1) + ' GB' : mb + ' MB'
}

function refreshAll() {
  refreshModels()
  loadAllModels()
}

onMounted(() => { if (!store.modelLibAll.checked) loadAllModels() })
</script>

<template>
  <div data-screen-label="模型库" style="animation:pageIn .24s cubic-bezier(.2,.8,.2,1) both;max-width:1280px;margin:0 auto">
    <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:24px;margin-bottom:24px">
      <div>
        <h1 style="margin:0;font-size:20px;line-height:28px;font-weight:600;color:var(--ink)">模型库</h1>
        <p style="margin:4px 0 0;font-size:14px;line-height:20px;color:var(--body)">一键下载到训练器目录;库中已有的模型在选择架构时自动填入训练表单。</p>
      </div>
      <button @click="refreshAll" class="hv-border"
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
          <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute)">当前训练表单对应的权重</span>
        </div>
        <div style="display:grid;grid-template-columns:150px 1fr 88px 110px 96px;gap:12px;padding:0 16px;height:36px;align-items:center;background:var(--surface-2);border-bottom:1px solid var(--hairline)">
          <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">ROLE</span>
          <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">FILE / SOURCE</span>
          <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute);text-align:right">SIZE</span>
          <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">STATUS</span>
          <span></span>
        </div>
        <div v-if="!store.modelLib.catalog.length"
          style="height:96px;display:flex;align-items:center;justify-content:center;font-family:var(--font-mono);font-size:12px;color:var(--mute)">该架构暂无单文件推荐清单 · 可手动导入到模型库目录</div>
        <div v-for="c in store.modelLib.catalog" :key="c.role + c.filename" class="hv-row"
          style="display:grid;grid-template-columns:150px 1fr 88px 110px 96px;gap:12px;padding:0 16px;min-height:52px;align-items:center;border-bottom:1px solid var(--hairline);transition:background .12s ease">
          <span style="font-size:14px;font-weight:500;color:var(--ink)">{{ ROLE_LABEL[c.role] || c.role }}<span v-if="c.optional" style="font-family:var(--font-mono);font-size:11px;color:var(--mute)"> · 可选</span></span>
          <div style="min-width:0">
            <div style="font-family:var(--font-mono);font-size:13px;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ c.filename }}</div>
            <div style="font-family:var(--font-mono);font-size:11px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ c.repo }}<span v-if="c.note"> · {{ c.note }}</span></div>
            <div v-if="!c.exists && dlInfo(c.filename)" style="margin:8px 0 6px;max-width:520px">
              <div style="position:relative;height:6px;background:var(--hairline);border-radius:6px;overflow:visible">
                <div :style="{ width: dlPct(c.filename) + '%', height: '6px', background: 'var(--ink)', borderRadius: '6px', transition: 'width .5s linear' }"></div>
                <div :style="{ position: 'absolute', top: '-2px', left: 'calc(' + dlPct(c.filename) + '% - 5px)', width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent)', transition: 'left .5s linear', animation: 'tailPulse 1.6s ease-out infinite' }"></div>
              </div>
              <div style="font-family:var(--font-mono);font-size:11px;color:var(--body);font-variant-numeric:tabular-nums;margin-top:4px">{{ dlLine(c.filename) }}</div>
            </div>
          </div>
          <span style="font-family:var(--font-mono);font-size:13px;color:var(--body);text-align:right;font-variant-numeric:tabular-nums">{{ sizeLabel(c.size_mb) }}</span>
          <span v-if="c.exists" style="display:inline-flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:12px;color:var(--accent)">
            <span style="width:6px;height:6px;border-radius:50%;background:var(--accent)"></span>已就绪
          </span>
          <span v-else-if="['queued', 'running', 'cancelling'].includes(dlStatus(c.filename))"
            style="display:inline-flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:12px;color:var(--accent)">
            <span style="width:6px;height:6px;border-radius:50%;background:var(--accent);animation:breathe 2s ease-in-out infinite"></span>下载中
          </span>
          <span v-else-if="dlStatus(c.filename) === 'failed'"
            style="display:inline-flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:12px;color:var(--error)">
            <span style="width:6px;height:6px;border-radius:50%;background:var(--error)"></span>失败
          </span>
          <span v-else style="display:inline-flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:12px;color:var(--mute)">
            <span style="width:6px;height:6px;border-radius:50%;background:var(--hairline-strong)"></span>未下载
          </span>
          <button v-if="!c.exists && ['queued', 'running'].includes(dlStatus(c.filename))"
            @click="cancelDownload(c.filename)" class="hv-line"
            style="height:32px;padding:0 12px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-size:13px;font-weight:500;color:var(--body);white-space:nowrap;cursor:pointer">取消</button>
          <button v-else-if="!c.exists && dlStatus(c.filename) !== 'cancelling'"
            @click="downloadModel(store.values.model_arch, c.filename)" class="hv-fade"
            style="height:32px;padding:0 12px;background:var(--primary);color:var(--on-primary);border:none;border-radius:6px;font-size:13px;font-weight:500;white-space:nowrap;cursor:pointer;transition:opacity .14s ease">{{ dlStatus(c.filename) === 'failed' ? '重试' : '下载' }}</button>
          <span v-else></span>
        </div>
      </section>

      <h2 style="margin:0 0 4px;font-size:16px;line-height:24px;font-weight:600;color:var(--ink)">全部模型</h2>
      <p style="margin:0 0 16px;font-size:12px;line-height:16px;color:var(--mute)">12 个架构的可训练权重总表(文件名与大小逐一实测核对;bf16/fp16 优先,fp8 量化版不可训练不收录,Ideogram4 官方仅有 fp8_scaled 除外)。</p>

      <section v-for="g in store.modelLibAll.architectures" :key="g.id"
        style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);overflow-x:auto;overflow-y:hidden;margin-bottom:16px">
        <div style="display:flex;align-items:center;gap:8px;padding:10px 16px;border-bottom:1px solid var(--hairline)">
          <span style="font-family:var(--font-mono);font-size:13px;font-weight:500;color:var(--ink)">{{ g.id }}</span>
          <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute);font-variant-numeric:tabular-nums">{{ g.entries.filter(e => e.exists).length }}/{{ g.entries.length }} 就绪</span>
        </div>
        <div v-for="c in g.entries" :key="c.role + c.filename" class="hv-row"
          style="display:grid;grid-template-columns:150px 1fr 88px 110px 96px;gap:12px;padding:0 16px;min-height:48px;align-items:center;border-bottom:1px solid var(--hairline);transition:background .12s ease">
          <div style="min-width:0">
            <div style="font-size:13px;font-weight:500;color:var(--ink)">{{ ROLE_LABEL[c.role] || c.role }}<span v-if="c.optional" style="font-family:var(--font-mono);font-size:11px;color:var(--mute)"> · 可选</span></div>
            <div v-if="c.variants" style="font-family:var(--font-mono);font-size:10px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ c.variants.join(' ') }}</div>
          </div>
          <div style="min-width:0">
            <div style="font-family:var(--font-mono);font-size:13px;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ c.filename }}</div>
            <div style="font-family:var(--font-mono);font-size:11px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ c.repo }}<span v-if="c.note"> · {{ c.note }}</span></div>
            <div v-if="!c.exists && dlInfo(c.filename)" style="margin:8px 0 6px;max-width:520px">
              <div style="position:relative;height:6px;background:var(--hairline);border-radius:6px;overflow:visible">
                <div :style="{ width: dlPct(c.filename) + '%', height: '6px', background: 'var(--ink)', borderRadius: '6px', transition: 'width .5s linear' }"></div>
                <div :style="{ position: 'absolute', top: '-2px', left: 'calc(' + dlPct(c.filename) + '% - 5px)', width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent)', transition: 'left .5s linear', animation: 'tailPulse 1.6s ease-out infinite' }"></div>
              </div>
              <div style="font-family:var(--font-mono);font-size:11px;color:var(--body);font-variant-numeric:tabular-nums;margin-top:4px">{{ dlLine(c.filename) }}</div>
            </div>
          </div>
          <span style="font-family:var(--font-mono);font-size:13px;color:var(--body);text-align:right;font-variant-numeric:tabular-nums">{{ sizeLabel(c.size_mb) }}</span>
          <span v-if="c.exists" style="display:inline-flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:12px;color:var(--accent)">
            <span style="width:6px;height:6px;border-radius:50%;background:var(--accent)"></span>已就绪
          </span>
          <span v-else-if="['queued', 'running', 'cancelling'].includes(dlStatus(c.filename))"
            style="display:inline-flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:12px;color:var(--accent)">
            <span style="width:6px;height:6px;border-radius:50%;background:var(--accent);animation:breathe 2s ease-in-out infinite"></span>下载中
          </span>
          <span v-else-if="dlStatus(c.filename) === 'failed'"
            style="display:inline-flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:12px;color:var(--error)">
            <span style="width:6px;height:6px;border-radius:50%;background:var(--error)"></span>失败
          </span>
          <span v-else style="display:inline-flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:12px;color:var(--mute)">
            <span style="width:6px;height:6px;border-radius:50%;background:var(--hairline-strong)"></span>未下载
          </span>
          <button v-if="!c.exists && ['queued', 'running'].includes(dlStatus(c.filename))"
            @click="cancelDownload(c.filename)" class="hv-line"
            style="height:30px;padding:0 12px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-size:12px;font-weight:500;color:var(--body);white-space:nowrap;cursor:pointer">取消</button>
          <button v-else-if="!c.exists && dlStatus(c.filename) !== 'cancelling'"
            @click="downloadModel(g.id, c.filename)" class="hv-border"
            style="height:30px;padding:0 12px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:12px;font-weight:500;color:var(--ink);white-space:nowrap;cursor:pointer;transition:border-color .14s ease">{{ dlStatus(c.filename) === 'failed' ? '重试' : '下载' }}</button>
          <span v-else></span>
        </div>
      </section>

      <section style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);padding:16px 20px;margin-top:32px">
        <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:4px">
          <div style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">LIBRARY</div>
          <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ store.modelLib.dir }}</span>
        </div>
        <p style="margin:0 0 12px;font-size:12px;line-height:16px;color:var(--mute)">手动导入:把模型文件放进对应子目录,点「刷新」即可被识别与自动选择。多分片权重(FLUX.2 dev 文本编码器、Kandinsky 文本编码器等)暂不支持一键下载,需手动准备。</p>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px">
          <div v-for="sub in LIB_SUBDIRS" :key="sub">
            <div style="font-family:var(--font-mono);font-size:12px;color:var(--mute);border-bottom:1px solid var(--hairline);padding-bottom:6px;margin-bottom:6px">{{ sub }}/</div>
            <div v-if="!(store.modelLib.files[sub] || []).length"
              style="font-family:var(--font-mono);font-size:12px;color:var(--mute);opacity:.6">(空)</div>
            <div v-for="f in store.modelLib.files[sub] || []" :key="f"
              style="font-family:var(--font-mono);font-size:12px;line-height:20px;color:var(--body);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ f }}</div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
