# Security Policy

Turnstil handles event registration and attendee contact data, so we ask that
security problems be disclosed privately.

## Reporting a vulnerability

**Do not open a public issue, PR, or discussion for a security problem.**

Report it privately through GitHub:

1. Go to the repository's **Security** tab → **Report a vulnerability**
   (<https://github.com/Susquehanna-Syntax/Turnstil/security/advisories/new>).
2. Include the details below.

This opens a private advisory visible only to you and the maintainers.

Please include:

- Affected area (a specific view/endpoint, QR check-in, the API) and version.
- Steps to reproduce or a proof of concept.
- Impact — what an attacker can read, change, or do.
- Any suggested remediation.

## Scope

In scope: authentication and session handling, registration and check-in
integrity, QR token/code handling, attendee-data access control, the REST API,
and CSRF/host handling.

Out of scope: findings that require a pre-compromised host or admin account,
and issues in third-party dependencies without a Turnstil-specific exploit path.

We aim to acknowledge reports within a few days and to coordinate a fix and
disclosure timeline with you.
