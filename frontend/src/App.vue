<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { getCatalog, getCategories, getMenu, liveUrl, saveNote, selectDish, unselectDish } from './api'
import AdminView from './components/AdminView.vue'
import MenuView from './components/MenuView.vue'
import SelectedView from './components/SelectedView.vue'
import type { CatalogDish, Category, LiveEvent, Selection } from './types'

const catalog = ref<CatalogDish[]>([])
const categories = ref<Category[]>([])
const selections = ref<Selection[]>([])
const loading = ref(true)
const error = ref('')
const connection = ref<'offline' | 'connecting' | 'online'>('offline')
const adminMode = ref(window.location.hash === '#kitchen')
const surface = ref<'selected' | 'catalog'>('selected')
let socket: WebSocket | null = null
let reconnectTimer: number | null = null
let secretClicks = 0
let secretReset: number | null = null

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [nextCatalog, nextCategories, menu] = await Promise.all([getCatalog(), getCategories(), getMenu()])
    catalog.value = nextCatalog
    categories.value = nextCategories
    selections.value = menu.selections
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '菜单加载失败'
  } finally {
    loading.value = false
  }
}

function upsertSelection(selection: Selection) {
  const index = selections.value.findIndex((item) => item.id === selection.id)
  if (index === -1) selections.value.push(selection)
  else selections.value[index] = selection
}

function connectLive() {
  socket?.close()
  connection.value = 'connecting'
  socket = new WebSocket(liveUrl())
  socket.onmessage = (message) => {
    const event = JSON.parse(message.data) as LiveEvent
    if (event.type === 'connected') connection.value = 'online'
    if (event.type === 'catalog.changed') void loadData()
    if (event.type === 'selection.created' || event.type === 'selection.updated') upsertSelection(event.selection)
    if (event.type === 'selection.deleted') selections.value = selections.value.filter((item) => item.id !== event.selection_id)
  }
  socket.onerror = () => socket?.close()
  socket.onclose = () => {
    connection.value = 'offline'
    reconnectTimer = window.setTimeout(connectLive, 2400)
  }
}

async function toggleDish(dish: CatalogDish, selected?: Selection) {
  error.value = ''
  try {
    if (selected) {
      selections.value = selections.value.filter((item) => item.id !== selected.id)
      await unselectDish(selected.id)
    } else {
      upsertSelection(await selectDish(dish.id))
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '操作失败'
    await loadData()
  }
}

async function updateNote(selection: Selection, note: string) {
  try {
    upsertSelection(await saveNote(selection.id, note))
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '备注保存失败'
  }
}

function secretTap() {
  secretClicks += 1
  if (secretReset !== null) window.clearTimeout(secretReset)
  if (secretClicks >= 5) {
    secretClicks = 0
    window.location.hash = 'kitchen'
    adminMode.value = true
    return
  }
  secretReset = window.setTimeout(() => { secretClicks = 0 }, 1800)
}

function leaveAdmin() {
  history.replaceState(null, '', window.location.pathname + window.location.search)
  adminMode.value = false
  void loadData()
}

onMounted(() => { void loadData(); connectLive() })
onBeforeUnmount(() => {
  socket?.close()
  if (reconnectTimer !== null) window.clearTimeout(reconnectTimer)
  if (secretReset !== null) window.clearTimeout(secretReset)
})
</script>

<template>
  <Transition name="page">
    <AdminView v-if="adminMode" key="admin" :catalog="catalog" :categories="categories" @back="leaveAdmin" @refresh="loadData" />
    <MenuView
      v-else-if="surface === 'catalog'"
      key="catalog"
      :catalog="catalog"
      :categories="categories"
      :selections="selections"
      :loading="loading"
      :error="error"
      :connection="connection"
      @toggle="toggleDish"
      @back="surface = 'selected'"
      @retry="loadData"
    />
    <SelectedView
      v-else
      key="selected"
      :selections="selections"
      :loading="loading"
      :error="error"
      :connection="connection"
      @secret-tap="secretTap"
      @open-menu="surface = 'catalog'"
      @remove="toggleDish($event.dish, $event)"
      @save-note="updateNote"
      @retry="loadData"
    />
  </Transition>
</template>
