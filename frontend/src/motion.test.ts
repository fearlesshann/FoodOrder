import { describe, expect, it } from 'vitest'
// @ts-expect-error Vitest runs in Node; the app intentionally does not ship Node type declarations.
import { readFileSync } from 'node:fs'

const app = readFileSync('src/App.vue', 'utf8')
const selectedView = readFileSync('src/components/SelectedView.vue', 'utf8')
const styles = readFileSync('src/styles.css', 'utf8')

describe('V30 primary dock timing', () => {
  it('mounts the next page immediately and avoids a nested dock entrance', () => {
    expect(app).toContain('<Transition name="page">')
    expect(app).not.toContain('<Transition name="page" mode="out-in">')
    expect(selectedView).not.toContain('<Transition name="dock">')
  })

  it('V31 keeps incoming fixed docks outside page-root entrance effects', () => {
    expect(styles).not.toMatch(/\.page-enter-active\s*\{/)
    expect(styles).not.toMatch(/\.page-enter-from\s*\{/)
  })
})
