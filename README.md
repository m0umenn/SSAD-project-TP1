# SSAD Toolkit

SSAD Toolkit is a Python 3.10+ desktop application for classical encryption exercises. It uses the standard library only: Tkinter/ttk for the GUI and small algorithm modules for Caesar, Playfair, and Hill.

## Run on Windows

From the project root, run:

```bash
python main.py
```

## Current status

- Caesar is implemented in `crypto/caesar.py`.
- Hill is implemented in `crypto/hill.py`.
- Playfair is implemented in `crypto/playfair.py`.
- The encryption page includes Caesar, Playfair, and Hill panels. Keys are always entered manually; no default or pre-filled keys exist in the interface.
- Entity B (receiver) has its own key field / matrix grid in all three panels. "Send to B" transfers only ciphertext (and Hill padding count), never keys.
- A "Clear keys" button clears key fields across sender and receiver. Hill grids follow key size changes and clear both grids on size change or algorithm switch.
- Password defence is implemented in `passwords/generators.py`, `passwords/protection.py`, and `gui/pages/passwords_page.py` (use cases 1 and 2, and Case 3 across lengths L=4, L=6, L=8 over the 64-character alphabet `a-z, A-Z, 0-9, +, *`, fast SHA-256 hash, PBKDF2-HMAC-SHA256 salted storage, constant-time verification, `make_checker`, `Lockout`, and the `SSADToolkitApp.shared` hand-off).
- Password attack modules (`passwords/brute_force.py`, `passwords/dictionary.py`), cipher attack modules (`attacks/*.py`), and `integrity/integrity.py` remain stubs.

## Project Tree

```text
SSAD/
  benchmarks.py
  main.py
  PROJECT_UPDATE.md
  README.md
  attacks/
    __init__.py
    caesar_attack.py
    hill_attack.py
    playfair_attack.py
  crypto/
    __init__.py
    caesar.py
    hill.py
    playfair.py
  docs/
    EXAMPLE_KEYS.md
    HOW_IT_WORKS.md
    PROJECT_GUIDE.md
  gui/
    __init__.py
    app.py
    background.py
    pages/
      __init__.py
      attacks_page.py
      base_page.py
      encryption_page.py
      integrity_page.py
      passwords_page.py
  integrity/
    __init__.py
    integrity.py
  passwords/
    __init__.py
    brute_force.py
    dictionary.py
    generators.py
    protection.py
  tests/
    __init__.py
    test_ciphers.py
    test_hill.py
    test_protection.py
    test_smoke.py
    vectors.py
```

## Verified example values

The application uses the real implementation in the crypto modules. Examples that were verified in the code are:

- Caesar: `Meriem` with key `4` -> `Qivmiq`
- Caesar: `Hello World 2026!` with key `5` -> `Mjqqt btwqi 2026!`
- Hill: `HELP` with key `[[3, 3], [2, 5]]` -> `HIAT`
- Hill: `BONJOUR` with key `[[3, 2], [5, 7]]` -> `FZFYECTM`
- Hill: `ALGORITHM` with key `[[6, 24, 1], [13, 16, 10], [20, 17, 15]]` -> `KCRGONILD`
- Playfair: `HELLO` with key `MONARCHY` -> `CFSUPM`
- Playfair: `MEETME` with key `MONARCHY` -> `CLKLCL`
- Playfair: `INSTRUMENTS` with key `MONARCHY` -> `GATLMZCLRQXA`
- Playfair: `INFORMATION` with key `MONARCHY` -> `GAPHMORSFAAW`
- Playfair: `EXAMPLE` with key `KEYWORD` -> `WURPSHWU`

## Running Tests

Run the full unit test suite (34 tests, all passing, including `tests/test_protection.py`, `tests/test_hill.py`, `tests/test_ciphers.py`, and `tests/test_smoke.py`) with:

```bash
python -m unittest discover -s tests -v
```

Run only the password defence tests with:

```bash
python -m unittest tests/test_protection.py -v
```

Run the benchmark helper with:

```bash
python benchmarks.py
```