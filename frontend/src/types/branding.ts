/**
 * Branding Types — Sprint 545b
 *
 * Interfaces for PDF branding configuration (Enterprise tier).
 */

export interface BrandingConfig {
  header_text: string
  footer_text: string
  logo_url: string | null
}
