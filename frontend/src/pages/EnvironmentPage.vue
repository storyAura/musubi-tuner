<script setup>
// 环境与设备诊断。设备卡来自当前机器真实数据(本地环境 API → WebGL 回退);
// 运行时/依赖/目录诊断需要后端环境 API(交接文档 UI-ENV-001),未连接时如实展示。
// 演示模式(?demo=1)显示原型的完整假数据。
import { computed } from 'vue'
import { store, demo } from '../store.js'

const DEMO_CARDS = [
  {
    eyebrow: 'RUNTIME', title: '运行时', rows: [
      { k: 'python', v: '3.10.11', dotOk: true }, { k: 'torch', v: '2.5.1+cu124', dotOk: true },
      { k: 'cuda', v: '12.4', dotOk: true }, { k: 'accelerate', v: '1.2.1', dotOk: true },
      { k: 'xformers', v: '未安装', dotOff: true }, { k: 'flash-attn', v: '未安装', dotOff: true },
    ],
  },
  {
    eyebrow: 'EXTRAS', title: '依赖 extras', rows: [
      { k: 'qwen-image', v: '已安装', dotOk: true }, { k: 'wan', v: '已安装', dotOk: true },
      { k: 'framepack', v: '已安装', dotOk: true }, { k: 'gradio', v: '5.9.1', dotOk: true },
      { k: 'sageattention', v: '不可用于训练', dotWarn: true },
    ],
  },
  {
    eyebrow: 'PATHS', title: '目录与启动', rows: [
      { k: 'output_dir', v: '可写', dotOk: true }, { k: 'cache_dir', v: '可写', dotOk: true },
      { k: 'logging_dir', v: '可写', dotOk: true },
      { k: 'accelerate', v: '单机单进程', dotWarn: true }, { k: 'num_processes', v: '1', dotOk: true },
    ],
  },
]

const deviceCard = computed(() => {
  const e = store.env
  if (e.source === 'nvidia') {
    const warn = e.vramTotalGb > 0 && e.vramUsedGb / e.vramTotalGb > 0.9
    return {
      eyebrow: 'DEVICE', title: '设备(实时)', rows: [
        { k: 'gpu', v: e.gpuName, dotOk: true },
        { k: 'vram', v: e.vramUsedGb.toFixed(1) + ' / ' + e.vramTotalGb.toFixed(1) + ' GB', dotWarn: warn, dotOk: !warn },
        { k: 'driver', v: e.driver || '—', dotOk: true },
        { k: 'compute', v: e.computeCap || '—', dotOk: true },
        { k: 'devices', v: String(e.gpuCount), dotOk: true },
      ],
    }
  }
  if (e.backend) {
    // 后端在线但 nvidia-smi 无 GPU:无卡模式或无 NVIDIA 显卡,如实显示,不冒用浏览器显卡
    return {
      eyebrow: 'DEVICE', title: '设备(训练机)', rows: [
        { k: 'gpu', v: '未检测到 · 无卡模式或无 NVIDIA GPU', dotWarn: true },
        { k: 'hint', v: '有卡开机后自动恢复实时显示', dotOff: true },
      ],
    }
  }
  if (e.source === 'webgl') {
    return {
      eyebrow: 'DEVICE', title: '设备(本机浏览器 · 非训练机)', rows: [
        { k: 'gpu', v: e.gpuName + '(浏览器设备)', dotOff: true },
        { k: 'vram', v: '未知 · 浏览器无法读取', dotOff: true },
        { k: 'driver', v: '未知 · 需后端环境 API', dotOff: true },
      ],
    }
  }
  return {
    eyebrow: 'DEVICE', title: '设备', rows: [
      { k: 'gpu', v: '未检测到', dotOff: true },
      { k: 'hint', v: '启动后端后可读取 nvidia-smi', dotOff: true },
    ],
  }
})

const backendCard = computed(() => {
  const e = store.env
  if (!e.backend) {
    return {
      eyebrow: 'BACKEND', title: '后端诊断', rows: [
        { k: 'api', v: '未连接', dotWarn: true },
        { k: 'start', v: 'python -m uvicorn backend.main:app --port 8787', dotOff: true },
        { k: 'python / torch', v: '未知', dotOff: true },
      ],
    }
  }
  return {
    eyebrow: 'BACKEND', title: '后端诊断', rows: [
      { k: 'api', v: 'connected · /api/v1', dotOk: true },
      { k: 'python', v: e.python || '—', dotOk: true },
      { k: 'torch', v: e.torch || '未安装', dotOk: !!e.torch, dotWarn: !e.torch },
      { k: 'accelerate', v: e.accelerate || '未安装 · 训练启动需要', dotOk: !!e.accelerate, dotWarn: !e.accelerate },
    ],
  }
})

const envCards = computed(() =>
  demo.demoMode
    ? [DEMO_CARDS[0], deviceCard.value, DEMO_CARDS[1], DEMO_CARDS[2]]
    : [deviceCard.value, backendCard.value])
</script>

<template>
  <div data-screen-label="环境诊断" style="animation:pageIn .24s cubic-bezier(.2,.8,.2,1) both;max-width:1280px;margin:0 auto">
    <h1 style="margin:0;font-size:20px;line-height:28px;font-weight:600;color:var(--ink)">环境与设备</h1>
    <p style="margin:4px 0 24px;font-size:14px;line-height:20px;color:var(--body)">提交前先看这里:「存在接口」不等于「当前能跑」。</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:24px">
      <section v-for="c in envCards" :key="c.eyebrow"
        style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);padding:16px 20px;animation:cardIn .26s cubic-bezier(.2,.8,.2,1) both">
        <div style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">{{ c.eyebrow }}</div>
        <h2 style="margin:6px 0 14px;font-size:16px;line-height:24px;font-weight:600;color:var(--ink)">{{ c.title }}</h2>
        <div style="display:flex;flex-direction:column">
          <div v-for="r in c.rows" :key="r.k"
            style="display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:32px;border-top:1px solid var(--hairline)">
            <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute)">{{ r.k }}</span>
            <div style="display:flex;align-items:center;gap:6px;min-width:0">
              <span v-if="r.dotOk" style="width:6px;height:6px;border-radius:50%;background:var(--accent);flex-shrink:0"></span>
              <span v-if="r.dotWarn" style="width:6px;height:6px;border-radius:50%;background:var(--warning);flex-shrink:0"></span>
              <span v-if="r.dotOff" style="width:6px;height:6px;border-radius:50%;background:var(--hairline-strong);flex-shrink:0"></span>
              <span style="font-family:var(--font-mono);font-size:13px;color:var(--ink);font-variant-numeric:tabular-nums;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ r.v }}</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
