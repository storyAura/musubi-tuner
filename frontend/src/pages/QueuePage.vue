<script setup>
// 作业队列:live 作业 + 排队任务(可编辑)+ 已完成/种子历史;状态来自作业状态机,不解析 stdout。
import { ui } from '../derived.js'
import StatusBadge from '../components/StatusBadge.vue'
</script>

<template>
  <div data-screen-label="作业队列" style="animation:pageIn .24s cubic-bezier(.2,.8,.2,1) both;max-width:1280px;margin:0 auto">
    <h1 style="margin:0;font-size:20px;line-height:28px;font-weight:600;color:var(--ink)">作业队列</h1>
    <p style="margin:4px 0 24px;font-size:14px;line-height:20px;color:var(--body)">状态来自作业状态机,不解析 stdout;排队原因与退出信息一并保留。</p>
    <section style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);overflow-x:auto;overflow-y:hidden">
      <div style="display:grid;grid-template-columns:130px 1fr 120px 90px 100px 92px 68px;gap:12px;padding:0 16px;height:36px;align-items:center;background:var(--surface-2);border-bottom:1px solid var(--hairline)">
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">JOB_ID</span>
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">WORKFLOW</span>
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">STATUS</span>
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute);text-align:right">PROGRESS</span>
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute);text-align:right">STARTED</span>
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute);text-align:right">DURATION</span>
        <span></span>
      </div>
      <div v-if="!ui.jobRows.length"
        style="height:96px;display:flex;align-items:center;justify-content:center;font-family:var(--font-mono);font-size:12px;color:var(--mute)">还没有作业 · 提交训练或缓存后出现在这里</div>
      <div v-for="j in ui.jobRows" :key="j.id" class="hv-row"
        style="display:grid;grid-template-columns:130px 1fr 120px 90px 100px 92px 68px;gap:12px;padding:0 16px;min-height:44px;align-items:center;border-bottom:1px solid var(--hairline);transition:background .12s ease">
        <span style="font-family:var(--font-mono);font-size:13px;color:var(--ink)">{{ j.id }}</span>
        <div style="min-width:0">
          <div style="font-family:var(--font-mono);font-size:13px;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ j.workflow }}</div>
          <div style="font-size:12px;line-height:16px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ j.note }}</div>
        </div>
        <div><StatusBadge :status="j.status" /></div>
        <span style="font-family:var(--font-mono);font-size:13px;color:var(--body);text-align:right;font-variant-numeric:tabular-nums">{{ j.progress }}</span>
        <span style="font-family:var(--font-mono);font-size:13px;color:var(--body);text-align:right;font-variant-numeric:tabular-nums">{{ j.started }}</span>
        <span style="font-family:var(--font-mono);font-size:13px;color:var(--body);text-align:right;font-variant-numeric:tabular-nums">{{ j.duration }}</span>
        <button @click="j.act" class="hv-line"
          style="height:28px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-size:12px;color:var(--body);cursor:pointer;transition:border-color .14s ease,color .14s ease">{{ j.actLabel }}</button>
      </div>
    </section>
  </div>
</template>
