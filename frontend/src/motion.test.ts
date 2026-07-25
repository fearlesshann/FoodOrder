import { describe, expect, it } from 'vitest'
// @ts-expect-error Vitest runs in Node; the app intentionally does not ship Node type declarations.
import { readFileSync } from 'node:fs'

const app = readFileSync('src/App.vue', 'utf8')
const selectedView = readFileSync('src/components/SelectedView.vue', 'utf8')

describe('V30 primary dock timing', () => {
  it('mounts the next page immediately and avoids a nested dock entrance', () => {
    expect(app).toContain('<Transition name="page">')
    expect(app).not.toContain('<Transition name="page" mode="out-in">')
    expect(selectedView).not.toContain('<Transition name="dock">')
  })
})
