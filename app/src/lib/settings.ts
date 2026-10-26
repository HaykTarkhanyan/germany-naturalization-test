// Per-device settings in localStorage, separate from the study progress (not exported).
import { useSyncExternalStore } from 'react'
import { z } from 'zod'

const KEY = 'einbuergerungstest.settings.v1'
export const LANGS = ['en', 'ru'] as const
/** Language of the explanations: lessons, the "why" after answers, video texts and videos (DECISIONS.md #25). */
export type Lang = (typeof LANGS)[number]
// videoLang (the name is historical: it first switched only the videos) has a default so settings saved before
// it existed still load. English by default (Hayk, 2026-10-26).
const SettingsSchema = z.strictObject({ showEnglish: z.boolean(), videoLang: z.enum(LANGS).default('en') })
export type Settings = z.infer<typeof SettingsSchema>
const DEFAULTS: Settings = { showEnglish: true, videoLang: 'en' }

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

function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function useSettings(): Settings {
  return useSyncExternalStore(subscribe, getSettings)
}

export function updateSettings(change: Partial<Settings>): void {
  const next = { ...read(), ...change } // what is stored now: another tab may have changed it
  localStorage.setItem(KEY, JSON.stringify(next))
  current = next
  for (const l of listeners) l()
}

// Another tab changed a setting: follow it.
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (e) => {
    if (e.key !== KEY && e.key !== null) return
    current = null
    for (const l of listeners) l()
  })
}
