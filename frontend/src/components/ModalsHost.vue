<script setup>
// 三个确认弹窗:停止训练(温和终止语义)、缓存清理计划(--keep_cache 开关)、argv 命令预览(秘密脱敏)。
import { computed } from 'vue'
import { store, demo, closeModal, confirmCancel, toggleKeep, confirmCleanup } from '../store.js'
import { ui, copyArgv } from '../derived.js'

// 演示模式的示例清单;真实模式不列虚构文件,删除行为由缓存器运行时决定(--keep_cache 控制)
const CLEANUP_LIST = [
  { path: 'cache/img_0093_1024x1024_qwen-image.safetensors', size: '2.0 MB' },
  { path: 'cache/img_0094_1024x1024_qwen-image.safetensors', size: '2.0 MB' },
  { path: 'cache/old_run_408.6MB_bucket', size: '408.6 MB' },
]
const CLEANUP_TOTAL = '412.6 MB · 3 个文件'

const stepLine = computed(() => store.step + '/' + store.totalSteps)
const keepHint = computed(() => store.keepCache ? '不删除任何文件,磁盘占用会增长' : '默认删除未被当前数据集引用的缓存')
const cleanupCta = computed(() => store.keepCache ? '开始缓存(保留旧文件)' : '删除并开始缓存')
</script>

