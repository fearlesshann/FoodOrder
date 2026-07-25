import type { Identity } from './types'

const STORAGE_KEY = 'dinner.identity'
const FAMILY_PATTERN = /^[A-Za-z0-9_-]{6,48}$/

export function loadIdentity(): Identity | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const value = JSON.parse(raw) as Partial<Identity>
    if (!value.familyCode || !value.nickname) return null
    return { familyCode: value.familyCode, nickname: value.nickname }
  } catch {
    return null
  }
}

export function saveIdentity(identity: Identity): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(identity))
}

export function validateIdentity(identity: Identity): string | null {
  if (!FAMILY_PATTERN.test(identity.familyCode)) {
    return '家庭码需为 6–48 位字母、数字、下划线或连字符'
  }
  const nicknameLength = [...identity.nickname.trim()].length
  if (nicknameLength < 1 || nicknameLength > 24) return '昵称需为 1–24 个字符'
  return null
}

