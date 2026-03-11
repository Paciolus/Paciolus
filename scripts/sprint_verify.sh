#!/bin/sh

# Paciolus Sprint Push Verifier
# Checks whether all local commits have been pushed to origin.

BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null)
UNPUSHED=$(git log "origin/${BRANCH}..HEAD" --oneline 2>/dev/null)

if [ -z "$UNPUSHED" ]; then
  echo "All commits pushed - sprint is live"
else
  echo "Unpushed commits:"
  echo "$UNPUSHED"
  echo ""
  echo "Run: git push origin $BRANCH"
fi
