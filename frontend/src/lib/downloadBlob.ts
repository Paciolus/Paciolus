/**
 * Fetch an API endpoint and trigger a blob download.
 * Consolidates the duplicated fetch -> blob -> anchor -> download pattern.
 */
export async function downloadBlob(options: {
  url: string
  body: unknown
  token: string
  fallbackFilename: string
}): Promise<void> {
  const response = await fetch(options.url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${options.token}`,
    },
    body: JSON.stringify(options.body),
  })
  if (!response.ok) throw new Error('Export failed')
  const blob = await response.blob()
  const disposition = response.headers.get('content-disposition') || ''
  const match = disposition.match(/filename="?([^"]+)"?/)
  const filename = match?.[1] || options.fallbackFilename
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
