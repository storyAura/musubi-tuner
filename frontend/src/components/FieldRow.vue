<script setup>
// 单个参数行:中文 label + mono 参数名徽章 + 按类型渲染的控件 + 校验错误。
// 9 种控件类型(path/text/num/secret/select/seg/area/slider/toggle)与原型一一对应,
// 普通字段与「高级参数」区共用本组件。
defineProps({ f: { type: Object, required: true } })
</script>

<template>
  <div style="display:grid;grid-template-columns:224px minmax(0,1fr);gap:16px;align-items:start">
    <div style="padding-top:8px">
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <span style="font-size:14px;line-height:20px;font-weight:500;color:var(--ink)">{{ f.label }}</span>
        <span style="font-family:var(--font-mono);font-size:12px;line-height:16px;color:var(--mute)">{{ f.flag }}</span>
      </div>
      <div v-if="f.hint" style="font-size:12px;line-height:16px;color:var(--mute);margin-top:2px">{{ f.hint }}</div>
    </div>
    <div style="min-width:0">
      <input v-if="f.isPath" :value="f.value" @input="f.onInput" :placeholder="f.ph"
        style="width:100%;height:36px;padding:0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:13px;color:var(--ink);transition:border-color .14s ease,box-shadow .14s ease" />

      <input v-else-if="f.isText" :value="f.value" @input="f.onInput" :placeholder="f.ph"
        style="width:100%;max-width:320px;height:36px;padding:0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:14px;color:var(--ink);transition:border-color .14s ease,box-shadow .14s ease" />

      <input v-else-if="f.isNum" :value="f.value" @input="f.onInput"
        style="width:148px;height:36px;padding:0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:13px;text-align:right;font-variant-numeric:tabular-nums;color:var(--ink);transition:border-color .14s ease,box-shadow .14s ease" />

      <input v-else-if="f.isSecret" :value="f.value" @input="f.onInput" type="password" placeholder="secret_ref"
        style="width:100%;max-width:320px;height:36px;padding:0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:13px;color:var(--ink);transition:border-color .14s ease,box-shadow .14s ease" />

      <div v-else-if="f.isSelect" style="position:relative;display:inline-block">
        <select :value="f.value" @change="f.onInput"
          style="appearance:none;-webkit-appearance:none;min-width:220px;height:36px;padding:0 30px 0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:13px;color:var(--ink);cursor:pointer;transition:border-color .14s ease,box-shadow .14s ease">
          <option v-for="o in f.options" :key="o.v" :value="o.v">{{ o.v }}</option>
        </select>
        <span style="position:absolute;right:10px;top:50%;transform:translateY(-50%);pointer-events:none;font-size:10px;color:var(--mute)">▾</span>
      </div>

      <div v-else-if="f.isSeg" style="display:inline-flex;gap:4px;padding:4px;background:var(--surface-2);border-radius:6px">
        <template v-for="o in f.segs" :key="o.label">
          <button v-if="o.active" @click="o.go"
            style="height:28px;padding:0 14px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:13px;font-weight:500;color:var(--ink);white-space:nowrap;cursor:pointer;box-shadow:var(--shadow-card);transition:background .14s ease,color .14s ease">{{ o.label }}</button>
          <button v-else @click="o.go" class="hv-ink"
            style="height:28px;padding:0 14px;background:transparent;border:1px solid transparent;border-radius:6px;font-size:13px;font-weight:400;color:var(--body);white-space:nowrap;cursor:pointer;transition:background .14s ease,color .14s ease">{{ o.label }}</button>
        </template>
      </div>

      <textarea v-else-if="f.isArea" :value="f.value" @input="f.onInput" rows="3" :placeholder="f.ph"
        style="width:100%;padding:8px 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-size:14px;line-height:20px;color:var(--ink);resize:vertical;transition:border-color .14s ease,box-shadow .14s ease"></textarea>

      <div v-else-if="f.isSlider" style="display:flex;align-items:center;gap:12px;height:36px">
        <input type="range" :value="f.value" @input="f.onInput" :min="f.min" :max="f.max" step="1"
          style="flex:1;max-width:260px;accent-color:var(--ink);height:4px" />
        <span style="font-family:var(--font-mono);font-size:13px;color:var(--ink);font-variant-numeric:tabular-nums;min-width:28px;text-align:right">{{ f.value }}</span>
        <span style="font-family:var(--font-mono);font-size:11px;color:var(--mute)">{{ f.max }}</span>
      </div>

      <button v-else-if="f.isOn" @click="f.onToggle"
        style="margin-top:8px;width:36px;height:20px;padding:0;position:relative;background:var(--ink);border:1px solid var(--ink);border-radius:6px;cursor:pointer;transition:background .16s ease,border-color .16s ease">
        <span style="position:absolute;top:2px;left:18px;width:14px;height:14px;border-radius:4px;background:var(--surface);transition:left .18s cubic-bezier(.2,.8,.2,1)"></span>
      </button>
      <button v-else-if="f.isOff" @click="f.onToggle"
        style="margin-top:8px;width:36px;height:20px;padding:0;position:relative;background:var(--surface-2);border:1px solid var(--hairline);border-radius:6px;cursor:pointer;transition:background .16s ease,border-color .16s ease">
        <span style="position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:4px;background:var(--hairline-strong);transition:left .18s cubic-bezier(.2,.8,.2,1)"></span>
      </button>

      <div v-if="f.error" style="font-size:12px;line-height:16px;color:var(--error);margin-top:6px;animation:rowIn .18s ease both">{{ f.error }}</div>
    </div>
  </div>
</template>
