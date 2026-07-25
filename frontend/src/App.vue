<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { addDish, getMenu, liveUrl, removeDish, renameDish } from './api'
import { loadIdentity, saveIdentity, validateIdentity } from './identity'
import type { Dish, Identity, LiveEvent } from './types'

const savedIdentity = loadIdentity()
const identity = ref<Identity>(savedIdentity ?? { familyCode: '', nickname: '' })
const showSetup = ref(!savedIdentity)
const setupError = ref('')
const dishes = ref<Dish[]>([])
const draft = ref('')
const editingId = ref<number | null>(null)
const editingName = ref('')
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const connection = ref<'offline' | 'connecting' | 'online'>('offline')
const composer = ref<HTMLInputElement | null>(null)
let socket: WebSocket | null = null
let reconnectTimer: number | null = null
let livePaused = false

const today = new Intl.DateTimeFormat('zh-CN', {
  month: 'long',
  day: 'numeric',
  weekday: 'long',
}).format(new Date())

const dishCount = computed(() => dishes.value.length)
const statusText = computed(() => {
  if (connection.value === 'online') return '实时同步'
  if (connection.value === 'connecting') return '正在连接'
  return '离线，正在重试'
})

function upsertDish(dish: Dish) {
  const index = dishes.value.findIndex((item) => item.id === dish.id)
  if (index === -1) dishes.value.push(dish)
  else dishes.value[index] = dish
}

async function loadMenu() {
  if (!identity.value.familyCode) return
  loading.value = true
  error.value = ''
  try {
    const menu = await getMenu(identity.value.familyCode)
    dishes.value = menu.dishes
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '菜单加载失败'
  } finally {
    loading.value = false
  }
}

function connectLive() {
  if (!identity.value.familyCode || livePaused) return
  socket?.close()
  connection.value = 'connecting'
  socket = new WebSocket(liveUrl(identity.value.familyCode))

  socket.onmessage = (message) => {
    const event = JSON.parse(message.data) as LiveEvent
    if (event.type === 'connected') connection.value = 'online'
    if (event.type === 'dish.created' || event.type === 'dish.updated') upsertDish(event.dish)
    if (event.type === 'dish.deleted') {
      dishes.value = dishes.value.filter((dish) => dish.id !== event.dish_id)
    }
  }
  socket.onerror = () => socket?.close()
  socket.onclose = () => {
    connection.value = 'offline'
    if (!livePaused) reconnectTimer = window.setTimeout(connectLive, 2400)
  }
}

async function startSession() {
  livePaused = false
  await loadMenu()
  connectLive()
  await nextTick()
  composer.value?.focus()
}

function confirmSetup() {
  identity.value = {
    familyCode: identity.value.familyCode.trim(),
    nickname: identity.value.nickname.trim(),
  }
  const validationError = validateIdentity(identity.value)
  if (validationError) {
    setupError.value = validationError
    return
  }
  setupError.value = ''
  saveIdentity(identity.value)
  showSetup.value = false
  void startSession()
}

async function submitDish() {
  const name = draft.value.trim()
  if (!name || saving.value) return
  if ([...name].length > 40) {
    error.value = '菜名最多 40 个字'
    return
  }
  saving.value = true
  error.value = ''
  try {
    const dish = await addDish(identity.value.familyCode, name, identity.value.nickname)
    upsertDish(dish)
    draft.value = ''
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '添加失败，输入已保留'
  } finally {
    saving.value = false
    composer.value?.focus()
  }
}

function beginEdit(dish: Dish) {
  editingId.value = dish.id
  editingName.value = dish.name
}

async function commitEdit(dish: Dish) {
  const name = editingName.value.trim()
  if (!name || name === dish.name) {
    editingId.value = null
    return
  }
  try {
    upsertDish(await renameDish(identity.value.familyCode, dish.id, name))
    editingId.value = null
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '修改失败'
  }
}

async function deleteDish(dish: Dish) {
  const previous = dishes.value
  dishes.value = dishes.value.filter((item) => item.id !== dish.id)
  try {
    await removeDish(identity.value.familyCode, dish.id)
  } catch (reason) {
    dishes.value = previous
    error.value = reason instanceof Error ? reason.message : '删除失败，已恢复'
  }
}

function changeIdentity() {
  livePaused = true
  showSetup.value = true
  socket?.close()
}

watch(showSetup, (open) => {
  if (open && reconnectTimer !== null) window.clearTimeout(reconnectTimer)
})

