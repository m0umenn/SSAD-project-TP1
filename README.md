# SSAD Toolkit

SSAD Toolkit is a beginner-friendly Python 3.10+ GUI skeleton for a university practical work about classical encryption, password attacks, and integrity tools. The app uses only the standard library: Tkinter and ttk.

## Run on Windows

From the project root, run:

```bash
python main.py
```

## Project Tree

```text
ssad_toolkit/
  main.py
  gui/
    __init__.py
    app.py
    pages/
      __init__.py
      base_page.py
      encryption_page.py
      passwords_page.py
      attacks_page.py
      integrity_page.py
  crypto/
    __init__.py
    caesar.py
    playfair.py
    hill.py
  passwords/
    __init__.py
    generators.py
    brute_force.py
    dictionary.py
    protection.py
  integrity/
    __init__.py
    integrity.py
  README.md
  .gitignore
```

## Where To Put Your Part

Use one file per teammate whenever possible. That keeps merge conflicts small.

### GUI team

- Edit `gui/pages/encryption_page.py` for the encryption/decryption screen.
- Edit `gui/pages/passwords_page.py` for password generation and attack tools.
- Edit `gui/pages/attacks_page.py` for attack demos and analysis widgets.
- Edit `gui/pages/integrity_page.py` for authenticity and integrity tools.
- Each page already inherits from `BasePage` in `gui/pages/base_page.py`.
- Add your widgets inside the page class where the `# TODO` comment already points.
- If you add a new page later, register it in `gui/app.py` by adding one line to `PAGE_DEFINITIONS`.

### Crypto team

- Put the algorithm logic in `crypto/caesar.py`, `crypto/playfair.py`, and `crypto/hill.py`.
- Keep the stubs and docstrings in place until the real implementation is ready.

### Passwords team

- Put password set helpers in `passwords/generators.py`.
- Put brute-force code in `passwords/brute_force.py`.
- Put dictionary attack code in `passwords/dictionary.py`.
- Put password protection helpers in `passwords/protection.py`.

### Integrity team

- Put hashing and verification helpers in `integrity/integrity.py`.

Rule: do not edit another person's file without telling them first.

## Git Workflow For Teammates

1. Clone the repository.
2. Create your own branch:

```bash
git checkout -b yourname-feature
```

3. Make your changes and commit them.
4. Push your branch:

```bash
git push -u origin yourname-feature
```

5. Open a pull request.

## First-Time Push To GitHub

If the repository is new on your machine, use this flow once:

```bash
git init
git add .
git commit -m "Initial SSAD Toolkit skeleton"
git branch -M main
git remote add origin https://github.com/m0umenn/SSAD-project-TP1.git
git push -u origin main
```