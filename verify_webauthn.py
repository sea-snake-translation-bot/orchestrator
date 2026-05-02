"""
Verify the NitroKey 3A WebAuthn assertion using data from the screenshots,
then test the IC's COSE parsing logic to identify the exact failure.
"""
import hashlib
import base64
import json
import struct
import cbor2
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

# ============================================================
# Data from Image 1 (Registration / webauthn.create)
# ============================================================

# Credential public key coordinates (base64 from screenshot)
x_b64 = "F/6bsJJHm7FP+qEdXMDXwu4cF90YpHOGx8obzZAnYW8="
y_b64 = "nA2Td4nUcJu5qsmUx6GE5BJ3tJNPjKgLEYUrMsG20pA="

x_bytes = base64.b64decode(x_b64)
y_bytes = base64.b64decode(y_b64)

print(f"Public key x ({len(x_bytes)} bytes): {x_bytes.hex()}")
print(f"Public key y ({len(y_bytes)} bytes): {y_bytes.hex()}")

# Construct the EC public key
public_numbers = ec.EllipticCurvePublicNumbers(
    x=int.from_bytes(x_bytes, 'big'),
    y=int.from_bytes(y_bytes, 'big'),
    curve=ec.SECP256R1()
)
public_key = public_numbers.public_key(default_backend())
print(f"\nPublic key constructed successfully: P-256")

# ============================================================
# Data from Image 2 (Authentication / webauthn.get)
# ============================================================

# DER-encoded ECDSA signature from screenshot
sig_hex = "3045022100822773881cad6e31d3d475c6524c334cf4c1d9671e9a220b36037ebd7dbfbef1022057a1e72ac7d89a87e76d77ebb8d80b07a0776451c333309d5bdecbd021ece790"
sig_der = bytes.fromhex(sig_hex)
print(f"\nSignature ({len(sig_der)} bytes DER): {sig_hex[:40]}...")

# Authenticator data from Image 2 (assertion response)
# rpIdHash (32 bytes) + flags (1 byte) + signCount (4 bytes) = 37 bytes
rp_id_hash_hex = "e9a88899f0e3ab9b98f693e0738a37725a3ef8130f3696b24ddddb145024880d"

# Verify rpIdHash = SHA256("www.webauthn.me")
computed_rp_hash = hashlib.sha256(b"www.webauthn.me").hexdigest()
print(f"\nrpIdHash from screenshot:  {rp_id_hash_hex}")
print(f"SHA256('www.webauthn.me'): {computed_rp_hash}")
print(f"rpIdHash match: {rp_id_hash_hex == computed_rp_hash}")

# Flags: UP=1, UV=1, AT=0, ED=0 → 0b00000101 = 0x05
flags = 0x05
# signCount = 71
sign_count = 71

authenticator_data = bytes.fromhex(rp_id_hash_hex) + struct.pack('>B', flags) + struct.pack('>I', sign_count)
print(f"\nAuthenticator data ({len(authenticator_data)} bytes): {authenticator_data.hex()}")

# ClientDataJSON from Image 2
# Try the exact formatting browsers typically use
client_data_json_str = '{"type":"webauthn.get","challenge":"d8itpwDBiLDRUFlUqA3eRIIvLey_aj4EohaDpxgmH3I","origin":"https://www.webauthn.me","crossOrigin":false}'
client_data_json_bytes = client_data_json_str.encode('utf-8')
print(f"\nClientDataJSON ({len(client_data_json_bytes)} bytes): {client_data_json_str[:60]}...")

# Compute the signed bytes: authenticator_data || SHA256(clientDataJSON)
client_data_hash = hashlib.sha256(client_data_json_bytes).digest()
signed_bytes = authenticator_data + client_data_hash

print(f"\nSHA256(clientDataJSON): {client_data_hash.hex()}")
print(f"Signed bytes ({len(signed_bytes)} bytes): {signed_bytes.hex()[:40]}...")

# ============================================================
# Verify the ECDSA signature
# ============================================================
print("\n" + "="*60)
print("SIGNATURE VERIFICATION")
print("="*60)

try:
    public_key.verify(sig_der, signed_bytes, ec.ECDSA(hashes.SHA256()))
    print("✓ Signature VALID!")
except Exception as e:
    print(f"✗ Signature verification failed: {e}")
    print("\n  This might be due to clientDataJSON formatting differences.")
    print("  Trying alternative formatting...")

    # Try with spaces after colons and commas
    alternatives = [
        '{"type":"webauthn.get","challenge":"d8itpwDBiLDRUFlUqA3eRIIvLey_aj4EohaDpxgmH3I","origin":"https://www.webauthn.me","crossOrigin":false}',
        '{"type": "webauthn.get", "challenge": "d8itpwDBiLDRUFlUqA3eRIIvLey_aj4EohaDpxgmH3I", "origin": "https://www.webauthn.me", "crossOrigin": false}',
        '{"type":"webauthn.get","challenge":"d8itpwDBiLDRUFlUqA3eRIIvLey_aj4EohaDpxgmH3I","origin":"https://www.webauthn.me"}',
    ]

    for i, alt in enumerate(alternatives):
        try:
            alt_bytes = alt.encode('utf-8')
            alt_hash = hashlib.sha256(alt_bytes).digest()
            alt_signed = authenticator_data + alt_hash
            public_key.verify(sig_der, alt_signed, ec.ECDSA(hashes.SHA256()))
            print(f"  ✓ Alternative {i+1} VALID! Formatting: {alt[:50]}...")
            break
        except Exception:
            print(f"  ✗ Alternative {i+1} failed")

