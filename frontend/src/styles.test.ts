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
