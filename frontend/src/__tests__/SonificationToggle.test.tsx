/**
 * SonificationToggle Tests — Sprint 407: Phase LVII
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'

// Mock dependencies
const mockToggleMute = jest.fn()
let mockEnabled = true
let mockIsMuted = false

jest.mock('@/hooks/useSonification', () => ({
  useSonification: () => ({
    isMuted: mockIsMuted,
    toggleMute: mockToggleMute,
    enabled: mockEnabled,
    playTone: jest.fn(),
  }),
}))

import { SonificationToggle } from '@/components/shared/SonificationToggle'

describe('SonificationToggle', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockEnabled = true
    mockIsMuted = false
  })

  it('renders speaker icon when enabled', () => {
    render(<SonificationToggle />)
    expect(screen.getByRole('button')).toBeInTheDocument()
    expect(screen.getByLabelText('Mute data sonification')).toBeInTheDocument()
  })

  it('returns null when feature is disabled', () => {
    mockEnabled = false
    const { container } = render(<SonificationToggle />)
    expect(container.firstChild).toBeNull()
  })

  it('calls toggleMute on click', () => {
    render(<SonificationToggle />)
    fireEvent.click(screen.getByRole('button'))
    expect(mockToggleMute).toHaveBeenCalledTimes(1)
  })

  it('shows muted label when muted', () => {
    mockIsMuted = true
    render(<SonificationToggle />)
    expect(screen.getByLabelText('Enable data sonification')).toBeInTheDocument()
  })

  it('shows active label when unmuted', () => {
    mockIsMuted = false
    render(<SonificationToggle />)
    expect(screen.getByLabelText('Mute data sonification')).toBeInTheDocument()
  })
})
