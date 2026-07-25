<script setup lang="ts">
import { computed, ref } from 'vue'
import { mediaUrl } from '../api'
import { filterCatalog, selectionForDish } from '../menu'
import type { CatalogDish, Category, Selection } from '../types'

const props = defineProps<{
  catalog: CatalogDish[]
  categories: Category[]
  selections: Selection[]
  loading: boolean
  error: string
  connection: 'offline' | 'connecting' | 'online'
}>()
const emit = defineEmits<{
  toggle: [dish: CatalogDish, selection?: Selection]
  back: []
  retry: []
}>()

const search = ref('')
const categoryId = ref<number | null>(null)
const filtered = computed(() => filterCatalog(props.catalog, categoryId.value, search.value))

function selected(dishId: number) { return selectionForDish(props.selections, dishId) }
</script>

<template>
  <main class="menu-page catalog-page">
    <header class="catalog-header">
      <div><h1>叶主厨的私房菜单</h1><p>点一下图片，立即加入今晚菜单</p></div>
      <span>{{ selections.length }} 道已选</span>
    </header>

    <section class="catalog-tools" aria-label="搜索和分类筛选">
      <label class="search-box"><span aria-hidden="true">⌕</span><input v-model="search" type="search" placeholder="搜索菜名" /></label>
      <div class="category-tabs" role="group" aria-label="菜品分类">
        <button type="button" :class="{ active: categoryId === null }" @click="categoryId = null">全部</button>
        <button v-for="category in categories" :key="category.id" type="button" :class="{ active: categoryId === category.id }" @click="categoryId = category.id">{{ category.name }}</button>
      </div>
    </section>

    <div v-if="error" class="page-error" role="alert"><span>{{ error }}</span><button type="button" @click="emit('retry')">重试</button></div>
    <div v-if="loading" class="menu-loading" role="status"><div></div><p>正在翻开菜单…</p></div>
    <div v-else-if="!filtered.length" class="menu-empty"><strong>没有找到这道菜</strong><p>换个名字或分类试试。</p></div>

    <ol v-else class="catalog-list">
      <li v-for="(dish, index) in filtered" :key="dish.id" class="catalog-item" :class="{ selected: selected(dish.id) }">
        <button class="dish-select" type="button" :aria-pressed="Boolean(selected(dish.id))" @click="emit('toggle', dish, selected(dish.id))">
          <img :src="mediaUrl(dish.image_url)" :alt="dish.name" width="1536" height="1024" :loading="index > 1 ? 'lazy' : 'eager'" />
          <span class="photo-shade" aria-hidden="true"></span>
          <span class="dish-category">{{ dish.category.name }}</span>
          <span class="dish-caption"><span class="dish-index">{{ String(index + 1).padStart(2, '0') }}</span><strong>{{ dish.name }}</strong></span>
          <span
            class="image-stamp"
            :style="{
              opacity: selected(dish.id) ? '1' : '0',
              transform: selected(dish.id) ? 'rotate(-10deg) scale(1)' : 'rotate(-10deg) scale(1.35)',
            }"
            aria-hidden="true"
          >已选</span>
        </button>
      </li>
    </ol>

    <button class="return-dock" type="button" @click="emit('back')">
      <span>已选 <strong>{{ selections.length }}</strong> 道</span>
      <span>选好了</span>
    </button>
  </main>
</template>
