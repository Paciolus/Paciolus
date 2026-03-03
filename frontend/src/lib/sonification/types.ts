/**
 * Sonification Types
 *
 * Type definitions for the Web Audio API sonification engine.
 */

export type ToneName = 'uploadStart' | 'success' | 'error' | 'exportDone'

export interface ToneConfig {
  /** Oscillator frequency in Hz */
  frequency: number
  /** Tone duration in seconds */
  duration: number
  /** Oscillator waveform type */
  type: OscillatorType
  /** Optional second frequency for chord tones (e.g., export flourish) */
  frequency2?: number
}
