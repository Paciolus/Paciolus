'use client'

/**
 * User Profile Settings Page - Sprint 48
 *
 * Personal account settings: display name, email, password.
 * Separate from Practice Settings (materiality, weighted config).
 */

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { ProfileDropdown } from '@/components/auth/ProfileDropdown'
import type { ProfileUpdate } from '@/types/auth'

export default function ProfileSettingsPage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading: authLoading, updateProfile, changePassword, logout } = useAuth()

  // Profile form state
  const [profileName, setProfileName] = useState('')
  const [profileEmail, setProfileEmail] = useState('')
  const [profileSaving, setProfileSaving] = useState(false)
  const [profileSuccess, setProfileSuccess] = useState(false)
  const [profileError, setProfileError] = useState('')

  // Password form state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordSaving, setPasswordSaving] = useState(false)
  const [passwordSuccess, setPasswordSuccess] = useState(false)
  const [passwordError, setPasswordError] = useState('')

  // Load user data
  useEffect(() => {
    if (user) {
      setProfileName(user.name || '')
      setProfileEmail(user.email || '')
    }
  }, [user])

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  // Handle profile save
  const handleProfileSave = async () => {
    setProfileSaving(true)
    setProfileError('')
    setProfileSuccess(false)

    const updates: ProfileUpdate = {}
    if (profileName !== (user?.name || '')) {
      updates.name = profileName
    }
    if (profileEmail !== user?.email) {
      updates.email = profileEmail
    }

    if (Object.keys(updates).length === 0) {
      setProfileSaving(false)
      return
    }

    const result = await updateProfile(updates)
    setProfileSaving(false)

    if (result.success) {
      setProfileSuccess(true)
      setTimeout(() => setProfileSuccess(false), 3000)
    } else {
      setProfileError(result.error || 'Failed to update profile')
    }
  }

  // Handle password change
  const handlePasswordChange = async () => {
    setPasswordSaving(true)
    setPasswordError('')
    setPasswordSuccess(false)

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match')
      setPasswordSaving(false)
      return
    }

    if (!currentPassword || !newPassword) {
      setPasswordError('Please fill in all password fields')
      setPasswordSaving(false)
      return
    }

    const result = await changePassword({
      current_password: currentPassword,
      new_password: newPassword,
    })
    setPasswordSaving(false)

    if (result.success) {
      setPasswordSuccess(true)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setTimeout(() => setPasswordSuccess(false), 3000)
    } else {
      setPasswordError(result.error || 'Failed to change password')
    }
  }

  // Input styling
  const inputClasses = 'w-full px-4 py-3 bg-surface-input border-2 border-theme rounded-lg text-content-primary font-sans transition-all duration-200 outline-none focus:border-sage-500 focus:ring-2 focus:ring-sage-500/20'

  if (authLoading) {
    return (
      <div className="min-h-screen bg-surface-page flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-surface-page">
      {/* Navigation - Sprint 56: Unified nav with ProfileDropdown */}
      <nav className="fixed top-0 w-full bg-surface-card backdrop-blur-md border-b border-theme z-50">
        <div className="max-w-6xl mx-auto px-6 py-3 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3">
            <img
              src="/PaciolusLogo_DarkBG.png"
              alt="Paciolus"
              className="h-10 w-auto max-h-10 object-contain"
              style={{ imageRendering: 'crisp-edges' }}
            />
            <span className="text-xl font-bold font-serif text-content-primary tracking-tight">
              Paciolus
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-content-secondary font-sans hidden sm:block">
              Profile Settings
            </span>
            {user && <ProfileDropdown user={user} onLogout={logout} />}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-24 pb-16 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-2 text-content-tertiary text-sm font-sans mb-4">
              <Link href="/" className="hover:text-content-secondary transition-colors">Home</Link>
              <span>/</span>
              <span className="text-content-secondary">Profile Settings</span>
            </div>
            <h1 className="text-3xl font-serif font-bold text-content-primary mb-2">
              Profile Settings
            </h1>
            <p className="text-content-secondary font-sans">
              Manage your personal account information and security settings.
            </p>
          </div>

          {/* Profile Information Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
 className="theme-card p-6 mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
              Profile Information
            </h2>
            <p className="text-content-tertiary text-sm font-sans mb-6">
              Update your display name and email address.
            </p>

            {/* Profile Messages */}
            {profileError && (
              <div className="mb-4 p-3 bg-clay-50 border border-clay-200 rounded-lg">
                <p className="text-clay-600 text-sm font-sans">{profileError}</p>
              </div>
            )}
            {profileSuccess && (
              <div className="mb-4 p-3 bg-sage-50 border border-sage-200 rounded-lg">
                <p className="text-sage-600 text-sm font-sans">Profile updated successfully!</p>
              </div>
            )}

            {/* Display Name */}
            <div className="mb-4">
              <label className="block text-content-secondary font-sans font-medium mb-2">
                Display Name
              </label>
              <input
                type="text"
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
                placeholder="Enter your name"
                className={inputClasses}
              />
              <p className="text-content-tertiary text-xs mt-1">
                This name will be shown in your workspace greeting.
              </p>
            </div>

            {/* Email */}
            <div className="mb-6">
              <label className="block text-content-secondary font-sans font-medium mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={profileEmail}
                onChange={(e) => setProfileEmail(e.target.value)}
                placeholder="your@email.com"
                className={inputClasses}
              />
            </div>

            {/* Save Button */}
            <button
              onClick={handleProfileSave}
              disabled={profileSaving}
              className="px-6 py-2.5 bg-sage-600 text-white rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {profileSaving ? 'Saving...' : 'Save Profile'}
            </button>
          </motion.div>

          {/* Change Password Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
 className="theme-card p-6 mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
              Change Password
            </h2>
            <p className="text-content-tertiary text-sm font-sans mb-6">
              Update your account password. You'll need to enter your current password to confirm.
            </p>

            {/* Password Messages */}
            {passwordError && (
              <div className="mb-4 p-3 bg-clay-50 border border-clay-200 rounded-lg">
                <p className="text-clay-600 text-sm font-sans">{passwordError}</p>
              </div>
            )}
            {passwordSuccess && (
              <div className="mb-4 p-3 bg-sage-50 border border-sage-200 rounded-lg">
                <p className="text-sage-600 text-sm font-sans">Password changed successfully!</p>
              </div>
            )}

            {/* Current Password */}
            <div className="mb-4">
              <label className="block text-content-secondary font-sans font-medium mb-2">
                Current Password
              </label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter current password"
                className={inputClasses}
              />
            </div>

            {/* New Password */}
            <div className="mb-4">
              <label className="block text-content-secondary font-sans font-medium mb-2">
                New Password
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
                className={inputClasses}
              />
              <p className="text-content-tertiary text-xs mt-1">
                Must be at least 8 characters with uppercase, lowercase, number, and special character.
              </p>
            </div>

            {/* Confirm Password */}
            <div className="mb-6">
              <label className="block text-content-secondary font-sans font-medium mb-2">
                Confirm New Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                className={`${inputClasses} ${
                  confirmPassword && newPassword !== confirmPassword
                    ? 'border-clay-500 focus:border-clay-400'
                    : ''
                }`}
              />
              {confirmPassword && newPassword !== confirmPassword && (
                <p className="text-clay-600 text-xs mt-1">Passwords do not match</p>
              )}
            </div>

            {/* Change Password Button */}
            <button
              onClick={handlePasswordChange}
              disabled={passwordSaving || !currentPassword || !newPassword || newPassword !== confirmPassword}
              className="px-6 py-2.5 bg-sage-600 text-white rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {passwordSaving ? 'Changing...' : 'Change Password'}
            </button>
          </motion.div>

          {/* Account Info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
 className="theme-card p-6"
          >
            <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
              Account Information
            </h2>
            <div className="space-y-3 text-sm font-sans">
              <div className="flex justify-between">
                <span className="text-content-tertiary">Account Status</span>
                <span className={user?.is_active ? 'text-sage-600' : 'text-clay-600'}>
                  {user?.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-tertiary">Member Since</span>
                <span className="text-content-secondary">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  }) : '-'}
                </span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </main>
  )
}
