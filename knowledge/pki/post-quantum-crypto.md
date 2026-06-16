# Post-Quantum Cryptography (PQC) and PKI Migration

## The threat

A sufficiently large, fault-tolerant quantum computer running Shor's algorithm could break the integer factorization and discrete-log problems underlying RSA, DSA, and ECC/ECDSA/ECDH — the algorithms almost all of today's PKI relies on for both signing and key exchange. While such a machine does not exist yet at the scale required, the "harvest now, decrypt later" risk is already real: traffic encrypted today can be recorded and decrypted retroactively once a capable quantum computer exists, which matters enormously for data with long confidentiality requirements (financial records, health data, state secrets).

## NIST's standardized algorithms

NIST's PQC standardization process selected algorithms based on lattice and hash-based mathematics believed to resist quantum attack:

- **ML-KEM (CRYSTALS-Kyber)** — key encapsulation mechanism, the PQC replacement for ECDH/RSA key exchange (FIPS 203).
- **ML-DSA (CRYSTALS-Dilithium)** — digital signatures, the primary PQC replacement for ECDSA/RSA signing (FIPS 204).
- **SLH-DSA (SPHINCS+)** — a hash-based signature scheme, more conservative and larger, used as a backup algorithm with different security assumptions (FIPS 205).

## Migration approach for PKI

1. **Crypto-agility first** — before swapping algorithms, ensure systems can support multiple algorithms and rotate without re-architecture. This is the actual hard problem; algorithm selection is comparatively easy.
2. **Hybrid certificates and hybrid key exchange** — combine a classical algorithm (ECDSA/ECDH) with a PQC algorithm (ML-DSA/ML-KEM) so that breaking either alone is insufficient. This is the dominant near-term transition strategy and is already supported in TLS 1.3 hybrid key exchange drafts and being piloted by major browsers and CAs.
3. **Inventory** — customers cannot migrate what they cannot see; a cryptographic asset inventory (which systems use which algorithms, key sizes, and certificate types) is typically the first deliverable.
4. **Root CA timelines** — root and intermediate CAs have long operational lifetimes (10–20+ years), so PQC root issuance needs to start well before classical algorithms are considered broken.

## Talking points for customers (CIO/CISO level)

- This is not hypothetical "someday" planning for regulated and long-data-lifetime industries (finance, healthcare, government) — "harvest now, decrypt later" makes the deadline effectively today for sensitive data.
- Hybrid approaches let customers move now without betting entirely on algorithms that, while NIST-standardized, have less real-world deployment history than RSA/ECC.
- The biggest cost driver is usually not the cryptography but inventory and crypto-agility retrofitting across legacy systems that hardcode algorithm assumptions.
