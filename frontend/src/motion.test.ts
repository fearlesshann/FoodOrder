import { describe, expect, it } from 'vitest'
// @ts-expect-error Vitest runs in Node; the app intentionally does not ship Node type declarations.
import { readFileSync } from 'node:fs'

const app = readFileSync('src/App.vue', 'utf8')
const selectedView = readFileSync('src/components/SelectedView.vue', 'utf8')
const menuView = readFileSync('src/components/MenuView.vue', 'utf8')
const styles = readFileSync('src/styles.css', 'utf8')

describe('V30 primary dock timing', () => {
  it('mounts the next page immediately and avoids a nested dock entrance', () => {
    expect(app).toContain('<Transition name="page">')
    expect(app).not.toContain('<Transition name="page" mode="out-in">')
    expect(selectedView).not.toContain('<Transition name="dock">')
  })

  it('V31/V32 keeps fixed docks outside page-root effects while preserving page entrance motion', () => {
    expect(selectedView).toMatch(/<Teleport to="body">\s*<button[^>]*class="open-menu-dock"/s)
    expect(menuView).toMatch(/<Teleport to="body">\s*<button[^>]*class="return-dock"/s)
    expect(styles).toMatch(/\.page-enter-active\s*\{/)
    expect(styles).toMatch(/\.page-enter-from\s*\{/)
  })
})
