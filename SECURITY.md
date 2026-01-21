# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within DuilioCode Studio, please:

1. **Do NOT** open a public GitHub issue
2. Send an email to the maintainers with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a detailed response
within 7 days indicating next steps.

## Security Considerations

DuilioCode Studio is designed with privacy in mind:

- **100% Local** - All AI processing happens on your machine
- **No Telemetry** - We don't collect any usage data
- **No External Calls** - The app works completely offline
- **File Access** - The app only accesses files you explicitly open

### Best Practices

1. Run DuilioCode on trusted networks only
2. Keep Ollama and dependencies updated
3. Review code before executing AI-generated scripts
4. Use workspace restrictions for sensitive projects
