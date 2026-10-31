# SSAD Toolkit: Interface Architecture & Password Technology Guide

This document explains two core aspects of the SSAD Toolkit:
1. **The Interface Architecture**: How the graphical user interface (GUI) was built, how it functions as a strictly separated presentation layer from the underlying cryptographic features, and how it handles inputs and outputs without coupling to business logic.
2. **The Password Technology**: How the updated Part 3 password defence mechanism works under the hood, including automated cryptographic key generation, atomic persistent storage, closure-based verification, and threat-model implications.

---

## Part 1: How the Interface Was Built

### 1. Architectural Structure & Modularity

The SSAD Toolkit interface is built using Python's standard library GUI framework (`tkinter` and `ttk`). It follows a clean, single-window controller pattern with dynamic frame stacking and decoupled secondary windows:

```
+---------------------------------------------------------------------------------+
| SSADToolkitApp (Root tk.Tk Window)                                              |
| +-------------------------+ +-------------------------------------------------+ |
| | Sidebar (Sidebar.TFrame)| | Content Container (Content.TFrame)              | |
| |                         | |                                                 | |
| | [ Encryption ] ---------->| Stacked Pages (BasePage frames):                 | |
| | [ Decryption ] ---------->|   • EncryptionPage                              | |
| | [ Passwords ] ---------->|   • DecryptionPage                              | |
| | [ Attacks ] ----------->|   • PasswordsPage                               | |
| | [ Integrity ] ---------->|   • AttacksPage                                 | |
| |                         | |   • IntegrityPage                               | |
| +-------------------------+ +-------------------------------------------------+ |
+---------------------------------------------------------------------------------+
               |
               +---> Standalone Pop-Out Window: DecryptionToplevel (Entity B)
```

- **`SSADToolkitApp` (`gui/app.py`)**:
  Serves as the root application container. It configures the ttk visual styles, constructs a responsive two-column grid (sidebar on column 0, content container on column 1), instantiates all application pages, and provides page navigation via `tkraise()`.
- **`BasePage` (`gui/pages/base_page.py`)**:
  Abstract parent frame for all application pages. Enforces a consistent header layout (title label and description subtitle) and provides a clean canvas for derived page layouts.
- **Detached Receiver Window (`DecryptionToplevel`)**:
  To simulate a real-world communication channel between two independent parties (Entity A - Sender and Entity B - Receiver), the Decryption page can be popped out into an independent OS top-level window. This allows testing message transmission across separate windows.

---

### 2. The Interface as a Separate Entity (Strict Separation of Concerns)

A fundamental architectural rule of the toolkit is that **the GUI is strictly an I/O presentation entity**:

```
[ User Interaction ]
         |  (Inputs: text fields, dropdown selections, button clicks)
         v
+-------------------------------------------------------------------+
| GUI Layer (gui/)                                                  |
| - Collects and validates GUI entry widgets                       |
| - Reads selections (e.g. Use Case, Cipher)                        |
| - Contains ZERO cryptographic, hashing, or key derivation math   |
+-------------------------------------------------------------------+
         |
         |  Direct function calls with plain Python primitives
         v
+-------------------------------------------------------------------+
| Feature Core (crypto/, passwords/, integrity/)                    |
| - Performs encryption, decryption, matrix math, hashing           |
| - Autonomous, stateless, standard-library only                     |
| - Independent from Tkinter (can run entirely headless or in CLI)  |
+-------------------------------------------------------------------+
         |
         |  Plain return values or exceptions
         v
+-------------------------------------------------------------------+
| GUI Presentation Rendering                                        |
| - Sets StringVar output variables                                 |
| - Formats status messages and applies color codes:                |
|     Green (#0f5132) = Success / Valid / Access Granted            |
|     Red   (#c92a2a) = Error / Locked / Intended Recipient Failed  |
+-------------------------------------------------------------------+
```

