"""
Brute-force find the correct base64 character(s) that were misread from the image.
"""
import base64
import string

# P-256 curve parameters
p = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
a = p - 3
b = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B

def is_on_curve(x_int, y_int):
    lhs = pow(y_int, 2, p)
    rhs = (pow(x_int, 3, p) + a * x_int + b) % p
    return lhs == rhs

def try_decode(b64_str):
    try:
        data = base64.b64decode(b64_str)
        if len(data) == 32:
            return int.from_bytes(data, 'big')
    except:
        pass
    return None

# Values as read from the screenshot
x_b64 = "F/6bsJJHm7FP+qEdXMDXwu4cF90YpHOGx8obzZAnYW8="
y_b64 = "nA2Td4nUcJu5qsmUx6GE5BJ3tJNPjKgLEYUrMsG20pA="

# Base64 alphabet
b64_chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + "+/"

print("Testing single-character substitutions in x...")
found = False
for i in range(len(x_b64) - 1):  # skip the '=' padding
    orig_char = x_b64[i]
    for c in b64_chars:
        if c == orig_char:
            continue
        test_x = x_b64[:i] + c + x_b64[i+1:]
        x_int = try_decode(test_x)
        if x_int is None:
            continue
        y_int = try_decode(y_b64)
        if y_int and is_on_curve(x_int, y_int):
            print(f"  FOUND! Position {i}: '{orig_char}' → '{c}'")
            print(f"  Corrected x: {test_x}")
            print(f"  x hex: {x_int.to_bytes(32, 'big').hex()}")
            found = True

print("\nTesting single-character substitutions in y...")
x_int_orig = try_decode(x_b64)
for i in range(len(y_b64) - 1):
    orig_char = y_b64[i]
    for c in b64_chars:
        if c == orig_char:
            continue
        test_y = y_b64[:i] + c + y_b64[i+1:]
        y_int = try_decode(test_y)
        if y_int is None:
            continue
        if x_int_orig and is_on_curve(x_int_orig, y_int):
            print(f"  FOUND! Position {i}: '{orig_char}' → '{c}'")
            print(f"  Corrected y: {test_y}")
            print(f"  y hex: {y_int.to_bytes(32, 'big').hex()}")
            found = True

if not found:
    print("\nNo single-character fix found. Trying common dual-character substitutions...")

    # Common misreads: m↔n, 0↔O, 1↔l↔I
    common_swaps = [
        ('m', 'n'), ('n', 'm'),
        ('0', 'O'), ('O', '0'),
        ('1', 'l'), ('l', '1'), ('1', 'I'), ('I', '1'), ('l', 'I'), ('I', 'l'),
        ('rn', 'm'), ('m', 'rn'),
        ('W', 'w'), ('w', 'W'),
        ('8', 'B'), ('B', '8'),
        ('5', 'S'), ('S', '5'),
        ('Z', 'z'), ('z', 'Z'),
    ]

    # Try one substitution in x, one in y
    for xi in range(len(x_b64) - 1):
        for xc in b64_chars:
            if xc == x_b64[xi]:
                continue
            test_x = x_b64[:xi] + xc + x_b64[xi+1:]
            x_int = try_decode(test_x)
            if x_int is None:
                continue
            for yi in range(len(y_b64) - 1):
                for yc in b64_chars:
                    if yc == y_b64[yi]:
                        continue
                    test_y = y_b64[:yi] + yc + y_b64[yi+1:]
                    y_int = try_decode(test_y)
                    if y_int is None:
                        continue
                    if is_on_curve(x_int, y_int):
                        print(f"  FOUND! x[{xi}]: '{x_b64[xi]}' → '{xc}', y[{yi}]: '{y_b64[yi]}' → '{yc}'")
                        print(f"  Corrected x: {test_x}")
                        print(f"  Corrected y: {test_y}")
                        found = True
                        if found:
                            break
                if found:
                    break
            if found:
                break
        if found:
            break
