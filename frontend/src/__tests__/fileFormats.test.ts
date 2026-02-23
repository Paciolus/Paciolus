import {
  ACCEPTED_FILE_EXTENSIONS,
  ACCEPTED_FILE_EXTENSIONS_STRING,
  ACCEPTED_FORMATS_LABEL,
  ACCEPTED_MIME_TYPES,
  isAcceptedFileType,
} from '@/utils/fileFormats'

describe('fileFormats constants', () => {
  it('ACCEPTED_FILE_EXTENSIONS has 5 entries', () => {
    expect(ACCEPTED_FILE_EXTENSIONS).toEqual(['.csv', '.tsv', '.txt', '.xlsx', '.xls'])
  })

  it('ACCEPTED_FILE_EXTENSIONS_STRING matches HTML accept format', () => {
    expect(ACCEPTED_FILE_EXTENSIONS_STRING).toBe('.csv,.tsv,.txt,.xlsx,.xls')
  })

  it('ACCEPTED_MIME_TYPES includes 7 types', () => {
    expect(ACCEPTED_MIME_TYPES).toHaveLength(7)
    expect(ACCEPTED_MIME_TYPES).toContain('text/csv')
    expect(ACCEPTED_MIME_TYPES).toContain('text/tab-separated-values')
    expect(ACCEPTED_MIME_TYPES).toContain('text/plain')
    expect(ACCEPTED_MIME_TYPES).toContain('application/vnd.ms-excel')
  })

  it('ACCEPTED_FORMATS_LABEL is human-readable', () => {
    expect(ACCEPTED_FORMATS_LABEL).toContain('CSV')
    expect(ACCEPTED_FORMATS_LABEL).toContain('TSV')
    expect(ACCEPTED_FORMATS_LABEL).toContain('Text')
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

  it('accepts TSV by MIME type', () => {
    expect(isAcceptedFileType(makeFile('data.tsv', 'text/tab-separated-values'))).toBe(true)
  })

  it('accepts TSV by extension when MIME is empty', () => {
    expect(isAcceptedFileType(makeFile('data.tsv', ''))).toBe(true)
  })

  it('accepts TXT by MIME type', () => {
    expect(isAcceptedFileType(makeFile('data.txt', 'text/plain'))).toBe(true)
  })

  it('accepts TXT by extension when MIME is wrong', () => {
    expect(isAcceptedFileType(makeFile('data.txt', 'application/json'))).toBe(true)
  })

  it('rejects PDF files', () => {
    expect(isAcceptedFileType(makeFile('doc.pdf', 'application/pdf'))).toBe(false)
  })

  it('accepts octet-stream (common browser behavior for CSV)', () => {
    expect(isAcceptedFileType(makeFile('data.bin', 'application/octet-stream'))).toBe(true)
  })
})
