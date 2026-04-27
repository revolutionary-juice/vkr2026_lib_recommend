export const CURRENT_USER_ID_KEY = 'currentUserId'
export const CURRENT_USER_KEY = 'currentUser'

export type CurrentUser = {
  id: number
  username: string
  email: string
  role: string
  is_blocked: number | boolean
}

export function getCurrentUser(): CurrentUser | null {
  const raw = localStorage.getItem(CURRENT_USER_KEY)
  if (!raw) {
    const legacyRawUserId = localStorage.getItem(CURRENT_USER_ID_KEY)
    if (!legacyRawUserId) {
      return null
    }

    const legacyUserId = Number(legacyRawUserId)
    if (legacyUserId === null) {
      return null
    }

    if (Number.isNaN(legacyUserId)) {
      return null
    }

    return {
      id: legacyUserId,
      username: '',
      email: '',
      role: 'reader',
      is_blocked: 0,
    }
  }

  try {
    return JSON.parse(raw) as CurrentUser
  } catch {
    return null
  }
}

export function getCurrentUserId(): number | null {
  const currentUserRaw = localStorage.getItem(CURRENT_USER_KEY)
  if (currentUserRaw) {
    try {
      const currentUser = JSON.parse(currentUserRaw) as CurrentUser
      return typeof currentUser.id === 'number' ? currentUser.id : null
    } catch {
      return null
    }
  }

  const raw = localStorage.getItem(CURRENT_USER_ID_KEY)
  if (!raw) return null

  const parsed = Number(raw)
  return Number.isNaN(parsed) ? null : parsed
}

export function getCurrentUserRole(): string | null {
  return getCurrentUser()?.role ?? null
}

export function isCurrentUserAdmin(): boolean {
  return getCurrentUserRole() === 'admin'
}

export function setCurrentUser(user: CurrentUser) {
  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user))
  localStorage.setItem(CURRENT_USER_ID_KEY, String(user.id))
}

export function setCurrentUserId(userId: number) {
  localStorage.setItem(CURRENT_USER_ID_KEY, String(userId))
}

export function clearCurrentUserId() {
  localStorage.removeItem(CURRENT_USER_ID_KEY)
  localStorage.removeItem(CURRENT_USER_KEY)
}

export function requireCurrentUserId(): number {
  const userId = getCurrentUserId()
  if (userId === null) {
    throw new Error('Current user is not selected')
  }
  return userId
}
