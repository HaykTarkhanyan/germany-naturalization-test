// Per-device settings in localStorage, separate from the study progress (not exported).
import { useSyncExternalStore } from 'react'
import { z } from 'zod'

const KEY = 'einbuergerungstest.settings.v1'
const SettingsSchema = z.strictObject({ showEnglish: z.boolean() })
export type Settings = z.infer<typeof SettingsSchema>
const DEFAULTS: Settings = { showEnglish: true }

let current: Settings | null = null
const listeners = new Set<() => void>()

function read(): Settings {
  const raw = localStorage.getItem(KEY)
  if (raw === null) return DEFAULTS
  let data: unknown
  try {
    data = JSON.parse(raw)
  } catch (err) {
    throw new Error(`Settings saved in this browser (localStorage "${KEY}") are not valid JSON: ${(err as Error).message}`)
  }
  const result = SettingsSchema.safeParse(data)
  if (!result.success) throw new Error(`Settings saved in this browser (localStorage "${KEY}") are invalid: ${result.error.issues[0]?.message}`)
  return result.data
}

function getSettings(): Settings {
  if (current === null) current = read()
  return current
}

export function useSettings(): Settings {
  return useSyncExternalStore(
    (l) => {
      listeners.add(l)
      return () => listeners.delete(l)
    },
    getSettings,
  )
}

export function updateSettings(change: Partial<Settings>): void {
  const next = { ...getSettings(), ...change }
  localStorage.setItem(KEY, JSON.stringify(next))
  current = next
  for (const l of listeners) l()
}
