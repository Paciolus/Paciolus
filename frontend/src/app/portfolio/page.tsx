'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { useClients } from '@/hooks/useClients';
import { ClientCard, CreateClientModal, EditClientModal } from '@/components/portfolio';
import { ProfileDropdown } from '@/components/auth';
import type { Client, ClientCreateInput } from '@/types/client';

/**
 * Portfolio Page - Sprint 17: Portfolio Dashboard & Entity UX
 *
 * Design: Premium "Client Ledger" grid with Oat & Obsidian palette
 * - Responsive grid (1-3 columns)
 * - Staggered card entrance animations
 * - "New Client" modal with form validation
 *
 * ZERO-STORAGE: Displays client metadata only, no financial data
 */

export default function PortfolioPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth();
  const {
    clients,
    totalCount,
    isLoading: clientsLoading,
    error,
    industries,
    createClient,
    updateClient,
    deleteClient,
    refresh,
  } = useClients();

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editClient, setEditClient] = useState<Client | null>(null);
  const [deleteConfirmClient, setDeleteConfirmClient] = useState<Client | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login?redirect=/portfolio');
    }
  }, [authLoading, isAuthenticated, router]);

  // Handle client creation
  // Sprint 23 Hotfix: Use ClientCreateInput type to fix Industry type mismatch
  const handleCreateClient = async (data: ClientCreateInput): Promise<boolean> => {
    const result = await createClient(data);
    return result !== null;
  };

  // Handle client deletion
  const handleDeleteClient = async (client: Client) => {
    setDeleteConfirmClient(client);
  };

  const confirmDelete = async () => {
    if (!deleteConfirmClient) return;

    setIsDeleting(true);
    const success = await deleteClient(deleteConfirmClient.id);
    setIsDeleting(false);

    // Only close modal on success
    if (success) {
      setDeleteConfirmClient(null);
    }
  };

  // Container animation for staggered children
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.04,
        delayChildren: 0.1,
      },
    },
  };

  // Button micro-interaction
  const buttonVariants = {
    rest: { y: 0 },
    hover: { y: -2 },
    tap: { y: 0, scale: 0.98 },
  };

  // Loading state
  if (authLoading || (!isAuthenticated && !authLoading)) {
    return (
      <div className="min-h-screen bg-surface-page flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
          <p className="text-content-secondary font-sans">Loading portfolio...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-surface-page">
      {/* Navigation */}
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

          {/* Navigation Links */}
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-sm text-content-secondary hover:text-content-primary font-sans transition-colors hidden sm:block"
            >
              Home
            </Link>
            <span className="text-content-tertiary hidden sm:block">|</span>
            <span className="text-sm text-content-secondary font-sans hidden sm:block">
              Client Portfolio
            </span>
            <span className="text-content-tertiary hidden sm:block">|</span>
            <Link
              href="/engagements"
              className="text-sm text-content-secondary hover:text-content-primary font-sans transition-colors hidden sm:block"
            >
              Workspaces
            </Link>
            {user && <ProfileDropdown user={user} onLogout={logout} />}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-24 pb-16 px-6">
        <div className="max-w-6xl mx-auto">
          {/* Page Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
            <div>
              <h1 className="text-3xl md:text-4xl font-serif font-bold text-content-primary">
                Client Portfolio
              </h1>
              <p className="text-content-secondary font-sans mt-1">
                {totalCount === 0
                  ? 'Add your first client to get started'
                  : `${totalCount} client${totalCount === 1 ? '' : 's'} in your portfolio`}
              </p>
            </div>

            {/* New Client Button */}
            <motion.button
              variants={buttonVariants}
              initial="rest"
              whileHover="hover"
              whileTap="tap"
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-5 py-3 bg-sage-600 hover:bg-sage-700 text-white font-sans font-bold rounded-xl transition-colors shadow-theme-card"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              New Client
            </motion.button>
          </div>

          {/* Error State */}
          {error && (
            <div className="mb-6 p-4 bg-clay-50 border border-clay-200 rounded-xl">
              <p className="text-clay-600 font-sans text-sm">{error}</p>
            </div>
          )}

          {/* Loading State */}
          {clientsLoading && clients.length === 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-surface-card rounded-xl border border-theme p-5 animate-pulse shadow-theme-card">
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="flex-1">
                      <div className="h-6 w-3/4 bg-surface-card-secondary rounded" />
                      <div className="h-4 w-1/2 bg-surface-card-secondary rounded mt-2" />
                    </div>
                    <div className="h-6 w-20 bg-surface-card-secondary rounded-full" />
                  </div>
                  <div className="flex gap-4 mb-4">
                    <div className="h-4 w-24 bg-surface-card-secondary rounded" />
                    <div className="h-4 w-20 bg-surface-card-secondary rounded" />
                  </div>
                  <div className="h-px bg-theme-divider mb-4" />
                  <div className="h-10 bg-surface-card-secondary rounded-lg" />
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!clientsLoading && clients.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-center py-16"
            >
              {/* Empty state illustration */}
              <div className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-surface-card-secondary border border-theme flex items-center justify-center">
                <svg className="w-12 h-12 text-content-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>

              <h2 className="text-2xl font-serif font-semibold text-content-primary mb-2">
                No Clients Yet
              </h2>
              <p className="text-content-secondary font-sans mb-8 max-w-md mx-auto">
                Start building your portfolio by adding your first client. Track their audits and keep your work organized.
              </p>

              <motion.button
                variants={buttonVariants}
                initial="rest"
                whileHover="hover"
                whileTap="tap"
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-2 px-6 py-3.5 bg-sage-600 hover:bg-sage-700 text-white font-sans font-bold rounded-xl transition-colors shadow-theme-card"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Add Your First Client
              </motion.button>

              {/* Zero-Storage badge */}
              <div className="mt-8 inline-flex items-center gap-2 bg-sage-50 border border-sage-200 rounded-full px-4 py-2">
                <svg className="w-4 h-4 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <span className="text-sage-700 text-sm font-sans">
                  Zero-Storage: Only client metadata is saved
                </span>
              </div>
            </motion.div>
          )}

          {/* Client Grid */}
          {clients.length > 0 && (
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {clients.map((client, index) => (
                <ClientCard
                  key={client.id}
                  client={client}
                  index={index}
                  lastAuditDate={null} // TODO: Fetch from activity logs
                  onEdit={(c) => setEditClient(c)}
                  onDelete={handleDeleteClient}
                />
              ))}
            </motion.div>
          )}
        </div>
      </div>

      {/* Create Client Modal */}
      <CreateClientModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateClient}
        industries={industries}
        isLoading={clientsLoading}
      />

      {/* Edit Client Modal */}
      <EditClientModal
        isOpen={!!editClient}
        client={editClient}
        onClose={() => setEditClient(null)}
        onSubmit={updateClient}
        industries={industries}
        isLoading={clientsLoading}
      />

      {/* Delete Confirmation Modal */}
      {deleteConfirmClient && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-obsidian-900/50 backdrop-blur-sm"
            onClick={() => setDeleteConfirmClient(null)}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="relative bg-surface-card rounded-2xl border border-theme shadow-theme-elevated w-full max-w-sm p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-clay-50 flex items-center justify-center">
                <svg className="w-5 h-5 text-clay-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-serif font-semibold text-content-primary">
                  Delete Client
                </h3>
                <p className="text-content-tertiary text-sm font-sans">
                  This action cannot be undone
                </p>
              </div>
            </div>

            <p className="text-content-secondary font-sans mb-6">
              Are you sure you want to delete <span className="font-semibold text-content-primary">{deleteConfirmClient.name}</span>?
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => setDeleteConfirmClient(null)}
                disabled={isDeleting}
                className="flex-1 px-4 py-2.5 bg-surface-card-secondary hover:bg-surface-card border border-theme text-content-primary font-sans font-medium rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={isDeleting}
                className="flex-1 px-4 py-2.5 bg-clay-600 hover:bg-clay-700 disabled:bg-clay-600/50 text-white font-sans font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                {isDeleting ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Deleting...
                  </>
                ) : (
                  'Delete'
                )}
              </button>
            </div>
          </motion.div>
        </div>
      )}

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-theme">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-content-tertiary text-sm font-sans">
            2025 Paciolus. Built for Financial Professionals.
          </div>
          <div className="text-content-tertiary text-sm font-sans">
            Zero-Storage Architecture. Your data stays yours.
          </div>
        </div>
      </footer>
    </main>
  );
}
