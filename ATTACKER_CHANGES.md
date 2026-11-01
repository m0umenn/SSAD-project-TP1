# ATTACKER_CHANGES.md — Password Protection Upgrades & Attacker Implementation Guide

*Written for Celina (Owner: `passwords/brute_force.py`, `passwords/dictionary.py`, and `gui/pages/attacks_page.py`)*

---

## 1. What Changed

In Part 3, passwords are still protected by **encryption** (Hill cipher by default, Caesar for comparison) rather than one-way hashing. However, the user is **no longer prompted to type a key** when storing or validating a password:

- **Automated Key Generation & Storage:**
  Keys are generated automatically on first use via `passwords/key_store.py` using cryptographically secure randomness (`secrets` module) and persisted to a separate local JSON file at `data/secret_keys.json`.
- **Per-(Cipher, Use-Case) Key Mapping:**
  The key file stores keys indexed by `"<cipher>:<use_case>"` (e.g., `"hill:2"`, `"caesar:1"`).
- **GUI Simplification:**
  In `gui/pages/passwords_page.py`, the secret key input entries and format hints have been removed. An informational label clarifies: *"Key: generated automatically and kept in a separate key file."*
- **Strict Key Isolation:**
  The key is never included in the protected record, never passed in `app.shared`, never logged, and never included in error messages.

---

## 2. What Did NOT Change

The fundamental defender architecture and attacker interfaces remain strictly backward-compatible:

1. **Protected Record Format:**
   Remains exactly:
   ```json
   {
     "use_case": 2,
     "cipher": "hill",
     "ciphertext": "4133",
     "params": {
       "modulus": 4,
       "block": 2
     }
   }
   ```
2. **Checker Closure API:**
   `protection.make_checker(record, key=None) -> check(candidate: str) -> bool`
   If `key` is omitted, the checker automatically retrieves the stored key from `key_store` and seals it entirely inside the returned `check(candidate)` closure. The closure returns only `True` or `False`.
3. **Lockout Policy:**
   `protection.Lockout(max_failures=5, lock_seconds=30.0, clock=...)`
   Locks authentication for 30 seconds after 5 consecutive failed attempts.
4. **Use Case Specifications & Generators:**
   `passwords.generators.USE_CASES` and `passwords.generators.candidates(alphabet, length)` are completely unchanged.
5. **Shared State Contract (`app.shared`):**
   Contains only `use_case`, `cipher`, and `record`. It **never** contains a key.

---

## 3. What You Must Do

### Online Attacks (Simulating Black-Box Login Trials)
- **Execution:** Must interact **only** through the `check(candidate)` callable returned by `make_checker(record)` and enforce the `Lockout` instance.
- **Rules:** The online attacker has no knowledge of the key or the internal ciphertext algorithm; they simply submit candidate passwords until granted access or locked out.

### Offline Attacks (Simulating Database Exfiltration)
- **Threat Model:** The attacker has stolen the database record (holding `use_case`, `cipher`, `ciphertext`, and `params`), but does **NOT** hold the secret key file.
- **Execution:** Offline attacks must enumerate possible cipher keys and decipher the ciphertext using `passwords.cipher_adapter.decrypt(ciphertext, candidate_key, use_case, cipher)`.
- **Strict Prohibition:** In normal offline and online attack modes, **never import `passwords.key_store` and never read `data/secret_keys.json`**. Doing so would be cheating the threat model.

---

## 4. Feasibility Table: Hill and Caesar Key Spaces

Because the encryption key is held on the server and unknown to an offline exfiltrator, the attacker must search the key space for the specified use case:

| Use Case | Alphabet ($m$) | Block Size ($n$) | Total Matrices ($m^{n^2}$) | Valid Invertible Hill Keys | Feasibility / Recommended Attack | Caesar Keys ($m - 1$) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | 2 (`01`) | 3 | $2^9 = 512$ | **168** | **Trivial brute force** (168 checks) | **1** ($k=1$) |
| **2** | 4 (`1234`) | 2 | $4^4 = 256$ | **96** | **Trivial brute force** (96 checks) | **3** ($k \in [1, 3]$) |
| **3** | 64 | 2 | $64^4 \approx 1.67 \times 10^7$ | **6,291,456** | **Feasible brute force** (~6.3M checks, few seconds in Python) | **63** |
| **4** | 64 | 3 | $64^9 \approx 1.80 \times 10^{16}$ | **$\approx 5.9 \times 10^{15}$** | **Infeasible by brute force**. Use **Known-Plaintext Attack**:<br>$K = C \cdot P^{-1} \pmod{64}$ | **63** |
| **5** | 64 | 2 | $64^4 \approx 1.67 \times 10^7$ | **6,291,456** | **Feasible brute force** (~6.3M checks) | **63** |

> **Key takeaway for Use Case 4:** Brute-forcing $5.9 \times 10^{15}$ keys is computationally prohibitive in Python. This demonstrates why Hill 3x3 over $m=64$ resists key brute force, while remaining vulnerable to linear algebraic known-plaintext attacks if 3 plaintext-ciphertext block pairs are known.

---

## 5. Optional Feature: "Key File Leaked" Demo Mode

To visually demonstrate why symmetric encryption fails to protect passwords once storage is compromised, you may add an optional, clearly separated mode to the Attacks page:

1. **Label:** Clearly label the section: *"Educational Demo: Compromised Key File (Catastrophic Failure)"*.
2. **Behavior:**
   - Provide a file dialog button (`tkinter.filedialog.askopenfilename`) allowing the user to select a key file (e.g., `data/secret_keys.json`).
   - Read the corresponding key for `record["use_case"]` and `record["cipher"]`.
   - Call `cipher_adapter.decrypt(record["ciphertext"], key, use_case, cipher)`.
   - Display the recovered plaintext password instantly in **0.00 seconds**.
3. **Educational Goal:** Proves that symmetric encryption relies entirely on secrecy of the key file. Once the server filesystem is compromised, all user passwords can be reversed instantaneously, proving why Part 4/industry standards require **salted, slow, one-way hashes**.

---

## 6. Testing & Development Advice

- **Temporary Key File in Tests:**
  In all unit tests, isolate the file store using `key_store.set_key_file(temp_path)`. Never allow tests to read or overwrite the development key file in `data/secret_keys.json`.
- **Deterministic Hand-Verified Test Vectors:**
  When writing tests that verify specific mathematical outputs, pass the explicit key parameter to `protect()` and `make_checker()`:
  - **Use Case 2 (Hill 2x2):** $K = \begin{pmatrix} 1 & 2 \\ 3 & 3 \end{pmatrix}$, password `"2431"` $\rightarrow$ `"4133"`
  - **Use Case 1 (Hill 3x3):** $K = \begin{pmatrix} 1 & 1 & 0 \\ 0 & 1 & 1 \\ 0 & 0 & 1 \end{pmatrix}$, password `"101"` $\rightarrow$ `"111"`
  - **Use Case 3 (Hill 2x2):** $K = \begin{pmatrix} 3 & 2 \\ 5 & 7 \end{pmatrix}$, password `"aB1+"` $\rightarrow$ `"29B7"`
  - **Use Case 3 (Caesar):** $k = 5$, password `"aB1+"` $\rightarrow$ `"fG6d"`

---

## 7. Done-When Checklist

- [ ] Online attack uses `make_checker(record)` and respects `Lockout` (terminates or halts after 5 failed attempts).
- [ ] Offline attack takes `record` from `app.shared` and enumerates keys without importing `passwords.key_store`.
- [ ] Hill key enumerators iterate through valid keys per the feasibility table above.
- [ ] Use Case 4 displays an explanation or switches to known-plaintext attack because $5.9 \times 10^{15}$ is infeasible.
- [ ] Optional demo mode allows loading a leaked key file and decrypting in one step.
- [ ] All tests run with temporary key files and do not create or touch `data/secret_keys.json`.