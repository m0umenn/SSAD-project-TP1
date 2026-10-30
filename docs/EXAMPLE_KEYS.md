# SSAD Toolkit — Password Encryption Examples

All examples below are **hand-verified** (round-trip tested by the test suite).
Use them to quickly try the **Passwords** page in the GUI.

> **How to use**
> 1. Open the app → click **Passwords** in the sidebar.
> 2. Select the **Use case** and **Cipher** from the dropdowns.
> 3. Type the **Password** and **Key** shown below, then click **Store**.
> 4. The record (ciphertext, modulus, block size) appears — the key is never stored.
> 5. To test login, type the same password and the same key in the **Log in** section.
> 6. Try a **different** key to see it correctly refuse access.

---

## Use Case 1 — Alphabet `01`, length 3, m=2

> ⚠️ Caesar has only one valid key (`k=1`) for this alphabet because `[1, m-1] = {1}`.
> Hill is strongly recommended here.

### Hill (default, recommended)

| Field | Value |
|-------|-------|
| Password | `101` |
| Cipher | Hill |
| Key (3×3, 9 integers, entries 0–1) | `1 1 0 0 1 1 0 0 1` |
| Expected ciphertext | `111` |

**Key matrix visualised:**
```
1 1 0
0 1 1
0 0 1
```
det = 1 (odd → valid ✓), not identity → valid ✓

### Caesar (for comparison only — trivially weak on UC1)

| Field | Value |
|-------|-------|
| Password | `101` |
| Cipher | Caesar |
| Key | `1` *(only valid value)* |
| Expected ciphertext | `010` |

---

## Use Case 2 — Alphabet `1234`, length 4, m=4

### Hill (default)

| Field | Value |
|-------|-------|
| Password | `2431` |
| Cipher | Hill |
| Key (2×2, 4 integers, entries 0–3) | `1 2 3 3` |
| Expected ciphertext | `4133` |

**Key matrix visualised:**
```
1 2
3 3
```
det = 3·1 − 2·3 = −3 ≡ 1 (mod 4) → valid ✓

### Caesar

| Field | Value |
|-------|-------|
| Password | `2431` |
| Cipher | Caesar |
| Key | `3` |
| Expected ciphertext | `1324` |

---

## Use Case 3 — Alphabet `a-zA-Z0-9+*`, length 4, m=64

### Hill (default)

| Field | Value |
|-------|-------|
| Password | `aB1+` |
| Cipher | Hill |
| Key (2×2, 4 integers, entries 0–63) | `3 2 5 7` |
| Expected ciphertext | `29B7` |

**Key matrix visualised:**
```
 3  2
 5  7
```
det = 21 − 10 = 11 (odd → valid ✓)

### Caesar

| Field | Value |
|-------|-------|
| Password | `aB1+` |
| Cipher | Caesar |
| Key | `5` |
| Expected ciphertext | `fG6d` |

---

## Use Case 4 — Alphabet `a-zA-Z0-9+*`, length 6, m=64

### Hill (default)

| Field | Value |
|-------|-------|
| Password | `Abc123` |
| Cipher | Hill |
| Key (3×3, 9 integers, entries 0–63) | `1 2 3 0 1 4 5 6 0` |
| Expected ciphertext | `Ijigsn` |

**Key matrix visualised:**
```
1 2 3
0 1 4
5 6 0
```
det = 1(0−24) − 2(0−20) + 3(0−5) = −24 + 40 − 15 = 1 (odd → valid ✓)

### Caesar

| Field | Value |
|-------|-------|
| Password | `Abc123` |
| Cipher | Caesar |
| Key | `7` |
| Expected ciphertext | `Hij89+` |

---

## Use Case 5 — Alphabet `a-zA-Z0-9+*`, length 8, m=64

### Hill (default)

| Field | Value |
|-------|-------|
| Password | `jK+73*Dd` |
| Cipher | Hill |
| Key (2×2, 4 integers, entries 0–63) | `3 2 5 7` |
| Expected ciphertext | `JPWtJmDM` |

*(Same key matrix as UC3 — reusable across use cases since entries 0–63 are valid for all m=64 cases.)*

### Caesar

| Field | Value |
|-------|-------|
| Password | `jK+73*Dd` |
| Cipher | Caesar |
| Key | `11` |
| Expected ciphertext | `uVjgckOo` |

---

## Hill Key Validity Rules (quick reference)

| Condition | Rule |
|-----------|------|
| Entry range | Each entry must be in `[0, m−1]` |
| Determinant | `gcd(det K, m) = 1` — for m=2,4,64 this means **det K must be odd** |
| Not identity | The key matrix must not be the identity matrix |
| Block size | Must divide the password length (no padding ever added) |

### Block sizes by use case

| Use case | Length | Block n | Matrix size |
|----------|--------|---------|-------------|
| 1 | 3 | 3 | 3×3 |
| 2 | 4 | 2 | 2×2 |
| 3 | 4 | 2 | 2×2 |
| 4 | 6 | 3 | 3×3 |
| 5 | 8 | 2 | 2×2 |

---

## Alphabet Index Reference

The 64-character alphabet (use cases 3–5) is indexed left-to-right as:

```
Index  0– 25:  a b c d e f g h i j k l m n o p q r s t u v w x y z
Index 26– 51:  A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
Index 52– 61:  0 1 2 3 4 5 6 7 8 9
Index 62:      +
Index 63:      *
```

Use case 1 (`01`): `0`→index 0, `1`→index 1.  
Use case 2 (`1234`): `1`→0, `2`→1, `3`→2, `4`→3.