# ============================================================
# Now test: Construct the COSE key and simulate IC parsing
# ============================================================
print("\n" + "="*60)
print("COSE KEY ANALYSIS")
print("="*60)

# Build the standard COSE key (5 fields, like most authenticators)
cose_key_standard = {
    1: 2,       # kty: EC2
    3: -7,      # alg: ES256
    -1: 1,      # crv: P-256
    -2: x_bytes,  # x coordinate
    -3: y_bytes,  # y coordinate
}

cose_cbor_standard = cbor2.dumps(cose_key_standard)
print(f"\nStandard COSE key (5 fields):")
print(f"  CBOR hex ({len(cose_cbor_standard)} bytes): {cose_cbor_standard.hex()}")
print(f"  First byte: 0x{cose_cbor_standard[0]:02x} = map({cose_cbor_standard[0] - 0xa0}) items")
print(f"  Fields: kty=2(EC2), alg=-7(ES256), crv=1(P-256), x, y")

# Decode and display all fields
decoded = cbor2.loads(cose_cbor_standard)
print(f"  Decoded map keys: {sorted(decoded.keys())}")

# Build COSE key WITH key_ops field (as some authenticators might include)
# Per RFC 8152 Section 7.1, key_ops should be an array
cose_key_with_ops = dict(cose_key_standard)
cose_key_with_ops[4] = [2]  # key_ops: [verify] - per COSE spec, value 2 = "verify"

cose_cbor_with_ops = cbor2.dumps(cose_key_with_ops)
print(f"\nCOSE key WITH key_ops (6 fields):")
print(f"  CBOR hex ({len(cose_cbor_with_ops)} bytes): {cose_cbor_with_ops.hex()}")
print(f"  First byte: 0x{cose_cbor_with_ops[0]:02x} = map({cose_cbor_with_ops[0] - 0xa0}) items")
print(f"  Decoded: {cbor2.loads(cose_cbor_with_ops)}")

# ============================================================
# Simulate IC's COSE parser behavior
# ============================================================
print("\n" + "="*60)
print("SIMULATING IC COSE PARSER")
print("="*60)

def simulate_ic_cose_parser(cose_bytes, label=""):
    """Simulate the IC's COSE key parsing logic from cose/src/lib.rs"""
    print(f"\n--- Parsing: {label} ---")

    # Step 1: CBOR decode (serde_cbor::from_slice)
    try:
        parsed = cbor2.loads(cose_bytes)
    except Exception as e:
        print(f"  CBOR parsing failed: {e}")
        print(f"  → IC error: MalformedPublicKey(Unspecified)")
        return

    if not isinstance(parsed, dict):
        print(f"  Not a CBOR map!")
        print(f"  → IC error: MalformedPublicKey(Unspecified)")
        return

    print(f"  CBOR parsed: map with {len(parsed)} entries")
    print(f"  Map keys: {sorted(parsed.keys())}")

    # Step 2: Check kty and alg
    kty = parsed.get(1)
    alg = parsed.get(3)

    if kty is None:
        print(f"  Missing 'kty' (key 1)")
        print(f"  → IC error: MalformedPublicKey(Unspecified)")
        return
    if alg is None:
        print(f"  Missing 'alg' (key 3)")
        print(f"  → IC error: MalformedPublicKey(Unspecified)")
        return

    print(f"  kty = {kty}, alg = {alg}")

    COSE_KTY_EC2 = 2
    COSE_ALG_ES256 = -7
    COSE_KTY_RSA = 3
    COSE_ALG_RS256 = -257

    if kty == COSE_KTY_EC2 and alg == COSE_ALG_ES256:
        print(f"  Algorithm: ECDSA P-256 (ES256) ✓")

        # Step 3: verify_key_ops check (THE BUG)
        key_ops = parsed.get(4)  # COSE_PARAM_KEY_OPS = 4
        if key_ops is not None:
            print(f"  key_ops field PRESENT: {key_ops} (type: {type(key_ops).__name__})")
            # IC checks: *key_ops != Value::Text("verify")
            if isinstance(key_ops, str) and key_ops == "verify":
                print(f"  key_ops check: PASS (bare string 'verify' - non-standard)")
            else:
                print(f"  key_ops check: FAIL!")
                print(f"  IC code: *key_ops != Value::Text(\"verify\")")
                print(f"  Actual value: {key_ops}")
                if isinstance(key_ops, list):
                    print(f"  This is an ARRAY (correct per RFC 8152), but IC expects bare Text")
                print(f"  → IC error: AlgorithmNotSupported")
                print(f"  → Full error: 'Invalid public key: Algorithm Unspecified not supported: Algorithm not supported in COSE parser'")
                return
        else:
            print(f"  key_ops field: not present (OK)")

        # Step 4: Check curve
        crv = parsed.get(-1)
        if crv != 1:  # P-256
            print(f"  Curve {crv} not P-256")
            print(f"  → IC error: AlgorithmNotSupported")
            return
        print(f"  crv = {crv} (P-256) ✓")

        # Step 5: Check x, y
        x = parsed.get(-2)
        y = parsed.get(-3)
        if not isinstance(x, bytes) or len(x) != 32:
            print(f"  x coordinate invalid")
            return
        if not isinstance(y, bytes) or len(y) != 32:
            print(f"  y coordinate invalid")
            return
        print(f"  x ({len(x)} bytes) ✓, y ({len(y)} bytes) ✓")
        print(f"  → IC result: SUCCESS - key parsed as EcdsaP256")

    elif kty == COSE_KTY_RSA and alg == COSE_ALG_RS256:
        print(f"  Algorithm: RSA SHA256 (RS256)")
    else:
        print(f"  Unknown kty/alg combination: kty={kty}, alg={alg}")
        print(f"  → IC error: AlgorithmNotSupported")
        print(f"  → Full error: 'Invalid public key: Algorithm Unspecified not supported: Algorithm not supported in COSE parser'")

