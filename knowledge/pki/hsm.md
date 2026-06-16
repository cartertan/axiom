# HSM (Hardware Security Module)

## What it is

An HSM is a dedicated, hardened physical (or cloud-attached) device that generates, stores, and uses cryptographic keys without ever exposing the private key material in plaintext outside the device's secure boundary. Cryptographic operations — signing, decryption, key generation — happen inside the HSM; only the operation's result leaves it. HSMs are typically certified against standards such as FIPS 140-2/3 Level 3 or Common Criteria, which matters for regulated customers who must demonstrate compliance.

## Why CAs depend on HSMs

A Certificate Authority's root and intermediate signing keys are the most sensitive secrets in the entire PKI — anyone who obtains them can issue trusted certificates for any identity. Public CA standards (CA/Browser Forum Baseline Requirements, WebTrust) mandate HSM-backed key storage for this reason. The HSM enforces:

- **Non-extractability** — the private key never exists outside the module in usable form.
- **Access control** — operations require authenticated, often multi-person (M-of-N), authorization.
- **Tamper response** — physical tampering triggers key zeroization.

## Deployment models

- **On-premises HSM appliances** (e.g., network-attached HSMs) — full physical control, common for high-assurance root CAs.
- **Cloud HSM services** — HSM-backed key management offered by cloud providers, trading some control for operational simplicity and elasticity.
- **HSM-as-a-Service / partner-hosted** — useful where customers want HSM assurance without owning hardware.

## Integration considerations for customers

- PKI platforms typically integrate with HSMs via PKCS#11, KMIP, or vendor-specific APIs — confirm which interface the customer's existing HSM estate supports before assuming compatibility.
- HSM clustering/high-availability is essential for production CAs: an HSM outage blocks issuance, OCSP/CRL signing, and any other operation needing the CA key, which can cascade into a wider outage.
- Key ceremonies (initial root key generation) are formal, witnessed, and scripted events — this is often a customer's first hands-on encounter with HSM operational rigor and a good opportunity to set expectations about ongoing M-of-N custodian processes.
- Latency: every signing operation now involves a network call to the HSM, so issuance throughput and OCSP response time targets should be validated against the customer's specific HSM model and network topology, not assumed from generic benchmarks.
