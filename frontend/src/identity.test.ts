import { beforeEach, describe, expect, it } from 'vitest'
import { loadIdentity, saveIdentity, validateIdentity } from './identity'

describe('identity', () => {
  beforeEach(() => localStorage.clear())

  it('persists a valid identity across visits', () => {
    saveIdentity({ familyCode: 'family-a', nickname: '小明' })
    expect(loadIdentity()).toEqual({ familyCode: 'family-a', nickname: '小明' })
  })

  it('rejects unsafe family codes and empty nicknames', () => {
    expect(validateIdentity({ familyCode: '!!bad!!', nickname: '小明' })).toContain('家庭码')
    expect(validateIdentity({ familyCode: 'family-a', nickname: '   ' })).toContain('昵称')
  })
})
