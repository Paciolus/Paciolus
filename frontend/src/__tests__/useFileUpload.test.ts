/**
 * Sprint 235: useFileUpload hook tests
 */
import { renderHook, act } from '@testing-library/react'
import { useFileUpload } from '@/hooks/useFileUpload'

describe('useFileUpload', () => {
  const mockOnFileSelected = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('initializes with isDragging false', () => {
    const { result } = renderHook(() => useFileUpload(mockOnFileSelected))
    expect(result.current.isDragging).toBe(false)
  })

  it('provides a file input ref', () => {
    const { result } = renderHook(() => useFileUpload(mockOnFileSelected))
    expect(result.current.fileInputRef).toBeDefined()
    expect(result.current.fileInputRef.current).toBeNull()
  })

  it('handleDragOver sets isDragging to true', () => {
    const { result } = renderHook(() => useFileUpload(mockOnFileSelected))

    act(() => {
      result.current.handleDragOver({
        preventDefault: jest.fn(),
      } as unknown as React.DragEvent)
    })

    expect(result.current.isDragging).toBe(true)
  })

  it('handleDragLeave sets isDragging to false', () => {
    const { result } = renderHook(() => useFileUpload(mockOnFileSelected))

    act(() => {
      result.current.handleDragOver({ preventDefault: jest.fn() } as unknown as React.DragEvent)
    })
    expect(result.current.isDragging).toBe(true)

    act(() => {
      result.current.handleDragLeave({ preventDefault: jest.fn() } as unknown as React.DragEvent)
    })
    expect(result.current.isDragging).toBe(false)
  })

  it('handleDrop calls onFileSelected with dropped file', () => {
    const { result } = renderHook(() => useFileUpload(mockOnFileSelected))
    const file = new File(['test'], 'test.csv', { type: 'text/csv' })

    act(() => {
      result.current.handleDrop({
        preventDefault: jest.fn(),
        dataTransfer: { files: [file] },
      } as unknown as React.DragEvent)
    })

    expect(mockOnFileSelected).toHaveBeenCalledWith(file)
    expect(result.current.isDragging).toBe(false)
  })

  it('handleDrop does nothing when no files', () => {
    const { result } = renderHook(() => useFileUpload(mockOnFileSelected))

    act(() => {
      result.current.handleDrop({
        preventDefault: jest.fn(),
        dataTransfer: { files: [] },
      } as unknown as React.DragEvent)
    })

    expect(mockOnFileSelected).not.toHaveBeenCalled()
  })

  it('handleFileSelect calls onFileSelected with selected file', () => {
    const { result } = renderHook(() => useFileUpload(mockOnFileSelected))
    const file = new File(['data'], 'data.xlsx')

    act(() => {
      result.current.handleFileSelect({
        target: { files: [file] },
      } as unknown as React.ChangeEvent<HTMLInputElement>)
    })

    expect(mockOnFileSelected).toHaveBeenCalledWith(file)
  })

  it('handleFileSelect does nothing when no files', () => {
    const { result } = renderHook(() => useFileUpload(mockOnFileSelected))

    act(() => {
      result.current.handleFileSelect({
        target: { files: null },
      } as unknown as React.ChangeEvent<HTMLInputElement>)
    })

    expect(mockOnFileSelected).not.toHaveBeenCalled()
  })

  it('returns all expected properties', () => {
    const { result } = renderHook(() => useFileUpload(mockOnFileSelected))
    expect(result.current).toHaveProperty('isDragging')
    expect(result.current).toHaveProperty('fileInputRef')
    expect(result.current).toHaveProperty('handleDrop')
    expect(result.current).toHaveProperty('handleDragOver')
    expect(result.current).toHaveProperty('handleDragLeave')
    expect(result.current).toHaveProperty('handleFileSelect')
    expect(result.current).toHaveProperty('resetFileInput')
  })
})
