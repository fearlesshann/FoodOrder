import { mount, type VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import MenuView from './MenuView.vue'
import { CATALOG_PAGE_SIZE, CATALOG_PRELOAD_PX } from '../menu'
import type { CatalogDish, Category } from '../types'

const categories = [
  { id: 1, name: '荤菜', sort_order: 1, created_at: '', updated_at: '' },
  { id: 2, name: '素菜', sort_order: 2, created_at: '', updated_at: '' },
  { id: 3, name: '汤品', sort_order: 3, created_at: '', updated_at: '' },
  { id: 4, name: '主食', sort_order: 4, created_at: '', updated_at: '' },
] as Category[]

const categorySizes = [40, 30, 20, 15]

function dish(id: number): CatalogDish {
  let cursor = 0
  let categoryIndex = 0
  for (let index = 0; index < categorySizes.length; index += 1) {
    cursor += categorySizes[index]
    if (id <= cursor) {
      categoryIndex = index
      break
    }
  }
  const category = categories[categoryIndex]
  return {
    id,
    name: id === 7 ? '龙井虾仁' : `菜品${id}`,
    image_url: `/${id}.webp`,
    sort_order: id,
    category,
    created_at: '',
    updated_at: '',
  }
}

const catalog = Array.from({ length: 105 }, (_, index) => dish(index + 1))

class RecordingObserver {
  static latest: RecordingObserver | null = null
  readonly callback: IntersectionObserverCallback
  readonly options: IntersectionObserverInit | undefined
  constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
    this.callback = callback
    this.options = options
    RecordingObserver.latest = this
  }
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords(): IntersectionObserverEntry[] { return [] }
}

function mountView(list: CatalogDish[] = catalog) {
  return mount(MenuView, {
    attachTo: document.body,
    global: { stubs: { transition: false, TransitionGroup: false, 'transition-group': false } },
    props: { catalog: list, categories, selections: [], loading: false, error: '', connection: 'online' },
  })
}

function names(wrapper: VueWrapper) {
  return wrapper.findAll('.dish-select img').map((img) => img.attributes('alt'))
}

async function flush() {
  for (let step = 0; step < 6; step += 1) await nextTick()
}

async function intersect(isIntersecting = true) {
  const observer = RecordingObserver.latest
  if (!observer) throw new Error('missing observer')
  await observer.callback([{ isIntersecting } as IntersectionObserverEntry], observer as unknown as IntersectionObserver)
  await nextTick()
}

function placeSentinel(top: number) {
  const sentinel = document.querySelector('.catalog-sentinel')
  if (!sentinel) throw new Error('missing sentinel')
  vi.spyOn(sentinel, 'getBoundingClientRect').mockImplementation(() => ({
    x: 0,
    y: top,
    top,
    left: 0,
    right: 8,
    bottom: top + 1,
    width: 8,
    height: 1,
    toJSON() { return {} },
  }) as DOMRect)
}

let scrollTo: ReturnType<typeof vi.spyOn>
const frames: FrameRequestCallback[] = []

beforeEach(() => {
  RecordingObserver.latest = null
  frames.length = 0
  vi.stubGlobal('IntersectionObserver', RecordingObserver)
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => {
    frames.push(callback)
    return frames.length
  })
  vi.stubGlobal('cancelAnimationFrame', () => {})
  scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
})

async function flushMotion() {
  await flush()
  for (let pass = 0; pass < 6; pass += 1) {
    const batch = frames.splice(0, frames.length)
    batch.forEach((callback) => callback(0))
    await nextTick()
    if (!batch.length && frames.length === 0) break
  }
}

