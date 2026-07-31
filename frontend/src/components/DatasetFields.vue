<script setup>
// 多数据集编辑器:每组独立目录/分辨率/批大小/重复次数/caption 扩展名,可增删。
// dataset_config 留空时,提交训练/缓存会按这里的内容自动生成 [[datasets]] TOML。
import { store, addDataset, removeDataset, setDatasetField } from '../store.js'

const ROWS = [
  { key: 'image_directory', label: '图片目录', flag: 'image_directory', type: 'path', hint: '图片与同名标注文件放在这里' },
  { key: 'resolution_w', label: '分辨率 宽', flag: 'resolution', type: 'num' },
  { key: 'resolution_h', label: '分辨率 高', flag: 'resolution', type: 'num' },
  { key: 'batch_size', label: '批大小', flag: 'batch_size', type: 'num' },
  { key: 'num_repeats', label: '重复次数', flag: 'num_repeats', type: 'num' },
  { key: 'caption_extension', label: 'caption 扩展名', flag: 'caption_extension', type: 'text' },
]
</script>

<template>
  <div style="display:flex;flex-direction:column;gap:16px;margin-top:16px">
    <div v-for="(d, i) in store.datasets" :key="i"
      style="border:1px solid var(--hairline);border-radius:8px;padding:14px 16px;animation:cardIn .2s ease both">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
        <span style="font-family:var(--font-mono);font-size:12px;letter-spacing:.5px;color:var(--mute)">DATASET {{ i + 1 }}</span>
        <span v-if="d.image_directory" style="width:6px;height:6px;border-radius:50%;background:var(--accent)"></span>
        <span v-else style="font-family:var(--font-mono);font-size:11px;color:var(--mute)">未填目录 · 不会提交</span>
        <span style="flex:1"></span>
        <button v-if="store.datasets.length > 1" @click="removeDataset(i)" class="hv-line"
          style="height:26px;padding:0 10px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-size:12px;color:var(--body);cursor:pointer">移除</button>
      </div>
      <div style="display:flex;flex-direction:column;gap:12px">
        <div v-for="r in ROWS" :key="r.key" style="display:grid;grid-template-columns:200px minmax(0,1fr);gap:16px;align-items:center">
          <div>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <span style="font-size:13px;line-height:18px;font-weight:500;color:var(--ink)">{{ r.label }}</span>
              <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute)">{{ r.flag }}</span>
            </div>
            <div v-if="r.hint" style="font-size:11px;line-height:14px;color:var(--mute);margin-top:2px">{{ r.hint }}</div>
          </div>
          <input v-if="r.type === 'path'" :value="d[r.key]" @input="setDatasetField(i, r.key, $event.target.value)"
            style="width:100%;height:34px;padding:0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:13px;color:var(--ink)" />
          <input v-else-if="r.type === 'num'" :value="d[r.key]" @input="setDatasetField(i, r.key, $event.target.value)"
            style="width:132px;height:34px;padding:0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:13px;text-align:right;font-variant-numeric:tabular-nums;color:var(--ink)" />
          <input v-else :value="d[r.key]" @input="setDatasetField(i, r.key, $event.target.value)"
            style="width:100%;max-width:200px;height:34px;padding:0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:13px;color:var(--ink)" />
        </div>
      </div>
    </div>
    <button @click="addDataset" class="hv-line"
      style="height:32px;padding:0 12px;display:inline-flex;align-items:center;gap:6px;align-self:flex-start;background:transparent;border:1px dashed var(--hairline);border-radius:6px;font-size:13px;font-weight:500;color:var(--body);cursor:pointer">
      <span style="font-family:var(--font-mono)">+</span><span>添加数据集</span>
    </button>
  </div>
</template>
