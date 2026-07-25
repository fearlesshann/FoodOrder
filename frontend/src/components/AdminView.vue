<script setup lang="ts">
import { ref, watch } from 'vue'
import { createCategory, createDish, deleteCategory, deleteDish, mediaUrl, updateCategory, updateDish } from '../api'
import type { CatalogDish, Category } from '../types'

const props = defineProps<{ catalog: CatalogDish[]; categories: Category[] }>()
const emit = defineEmits<{ back: []; refresh: [] }>()
const newName = ref('')
const newImage = ref<File | null>(null)
const newCategoryId = ref<number | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const editingId = ref<number | null>(null)
const editingName = ref('')
const editingImage = ref<File | null>(null)
const editingCategoryId = ref<number | null>(null)
const categoryName = ref('')
const editingCategoryIdValue = ref<number | null>(null)
const editingCategoryName = ref('')
const busy = ref(false)
const message = ref('')
const error = ref('')

watch(() => props.categories, (categories) => {
  if (newCategoryId.value === null && categories.length) newCategoryId.value = categories[0].id
}, { immediate: true })

function form(name: string, categoryId: number, image?: File | null) {
  const data = new FormData()
  data.append('name', name.trim())
  data.append('category_id', String(categoryId))
  if (image) data.append('image', image)
  return data
}

async function add() {
  if (!newName.value.trim() || !newImage.value || newCategoryId.value === null || busy.value) return
  busy.value = true; error.value = ''; message.value = ''
  try {
    await createDish(form(newName.value, newCategoryId.value, newImage.value))
    newName.value = ''; newImage.value = null
    if (fileInput.value) fileInput.value.value = ''
    message.value = '菜品已加入菜单'
    emit('refresh')
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '新增失败' }
  finally { busy.value = false }
}

function edit(dish: CatalogDish) { editingId.value = dish.id; editingName.value = dish.name; editingImage.value = null; editingCategoryId.value = dish.category.id }

async function save(dish: CatalogDish) {
  if (!editingName.value.trim() || editingCategoryId.value === null || busy.value) return
  busy.value = true; error.value = ''; message.value = ''
  try {
    await updateDish(dish.id, form(editingName.value, editingCategoryId.value, editingImage.value))
    editingId.value = null; message.value = '修改已保存'; emit('refresh')
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '保存失败' }
  finally { busy.value = false }
}

async function remove(dish: CatalogDish) {
  if (!window.confirm(`确认删除“${dish.name}”？`)) return
  busy.value = true; error.value = ''; message.value = ''
  try { await deleteDish(dish.id); message.value = '菜品已删除'; emit('refresh') }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '删除失败' }
  finally { busy.value = false }
}

async function addCategory() {
  if (!categoryName.value.trim() || busy.value) return
  busy.value = true; error.value = ''; message.value = ''
  try { await createCategory(categoryName.value.trim()); categoryName.value = ''; message.value = '分类已添加'; emit('refresh') }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '分类新增失败' }
  finally { busy.value = false }
}

async function saveCategory(category: Category) {
  if (!editingCategoryName.value.trim() || busy.value) return
  busy.value = true; error.value = ''; message.value = ''
  try { await updateCategory(category.id, editingCategoryName.value.trim()); editingCategoryIdValue.value = null; message.value = '分类已更新'; emit('refresh') }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '分类修改失败' }
  finally { busy.value = false }
}

async function removeCategory(category: Category) {
  if (!window.confirm(`确认删除分类“${category.name}”？`)) return
  busy.value = true; error.value = ''; message.value = ''
  try { await deleteCategory(category.id); message.value = '分类已删除'; emit('refresh') }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '分类删除失败' }
  finally { busy.value = false }
}
</script>

