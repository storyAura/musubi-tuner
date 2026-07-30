<script setup>
// 设置:平台 Token(HuggingFace / 魔搭)、下载线路等。
// Token 明文只保存在训练机 backend/.runtime/settings.json(不进 git),
// API 只回传脱敏状态;作业进程通过环境变量使用,不进 argv 与日志。
import { computed, ref } from 'vue'
import { store, demo, saveSettings, loadSettings } from '../store.js'

const hfInput = ref('')
const msInput = ref('')

const connected = computed(() => demo.demoMode || store.settings.loaded)

const ROUTES = [
  { v: 'auto', label: '自动(推荐)', hint: '并行实测三条线路速度,谁快用谁;失败自动回退到次快' },
  { v: 'hf', label: '仅 HF 直连', hint: '有代理/海外网络时最快;gated 模型需 Token' },
  { v: 'mirror', label: '仅 hf-mirror', hint: '国内直连镜像;不能绕过 gated 授权' },
  { v: 'modelscope', label: '仅魔搭', hint: '国内直连;多数 gated 模型免授权' },
]

async function saveTokens() {
  const patch = {}
  if (hfInput.value.trim()) patch.hf_token = hfInput.value.trim()
  if (msInput.value.trim()) patch.modelscope_token = msInput.value.trim()
  if (!Object.keys(patch).length) return
  if (await saveSettings(patch)) { hfInput.value = ''; msInput.value = '' }
}

function clearToken(key) { saveSettings({ [key]: '' }) }
function setRoute(v) { saveSettings({ download_route: v }) }
</script>

