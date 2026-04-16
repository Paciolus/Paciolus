/**
 * Sprint 652: useAuthSession thin-export smoke test.
 *
 * Thorough session lifecycle tests live in AuthContext.test.tsx (which
 * exercises the underlying `useAuth` from AuthSessionContext). This file
 * locks the public re-export so consumers can rely on the `@/hooks`
 * import path surviving a refactor.
 */
import { useAuthSession as contextUseAuthSession } from '@/contexts/AuthSessionContext'
import { useAuthSession } from '@/hooks/useAuthSession'

describe('useAuthSession (hooks/ re-export)', () => {
  it('re-exports the same function exposed by AuthSessionContext', () => {
    expect(useAuthSession).toBe(contextUseAuthSession)
  })
})
