import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'
import SelectedView from './SelectedView.vue'
import type { Selection } from '../types'

const selections = [
  { id: 1, note: '', dish: { id: 1, name: '红烧肉', image_url: '/one.webp', category: { id: 1, name: '荤菜' } } },
  { id: 2, note: '', dish: { id: 2, name: '蒜蓉生菜', image_url: '/two.webp', category: { id: 2, name: '素菜' } } },
] as Selection[]

function mountView() {
  return mount(SelectedView, {
    attachTo: document.body,
    props: { selections, loading: false, error: '', connection: 'online' },
  })
}

describe('SelectedView V21 note editor', () => {
  it('keeps only one editor open when switching dishes', async () => {
    const wrapper = mountView()
    const triggers = wrapper.findAll('.note-trigger')
    await triggers[0].trigger('click')
    expect(wrapper.findAll('textarea')).toHaveLength(1)
    await wrapper.findAll('.note-trigger')[0].trigger('click')
    expect(wrapper.findAll('textarea')).toHaveLength(1)
    wrapper.unmount()
  })

  it('focuses on open, ignores keyboard scroll, then closes on a real swipe', async () => {
    const wrapper = mountView()
    await wrapper.findAll('.note-trigger')[0].trigger('click')
    await nextTick()
    expect(document.activeElement).toBe(wrapper.get('textarea').element)
    await wrapper.get('textarea').setValue('少辣')
    window.dispatchEvent(new Event('scroll'))
    await nextTick()
    expect(wrapper.find('textarea').exists()).toBe(true)
    window.dispatchEvent(new Event('touchmove'))
    window.dispatchEvent(new Event('scroll'))
    await nextTick()
    expect(wrapper.find('textarea').exists()).toBe(false)
    expect(wrapper.emitted('save-note')?.[0]).toEqual([selections[0], '少辣'])
    wrapper.unmount()
  })
})
