# CRL (Certificate Revocation List)

## What it is

A CRL is a signed, timestamped list published by a Certificate Authority (CA) that enumerates the serial numbers of certificates it has revoked before their natural expiry, along with the revocation date and (optionally) a reason code (key compromise, CA compromise, affiliation changed, superseded, cessation of operation, etc.). Relying parties download the CRL from a distribution point referenced in the certificate's `CRL Distribution Points` extension and check whether the certificate they are validating appears on it.

## How it works

- CAs publish CRLs on a schedule (commonly hours to days) via the `thisUpdate` / `nextUpdate` fields, which bound how stale a cached CRL is allowed to be.
- Large CAs often split revocation data across multiple CRLs or use Delta CRLs — incremental lists of changes since the last full CRL — to reduce bandwidth.
- The CRL itself is signed by the CA, so its integrity can be verified offline once fetched.

## CRL vs. OCSP

CRLs are pull-based and bulk: a relying party downloads the entire list and caches it locally, which scales well for offline or air-gapped environments but introduces revocation latency bounded by the publication interval. [[OCSP]] is request-based and per-certificate, giving near-real-time status at the cost of a live network dependency on the responder. Most production PKI deployments support both: CRLs as the durable, always-available fallback, and OCSP (often stapled) as the fast path.

## Operational considerations for customers

- CRL size matters: a CA with millions of issued certificates and high revocation churn (e.g., short-lived device certificates) needs Delta CRLs or partitioned CRLs to keep download size manageable.
- Distribution point availability is critical — if the CRL endpoint is unreachable, clients fall back to their configured revocation policy (soft-fail vs. hard-fail), which has real security implications: soft-fail effectively disables revocation checking under an outage.
- CRLs remain mandatory in many compliance frameworks (e.g., WebTrust, eIDAS) even where OCSP is also deployed, so a presales conversation about removing CRLs entirely should flag this as a compliance, not just a technical, decision.
- For HSM-backed CAs, CRL signing operations should be scheduled and monitored like any other HSM-dependent operation, since an HSM outage at publish time can cause stale CRLs.
