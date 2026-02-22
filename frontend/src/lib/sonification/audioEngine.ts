/**
 * Audio Engine — Sprint 407: Phase LVII
 *
 * Singleton Web Audio API engine for data sonification.
 * Lazy AudioContext creation (respects browser autoplay policy).
 * Short oscillator tones with gain envelope. No audio files, no network.
 * Mute state persisted in sessionStorage (Zero-Storage compliant).
 */

import type { ToneName, ToneConfig } from './types'

const STORAGE_KEY = 'paciolus_sonification_muted'

const TONE_MAP: Record<ToneName, ToneConfig> = {
  uploadStart: { frequency: 440, duration: 0.15, type: 'sine' },       // A4
  success:     { frequency: 659.25, duration: 0.2, type: 'sine' },     // E5
  error:       { frequency: 329.63, duration: 0.25, type: 'triangle' }, // E4
  exportDone:  { frequency: 523.25, duration: 0.3, type: 'sine', frequency2: 659.25 }, // C5+E5
}

let audioCtx: AudioContext | null = null

function getContext(): AudioContext | null {
  if (typeof window === 'undefined') return null
  if (!audioCtx) {
    try {
      audioCtx = new AudioContext()
    } catch {
      return null
    }
  }
  return audioCtx
}

function playOscillator(ctx: AudioContext, freq: number, duration: number, type: OscillatorType): void {
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()

  osc.type = type
  osc.frequency.setValueAtTime(freq, ctx.currentTime)

  // Gentle gain envelope: quick attack, smooth release
  gain.gain.setValueAtTime(0, ctx.currentTime)
  gain.gain.linearRampToValueAtTime(0.08, ctx.currentTime + 0.02)
  gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration)

  osc.connect(gain)
  gain.connect(ctx.destination)

  osc.start(ctx.currentTime)
  osc.stop(ctx.currentTime + duration)
}

/**
 * Play a named tone. No-op if muted or AudioContext unavailable.
 */
export function playTone(name: ToneName): void {
  if (isMuted()) return

  const ctx = getContext()
  if (!ctx) return

  // Resume suspended context (browser autoplay policy)
  if (ctx.state === 'suspended') {
    ctx.resume().catch(() => {})
  }

  const config = TONE_MAP[name]
  if (!config) return

  playOscillator(ctx, config.frequency, config.duration, config.type)

  // Second frequency for chord tones
  if (config.frequency2) {
    playOscillator(ctx, config.frequency2, config.duration, config.type)
  }
}

/**
 * Check if sonification is muted.
 */
export function isMuted(): boolean {
  if (typeof window === 'undefined') return true
  return sessionStorage.getItem(STORAGE_KEY) === 'true'
}

/**
 * Set mute state (persisted in sessionStorage).
 */
export function setMuted(muted: boolean): void {
  if (typeof window === 'undefined') return
  if (muted) {
    sessionStorage.setItem(STORAGE_KEY, 'true')
  } else {
    sessionStorage.removeItem(STORAGE_KEY)
  }
}
