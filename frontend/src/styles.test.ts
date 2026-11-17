import { describe, expect, it } from 'vitest'
// @ts-expect-error Vitest runs in Node; the app intentionally does not ship Node type declarations.
import { readFileSync } from 'node:fs'

const styles = readFileSync('src/styles.css', 'utf8')

describe('V29 category filter transition stability', () => {
  it('removes leaving catalog items from document flow', () => {
    expect(styles).toMatch(/\.catalog-list\s*\{[^}]*position:\s*relative;/s)
    expect(styles).toMatch(/\.catalog-list-leave-active\s*\{[^}]*position:\s*absolute;/s)
    expect(styles).toMatch(/\.catalog-list-leave-active\s*\{[^}]*width:\s*100%;/s)
  })
})

describe('catalog scroll pagination motion', () => {
  it('keeps appended rows on a short fade and does not anchor scroll to the sentinel', () => {
    expect(styles).toMatch(/\.catalog-list-enter-from\s*\{[^}]*translateY\(6px\)/s)
    expect(styles).toMatch(/\.catalog-list-enter-active\s*\{[^}]*220ms/s)
    expect(styles).toMatch(/\.catalog-sentinel\s*\{[^}]*overflow-anchor:\s*none;/s)
    expect(styles).toMatch(/\.catalog-list\s*\{[^}]*overflow-anchor:\s*none;/s)
  })
})