<template>
  <div data-screen-label="设置" style="animation:pageIn .24s cubic-bezier(.2,.8,.2,1) both;max-width:1280px;margin:0 auto">
    <h1 style="margin:0;font-size:20px;line-height:28px;font-weight:600;color:var(--ink)">设置</h1>
    <p style="margin:4px 0 24px;font-size:14px;line-height:20px;color:var(--body)">Token 明文只保存在训练机本地(backend/.runtime/settings.json),界面与日志一律脱敏。</p>

    <section v-if="!connected"
      style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);padding:24px;text-align:center;font-family:var(--font-mono);font-size:12px;color:var(--mute)">
      后端未连接 · 启动后端后可读写设置
    </section>

    <div v-else style="display:flex;flex-direction:column;gap:32px;max-width:760px">

      <section style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);padding:20px 24px 24px">
        <div style="font-family:var(--font-mono);font-size:12px;line-height:16px;letter-spacing:.5px;color:var(--mute)">TOKENS</div>
        <h2 style="margin:6px 0 0;font-size:16px;line-height:24px;font-weight:600;color:var(--ink)">平台 Token</h2>
        <p style="margin:6px 0 16px;font-size:12px;line-height:16px;color:var(--mute)">配置后作业进程经环境变量使用:HF Token 可下载 gated 模型(FLUX/Krea-2 官方仓库等);魔搭 Token 备将来受限模型使用。</p>

        <div style="display:flex;flex-direction:column;gap:16px">
          <div style="display:grid;grid-template-columns:224px minmax(0,1fr);gap:16px;align-items:start">
            <div style="padding-top:8px">
              <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                <span style="font-size:14px;line-height:20px;font-weight:500;color:var(--ink)">HuggingFace Token</span>
                <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute)">HF_TOKEN</span>
              </div>
              <div style="font-size:12px;line-height:16px;color:var(--mute);margin-top:2px">
                <span v-if="store.settings.hf_token_set" style="color:var(--accent)">已设置 {{ store.settings.hf_token_hint }}</span>
                <span v-else>未设置</span>
              </div>
            </div>
            <div style="display:flex;gap:8px;align-items:center;min-width:0">
              <input v-model="hfInput" type="password" placeholder="hf_xxxxxxxx(留空则不修改)"
                style="flex:1;max-width:360px;height:36px;padding:0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:13px;color:var(--ink)" />
              <button v-if="store.settings.hf_token_set" @click="clearToken('hf_token')" class="hv-line"
                style="height:32px;padding:0 10px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-size:12px;color:var(--body);white-space:nowrap;cursor:pointer">清除</button>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:224px minmax(0,1fr);gap:16px;align-items:start">
            <div style="padding-top:8px">
              <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                <span style="font-size:14px;line-height:20px;font-weight:500;color:var(--ink)">魔搭 Token</span>
                <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute)">MODELSCOPE_API_TOKEN</span>
              </div>
              <div style="font-size:12px;line-height:16px;color:var(--mute);margin-top:2px">
                <span v-if="store.settings.modelscope_token_set" style="color:var(--accent)">已设置 {{ store.settings.modelscope_token_hint }}</span>
                <span v-else>未设置(多数模型匿名即可下载)</span>
              </div>
            </div>
            <div style="display:flex;gap:8px;align-items:center;min-width:0">
              <input v-model="msInput" type="password" placeholder="留空则不修改"
                style="flex:1;max-width:360px;height:36px;padding:0 10px;background:var(--surface);border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:13px;color:var(--ink)" />
              <button v-if="store.settings.modelscope_token_set" @click="clearToken('modelscope_token')" class="hv-line"
                style="height:32px;padding:0 10px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-size:12px;color:var(--body);white-space:nowrap;cursor:pointer">清除</button>
            </div>
          </div>
        </div>

        <button @click="saveTokens" :disabled="!hfInput.trim() && !msInput.trim()"
          :style="(!hfInput.trim() && !msInput.trim()) ? 'opacity:.4;cursor:not-allowed' : 'cursor:pointer'"
          class="hv-fade"
          style="margin-top:20px;height:36px;padding:0 16px;background:var(--primary);color:var(--on-primary);border:none;border-radius:6px;font-size:14px;font-weight:500;transition:opacity .14s ease">保存 Token</button>
      </section>

      <section style="background:var(--surface);border-radius:8px;box-shadow:var(--shadow-card);padding:20px 24px 24px">
        <div style="font-family:var(--font-mono);font-size:12px;line-height:16px;letter-spacing:.5px;color:var(--mute)">DOWNLOAD</div>
        <h2 style="margin:6px 0 0;font-size:16px;line-height:24px;font-weight:600;color:var(--ink)">下载线路</h2>
        <p style="margin:6px 0 16px;font-size:12px;line-height:16px;color:var(--mute)">对新提交的模型下载生效;每次尝试的线路在终端日志中如实可见。</p>
        <div style="display:flex;flex-direction:column;gap:8px">
          <button v-for="r in ROUTES" :key="r.v" @click="setRoute(r.v)"
            :style="store.settings.download_route === r.v
              ? 'border:1px solid var(--ink);background:var(--surface-2)'
              : 'border:1px solid var(--hairline);background:var(--surface)'"
            class="hv-border"
            style="display:flex;align-items:baseline;gap:12px;padding:10px 14px;border-radius:6px;cursor:pointer;text-align:left;transition:border-color .14s ease">
            <span style="width:14px;flex-shrink:0;font-family:var(--font-mono);font-size:13px;color:var(--accent)">{{ store.settings.download_route === r.v ? '●' : '' }}</span>
            <span style="font-size:14px;font-weight:500;color:var(--ink);white-space:nowrap">{{ r.label }}</span>
            <span style="font-size:12px;color:var(--mute)">{{ r.hint }}</span>
          </button>
        </div>
      </section>

      <section style="border:1px dashed var(--hairline);border-radius:8px;padding:14px 20px">
        <span style="font-family:var(--font-mono);font-size:12px;color:var(--mute)">更多设置项(采样默认值、并发策略、外部追踪等)将随功能加入此页。</span>
        <button @click="loadSettings" class="hv-line"
          style="margin-left:12px;height:26px;padding:0 8px;background:transparent;border:1px solid var(--hairline);border-radius:6px;font-family:var(--font-mono);font-size:11px;color:var(--body);cursor:pointer">重新读取</button>
      </section>
    </div>
  </div>
</template>