afterEach(() => {
  document.body.innerHTML = ''
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('MenuView scroll pagination', () => {
  it('mounts only the first page of a long photo list', async () => {
    const wrapper = mountView()
    await flush()
    const shown = names(wrapper)
    expect(CATALOG_PAGE_SIZE).toBeLessThan(catalog.length)
    expect(shown).toHaveLength(CATALOG_PAGE_SIZE)
    expect(shown[0]).toBe('菜品1')
    expect(shown).not.toContain('菜品105')
    expect(wrapper.find('ol.catalog-list').exists()).toBe(true)
    expect(wrapper.find('.dish-index').text()).toBe('01')
    const images = wrapper.findAll('.dish-select img')
    expect(images[0].attributes('loading')).toBe('eager')
    expect(images[1].attributes('loading')).toBe('eager')
    expect(images[2].attributes('loading')).toBe('lazy')
    expect(wrapper.get('.catalog-live-status').text()).toContain(`已显示 ${CATALOG_PAGE_SIZE} 道，共 105 道`)
    expect(RecordingObserver.latest?.options?.rootMargin).toBe(`0px 0px ${CATALOG_PRELOAD_PX}px 0px`)
    wrapper.unmount()
  })

  it('appends the next page when the list end enters the preload zone', async () => {
    const wrapper = mountView()
    await flush()
    await intersect(false)
    expect(names(wrapper)).toHaveLength(CATALOG_PAGE_SIZE)
    await intersect(true)
    const shown = names(wrapper)
    expect(shown).toHaveLength(CATALOG_PAGE_SIZE * 2)
    expect(shown.at(-1)).toBe(`菜品${CATALOG_PAGE_SIZE * 2}`)
    expect(wrapper.findAll('.dish-index').at(-1)?.text()).toBe(String(CATALOG_PAGE_SIZE * 2).padStart(2, '0'))
    expect(wrapper.findAll('.dish-select img').at(-1)?.attributes('loading')).toBe('lazy')
    wrapper.unmount()
  })

  it('keeps filling while the sentinel stays near the viewport, then stops', async () => {
    const wrapper = mountView()
    await flush()
    let checks = 0
    const sentinel = document.querySelector('.catalog-sentinel')
    if (!sentinel) throw new Error('missing sentinel')
    vi.spyOn(sentinel, 'getBoundingClientRect').mockImplementation(() => {
      checks += 1
      const top = checks <= 1 ? 100 : 4000
      return {
        x: 0, y: top, top, left: 0, right: 8, bottom: top + 1, width: 8, height: 1, toJSON() { return {} },
      } as DOMRect
    })
    await intersect(true)
    expect(names(wrapper)).toHaveLength(CATALOG_PAGE_SIZE * 3)
    wrapper.unmount()
  })

  it('mounts every remaining dish when the viewport still reaches the list end', async () => {
    const wrapper = mountView()
    await flush()
    placeSentinel(20)
    await intersect(true)
    expect(names(wrapper)).toHaveLength(catalog.length)
    expect(wrapper.get('.catalog-live-status').text()).toBe('已显示 105 道，共 105 道')
    wrapper.unmount()
  })

  it('returns to the first page when the category or search changes', async () => {
    const wrapper = mountView()
    await flush()
    scrollTo.mockClear()
    await intersect(true)
    expect(names(wrapper)).toHaveLength(CATALOG_PAGE_SIZE * 2)

    await wrapper.findAll('.category-tabs button')[2].trigger('click')
    await flush()
    const vegetables = names(wrapper)
    expect(vegetables).toHaveLength(CATALOG_PAGE_SIZE)
    expect(vegetables[0]).toBe('菜品41')
    expect(wrapper.findAll('.dish-category').every((node) => node.text() === '素菜')).toBe(true)
    expect(scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'auto' })

    await wrapper.findAll('.category-tabs button')[0].trigger('click')
    await flush()
    expect(names(wrapper)).toHaveLength(CATALOG_PAGE_SIZE)
    expect(names(wrapper)[0]).toBe('菜品1')

    await wrapper.get('input').setValue('龙井')
    await flush()
    expect(names(wrapper)).toEqual(['龙井虾仁'])
    expect(wrapper.find('.menu-empty').exists()).toBe(false)

    await wrapper.get('input').setValue('没有这道菜')
    await flushMotion()
    expect(wrapper.find('.menu-empty').exists()).toBe(true)
    expect(wrapper.find('.catalog-item').exists()).toBe(false)

    await wrapper.get('input').setValue('')
    await flushMotion()
    expect(names(wrapper)).toHaveLength(CATALOG_PAGE_SIZE)
    expect(names(wrapper)[0]).toBe('菜品1')
    expect(names(wrapper)).not.toContain('菜品105')
    wrapper.unmount()
  })

  it('renders the whole filtered list when visibility cannot be observed', async () => {
    vi.stubGlobal('IntersectionObserver', undefined)
    const wrapper = mountView()
    await flush()
    expect(names(wrapper)).toHaveLength(catalog.length)
    wrapper.unmount()
  })
})
