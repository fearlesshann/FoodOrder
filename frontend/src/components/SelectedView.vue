<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { mediaUrl } from '../api'
import { cleanNote } from '../menu'
import type { Selection } from '../types'

const props = defineProps<{
  selections: Selection[]
  loading: boolean
  error: string
  connection: 'offline' | 'connecting' | 'online'
}>()
const emit = defineEmits<{
  'secret-tap': []
  'open-menu': []
  remove: [selection: Selection]
  'save-note': [selection: Selection, note: string]
  retry: []
}>()
const noteDrafts = ref<Record<number, string>>({})
const editingNoteId = ref<number | null>(null)
const today = new Intl.DateTimeFormat('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' }).format(new Date())

function noteValue(selection: Selection) { return noteDrafts.value[selection.id] ?? selection.note }
function isEditingNote(selectionId: number) { return editingNoteId.value === selectionId }
function editNote(selection: Selection) {
  if (editingNoteId.value === selection.id) return
  closeActiveNote()
  noteDrafts.value[selection.id] = noteValue(selection)
  editingNoteId.value = selection.id
}
function save(selection: Selection) {
  const value = cleanNote(noteValue(selection))
  noteDrafts.value[selection.id] = value
  if (value !== selection.note) emit('save-note', selection, value)
  if (editingNoteId.value === selection.id) editingNoteId.value = null
}
function closeActiveNote() {
  if (editingNoteId.value === null) return
  const selection = props.selections.find((item) => item.id === editingNoteId.value)
  if (selection) save(selection)
  else editingNoteId.value = null
}

onMounted(() => window.addEventListener('scroll', closeActiveNote, { passive: true }))
onBeforeUnmount(() => window.removeEventListener('scroll', closeActiveNote))
</script>

<template>
  <main class="selected-page">
    <header class="selected-header">
      <button class="brand-mark" type="button" aria-label="小袁的专属食堂" @click="emit('secret-tap')">晚</button>
      <div><p>{{ today }}</p><h1>小袁的专属食堂</h1></div>
      <div class="live-status" :data-state="connection" role="status"><span></span>{{ connection === 'online' ? '实时同步' : connection === 'connecting' ? '正在连接' : '离线重试中' }}</div>
    </header>

    <div v-if="error" class="page-error selected-error" role="alert"><span>{{ error }}</span><button type="button" @click="emit('retry')">重试</button></div>
    <div v-if="loading" class="selected-loading" role="status">正在摆好今晚菜单…</div>
    <section v-else-if="!selections.length" class="selected-empty">
      <span aria-hidden="true">00</span><h2>今晚还没点菜</h2><p>去菜单看看，想吃什么就点什么。</p>
      <button type="button" @click="emit('open-menu')">去菜单点菜 →</button>
    </section>

    <section v-else class="selected-content" aria-label="小袁今晚已点菜品">
      <div class="selected-summary"><p>今晚一共</p><strong>{{ selections.length }}</strong><span>道菜</span></div>
      <div class="selected-grid">
        <article v-for="selection in selections" :key="selection.id" class="selected-card">
          <div class="selected-photo">
            <img :src="mediaUrl(selection.dish.image_url)" :alt="selection.dish.name" width="720" height="540" />
            <span>{{ selection.dish.category.name }}</span>
            <button type="button" :aria-label="`取消${selection.dish.name}`" @click="emit('remove', selection)">×</button>
          </div>
          <div class="selected-card-body">
            <h2>{{ selection.dish.name }}</h2>
            <div v-if="isEditingNote(selection.id)" class="note-editor">
              <label :for="`selected-note-${selection.id}`">特殊要求</label>
              <textarea
              :id="`selected-note-${selection.id}`"
              :value="noteValue(selection)"
              maxlength="120"
              rows="2"
              placeholder="少辣、不要香菜…"
              autofocus
              @input="noteDrafts[selection.id] = ($event.target as HTMLTextAreaElement).value"
              @blur="save(selection)"
              ></textarea>
            </div>
            <button v-else type="button" class="note-trigger" @click="editNote(selection)">
              <template v-if="noteValue(selection)"><span>备注</span><strong>{{ noteValue(selection) }}</strong></template>
              <template v-else><span aria-hidden="true">＋</span> 添加备注</template>
            </button>
          </div>
        </article>
      </div>
    </section>

    <button v-if="selections.length" class="open-menu-dock" type="button" @click="emit('open-menu')"><span>＋</span> 加菜</button>
  </main>
</template>
