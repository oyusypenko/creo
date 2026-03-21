# Security Policy

## Reporting a Vulnerability

Do **not** open a public issue. Instead, use [GitHub Security Advisories](https://github.com/oyusypenko/creo/security/advisories/new) to report the vulnerability privately.

Alternatively, contact the maintainer directly.

## Supported Versions

Only the latest version receives security updates.

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Security Practices

- No credentials are stored in the repository
- Install scripts write only to user-level directories (`~/.claude/`)
- Extension Python dependencies are installed in isolated virtual environments
- Extension Node.js dependencies are installed locally (no global installs)
