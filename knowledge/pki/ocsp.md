# OCSP (Online Certificate Status Protocol)

## What it is

OCSP is a real-time protocol clients use to check whether a specific X.509 certificate has been revoked, without downloading an entire Certificate Revocation List (CRL). A client (typically a browser, TLS library, or relying-party application) sends an OCSP request containing the certificate's serial number to an OCSP responder operated by, or on behalf of, the issuing CA. The responder replies with a signed status: good, revoked, or unknown.

## Why it matters

CRLs grow linearly with the number of revoked certificates and can become large (megabytes) for high-volume CAs, making them slow to fetch and parse on every connection. OCSP solves this by returning a small, single-certificate answer, which keeps revocation checking fast enough to perform on the TLS handshake path.

## OCSP stapling

In standard OCSP, the client contacts the OCSP responder directly, which leaks browsing metadata to the CA (the responder learns which sites a given client is visiting) and adds a round trip — and a potential point of failure — to every TLS handshake. OCSP stapling moves the burden to the server: the server itself periodically fetches a signed OCSP response from the CA and "staples" it to the TLS handshake (via the `status_request` extension, historically known as the "OCSP Must-Staple" path). The client then validates the stapled response's signature instead of making its own network call.

Benefits of stapling:
- Eliminates the extra client-to-CA round trip, improving handshake latency.
- Removes the privacy leak of clients contacting the CA's responder directly.
- Improves reliability — a slow or unreachable OCSP responder no longer blocks every client connection; the server can cache and retry independently.

## Operational considerations for customers

- Stapled responses are time-bound (`nextUpdate`); servers must refresh them before expiry or risk serving a stale/invalid staple, which some clients treat as a hard failure under OCSP Must-Staple.
- High-availability deployments need OCSP responder redundancy and monitoring, since a CA outage otherwise degrades every relying server's ability to refresh staples.
- For banks and other regulated entities, OCSP (stapled or not) is generally required over CRLs alone, because revocation latency directly affects fraud and compliance exposure.
