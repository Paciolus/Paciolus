'use client';

/**
 * CommentThread — Sprint 113
 *
 * Threaded comment display with inline reply form.
 * Renders inside the FollowUpItemsTable expanded detail view.
 *
 * Zero-Storage: narratives only, no financial data.
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useFollowUpComments } from '@/hooks/useFollowUpComments';
import type { FollowUpComment } from '@/types/engagement';

interface CommentThreadProps {
  itemId: number;
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function CommentBubble({
  comment,
  isReply,
  onReply,
  onDelete,
  currentUserId,
}: {
  comment: FollowUpComment;
  isReply?: boolean;
  onReply: (parentId: number) => void;
  onDelete: (commentId: number) => void;
  currentUserId: number | null;
}) {
  return (
    <div className={`${isReply ? 'ml-6 border-l-2 border-theme pl-3' : ''}`}>
      <div className="flex items-start gap-2 group">
        <div className="w-6 h-6 rounded-full bg-oatmeal-200 flex items-center justify-center text-xs font-sans text-content-secondary flex-shrink-0 mt-0.5">
          {(comment.author_name || 'U').charAt(0).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2">
            <span className="text-xs font-sans font-medium text-content-primary">
              {comment.author_name || `User ${comment.user_id}`}
            </span>
            <span className="text-xs font-mono text-content-tertiary">
              {formatTimestamp(comment.created_at)}
            </span>
          </div>
          <p className="text-sm font-sans text-content-secondary mt-0.5 whitespace-pre-wrap">
            {comment.comment_text}
          </p>
          <div className="flex items-center gap-3 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {!isReply && (
              <button
                onClick={() => onReply(comment.id)}
                className="text-xs font-sans text-content-tertiary hover:text-content-secondary transition-colors"
              >
                Reply
              </button>
            )}
            {currentUserId === comment.user_id && (
              <button
                onClick={() => onDelete(comment.id)}
                className="text-xs font-sans text-clay-500/70 hover:text-clay-600 transition-colors"
              >
                Delete
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function CommentThread({ itemId }: CommentThreadProps) {
  const {
    comments,
    isLoading,
    error,
    fetchComments,
    createComment,
    deleteComment,
  } = useFollowUpComments();

  const [newText, setNewText] = useState('');
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Get current user ID from auth context indirectly — comments have user_id
  // We compare against comment.user_id for delete permissions
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);

  useEffect(() => {
    fetchComments(itemId);
  }, [itemId, fetchComments]);

  // Build thread structure
  const { topLevel, repliesByParent } = useMemo(() => {
    const top: FollowUpComment[] = [];
    const replies: Record<number, FollowUpComment[]> = {};

    for (const c of comments) {
      if (c.parent_comment_id === null) {
        top.push(c);
      } else {
        const parentId = c.parent_comment_id;
        if (!replies[parentId]) {
          replies[parentId] = [];
        }
        replies[parentId]!.push(c);
      }
    }

    return { topLevel: top, repliesByParent: replies };
  }, [comments]);

  const handleSubmit = useCallback(async () => {
    if (!newText.trim()) return;
    setSubmitting(true);

    const result = await createComment(itemId, {
      comment_text: newText.trim(),
      ...(replyingTo ? { parent_comment_id: replyingTo } : {}),
    });

    if (result) {
      // Track current user from successful creation
      if (!currentUserId) setCurrentUserId(result.user_id);
      setNewText('');
      setReplyingTo(null);
    }

    setSubmitting(false);
  }, [newText, replyingTo, itemId, createComment, currentUserId]);

  const handleDelete = useCallback(async (commentId: number) => {
    await deleteComment(commentId);
  }, [deleteComment]);

  const handleReply = useCallback((parentId: number) => {
    setReplyingTo(parentId);
  }, []);

  return (
    <div className="mt-3 pt-3 border-t border-theme-divider">
      <h5 className="text-xs font-sans font-medium text-content-tertiary mb-2">
        Comments {comments.length > 0 && `(${comments.length})`}
      </h5>

      {isLoading && (
        <div className="flex items-center gap-2 py-2">
          <div className="w-4 h-4 border-2 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
          <span className="text-xs font-sans text-content-tertiary">Loading...</span>
        </div>
      )}

      {error && (
        <p className="text-xs font-sans text-clay-600 mb-2">{error}</p>
      )}

      {/* Comment list */}
      {!isLoading && comments.length === 0 && (
        <p className="text-xs font-sans text-content-tertiary mb-2">No comments yet</p>
      )}

      <div className="space-y-2 mb-3">
        {topLevel.map(comment => (
          <div key={comment.id}>
            <CommentBubble
              comment={comment}
              onReply={handleReply}
              onDelete={handleDelete}
              currentUserId={currentUserId}
            />
            {/* Replies */}
            {repliesByParent[comment.id]?.map(reply => (
              <div key={reply.id} className="mt-1.5">
                <CommentBubble
                  comment={reply}
                  isReply
                  onReply={handleReply}
                  onDelete={handleDelete}
                  currentUserId={currentUserId}
                />
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Reply indicator */}
      {replyingTo && (
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-sans text-content-tertiary">
            Replying to comment
          </span>
          <button
            onClick={() => setReplyingTo(null)}
            className="text-xs font-sans text-content-tertiary hover:text-content-secondary transition-colors"
          >
            Cancel
          </button>
        </div>
      )}

      {/* New comment form */}
      <div className="flex gap-2">
        <input
          type="text"
          value={newText}
          onChange={(e) => setNewText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); } }}
          placeholder={replyingTo ? 'Write a reply...' : 'Add a comment...'}
          className="flex-1 px-3 py-1.5 bg-surface-input border border-theme rounded-lg text-sm text-content-primary placeholder-content-tertiary font-sans focus:border-sage-500 focus:outline-none transition-colors"
          disabled={submitting}
        />
        <button
          onClick={handleSubmit}
          disabled={submitting || !newText.trim()}
          className="px-3 py-1.5 text-xs font-sans bg-sage-50 text-sage-700 border border-sage-200 rounded-lg hover:bg-sage-100 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {submitting ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
}
