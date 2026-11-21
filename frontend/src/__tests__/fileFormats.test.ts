/**
 * Sprint 890 (CEO brief 15B): accepted types, labels and limits are derived from the
 * backend's GET /upload/capabilities response; DEFAULT_UPLOAD_CAPABILITIES mirrors the
 * backend defaults (100 MiB, 500,000 rows, 5 bulk files, ODS off).
 */
import {
  DEFAULT_UPLOAD_CAPABILITIES,
  acceptString,
  fileTooLargeMessage,
  formatsLabel,
  getUploadCapabilities,
  isAcceptedFileType,
  setUploadCapabilities,
  sizeLimitLabel,
  type UploadCapabilities,
} from '@/utils/fileFormats'

const makeFile = (name: string, type = ''): File => new File([''], name, { type })

const withOds: UploadCapabilities = {
  ...DEFAULT_UPLOAD_CAPABILITIES,
  formats: [
    ...DEFAULT_UPLOAD_CAPABILITIES.formats,
    { format: 'ods', label: 'ODS (.ods)', extensions: ['.ods'], mime_types: ['application/vnd.oasis.opendocument.spreadsheet'] },
  ],
}

afterEach(() => setUploadCapabilities(DEFAULT_UPLOAD_CAPABILITIES))

describe('defaults mirror the backend', () => {
  it('100 MB, 500,000 rows, 5 bulk files', () => {
    expect(DEFAULT_UPLOAD_CAPABILITIES.max_file_size_bytes).toBe(100 * 1024 * 1024)
    expect(sizeLimitLabel(DEFAULT_UPLOAD_CAPABILITIES)).toBe('100 MB')
    expect(DEFAULT_UPLOAD_CAPABILITIES.max_rows).toBe(500_000)
    expect(DEFAULT_UPLOAD_CAPABILITIES.bulk_max_files).toBe(5)
  })

  it('ODS is off by default; DOCX is on', () => {
    const accept = acceptString(DEFAULT_UPLOAD_CAPABILITIES)
    expect(accept).not.toContain('.ods')
    expect(accept).toContain('.docx')
    expect(accept.split(',')).toHaveLength(10)
  })
})

describe('a disabled format', () => {
  it('is refused by the client-side check', () => {
    expect(isAcceptedFileType(makeFile('sheet.ods'))).toBe(false)
    expect(isAcceptedFileType(makeFile('sheet.ods'), withOds)).toBe(true)
  })

  it('is left out of the picker and the label until the backend enables it', () => {
    expect(formatsLabel()).not.toContain('ODS')
    setUploadCapabilities(withOds)
    expect(getUploadCapabilities()).toBe(withOds)
    expect(acceptString()).toContain('.ods')
    expect(formatsLabel()).toContain('ODS')
  })
})

describe('isAcceptedFileType', () => {
  it('decides by extension, whatever the browser reports as MIME type', () => {
    expect(isAcceptedFileType(makeFile('data.CSV', ''))).toBe(true)
    expect(isAcceptedFileType(makeFile('report.xlsx', 'application/octet-stream'))).toBe(true)
    expect(isAcceptedFileType(makeFile('notes.dat', 'text/plain'))).toBe(false)
    expect(isAcceptedFileType(makeFile('noextension', 'text/csv'))).toBe(false)
  })
})

describe('messages follow the served limit', () => {
  it('too-large message names the limit', () => {
    expect(fileTooLargeMessage()).toContain('100 MB')
    setUploadCapabilities({ ...DEFAULT_UPLOAD_CAPABILITIES, max_file_size_mb: 25 })
    expect(fileTooLargeMessage()).toContain('25 MB')
  })
})
