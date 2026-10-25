# Example keys and outputs

This file records verified examples from the actual cipher implementations in the project. These values were checked against the runtime code rather than guessed from stale documentation.

## Caesar

- `Meriem` with key `4` -> `Qivmiq`
- `Zoe` with key `3` -> `crh`
- `Hello World 2026!` with key `5` -> `Mjqqt btwqi 2026!`
- `abc` with key `-3` -> `XYZ`

## Hill

- `HELP` with key `[[3, 3], [2, 5]]` -> `HIAT`
- `BONJOUR` with key `[[3, 2], [5, 7]]` -> `FZFYECTM`
- `ALGORITHM` with key `[[6, 24, 1], [13, 16, 10], [20, 17, 15]]` -> `KCRGONILD`

## Playfair

- `HELLO` with key `MONARCHY` -> `CFSUPM`
- `MEETME` with key `MONARCHY` -> `CLKLCL`
- `INSTRUMENTS` with key `MONARCHY` -> `GATLMZCLRQXA`
- `INFORMATION` with key `MONARCHY` -> `GAPHMORSFAAW`
- `EXAMPLE` with key `KEYWORD` -> `WURPSHWU`
- `ATTACK` with key `MONARCHY` -> `RSSRDE`
- `HELLO` with key `KEYWORD` -> `GYIZSC`