# Test 1: Standard COSE key (no key_ops)
simulate_ic_cose_parser(cose_cbor_standard, "Standard COSE key (5 fields, no key_ops)")

# Test 2: COSE key with key_ops as array [2] (spec-compliant)
simulate_ic_cose_parser(cose_cbor_with_ops, "COSE key with key_ops=[2] (RFC 8152 compliant)")

# Test 3: COSE key with key_ops as array ["verify"]
cose_key_with_text_ops = dict(cose_key_standard)
cose_key_with_text_ops[4] = ["verify"]
simulate_ic_cose_parser(cbor2.dumps(cose_key_with_text_ops), "COSE key with key_ops=['verify'] (array of text)")

# Test 4: COSE key with key_ops as bare string "verify" (non-standard, but what IC expects)
cose_key_with_bare_ops = dict(cose_key_standard)
cose_key_with_bare_ops[4] = "verify"
simulate_ic_cose_parser(cbor2.dumps(cose_key_with_bare_ops), "COSE key with key_ops='verify' (bare text, non-standard)")

# Test 5: COSE key with trailing extension data (simulating Discourse-like bug)
print("\n" + "="*60)
print("TESTING TRAILING EXTENSION DATA (DISCOURSE BUG)")
print("="*60)

extension_data = cbor2.dumps({"hmac-secret": False})
cose_with_trailing = cose_cbor_standard + extension_data
print(f"\nCOSE key + extension data ({len(cose_with_trailing)} bytes)")
print(f"  COSE key: {len(cose_cbor_standard)} bytes")
print(f"  Extension data: {len(extension_data)} bytes ({extension_data.hex()})")

try:
    # serde_cbor::from_slice checks for trailing data
    parsed = cbor2.loads(cose_with_trailing)
    print(f"  cbor2.loads succeeded (ignoring trailing data)")
    print(f"  Note: serde_cbor 0.11.2's from_slice() calls end() which REJECTS trailing data")
    print(f"  → IC error would be: MalformedPublicKey (CBOR TrailingData)")
except Exception as e:
    print(f"  cbor2.loads failed: {e}")
    print(f"  → IC behavior: serde_cbor::from_slice would similarly fail")
    print(f"  → IC error: MalformedPublicKey")

# Also try with cbor2's strict mode
try:
    decoder = cbor2.CBORDecoder(cbor2.loads)
except:
    pass

# Use a streaming decoder to show what happens
import io
print(f"\n  Streaming decode (first object only):")
with io.BytesIO(cose_with_trailing) as f:
    first_obj = cbor2.CBORDecoder(f).decode()
    remaining = f.read()
    print(f"    First CBOR object: map with {len(first_obj)} entries ✓")
    print(f"    Remaining bytes: {len(remaining)} ({remaining.hex()})")
    print(f"    → These trailing bytes would cause serde_cbor::from_slice to fail")

print("\n" + "="*60)
print("CONCLUSION")
print("="*60)
print("""
The NitroKey 3A's credential public key (from the screenshot) shows:
  kty=EC, alg=ES256, crv=P-256, x, y

If the COSE key has ONLY these 5 standard fields, the IC's parser
would accept it. The error 'Algorithm not supported in COSE parser'
can only occur if:

  1. The kty/alg values don't match (unlikely given the screenshot)
  2. A 'key_ops' field (COSE label 4) is present in the COSE key
     → IC's verify_key_ops() rejects ANY spec-compliant key_ops value
  3. The crv value doesn't match P-256 (unlikely given the screenshot)

To confirm: download the raw COSE bytes and check if label 4 exists.
""")
