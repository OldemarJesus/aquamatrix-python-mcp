# Security

## Credentials and logs

Credentials are read from environment variables at server startup and remain in process memory for the client lifetime. They are not MCP arguments, stored persistently, or intentionally logged. SDK operation failures are translated to generic tool messages so upstream exception text, credentials, and personal billing data are not returned to the MCP client or emitted through exception tracebacks.

Hosts and deployment platforms may capture process output independently. Restrict log access and do not enable HTTP wire/debug logging around account operations. Avoid sharing logs, environment dumps, container inspection output, or unredacted diagnostic captures.

## Network boundary

stdio is the preferred local-host transport. Streamable HTTP binds to loopback by default and has no authentication. The explicit `MCP_ALLOW_NON_LOOPBACK=true` option only changes the bind-address guard; it does not secure the service. The Compose example maps the host port to loopback. Remote hosting requires an independently reviewed authentication, TLS, and authorization boundary.

## Read-only scope and upstream limits

The tools only retrieve billing data. They do not submit payments, modify account details, automate a browser, or bypass CAPTCHA/MFA. Aquamatrix's portal is not a documented stable API, so behavior can change; the upstream SDK owns protocol handling and reports failures through stable errors.

This is an unofficial project and is not affiliated with or endorsed by SIMAR or Aquamatrix. Use it only with an account you are authorized to access and in accordance with applicable terms.