#### Why This Separation Matters:
1. **Zero Cryptographic Logic in Widgets**:
   Widgets only call clean backend APIs:
   - Encryption calls `crypto.caesar.encrypt`, `crypto.playfair.encrypt`, or `crypto.hill.encrypt`.
   - Passwords call `passwords.protection.protect` and `passwords.protection.make_checker`.
   - Authenticity calls `integrity.hashing.hash_protected` and `integrity.hashing.verify_protected`.
2. **Headless Testability**:
   Because backend modules have no Tkinter dependencies, the entire cryptographic test suite (95+ unit tests) runs in fractions of a second without launching GUI windows.
3. **Decoupled Inter-Page Communication (`app.shared`)**:
   Pages do not directly access or mutate each other's internal state. Information transfer (such as sending a protected password target from `PasswordsPage` to `AttacksPage`, or ciphertext from `EncryptionPage` to `DecryptionPage`) is routed through a sanitized dictionary:
   ```python
   app.shared = {
       "use_case": 2,
       "cipher": "hill",
       "record": { ... }  # Strictly metadata and ciphertext — NEVER a key
   }
   ```

---

## Part 2: How the Password Technology Works

Part 3 of the SSAD Toolkit explores defending stored passwords using **reversible ciphers** (Hill cipher by default, Caesar for comparison) over five predefined operational use cases. 

In this updated version, password storage and verification have been upgraded with automated key lifecycle management.

---

### 1. The Automated Key Store (`passwords/key_store.py`)

Previously, users had to invent, type, and remember a mathematical cipher key (e.g., an invertible modulo-m matrix) every time they stored or validated a password. The updated technology automates key management entirely:

```
[ Store Password Request ]
          |
          v
[ passwords.key_store.get_key(use_case, cipher) ]
          |
          +---> Does key file (data/secret_keys.json) exist?
          |        |-- NO  --> Create file
          |        `-- YES --> Read and validate JSON
          |
          +---> Is key entry "<cipher>:<use_case>" present?
                   |-- YES --> Return existing key
                   `-- NO  --> Generate cryptographically secure key:
                               • Caesar: secrets.randbelow(m - 1) + 1
                               • Hill:   Generate random n x n matrix via secrets
                                         Validate gcd(det, m) == 1 and non-identity
                                         Save file atomically (tempfile + os.replace)
                                         Return generated key
```

#### Key Store Features:
- **Cryptographic Randomness**:
  Keys are generated using Python's `secrets` module (providing OS-level CSPRNG randomness, suitable for security-sensitive cryptographic keys).
- **Per-(Cipher, Use-Case) Isolation**:
  Keys are partitioned by cipher and use case (`"hill:1"`, `"hill:2"`, `"caesar:3"`, etc.).
- **Atomic Persistence**:
  When updating the key file, writes occur via `tempfile.mkstemp` and `os.replace`, guaranteeing that crashes or power interruptions never result in a partially written or corrupted key file.
- **Access Control & Git Exclusion**:
  Best-effort `os.chmod(..., 0o600)` restricts read permissions to the running process owner. The `data/` folder is added to `.gitignore` so keys are never accidentally committed to version control.
- **Corruption Safety**:
  If the key file is corrupted or contains invalid entries, `key_store` raises `ValueError("Key file is corrupted")` and strictly refuses to overwrite it, preventing silent data loss.

---

### 2. The Password Protection & Verification Flow (`passwords/protection.py`)

#### Storing a Password (`protect`)
When storing a password:
1. `validate_password(password, use_case)` validates password length and alphabet characters.
2. `protect(password, use_case, cipher=None, key=None)` is invoked.
3. If `key` is `None`, it is fetched automatically from `key_store.get_key(use_case, cipher)`.
4. The password is encrypted using `passwords.cipher_adapter.encrypt`.
5. The function returns a sanitized protected record:
   ```python
   {
       "use_case": 3,
       "cipher": "hill",
       "ciphertext": "29B7",
       "params": {
           "modulus": 64,
           "block": 2
       }
   }
   ```
