# Contributing standards

Conventions for issues, branches, commits, and pull requests in Turnstil. The
templates in `.github/` enforce most of this — this is the why.

## Issues

- Use the Bug report or Feature request form (blank issues are disabled).
- One issue = one problem or one request.
- Security issues go through a private advisory, never a public issue.
- Never paste secrets, keys, or attendee personal data.

## Branches

Short, prefixed, kebab-case off `main`:

```
fix/checkin-double-scan
feat/waitlist-promotion
docs/proxy-deployment
chore/bump-2026.2.1
```

## Commits

- Plain style. Short subject with the version in parens when it's a release,
  e.g. `Add QR re-scan grace window on check-in (2026.2.1)`.
- One sentence per change on its own line in the body; no bullet lists.
- **No AI / Co-Authored-By trailers.**
- Don't commit secrets, keys, or attendee data.

## Pull requests

- Fill in the PR template, including the proposed commit message.
- Tests must pass: `python manage.py test`.
- Run `makemigrations` if a model changed, and commit the migration.

## Releases

Turnstil's version lives in git tags. A release is a `vYYYY.N.P` tag on `main`
after the PR merges.
