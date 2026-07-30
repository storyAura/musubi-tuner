<script setup>
import { computed } from 'vue'

const props = defineProps({ status: { type: String, required: true } })

// [文案, 前景色, 底色, 是否呼吸动画] — 语义色只有 蓝/红/琥珀,成功也是蓝(设计规范 §1.5)
const MAP = {
  idle: ['空闲', 'var(--mute)', 'transparent', false],
  queued: ['排队中', 'var(--mute)', 'var(--surface-2)', false],
  validating: ['校验中', 'var(--accent)', 'var(--accent-soft)', true],
  running: ['训练中', 'var(--accent)', 'var(--accent-soft)', true],
  cancelling: ['取消中', 'var(--warning)', 'var(--warning-soft)', true],
  cancelled: ['已取消', 'var(--mute)', 'var(--surface-2)', false],
  succeeded: ['已完成', 'var(--accent)', 'var(--accent-soft)', false],
  failed: ['失败', 'var(--error)', 'var(--error-soft)', false],
}

const m = computed(() => MAP[props.status] || MAP.idle)
</script>

<template>
  <span :style="{
    display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '2px 8px',
    borderRadius: '6px', background: m[2],
    border: m[2] === 'transparent' ? '1px solid var(--hairline)' : '1px solid transparent',
    fontFamily: 'var(--font-mono)', fontSize: '12px', lineHeight: '16px', color: m[1],
  }">
    <span :style="{
      width: '6px', height: '6px', borderRadius: '50%', background: m[1],
      animation: m[3] ? 'breathe 2s ease-in-out infinite' : 'none',
    }"></span>
    <span>{{ m[0] }}</span>
  </span>
</template>
