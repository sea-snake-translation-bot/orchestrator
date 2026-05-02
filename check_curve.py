"""
Check if x or y coordinates are valid on P-256 and compute expected partners.
"""
import base64
import hashlib

# P-256 curve parameters
p = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
a = p - 3
b_curve = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B

x_b64 = "F/6bsJJHm7FP+qEdXMDXwu4cF90YpHOGx8obzZAnYW8="
y_b64 = "nA2Td4nUcJu5qsmUx6GE5BJ3tJNPjKgLEYUrMsG20pA="

x_bytes = base64.b64decode(x_b64)
y_bytes = base64.b64decode(y_b64)

x_int = int.from_bytes(x_bytes, 'big')
y_int = int.from_bytes(y_bytes, 'big')

print(f"x = 0x{x_int:064x}")
print(f"y = 0x{y_int:064x}")

# Check if x is a valid x-coordinate (i.e., x³ + ax + b is a QR mod p)
rhs = (pow(x_int, 3, p) + a * x_int + b_curve) % p
print(f"\nx³ + ax + b mod p = 0x{rhs:064x}")

# Check if rhs is a quadratic residue mod p
# For p ≡ 3 (mod 4), sqrt can be computed as rhs^((p+1)/4) mod p
# P-256's p ≡ 3 (mod 4)? Let's check: p mod 4
print(f"p mod 4 = {p % 4}")

if pow(rhs, (p - 1) // 2, p) == 1:
    print("rhs IS a quadratic residue → x is a valid x-coordinate")
    # Compute sqrt using Tonelli-Shanks or since p ≡ 3 mod 4: y = rhs^((p+1)/4)
    y_computed = pow(rhs, (p + 1) // 4, p)
    y_computed_neg = p - y_computed

    print(f"\nComputed y₁ = 0x{y_computed:064x}")
    print(f"Computed y₂ = 0x{y_computed_neg:064x}")
    print(f"Given    y  = 0x{y_int:064x}")

    # Check how many bytes differ
    y1_bytes = y_computed.to_bytes(32, 'big')
    y2_bytes = y_computed_neg.to_bytes(32, 'big')

    diff1 = sum(1 for a, b in zip(y1_bytes, y_bytes) if a != b)
    diff2 = sum(1 for a, b in zip(y2_bytes, y_bytes) if a != b)

    print(f"\nDifference from y₁: {diff1} bytes")
    print(f"Difference from y₂: {diff2} bytes")

    # Find specific differing bytes
    closer = y1_bytes if diff1 < diff2 else y2_bytes
    for i, (a, b) in enumerate(zip(closer, y_bytes)):
        if a != b:
            print(f"  Byte {i}: expected 0x{a:02x}, got 0x{b:02x}")

    # Encode the correct y as base64 and compare character by character
    correct_y_b64 = base64.b64encode(closer).decode()
    print(f"\nCorrect y base64: {correct_y_b64}")
    print(f"Given   y base64: {y_b64}")
    for i, (a, b) in enumerate(zip(correct_y_b64, y_b64)):
        if a != b:
            print(f"  Position {i}: expected '{a}', got '{b}'")
else:
    print("rhs is NOT a quadratic residue → x is NOT a valid x-coordinate")
    print("\nThe x-coordinate itself must have a misread character.")

    # Try computing valid y from the given y to see if y is a valid y-coordinate
    # (find x such that x³ + ax + b = y² mod p)
    lhs = pow(y_int, 2, p)
    print(f"\ny² mod p = 0x{lhs:064x}")
    print("(Would need to solve cubic to find matching x - skipping)")

    # Instead, try common character substitutions for x
    import string
    b64_chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + "+/"

    print("\nTrying substitutions in x that make it a valid x-coordinate...")
    for i in range(len(x_b64) - 1):
        orig = x_b64[i]
        for c in b64_chars:
            if c == orig:
                continue
            test = x_b64[:i] + c + x_b64[i+1:]
            try:
                test_bytes = base64.b64decode(test)
                if len(test_bytes) != 32:
                    continue
                test_int = int.from_bytes(test_bytes, 'big')
                test_rhs = (pow(test_int, 3, p) + a * test_int + b_curve) % p
                if pow(test_rhs, (p - 1) // 2, p) == 1:
                    # Valid x-coordinate, compute y
                    test_y = pow(test_rhs, (p + 1) // 4, p)
                    test_y_neg = p - test_y
                    if test_y == y_int or test_y_neg == y_int:
                        print(f"  MATCH! x[{i}]: '{orig}' → '{c}'")
                        print(f"  Corrected x: {test}")
                        print(f"  x hex: {test_int.to_bytes(32, 'big').hex()}")
            except:
                continue

    print("\nAlso trying substitutions in y for original x...")
    for i in range(len(y_b64) - 1):
        orig = y_b64[i]
        for c in b64_chars:
            if c == orig:
                continue
            test = y_b64[:i] + c + y_b64[i+1:]
            try:
                test_bytes = base64.b64decode(test)
                if len(test_bytes) != 32:
                    continue
                test_int = int.from_bytes(test_bytes, 'big')
                if pow(test_int, 2, p) == rhs:
                    print(f"  MATCH! y[{i}]: '{orig}' → '{c}'")
                    print(f"  Corrected y: {test}")
                    print(f"  y hex: {test_int.to_bytes(32, 'big').hex()}")
            except:
                continue
