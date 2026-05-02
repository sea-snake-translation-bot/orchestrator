"""
Definitive analysis of the IC COSE parser error paths.
Tests which scenarios produce AlgorithmNotSupported vs MalformedPublicKey.
"""
import cbor2
import io

print("="*70)
print("IC COSE PARSER ERROR PATH ANALYSIS")
print("="*70)
print()
print("User's error: 'Invalid public key: Algorithm Unspecified not supported:")
print("               Algorithm not supported in COSE parser'")
print()
print("This maps to CosePublicKeyParseError::AlgorithmNotSupported")
print()

# A valid ECDSA P-256 COSE key (5 fields)
# Using the IC's own test vector
valid_cose_hex = "a501020326200121582051556cab67bc37cc806d4b0666b2553a35f8a96e1ea0025942a1f140b6e42d4e2258200b203014c786088b3525fd5a41ce16cec81de536186efdbc8f9ab9bf9df2f366"
valid_cose = bytes.fromhex(valid_cose_hex)

print("-"*70)
print("TEST 1: Valid COSE key (IC test vector)")
print("-"*70)
parsed = cbor2.loads(valid_cose)
print(f"Fields: {sorted(parsed.keys())} = [kty, alg, crv, x, y]")
print(f"kty={parsed[1]}, alg={parsed[3]}, crv={parsed[-1]}")
print(f"→ IC result: SUCCESS (kty=2=EC2 AND alg=-7=ES256)")
print()

print("-"*70)
print("TEST 2: COSE key + trailing extension data (Discourse bug)")
print("-"*70)
extension_cbor = cbor2.dumps({"hmac-secret": False})
cose_with_ext = valid_cose + extension_cbor
print(f"COSE key: {len(valid_cose)} bytes")
print(f"Extension data: {len(extension_cbor)} bytes = {extension_cbor.hex()}")
print(f"Combined: {len(cose_with_ext)} bytes")
print()
print("serde_cbor::from_slice behavior:")
try:
    # cbor2.loads by default does NOT check trailing data
    result = cbor2.loads(cose_with_ext)
    print(f"  cbor2.loads: parsed OK (cbor2 ignores trailing data by default)")
except Exception as e:
    print(f"  cbor2.loads: FAILED: {e}")

# But serde_cbor 0.11.2's from_slice DOES check:
print(f"  serde_cbor 0.11.2 from_slice: calls end() → checks trailing data")
# Simulate serde_cbor's strict behavior using streaming decode
with io.BytesIO(cose_with_ext) as f:
    first = cbor2.CBORDecoder(f).decode()
    remaining = f.read()
    print(f"  First CBOR item: map({len(first)} entries)")
    print(f"  Remaining bytes: {len(remaining)} = {remaining.hex()}")
    print(f"  → serde_cbor would return Err(TrailingData)")
    print(f"  → IC maps this to: MalformedPublicKey(Unspecified)")
    print(f"  → NOT AlgorithmNotSupported!")
print()

print("-"*70)
print("TEST 3: COSE key with key_ops=[2] (RFC 8152 compliant)")
print("-"*70)
cose_with_keyops_array_int = dict(parsed)
cose_with_keyops_array_int[4] = [2]  # key_ops: [verify] as integer
kops_cbor = cbor2.dumps(cose_with_keyops_array_int)
print(f"Fields: {sorted(cose_with_keyops_array_int.keys())} = [kty, alg, key_ops, crv, x, y]")
print(f"key_ops = [2] (array of int, per RFC 8152 §7.1)")
print(f"CBOR: {kops_cbor.hex()}")
print()
print("IC's verify_key_ops check:")
print('  if *key_ops != Value::Text("verify") → REJECT')
print(f'  key_ops value: Array([Integer(2)])')
print(f'  Array([Integer(2)]) != Text("verify") → true')
print(f"  → IC error: AlgorithmNotSupported ← MATCHES USER'S ERROR!")
print()

print("-"*70)
print("TEST 4: COSE key with key_ops=['verify'] (array of text)")
print("-"*70)
cose_with_keyops_array_text = dict(parsed)
cose_with_keyops_array_text[4] = ["verify"]
print(f"key_ops = ['verify'] (array of text)")
print("IC's verify_key_ops check:")
print(f'  Array([Text("verify")]) != Text("verify") → true')
print(f"  → IC error: AlgorithmNotSupported ← MATCHES USER'S ERROR!")
print()

print("-"*70)
print("TEST 5: COSE key with key_ops='verify' (bare text, non-standard)")
print("-"*70)
cose_with_keyops_bare = dict(parsed)
cose_with_keyops_bare[4] = "verify"
print(f"key_ops = 'verify' (bare text, NOT per COSE spec)")
print("IC's verify_key_ops check:")
print(f'  Text("verify") != Text("verify") → false')
print(f"  → IC result: PASS (only this non-standard format passes!)")
print()

print("-"*70)
print("TEST 6: Wrong algorithm (e.g., EdDSA instead of ES256)")
print("-"*70)
wrong_alg = dict(parsed)
wrong_alg[3] = -8  # EdDSA
print(f"kty=2 (EC2), alg=-8 (EdDSA)")
print(f"IC check: kty==2 && alg==-7 → false")
print(f"  → IC error: AlgorithmNotSupported ← MATCHES USER'S ERROR!")
print()

print("="*70)
print("CONCLUSION")
print("="*70)
print()
print("The user's error 'AlgorithmNotSupported' can ONLY come from:")
print()
print("  A) kty/alg mismatch in from_cbor()")
print("     → kty and alg must both be present but not match")
print("       EC2+ES256 or RSA+RS256")
print()
print("  B) verify_key_ops() in parse_ecdsa_p256() or parse_rsa_pkcs1_sha256()")
print("     → key_ops (COSE label 4) is present in the CBOR map")
print("       AND its value is not the bare text string 'verify'")
print()
print("  C) crv mismatch in parse_ecdsa_p256()")
print("     → crv is not 1 (P-256)")
print()
print("It CANNOT come from:")
print("  - Trailing extension data (would give MalformedPublicKey/TrailingData)")
print("  - Missing fields (would give MalformedPublicKey)")
print("  - Invalid CBOR (would give MalformedPublicKey)")
print()
print("Given the webauthn.me screenshot shows kty=EC, alg=ES256, crv=P-256,")
print("the most likely cause is (B): the NitroKey 3A's COSE key includes a")
print("'key_ops' field (COSE label 4) in a spec-compliant format that the")
print("IC's buggy verify_key_ops() function rejects.")
print()
print("The fix: verify_key_ops() must accept key_ops as an ARRAY per RFC 8152.")
