"""Generate the RETAIL_SVC key pair for Snowflake key-pair authentication (no secrets are printed).

    python snowflake/setup/generate_key_pair.py [--dir ~/.snowflake/keys] [--name retail_svc_rsa_key] [--no-passphrase]

Writes, OUTSIDE the repository:
    <dir>/<name>.p8        PKCS#8 private key, encrypted with a random passphrase (file mode 600 where supported)
    <dir>/<name>.pub       PEM public key
    <dir>/<name>.pass      the passphrase (only when encrypted)
and prints only the public-key body to paste into 04_service_user.sql (a public key is not a secret).
Refuses to overwrite existing files. Point SNOWFLAKE_PRIVATE_KEY_PATH / SNOWFLAKE_PRIVATE_KEY_PASSPHRASE at them.
"""

import argparse
import os
import secrets
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", type=Path, default=Path.home() / ".snowflake" / "keys")
    ap.add_argument("--name", default="retail_svc_rsa_key")
    ap.add_argument("--no-passphrase", action="store_true")
    args = ap.parse_args()

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    out = args.dir.expanduser().resolve()
    if out == REPO or REPO in out.parents:
        print(f"refusing to write a private key inside the repository ({out})", file=sys.stderr)
        return 1
    files = {ext: out / f"{args.name}.{ext}" for ext in ("p8", "pub", "pass")}
    existing = [p for p in files.values() if p.exists()]
    if existing:
        print(f"refusing to overwrite existing key files: {', '.join(map(str, existing))}", file=sys.stderr)
        return 1
    out.mkdir(parents=True, exist_ok=True)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    passphrase = None if args.no_passphrase else secrets.token_urlsafe(32)
    enc = serialization.NoEncryption() if passphrase is None else \
        serialization.BestAvailableEncryption(passphrase.encode())
    files["p8"].write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, enc))
    pub_pem = key.public_key().public_bytes(serialization.Encoding.PEM,
                                            serialization.PublicFormat.SubjectPublicKeyInfo)
    files["pub"].write_bytes(pub_pem)
    if passphrase:
        files["pass"].write_text(passphrase, encoding="utf-8")
    for p in (files["p8"], files["pass"]):
        if p.exists():
            try:
                os.chmod(p, 0o600)
            except OSError:
                pass

    body = "".join(l for l in pub_pem.decode().splitlines() if "PUBLIC KEY" not in l)
    print(f"private key : {files['p8']}")
    if passphrase:
        print(f"passphrase  : {files['pass']}  (not printed)")
    print("public key body for RSA_PUBLIC_KEY:")
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
