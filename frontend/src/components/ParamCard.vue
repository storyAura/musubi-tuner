<script setup>
// 一张分组参数卡:头部点击折叠(grid-rows 过渡)、字段列表、高级参数二级折叠、
// 数据集卡附带缓存操作行(缓存 latents 走清理计划确认弹窗)。
import FieldRow from './FieldRow.vue'
import DatasetFields from './DatasetFields.vue'
import { planCleanup, cacheText } from '../store.js'

defineProps({ g: { type: Object, required: true } })
</script>

<template>
  <section style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);padding:20px 24px 24px;animation:cardIn .26s cubic-bezier(.2,.8,.2,1) both">
    <div @click="g.toggleCollapse" title="点击折叠/展开"
      style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;cursor:pointer;margin:-20px -24px 0;padding:20px 24px 0">
      <div style="min-width:0">
        <div style="font-family:var(--font-mono);font-size:12px;line-height:16px;letter-spacing:.5px;color:var(--mute)">{{ g.eyebrow }}</div>
        <h2 style="margin:6px 0 0;font-size:16px;line-height:24px;font-weight:600;color:var(--ink)">{{ g.title }}</h2>
        <p style="margin:6px 0 0;font-size:12px;line-height:16px;color:var(--mute)">{{ g.desc }}</p>
      </div>
      <span :style="g.caretStyle">▾</span>
    </div>
    <div :style="g.bodyWrapStyle">
      <div style="min-height:0;overflow:hidden;padding:0 24px">
        <div style="height:1px;background:var(--hairline);margin:16px -24px 16px"></div>
        <div style="display:flex;flex-direction:column;gap:16px">
          <FieldRow v-for="f in g.fields" :key="f.flag" :f="f" />
        </div>

        <DatasetFields v-if="g.custom === 'datasets'" />

        <div v-if="g.advOpen"
          style="margin-top:16px;padding-top:16px;border-top:1px dashed var(--hairline);display:flex;flex-direction:column;gap:16px;animation:rowIn .2s ease both">
          <FieldRow v-for="f in g.advFields" :key="f.flag" :f="f" />
        </div>

        <button v-if="g.hasAdv" @click="g.toggleAdv" class="hv-line"
          style="margin-top:16px;height:28px;padding:0 10px;display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:12px;color:var(--body);cursor:pointer;transition:border-color .14s ease,color .14s ease">
          <span>{{ g.advCaret }}</span><span>{{ g.advLabel }}</span>
        </button>

        <div v-if="g.hasCache"
          style="margin-top:20px;padding-top:16px;border-top:1px solid var(--hairline);display:flex;align-items:center;gap:8px;flex-wrap:wrap">
          <button @click="planCleanup" class="hv-border"
            style="height:32px;padding:0 12px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:13px;font-weight:500;color:var(--ink);white-space:nowrap;cursor:pointer;transition:border-color .14s ease">缓存 latents</button>
          <button @click="cacheText" class="hv-border"
            style="height:32px;padding:0 12px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:13px;font-weight:500;color:var(--ink);white-space:nowrap;cursor:pointer;transition:border-color .14s ease">缓存文本编码器</button>
        </div>
      </div>
    </div>
  </section>
</template>