if (savedIdentity) void startSession()

onBeforeUnmount(() => {
  socket?.close()
  if (reconnectTimer !== null) window.clearTimeout(reconnectTimer)
})
</script>

<template>
  <main class="shell">
    <div class="ambient" aria-hidden="true"></div>

    <header class="topbar">
      <button class="identity-button" type="button" @click="changeIdentity">
        <span class="identity-mark" aria-hidden="true">晚</span>
        <span>{{ identity.familyCode || '今晚菜单' }}</span>
      </button>
      <div class="sync-state" :data-state="connection" role="status">
        <span class="sync-dot" aria-hidden="true"></span>
        {{ statusText }}
      </div>
    </header>

    <section class="hero" aria-labelledby="page-title">
      <div class="hero-copy">
        <p class="date-line">{{ today }}</p>
        <h1 id="page-title">今晚<br /><span>吃什么？</span></h1>
        <p class="hero-note">想到什么就点什么。<br />不用提交，随时可以改。</p>
      </div>

      <section class="ticket" aria-label="今晚菜单">
        <div class="ticket-heading">
          <div>
            <p>今晚菜单</p>
            <strong>{{ dishCount ? `${dishCount} 道菜` : '等你开席' }}</strong>
          </div>
          <span class="ticket-date">{{ today.split('星期')[0] }}</span>
        </div>

        <div v-if="loading" class="menu-message" role="status">正在摆好餐桌…</div>
        <div v-else-if="!dishes.length" class="empty-state">
          <span class="empty-number">00</span>
          <p>今晚还没点菜。<br />第一道，听你的。</p>
        </div>

        <TransitionGroup v-else name="dish" tag="ol" class="dish-list">
          <li v-for="(dish, index) in dishes" :key="dish.id" class="dish-row">
            <span class="dish-number">{{ String(index + 1).padStart(2, '0') }}</span>
            <div class="dish-main">
              <input
                v-if="editingId === dish.id"
                v-model="editingName"
                class="edit-input"
                maxlength="40"
                aria-label="修改菜名"
                @keyup.enter="commitEdit(dish)"
                @keyup.escape="editingId = null"
                @blur="commitEdit(dish)"
              />
              <button v-else class="dish-name" type="button" @click="beginEdit(dish)">
                {{ dish.name }}
              </button>
              <span class="ordered-by">{{ dish.ordered_by }} 点的</span>
            </div>
            <button class="delete-button" type="button" :aria-label="`删除${dish.name}`" @click="deleteDish(dish)">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M6 6l12 12M18 6L6 18" />
              </svg>
            </button>
          </li>
        </TransitionGroup>

        <form class="composer" @submit.prevent="submitDish">
          <label for="dish-name">我今晚想吃</label>
          <div class="composer-control">
            <input
              id="dish-name"
              ref="composer"
              v-model="draft"
              type="text"
              maxlength="40"
              autocomplete="off"
              enterkeyhint="send"
              placeholder="比如：糖醋排骨"
            />
            <button type="submit" :disabled="!draft.trim() || saving" aria-label="添加菜品">
              <span aria-hidden="true">{{ saving ? '···' : '＋' }}</span>
            </button>
          </div>
          <p v-if="error" class="error-message" role="alert">{{ error }}</p>
          <p v-else class="composer-hint">按回车添加 · 点击菜名修改</p>
        </form>
      </section>
    </section>

    <footer>
      <span>{{ identity.nickname || '家人' }}的今晚菜单</span>
      <span>所有修改自动同步</span>
    </footer>
  </main>

  <dialog :open="showSetup" class="setup-dialog" aria-labelledby="setup-title">
    <form class="setup-panel" @submit.prevent="confirmSetup">
      <div class="setup-mark" aria-hidden="true">晚</div>
      <p>第一次来</p>
      <h2 id="setup-title">先认个门，<br />再点今晚的菜。</h2>
      <label>
        家庭码
        <input v-model="identity.familyCode" maxlength="48" autocomplete="off" placeholder="例如：yehan-home" />
      </label>
      <label>
        你的昵称
        <input v-model="identity.nickname" maxlength="24" autocomplete="nickname" placeholder="家里人怎么叫你" />
      </label>
      <p v-if="setupError" class="setup-error" role="alert">{{ setupError }}</p>
      <button class="setup-submit" type="submit">进入今晚菜单 <span aria-hidden="true">→</span></button>
      <small>相同家庭码会进入同一份菜单</small>
    </form>
  </dialog>
</template>