<template>
  <main class="kitchen-page">
    <header class="kitchen-header">
      <button type="button" class="back-button" @click="emit('back')">← 返回菜单</button>
      <div><p>隐藏区域</p><h1>后厨工作台</h1></div>
      <span>{{ catalog.length }} 道菜</span>
    </header>

    <section class="category-station" aria-labelledby="category-title">
      <div class="category-station-heading"><span>分类</span><h2 id="category-title">菜品分类</h2><p>被菜品使用的分类不能删除</p></div>
      <div class="category-maintenance">
        <form class="category-create" @submit.prevent="addCategory"><label>新分类<input v-model="categoryName" maxlength="20" placeholder="例如：主食" /></label><button type="submit" :disabled="!categoryName.trim() || busy">添加</button></form>
        <div class="category-list">
          <div v-for="category in categories" :key="category.id" class="category-row">
            <template v-if="editingCategoryIdValue === category.id">
              <input v-model="editingCategoryName" maxlength="20" aria-label="分类名称" />
              <button type="button" @click="saveCategory(category)">保存</button>
              <button type="button" class="quiet" @click="editingCategoryIdValue = null">取消</button>
            </template>
            <template v-else>
              <strong>{{ category.name }}</strong><span>{{ catalog.filter(dish => dish.category.id === category.id).length }} 道菜</span>
              <button type="button" class="quiet" @click="editingCategoryIdValue = category.id; editingCategoryName = category.name">编辑</button>
              <button type="button" class="danger" @click="removeCategory(category)">删除</button>
            </template>
          </div>
        </div>
      </div>
    </section>

    <section class="create-station" aria-labelledby="create-title">
      <div><span>新菜</span><h2 id="create-title">加入菜单</h2></div>
      <form @submit.prevent="add">
        <label>菜名<input v-model="newName" maxlength="40" placeholder="输入菜名" /></label>
        <label>分类<select v-model="newCategoryId"><option v-for="category in categories" :key="category.id" :value="category.id">{{ category.name }}</option></select></label>
        <label>菜品图片<input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp" @change="newImage = ($event.target as HTMLInputElement).files?.[0] ?? null" /></label>
        <button type="submit" :disabled="!newName.trim() || !newImage || newCategoryId === null || busy">{{ busy ? '处理中…' : '添加菜品' }}</button>
      </form>
    </section>

    <p v-if="error" class="workbench-alert error" role="alert">{{ error }}</p>
    <p v-if="message" class="workbench-alert success" role="status">{{ message }}</p>

    <section class="dish-inventory" aria-labelledby="inventory-title">
      <div class="inventory-heading"><h2 id="inventory-title">现有菜品</h2><span>图片支持 JPG / PNG / WebP，最大 8MB</span></div>
      <div class="inventory-list">
        <article v-for="(dish, index) in catalog" :key="dish.id" class="inventory-row">
          <span class="inventory-index">{{ String(index + 1).padStart(2, '0') }}</span>
          <img :src="mediaUrl(dish.image_url)" :alt="dish.name" width="180" height="120" />
          <div v-if="editingId === dish.id" class="edit-fields">
            <label>菜名<input v-model="editingName" maxlength="40" /></label>
            <label>分类<select v-model="editingCategoryId"><option v-for="category in categories" :key="category.id" :value="category.id">{{ category.name }}</option></select></label>
            <label>更换图片（可选）<input type="file" accept="image/jpeg,image/png,image/webp" @change="editingImage = ($event.target as HTMLInputElement).files?.[0] ?? null" /></label>
          </div>
          <div v-else class="inventory-name"><strong>{{ dish.name }}</strong><span>{{ dish.category.name }} · ID {{ dish.id }}</span></div>
          <div class="row-actions">
            <template v-if="editingId === dish.id"><button type="button" @click="save(dish)">保存</button><button type="button" class="quiet" @click="editingId = null">取消</button></template>
            <template v-else><button type="button" class="quiet" @click="edit(dish)">编辑</button><button type="button" class="danger" @click="remove(dish)">删除</button></template>
          </div>
        </article>
      </div>
    </section>
  </main>
</template>
