"""Write a PEM bundle of the Windows trusted root certificates, for dbt behind a TLS-inspecting proxy.

    python snowflake/dbt/make_ca_bundle.py [OUT]     # default: ~/.snowflake/ca-bundle-with-windows-roots.pem
    $env:REQUESTS_CA_BUNDLE = "<OUT>"                 # then run dbt in the same session

Why: antivirus web shields (Avast on the author's machine) and corporate proxies re-sign HTTPS traffic with their own
root certificate, which Windows trusts but the certifi bundle inside the dbt venv does not. dbt-snowflake then fails
with `SSL: CERTIFICATE_VERIFY_FAILED`. Pointing REQUESTS_CA_BUNDLE at the Windows roots fixes it for that session
only; nothing global changes. The repo `.venv` (snowflake-connector-python 5.2) did not need this on the same machine.

The bundle holds public certificates only (no keys), but it is written outside the repository on purpose.
Windows only: it reads the certificate store through ssl.enum_certificates.
"""

from __future__ import annotations

import ssl
import sys
from pathlib import Path

SERVER_AUTH = "1.3.6.1.5.5.7.3.1"


def main() -> int:
    if not hasattr(ssl, "enum_certificates"):
        print("Windows only: this platform has no Windows certificate store.", file=sys.stderr)
        return 1
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / ".snowflake" / "ca-bundle-with-windows-roots.pem"
    pems = [
        ssl.DER_cert_to_PEM_cert(cert)
        for store in ("ROOT", "CA")
        for cert, encoding, trust in ssl.enum_certificates(store)
        if encoding == "x509_asn" and (trust is True or SERVER_AUTH in trust)
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(pems), encoding="ascii")
    print(f"wrote {len(pems)} certificates to {out}")
    print(f'next: $env:REQUESTS_CA_BUNDLE = "{out}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