<template>
  <div v-if="store.modal === 'cancel'"
    style="position:fixed;inset:0;z-index:100;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;padding:24px;animation:overlayIn .16s ease both">
    <div style="width:480px;max-width:100%;background:var(--surface);border-radius:12px;box-shadow:var(--shadow-modal);padding:24px;animation:modalIn .22s cubic-bezier(.2,.8,.2,1) both">
      <h3 style="margin:0;font-size:16px;line-height:24px;font-weight:600;color:var(--ink)">停止当前训练?</h3>
      <p style="margin:8px 0 0;font-size:14px;line-height:20px;color:var(--body)">会先温和终止,等待当前 step 与保存完成;超时后终止整个进程组。已写入的检查点会保留。</p>
      <div style="margin-top:16px;background:var(--surface-2);border-radius:6px;padding:10px 12px;font-family:var(--font-mono);font-size:12px;line-height:20px;color:var(--body)">
        <div>job_id     {{ store.jobId }}</div>
        <div>stage      training</div>
        <div>step       {{ stepLine }}</div>
      </div>
      <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:20px">
        <button @click="closeModal"
          style="height:36px;padding:0 14px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:14px;font-weight:500;color:var(--ink);white-space:nowrap;cursor:pointer">继续训练</button>
        <button @click="confirmCancel" class="hv-danger"
          style="height:36px;padding:0 14px;background:var(--surface);border:1px solid var(--error);border-radius:6px;font-size:14px;font-weight:500;color:var(--error);white-space:nowrap;cursor:pointer;transition:background .14s ease,color .14s ease">停止训练</button>
      </div>
    </div>
  </div>

  <div v-if="store.modal === 'cleanup'"
    style="position:fixed;inset:0;z-index:100;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;padding:24px;animation:overlayIn .16s ease both">
    <div style="width:600px;max-width:100%;background:var(--surface);border-radius:12px;box-shadow:var(--shadow-modal);padding:24px;animation:modalIn .22s cubic-bezier(.2,.8,.2,1) both">
      <h3 style="margin:0;font-size:16px;line-height:24px;font-weight:600;color:var(--ink)">缓存 latents</h3>
      <p style="margin:8px 0 0;font-size:14px;line-height:20px;color:var(--body)">缓存器默认会删除未被当前数据集引用的旧缓存(<span style="font-family:var(--font-mono)">--keep_cache</span> 可保留)。</p>
      <div v-if="demo.demoMode" style="margin-top:16px;border:1px solid var(--hairline);border-radius:6px;overflow:hidden">
        <div v-for="c in CLEANUP_LIST" :key="c.path"
          style="display:flex;align-items:center;justify-content:space-between;gap:12px;padding:8px 12px;border-bottom:1px solid var(--hairline)">
          <span style="font-family:var(--font-mono);font-size:12px;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ c.path }}</span>
          <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute);flex-shrink:0;font-variant-numeric:tabular-nums">{{ c.size }}</span>
        </div>
        <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;padding:8px 12px;background:var(--surface-2)">
          <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute)">total</span>
          <span style="font-family:var(--font-mono);font-size:12px;color:var(--ink);font-variant-numeric:tabular-nums">{{ CLEANUP_TOTAL }}</span>
        </div>
      </div>
      <div v-else style="margin-top:16px;background:var(--surface-2);border-radius:6px;padding:10px 12px;font-family:var(--font-mono);font-size:12px;line-height:20px;color:var(--body)">
        <div>dataset_config  {{ store.values.dataset_config || '(未填写)' }}</div>
        <div>vae             {{ store.values.vae || '(未填写)' }}</div>
        <div>删除清单由缓存器运行时决定(精确预览待 cleanup-plan API)</div>
      </div>
      <div style="display:flex;align-items:center;gap:10px;margin-top:16px">
        <button v-if="store.keepCache" @click="toggleKeep"
          style="width:36px;height:20px;padding:0;position:relative;background:var(--ink);border:1px solid var(--ink);border-radius:6px;cursor:pointer;flex-shrink:0">
          <span style="position:absolute;top:2px;left:18px;width:14px;height:14px;border-radius:4px;background:var(--surface);transition:left .18s cubic-bezier(.2,.8,.2,1)"></span>
        </button>
        <button v-else @click="toggleKeep"
          style="width:36px;height:20px;padding:0;position:relative;background:var(--surface-2);border:1px solid var(--hairline);border-radius:6px;cursor:pointer;flex-shrink:0">
          <span style="position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:4px;background:var(--hairline-strong);transition:left .18s cubic-bezier(.2,.8,.2,1)"></span>
        </button>
        <div>
          <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:14px;font-weight:500;color:var(--ink)">保留旧缓存</span>
            <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute)">--keep_cache</span>
          </div>
          <div style="font-size:12px;line-height:16px;color:var(--mute)">{{ keepHint }}</div>
        </div>
      </div>
      <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:20px">
        <button @click="closeModal"
          style="height:36px;padding:0 14px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:14px;font-weight:500;color:var(--ink);white-space:nowrap;cursor:pointer">取消</button>
        <button @click="confirmCleanup" class="hv-fade"
          style="height:36px;padding:0 14px;background:var(--primary);color:var(--on-primary);border:none;border-radius:6px;font-size:14px;font-weight:500;white-space:nowrap;cursor:pointer;transition:opacity .14s ease">{{ cleanupCta }}</button>
      </div>
    </div>
  </div>

  <div v-if="store.modal === 'command'"
    style="position:fixed;inset:0;z-index:100;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;padding:24px;animation:overlayIn .16s ease both">
    <div style="width:720px;max-width:100%;background:var(--surface);border-radius:12px;box-shadow:var(--shadow-modal);padding:24px;animation:modalIn .22s cubic-bezier(.2,.8,.2,1) both">
      <h3 style="margin:0;font-size:16px;line-height:24px;font-weight:600;color:var(--ink)">将要执行的命令</h3>
      <p style="margin:8px 0 0;font-size:14px;line-height:20px;color:var(--body)">由后端选择入口脚本并渲染 argv 数组(shell=False),秘密以 <span style="font-family:var(--font-mono)">&lt;redacted&gt;</span> 呈现。</p>
      <div style="margin-top:16px;background:var(--terminal-bg);border-radius:6px;padding:14px 16px;max-height:360px;overflow:auto">
        <div v-for="(l, i) in ui.argvLines" :key="i"
          style="font-family:var(--font-mono);font-size:13px;line-height:20px;color:#ededed;white-space:pre-wrap;word-break:break-all">{{ l.text }}</div>
      </div>
      <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:20px">
        <button @click="closeModal"
          style="height:36px;padding:0 14px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:14px;font-weight:500;color:var(--ink);white-space:nowrap;cursor:pointer">关闭</button>
        <button @click="copyArgv" class="hv-fade"
          style="height:36px;padding:0 14px;background:var(--primary);color:var(--on-primary);border:none;border-radius:6px;font-size:14px;font-weight:500;white-space:nowrap;cursor:pointer;transition:opacity .14s ease">复制</button>
      </div>
    </div>
  </div>
</template>
