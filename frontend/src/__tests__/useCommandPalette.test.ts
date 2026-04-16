/**
 * Sprint 652: useCommandPalette hook test — verifies the thin context
 * passthrough (isOpen, openPalette, closePalette) and the error when
 * consumed outside the provider.
 */
import { renderHook } from '@testing-library/react'
import { useCommandPalette } from '@/hooks/useCommandPalette'

const mockIsOpen = jest.fn()
const mockOpen = jest.fn()
const mockClose = jest.fn()
const mockUseCommandPaletteContext = jest.fn()

jest.mock('@/contexts/CommandPaletteContext', () => ({
  useCommandPaletteContext: () => mockUseCommandPaletteContext(),
}))

describe('useCommandPalette', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockIsOpen.mockReturnValue(false)
    mockUseCommandPaletteContext.mockReturnValue({
      isOpen: false,
      openPalette: mockOpen,
      closePalette: mockClose,
      // intentionally extra fields the thin hook should NOT re-expose
      registerCommands: jest.fn(),
      unregisterCommands: jest.fn(),
      getAllCommands: jest.fn(),
      recordRecentCommand: jest.fn(),
      recentIds: [],
    })
  })

  it('re-exposes only the minimal surface (isOpen + open + close)', () => {
    const { result } = renderHook(() => useCommandPalette())
    expect(Object.keys(result.current).sort()).toEqual(['closePalette', 'isOpen', 'openPalette'])
  })

  it('forwards openPalette calls to context', () => {
    const { result } = renderHook(() => useCommandPalette())
    result.current.openPalette('button')
    expect(mockOpen).toHaveBeenCalledWith('button')
  })

  it('forwards closePalette calls to context', () => {
    const { result } = renderHook(() => useCommandPalette())
    result.current.closePalette()
    expect(mockClose).toHaveBeenCalled()
  })

  it('reflects the context isOpen flag', () => {
    mockUseCommandPaletteContext.mockReturnValue({
      isOpen: true,
      openPalette: mockOpen,
      closePalette: mockClose,
      registerCommands: jest.fn(),
      unregisterCommands: jest.fn(),
      getAllCommands: jest.fn(),
      recordRecentCommand: jest.fn(),
      recentIds: [],
    })
    const { result } = renderHook(() => useCommandPalette())
    expect(result.current.isOpen).toBe(true)
  })
})