6. **Key Isolation**: The secret key is never stored in the record, never displayed in the GUI, and never logged.

#### Verifying a Login (`make_checker` & `Lockout`)
When a user attempts to log in:
1. `make_checker(record, key=None)` is called.
2. The key is retrieved from `key_store` and closed over entirely inside a local `check(candidate)` closure:
   ```python
   def make_checker(record, key=None):
       # Key loaded and closed over here...
       parsed_key = cipher_adapter.parse_key(key, use_case, cipher_name)
       
       def check(candidate: str) -> bool:
           # Encrypts candidate with parsed_key and compares to expected ciphertext
           return candidate_ciphertext == expected_ciphertext
       
       return check
   ```
   The key never leaves the closure, and `check` returns only `True` or `False`.
3. The result is passed to `Lockout.record(success)`:
   - 5 consecutive failures trigger a **30-second lockout window**.
   - During lockout, any further attempt raises `ValueError("Locked. Try again in N s.")`.
   - A successful login resets the failure counter to zero.

---

### 3. Recipient Verification via Algorithm Label (`crypto/recipient_check.py`)

In the separate Encrypt and Decrypt windows, classical ciphers are transmitted with an algorithm label:

- **Public Algorithm Label**:
  When transmitting a message from Entity A (Encrypt) to Entity B (Decrypt), the system sends the ciphertext, the optional Hill padding length, and an algorithm label (`"caesar"`, `"playfair"`, or `"hill"`).
  - The algorithm label is public information. The secret key is never sent.
  - The ciphertext is purely what the cipher produces from the plaintext, with no marker or envelope prefix.
- **Recipient Verification & Defense**:
  - The received label is held internally by the Decryption window without displaying it or altering the dropdown selection.
  - When the user clicks **Decrypt Message**:
    - If the user's selected algorithm does not match the received label, decryption is aborted and the window displays in red:
      ```
      "You are not the intended recipient."
      ```
      The window does not reveal which algorithm was expected.
    - If the algorithm matches, decryption runs. If an error occurs during decryption (such as an invalid key format, non-invertible matrix, or incorrect key dimension), the same red error is shown.
    - If a valid key format is entered but the key is wrong, classical ciphers perform the mathematical inverse shift/transformation directly, producing garbled text (a wrong key is not detected).
    - If no label was received (e.g. ciphertext entered by hand), decryption proceeds without any check. Pasting or typing new ciphertext automatically clears the stored label.

---

### 4. Threat Model: Why Encryption Is Not Hashing

Part 3's cipher-based password defence illuminates the fundamental difference between **symmetric encryption** and **one-way hashing**:

| Threat Model Scenario | Encryption-Based Password Protection (Part 3) | Salted One-Way Hashing (Part 4) |
|:---|:---|:---|
| **Online Brute-Force** | Blocked by `Lockout` (5 attempts $\rightarrow$ 30 s lock). | Blocked by rate limiting / lockout. |
| **Offline Attacker with Database Record Only** | Attacker must brute-force the cipher key over the use-case alphabet ($m^{n^2}$). Infeasible for Hill 3x3 ($5.9 \times 10^{15}$ keys), but feasible for small alphabets or via known-plaintext cryptanalysis. | Attacker must brute-force the password against iterated HMAC-SHA256 (PBKDF2). |
| **Server Compromise (Database + Key File Leaked)** | **CATASTROPHIC FAILURE**: Attacker reads `data/secret_keys.json` and decrypts all user passwords in **0.00 seconds**. | **PROTECTED**: Even with the database and salt, PBKDF2 cannot be inverted. Passwords remain safe against direct reversal. |

This comparison highlights why Part 4 introduces salted, slow one-way key derivation functions: symmetric password encryption is only as secure as the key file on the server.

