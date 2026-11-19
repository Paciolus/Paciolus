/**
 * Sprint 886 (review OUT-18): a memo export names the engagement its run belongs
 * to, so the server resolves the client's reporting framework (FASB or GASB) and
 * the memo says which it used. With no engagement linked the server uses FASB and
 * labels it the default.
 */
export function withLinkedEngagement<T extends object>(
  body: T,
  engagementId: number | null | undefined,
): T & { engagement_id?: number } {
  return engagementId ? { ...body, engagement_id: engagementId } : body
}
