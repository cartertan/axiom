# Certificate Lifecycle Management (CLM)

## What it is

Certificate lifecycle management covers every stage a digital certificate passes through: request/enrollment, issuance, deployment/installation, monitoring, renewal, and revocation or expiry. At enterprise scale — thousands to millions of certificates across TLS endpoints, code signing, device identity, and internal service-to-service mTLS — manual tracking fails, and expired certificates become one of the most common causes of unplanned outages.

## Stages in detail

1. **Enrollment** — A key pair is generated and a Certificate Signing Request (CSR) is submitted to a CA, either manually, via API, or via an automated protocol.
2. **Issuance** — The CA validates the request (domain control, organization identity, or device identity depending on certificate type) and issues the signed certificate.
3. **Deployment** — The certificate and private key are installed on the target system: a load balancer, web server, IoT device, or application keystore.
4. **Monitoring** — Expiry dates, revocation status, and policy compliance (key length, algorithm, validity period) are tracked continuously.
5. **Renewal** — Before expiry, a new certificate is requested and deployed, ideally with zero manual intervention.
6. **Revocation/Retirement** — If a key is compromised or a certificate is no longer needed, it is revoked (added to a CRL/OCSP responder) and decommissioned.

## Automation: ACME and beyond

The ACME protocol (Automated Certificate Management Environment, RFC 8555) automates enrollment, validation, issuance, and renewal without human intervention, originally popularized by Let's Encrypt for public TLS and now widely used inside enterprises for internal CAs as well. ACME clients prove control of an identifier (domain, IP) via HTTP-01, DNS-01, or TLS-ALPN-01 challenges, then receive a short-lived certificate that renews automatically.

Enterprises increasingly favor short validity periods (90 days or less, sometimes days) precisely because automation makes frequent renewal cheap — this shrinks the window of exposure from a compromised or misissued certificate.

## Operational considerations for customers

- A CLM platform should provide full visibility across all CAs (internal and public) — discovery of "unknown" certificates is often the first finding in a CLM engagement.
- Integration with existing infrastructure (load balancers, Kubernetes ingress, HSMs) determines how much of the lifecycle can actually be automated versus left manual.
- SLA commitments (e.g., 99.99% uptime) depend directly on renewal automation reliability — a missed renewal is a self-inflicted outage, not an external risk.
- Audit trails (who issued what, when, under which policy) are typically a hard compliance requirement, not optional tooling.
