# How this project works

## 1. What this project is, and how to start it

This project is a teaching toolkit for classical ciphers, password work, and basic security ideas. It is not a polished commercial app; it is a small Python desktop app built with Tkinter that helps students see how a GUI can call a maths routine without doing the maths itself. The main screen is in [main.py](../main.py#L1-L6), and the actual window setup starts in [SSADToolkitApp](../gui/app.py#L25) inside [gui/app.py](../gui/app.py#L25-L190).

To start it, open the project root and run python [main.py](../main.py#L1-L6). That tiny file calls [run_app()](../gui/app.py#L186-L190), which creates the window and keeps it open until the user closes it.

Files to open for this section
- [main.py](../main.py#L1-L6) — the app entry point.
- [gui/app.py](../gui/app.py#L25-L190) — the main window and page switching logic.

## 2. The map

A simple way to picture the project is this:

```text
ssad_toolkit/
  main.py
  gui/
    app.py
    pages/
      base_page.py
      encryption_page.py
      passwords_page.py
      attacks_page.py
      integrity_page.py
  crypto/
    hill.py
    caesar.py
    playfair.py
  passwords/
    generators.py
    brute_force.py
    dictionary.py
    protection.py
  integrity/
    integrity.py
  tests/
    vectors.py
    test_hill.py
    test_ciphers.py
```

The top-level structure is split into a few teams of work. The GUI folder holds the screen and buttons, the crypto folder holds the cipher maths, and the tests folder checks that the maths still works. The key idea is that the screen and the maths live in different files, and the GUI never does cipher maths itself. That is good for a team because one person can rebuild the screen while another improves the matrix arithmetic, and they only meet at a clear border: the GUI reads values, sends them to a function, and shows the result.

The GUI screen classes live in [gui/app.py](../gui/app.py#L25-L190) and [gui/pages/encryption_page.py](../gui/pages/encryption_page.py#L11-L333). The Hill logic lives in [crypto/hill.py](../crypto/hill.py#L16-L220). The tests live in [tests/test_hill.py](../tests/test_hill.py#L11-L117) and [tests/test_ciphers.py](../tests/test_ciphers.py#L43-L63).

Files to open for this section
- [gui/app.py](../gui/app.py#L25-L190) — the app shell and window layout.
- [gui/pages/encryption_page.py](../gui/pages/encryption_page.py#L11-L333) — the visible screen for encryption tasks.
- [crypto/hill.py](../crypto/hill.py#L16-L220) — the cipher maths itself.

## 3. How the window is built

The story starts in [main.py](../main.py#L1-L6): it just calls [run_app()](../gui/app.py#L186-L190). That function creates an instance of [SSADToolkitApp](../gui/app.py#L25), and the app class sets up the whole desktop window.

Inside [SSADToolkitApp.__init__()](../gui/app.py#L25-L52), the app does a few important jobs in order. It gives the window a title and a size: 1000 by 650 pixels, then it calls [_setup_style()](../gui/app.py#L54-L108) to choose the colours and button style. After that, it creates two big regions: the sidebar on the left and the content area on the right. The sidebar is a frame with a dark background, and the content area is the white space where each page is shown. The code creates these frames in [__init__()](../gui/app.py#L25-L52), with the sidebar built by [_build_sidebar()](../gui/app.py#L130-L159) and the page container built by [_build_pages()](../gui/app.py#L161-L165).

The page stack is a dictionary of page names to page widgets. The app keeps a list called [PAGE_DEFINITIONS](../gui/app.py#L15-L19), which tells it the names and classes for each page. Then [_build_pages()](../gui/app.py#L161-L165) creates a page instance for each item and stores it in the dictionary. Later, when the user clicks a sidebar button, the app calls [show_page()](../gui/app.py#L167-L177), which raises the chosen page to the top and hides the others. The button highlight is updated by [_update_sidebar_state()](../gui/app.py#L179-L184). That is how one simple click swaps the visible screen.

Finally, the app sizes the window to fit its contents by calling [_size_window_to_content()](../gui/app.py#L110-L128), which measures each page and then sets the final window size and centre position. This is why the app opens at a sensible size instead of being tiny or stretched.

Files to open for this section
- [main.py](../main.py#L1-L6) — the entry point.
- [gui/app.py](../gui/app.py#L15-L190) — the full app lifecycle from launch to page switching.

## 4. How pages are built

Every page inherits from [BasePage](../gui/pages/base_page.py#L8-L25), which is a small Tkinter frame that gives each screen a title area and a body area. In plain English, a page is a card in a stack: one card sits in the content area, and the app shows one card at a time. The shared page base creates the title line and then leaves the rest of the space for the real page content. That is why the structure is consistent across the app.

The real page classes are created in their own files. [EncryptionPage](../gui/pages/encryption_page.py#L11-L333) is the page that handles cipher controls and the Hill panel. [PasswordsPage](../gui/pages/passwords_page.py#L8-L16), [AttacksPage](../gui/pages/attacks_page.py#L8-L17), and [IntegrityPage](../gui/pages/integrity_page.py#L8-L17) are still shells: they inherit from the base class and show a simple placeholder message. They are not full implementations yet, so they are placeholders rather than finished tools. In contrast, [EncryptionPage](../gui/pages/encryption_page.py#L11-L333) is the real page today because it already builds the controls and calls the Hill functions.

If someone wants to add a new page, there are only a few places to edit. First, add the new page class in a new file or in a page file. Second, register it in [PAGE_DEFINITIONS](../gui/app.py#L15-L19) inside [gui/app.py](../gui/app.py#L15-L19). Third, if the new page needs a shared title/placeholder style, it can inherit from [BasePage](../gui/pages/base_page.py#L8-L25). The pattern is simple: define the page class, add it to the app, then build widgets inside the page's own constructor.

Files to open for this section
- [gui/pages/base_page.py](../gui/pages/base_page.py#L8-L25) — the shared page layout.
- [gui/pages/encryption_page.py](../gui/pages/encryption_page.py#L11-L333) — a real page example.
- [gui/pages/passwords_page.py](../gui/pages/passwords_page.py#L8-L16) — a placeholder page.
- [gui/app.py](../gui/app.py#L15-L19) — where pages are registered.

## 5. The Hill panel from the user's side

The Hill page is the most complete part of the app. It is built by [_build_hill_panel()](../gui/pages/encryption_page.py#L99-L203), and it is the user-facing version of the Hill cipher. On the left side, the sender is called “Entity A (sender)”, and on the right side, the receiver is called “Entity B (receiver)”. The page starts with an algorithm selector at the top, created by [_build_algorithm_selector()](../gui/pages/encryption_page.py#L44-L62). It lets the user switch between Caesar, Playfair, and Hill.

Here is the sender side, control by control:

- Key size: created in [_build_hill_panel()](../gui/pages/encryption_page.py#L99-L203) with a combobox that offers 2x2 and 3x3. The chosen value is stored in `self.hill_key_size_var` and the matrix cells are rebuilt by [_rebuild_hill_key_grid()](../gui/pages/encryption_page.py#L205-L224).
- Matrix cells: each cell is an editable field created in [_rebuild_hill_key_grid()](../gui/pages/encryption_page.py#L205-L224). The current key is read back by [_current_hill_key()](../gui/pages/encryption_page.py#L226-L238).
- Check key: the button is created in [_build_hill_panel()](../gui/pages/encryption_page.py#L99-L203), and its action calls [_check_hill_key()](../gui/pages/encryption_page.py#L264-L284). It validates the matrix using [hill.validate_key()](../crypto/hill.py#L123-L135).
- Message: the large text box is created in [_build_hill_panel()](../gui/pages/encryption_page.py#L99-L203). The user writes a message there, for example HELP.
- Encrypt: the button is created in [_build_hill_panel()](../gui/pages/encryption_page.py#L99-L203), and it calls [_encrypt_hill_message()](../gui/pages/encryption_page.py#L286-L300).
- Ciphertext: the output field is a read-only entry created in [_build_hill_panel()](../gui/pages/encryption_page.py#L99-L203). The value is set by [_encrypt_hill_message()](../gui/pages/encryption_page.py#L286-L300).
- Padding counter: the label is also created in the same area and is set by [_encrypt_hill_message()](../gui/pages/encryption_page.py#L286-L300). It shows how many X letters were added to finish the block.
- Send to B: this button copies the ciphertext and padding count to Entity B and calls [_send_hill_cipher_to_b()](../gui/pages/encryption_page.py#L302-L309).
- Entity B fields: the receiver side has a ciphertext entry, an optional padding field, and a result field, all created in [_build_hill_panel()](../gui/pages/encryption_page.py#L99-L203).
- Decrypt: the button calls [_decrypt_hill_message()](../gui/pages/encryption_page.py#L311-L325).
- Result: the decrypted text shows up in the receiver result field.
- Status line and colours: the status message starts in [_build_algorithm_selector()](../gui/pages/encryption_page.py#L44-L62) and is updated by [_set_status()](../gui/pages/encryption_page.py#L257-L262). If an error occurs, it turns red and sets the message text. If the action succeeds, it turns green and says the task completed.

This is the user-side story: the user fills in values, presses a button, and the GUI reads the values, sends them to the crypto module, and writes the answer back on the screen.

Files to open for this section
- [gui/pages/encryption_page.py](../gui/pages/encryption_page.py#L44-L325) — the full Hill UI.
- [crypto/hill.py](../crypto/hill.py#L123-L220) — the validation and decryption logic used by the page.

## 6. How the interface and the Hill logic talk to each other

This is the border between the GUI and the maths. The GUI does not do matrix arithmetic. It only reads widgets, checks whether values are valid, and calls the functions in [crypto/hill.py](../crypto/hill.py#L16-L220). The math file then does the actual uppercase cleaning, block splitting, padding, matrix multiplication, inverse matrix work, and decryption.

Here is one complete example, step by step, using the message HELP and the key [[3, 3], [2, 5]]. In a 2x2 Hill key, the matrix is a small table of numbers. The user types HELP into the message box and clicks Encrypt.

1. [_encrypt_hill_message()](../gui/pages/encryption_page.py#L286-L300) reads the text from the message widget.
2. It calls [hill.encrypt()](../crypto/hill.py#L154-L184) with the text and key.
3. Inside [hill.encrypt()](../crypto/hill.py#L154-L184), [hill.normalize()](../crypto/hill.py#L16-L21) removes non-letters and turns everything uppercase, so HELP stays HELP.
4. The function checks the key by calling [hill.validate_key()](../crypto/hill.py#L123-L135), which makes sure the matrix is valid and invertible modulo 26.
5. [hill.padding_length()](../crypto/hill.py#L137-L144) works out how many X letters are needed to complete a 2x2 block. Because HELP has 4 letters, it needs 0 extra X letters in this case, but the app still checks the pad length for the message.
6. The function splits the message into blocks, turns each letter into a number from 0 to 25, multiplies the vector by the key matrix, and converts the result back to letters. With this key, the final ciphertext is HIAT.
7. [_encrypt_hill_message()](../gui/pages/encryption_page.py#L286-L300) writes the ciphertext into the read-only field and sets the padding label.

This is what the user sees: the message HELP becomes the ciphertext HIAT, and the GUI simply reports it on the screen. The math is all in [crypto/hill.py](../crypto/hill.py#L154-L184).

Now look at the second example: BONJOUR with the key [[3, 2], [5, 7]]. This is the one that shows padding clearly. The message has 7 letters, and a 2x2 key works on two-letter blocks. In plain language, 7 does not divide neatly by 2, so the sender adds one filler letter X at the end to reach 8 letters.

1. The user types BONJOUR into the sender field and clicks Encrypt. [ _encrypt_hill_message() ](../gui/pages/encryption_page.py#L286-L300) calls [hill.encrypt()](../crypto/hill.py#L154-L184).
2. [hill.padding_length()](../crypto/hill.py#L137-L144) calculates that one X is needed.
3. The ciphertext is created, and the app stores the padded count in the sender label.
4. The user clicks Send to B. [_send_hill_cipher_to_b()](../gui/pages/encryption_page.py#L302-L309) copies the ciphertext and the padding number into Entity B’s fields.
5. On the receiver side, the user can either leave the padding field empty or type 1 and then click Decrypt. The action calls [_decrypt_hill_message()](../gui/pages/encryption_page.py#L311-L325).
6. [_decrypt_hill_message()](../gui/pages/encryption_page.py#L311-L325) reads the ciphertext and the optional pad length, then calls [hill.decrypt()](../crypto/hill.py#L186-L220).
7. If the padding number is omitted, [hill.decrypt()](../crypto/hill.py#L186-L220) returns the decrypted text including the extra X. If the padding number is 1, it strips the last letter and returns BONJOUR.

The boundary is very clear in this app: the GUI handles screen values and button clicks, while [crypto/hill.py](../crypto/hill.py#L16-L220) handles the mathematics. The GUI also turns errors into a red status message instead of crashing. When an invalid key or a bad padding value appears, [_parse_hill_key()](../gui/pages/encryption_page.py#L240-L255) or [hill.decrypt()](../crypto/hill.py#L186-L220) raises a ValueError, and the GUI catches it in [_check_hill_key()](../gui/pages/encryption_page.py#L264-L284), [_encrypt_hill_message()](../gui/pages/encryption_page.py#L286-L300), or [_decrypt_hill_message()](../gui/pages/encryption_page.py#L311-L325) and sends the message to the red status line using [_set_error_status()](../gui/pages/encryption_page.py#L261-L262).

Files to open for this section
- [gui/pages/encryption_page.py](../gui/pages/encryption_page.py#L264-L325) — the GUI actions behind the buttons.
- [crypto/hill.py](../crypto/hill.py#L16-L220) — the math functions that do the real work.
- [tests/test_hill.py](../tests/test_hill.py#L92-L110) — tests for padding and decryption behavior.

## 7. How the Hill algorithm was built

The Hill cipher works by turning the message into numbers, grouping those numbers into small blocks, and then multiplying each block by a key matrix. The important idea is that we do all arithmetic modulo 26, which means “wrap around” after Z. In other words, after 25 comes 0 again, just like a clock wraps after 12. That is why the alphabet is treated as a circle of 26 letters.

A tiny example helps. Suppose the key is [[3, 3], [2, 5]], and the message is HELP. The app turns H, E, L, P into numbers: H = 7, E = 4, L = 11, P = 15. Then it groups them into a two-letter vector, like [7, 4], and multiplies by the matrix using ordinary arithmetic mod 26. The result is a new vector of numbers, which is converted back to letters. The whole algorithm is implemented in [encrypt()](../crypto/hill.py#L154-L184), and the reverse process is in [decrypt()](../crypto/hill.py#L186-L220).

Here is a plain-English map of the important ideas:

| Idea | Plain explanation | Function (linked) |
| --- | --- | --- |
| Turning letters into numbers | Each letter becomes a number from 0 to 25, so A is 0 and Z is 25. | [normalize()](../crypto/hill.py#L16-L21), [encrypt()](../crypto/hill.py#L154-L184) |
| Cutting the message into blocks | The key size decides the block size. A 2x2 key uses pairs, and a 3x3 key uses triplets. | [padding_length()](../crypto/hill.py#L137-L144), [encrypt()](../crypto/hill.py#L154-L184) |
| Padding | If the message length is not a multiple of the block size, the app adds X to the end so the calculation has a full block. | [padding_length()](../crypto/hill.py#L137-L144), [encrypt()](../crypto/hill.py#L154-L184) |
| Matrix multiplication | Each block is treated like a column vector and multiplied by the key matrix modulo 26. | [_matrix_multiply()](../crypto/hill.py#L146-L152), [encrypt()](../crypto/hill.py#L154-L184) |
| Why the key must be invertible | A valid Hill key must have a determinant that shares no factor with 26. In plain English, the key must be “reversible” so decryption can undo encryption. | [determinant()](../crypto/hill.py#L49-L70), [validate_key()](../crypto/hill.py#L123-L135), [inverse_key()](../crypto/hill.py#L72-L121) |
| GCD and modular arithmetic | GCD means greatest common divisor. If gcd(det, 26) is 1, then the determinant has an inverse modulo 26, so the key can be reversed. | [inverse_key()](../crypto/hill.py#L72-L121) |
| Inverse key | Decryption uses the inverse of the key matrix, not the original key. | [inverse_key()](../crypto/hill.py#L72-L121) |
| Decryption | The receiver multiplies the ciphertext vector by the inverse key, then converts the numbers back to letters. | [decrypt()](../crypto/hill.py#L186-L220) |
| Removing padding | If the sender tells the receiver how many X letters were added, the receiver drops that many letters from the end. | [padding_length()](../crypto/hill.py#L137-L144), [decrypt()](../crypto/hill.py#L186-L220) |

The key idea is that the matrix must be invertible modulo 26. If it is not, there is no way to undo the encryption cleanly. That is why the app checks the key before it will encrypt or decrypt.

Files to open for this section
- [crypto/hill.py](../crypto/hill.py#L16-L220) — the full algorithm and the matrix maths.
- [tests/test_hill.py](../tests/test_hill.py#L11-L117) — the tests that exercise the algorithm.

## 8. The padding number, explained simply

The padding number is the number of filler letters the sender added at the end of the message so the block size fits. The program cannot guess which X is the filler, because the original message could honestly contain X letters. A message like BOX is a good example: it is three letters, and with a 2x2 key the sender must pad to four letters. The encrypted text is then decrypted in two ways in the tests: with a padding number it comes back as BOX, and without it the message still ends with X, which is the filler letter. That behavior is checked in [tests/test_hill.py](../tests/test_hill.py#L92-L110).

This is why the sender and receiver need to agree on the padding count. The sender puts the count in the padding label, and the app copies it to Entity B. The flow is: [_encrypt_hill_message()](../gui/pages/encryption_page.py#L286-L300) sets the sender-side padding display, [_send_hill_cipher_to_b()](../gui/pages/encryption_page.py#L302-L309) copies the ciphertext and padding count to the receiver side, and [_decrypt_hill_message()](../gui/pages/encryption_page.py#L311-L325) passes the number into [hill.decrypt()](../crypto/hill.py#L186-L220). Without that number, decryption has no way to know where the actual message ends and where the filler begins.

This means the X is not random noise; it is a deliberate placeholder, and the receiver must know exactly how many letters to cut off at the end. That is the whole point of the padding number in the interface.

Files to open for this section
- [gui/pages/encryption_page.py](../gui/pages/encryption_page.py#L286-L325) — the sender-to-receiver padding flow.
- [crypto/hill.py](../crypto/hill.py#L137-L220) — the logic that calculates and removes the padding.
- [tests/test_hill.py](../tests/test_hill.py#L92-L110) — the BOX example and padding checks.

## 9. How we know it works

The project uses test vectors and unit tests. A test vector is just a known-good example: a plaintext, a key, and the expected ciphertext. The math team fills in the vectors in [tests/vectors.py](../tests/vectors.py#L1-L13), and the app then checks those examples in [tests/test_ciphers.py](../tests/test_ciphers.py#L43-L63). The file [tests/test_hill.py](../tests/test_hill.py#L11-L117) goes deeper: it checks invalid keys, valid round-trips, padding length, random messages, and the BOX-style padding case.

The method is simple and useful. First, the maths team defines known examples such as HELP and BONJOUR with fixed keys. Then the test code calls the real implementation in [crypto/hill.py](../crypto/hill.py#L16-L220) and compares the output to the expected result. If the output matches, it is a strong sign that the algorithm is behaving correctly. The app does not only test one happy-path case: it also tests broken keys, empty messages, and the padding limits.

To run the tests, use the command shown in [README.md](../README.md): python -m unittest discover -s tests -v. In a normal run, the result looks like “OK” after the test summary, with no failing tests. A passing run means the cipher logic is consistent with the vectors and the edge-case checks.

Files to open for this section
- [tests/vectors.py](../tests/vectors.py#L1-L13) — the known-good examples.
- [tests/test_hill.py](../tests/test_hill.py#L11-L117) — the Hill-specific logic checks.
- [tests/test_ciphers.py](../tests/test_ciphers.py#L43-L63) — the vector runner that exercises the known examples.

## 10. How a teammate adds their own cipher or feature

Use this short checklist when you want to add something new:

1. Put the algorithm maths in the right crypto file, such as [crypto/hill.py](../crypto/hill.py#L16-L220), [crypto/caesar.py](../crypto/caesar.py), or [crypto/playfair.py](../crypto/playfair.py).
2. Add the UI to the page that matches the feature. For the encryption screen, start at [gui/pages/encryption_page.py](../gui/pages/encryption_page.py#L44-L325). If the feature is a new screen, register it in [gui/app.py](../gui/app.py#L15-L19) and make it inherit from [BasePage](../gui/pages/base_page.py#L8-L25).
3. Add a known-good vector to [tests/vectors.py](../tests/vectors.py#L1-L13) and then add logic checks in [tests/test_hill.py](../tests/test_hill.py#L11-L117) or the relevant test module.
4. Place the user-facing error message in the status line that already exists in [_set_status()](../gui/pages/encryption_page.py#L257-L262) and [_set_error_status()](../gui/pages/encryption_page.py#L261-L262).
5. Keep the GUI and maths separate. The GUI should read widgets and call a function; the maths file should do the calculation and return a result.

This pattern is the project’s main rule: screen code calls algorithm code, and the algorithm code does not know anything about the GUI.

Files to open for this section
- [gui/app.py](../gui/app.py#L15-L19) — add a new page registration here.
- [gui/pages/base_page.py](../gui/pages/base_page.py#L8-L25) — shared page pattern.
- [gui/pages/encryption_page.py](../gui/pages/encryption_page.py#L44-L325) — how a real page is built.
- [tests/vectors.py](../tests/vectors.py#L1-L13) — where known examples go.

## 11. Things that are not finished or could be better

This project is a strong teaching shell, but it is not a complete security toolkit. A few parts are clearly placeholders today. The Caesar and Playfair screens are not implemented in [gui/pages/encryption_page.py](../gui/pages/encryption_page.py#L81-L97), and the other page classes show placeholder text in [gui/pages/passwords_page.py](../gui/pages/passwords_page.py#L8-L16), [gui/pages/attacks_page.py](../gui/pages/attacks_page.py#L8-L17), and [gui/pages/integrity_page.py](../gui/pages/integrity_page.py#L8-L17).

The app also has a few rough edges. The status line is helpful, but it is simple: it only stores a message and flips between green and red. There is no formal logging system, no strict error model, and no full screen validation for every field. The project is clearly meant for teaching, not production use.

One practical issue is that [README.md](../README.md) is a little stale compared with the actual repository layout. It describes a top-level folder called ssad_toolkit in one place, while the project itself is already the root folder. That does not break the app, but it does make the project look slightly less tidy than it really is. The practical point is that this is a student toolkit and a team skeleton, not a final polished product.

Files to open for this section
- [gui/pages/encryption_page.py](../gui/pages/encryption_page.py#L81-L97) — the unfinished Caesar and Playfair screens.
- [gui/pages/passwords_page.py](../gui/pages/passwords_page.py#L8-L16) — placeholder password page.
- [gui/pages/attacks_page.py](../gui/pages/attacks_page.py#L8-L17) — placeholder attacks page.
- [gui/pages/integrity_page.py](../gui/pages/integrity_page.py#L8-L17) — placeholder integrity page.

## 12. One-page cheat sheet

Here are the five things to remember:

- The GUI and the cipher maths live in different files, and the GUI never does the matrix work itself.
- The real Hill logic is in [crypto/hill.py](../crypto/hill.py#L16-L220), not in the page widgets.
- Padding is needed when the message length does not fit a full block; the sender and receiver must agree on the count.
- A valid Hill key must be invertible modulo 26, which is why the code checks the determinant and the GCD.
- The app uses tests and vectors to catch mistakes before the project grows bigger.

Table: I want to change X -> open this file

| I want to change X | Open this file |
| --- | --- |
| The whole app window and sidebar | [gui/app.py](../gui/app.py#L25-L190) |
| The shared title/body layout for every page | [gui/pages/base_page.py](../gui/pages/base_page.py#L8-L25) |
| The Hill panel and button actions | [gui/pages/encryption_page.py](../gui/pages/encryption_page.py#L99-L325) |
| The actual Hill algorithm | [crypto/hill.py](../crypto/hill.py#L16-L220) |
| The math test vectors | [tests/vectors.py](../tests/vectors.py#L1-L13) |
| The Hill unit tests | [tests/test_hill.py](../tests/test_hill.py#L11-L117) |
| The general test runner | [tests/test_ciphers.py](../tests/test_ciphers.py#L43-L63) |
| The entry point for the app | [main.py](../main.py#L1-L6) |

That is the project in one sentence: a small GUI shell that sends user inputs to neat maths functions, then writes the answer back to the screen so students can learn the ideas without getting buried in a giant codebase.

Files to open for this section
- [gui/app.py](../gui/app.py#L25-L190) — the app shell and switching logic.
- [gui/pages/encryption_page.py](../gui/pages/encryption_page.py#L99-L325) — the Hill UI.
- [crypto/hill.py](../crypto/hill.py#L16-L220) — the real algorithm.
