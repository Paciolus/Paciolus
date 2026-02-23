import {
  ACCEPTED_FILE_EXTENSIONS,
  ACCEPTED_FILE_EXTENSIONS_STRING,
  ACCEPTED_FORMATS_LABEL,
  ACCEPTED_MIME_TYPES,
  isAcceptedFileType,
} from '@/utils/fileFormats'

describe('fileFormats constants', () => {
  it('ACCEPTED_FILE_EXTENSIONS has 3 entries', () => {
    expect(ACCEPTED_FILE_EXTENSIONS).toEqual(['.csv', '.xlsx', '.xls'])
  })

  it('ACCEPTED_FILE_EXTENSIONS_STRING matches HTML accept format', () => {
    expect(ACCEPTED_FILE_EXTENSIONS_STRING).toBe('.csv,.xlsx,.xls')
  })

  it('ACCEPTED_MIME_TYPES includes 5 types', () => {
    expect(ACCEPTED_MIME_TYPES).toHaveLength(5)
    expect(ACCEPTED_MIME_TYPES).toContain('text/csv')
    expect(ACCEPTED_MIME_TYPES).toContain('application/vnd.ms-excel')
  })

  it('ACCEPTED_FORMATS_LABEL is human-readable', () => {
    expect(ACCEPTED_FORMATS_LABEL).toContain('CSV')
    expect(ACCEPTED_FORMATS_LABEL).toContain('.xlsx')
  })
})

describe('isAcceptedFileType', () => {
  const makeFile = (name: string, type: string): File =>
    new File([''], name, { type })

  it('accepts CSV by MIME type', () => {
    expect(isAcceptedFileType(makeFile('data.csv', 'text/csv'))).toBe(true)
  })

  it('accepts XLSX by MIME type', () => {
    expect(isAcceptedFileType(makeFile('report.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))).toBe(true)
  })

  it('accepts CSV by extension when MIME is empty', () => {
    expect(isAcceptedFileType(makeFile('data.csv', ''))).toBe(true)
  })

  it('accepts XLS by extension when MIME is wrong', () => {
    expect(isAcceptedFileType(makeFile('data.xls', 'application/json'))).toBe(true)
  })

  it('rejects TXT files', () => {
    expect(isAcceptedFileType(makeFile('notes.txt', 'text/plain'))).toBe(false)
  })

  it('rejects PDF files', () => {
    expect(isAcceptedFileType(makeFile('doc.pdf', 'application/pdf'))).toBe(false)
  })

  it('accepts octet-stream (common browser behavior for CSV)', () => {
    expect(isAcceptedFileType(makeFile('data.bin', 'application/octet-stream'))).toBe(true)
  })
})
