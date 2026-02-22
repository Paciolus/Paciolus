/**
 * Sonification Engine Tests — Sprint 407: Phase LVII
 */

const mockOscillator = {
  type: 'sine',
  frequency: { setValueAtTime: jest.fn() },
  connect: jest.fn(),
  start: jest.fn(),
  stop: jest.fn(),
}

const mockGain = {
  gain: {
    setValueAtTime: jest.fn(),
    linearRampToValueAtTime: jest.fn(),
    exponentialRampToValueAtTime: jest.fn(),
  },
  connect: jest.fn(),
}

const mockAudioContext = {
  currentTime: 0,
  state: 'running',
  destination: {},
  createOscillator: jest.fn(() => ({ ...mockOscillator })),
  createGain: jest.fn(() => ({
    ...mockGain,
    gain: {
      setValueAtTime: jest.fn(),
      linearRampToValueAtTime: jest.fn(),
      exponentialRampToValueAtTime: jest.fn(),
    },
  })),
  resume: jest.fn().mockResolvedValue(undefined),
}

// Mock AudioContext globally
Object.defineProperty(globalThis, 'AudioContext', {
  writable: true,
  value: jest.fn(() => mockAudioContext),
})

// Must import after mock
import { playTone, isMuted, setMuted } from '@/lib/sonification'

describe('sonification audioEngine', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    sessionStorage.clear()
  })

  it('creates an oscillator when playing a tone', () => {
    playTone('success')
    expect(mockAudioContext.createOscillator).toHaveBeenCalled()
    expect(mockAudioContext.createGain).toHaveBeenCalled()
  })

  it('does not play when muted', () => {
    setMuted(true)
    mockAudioContext.createOscillator.mockClear()
    playTone('success')
    expect(mockAudioContext.createOscillator).not.toHaveBeenCalled()
  })

  it('plays after unmuting', () => {
    setMuted(true)
    setMuted(false)
    playTone('success')
    expect(mockAudioContext.createOscillator).toHaveBeenCalled()
  })

  it('creates two oscillators for exportDone chord', () => {
    mockAudioContext.createOscillator.mockClear()
    playTone('exportDone')
    expect(mockAudioContext.createOscillator).toHaveBeenCalledTimes(2)
  })

  it('persists mute state in sessionStorage', () => {
    setMuted(true)
    expect(sessionStorage.getItem('paciolus_sonification_muted')).toBe('true')
    setMuted(false)
    expect(sessionStorage.getItem('paciolus_sonification_muted')).toBeNull()
  })

  it('isMuted reflects sessionStorage state', () => {
    expect(isMuted()).toBe(false)
    sessionStorage.setItem('paciolus_sonification_muted', 'true')
    expect(isMuted()).toBe(true)
  })
})
