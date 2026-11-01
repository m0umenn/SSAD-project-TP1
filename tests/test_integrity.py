"""Unit tests for integrity and hashing mechanisms (Part 4).

Tests fast hashing, PBKDF2 stretching, constant-time comparison,
record validation, timing estimation, message/file digests and HMAC,
without importing from passwords/ or gui/.
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from integrity import (
    ITERATIONS,
    SALT_BYTES,
    compare_hashes,
    estimate_slowdown,
    generate_salt,
    hash_data,
    hash_file,
    hash_fast,
    hash_protected,
    hmac_sha256,
    parse_record,
    verify_data,
    verify_digest,
    verify_hmac,
    verify_protected,
)


ABC_SHA256 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class TestIntegrityHashing(unittest.TestCase):
    """Tests for integrity.hashing functions and constants."""

    FAST_ITERATIONS = 1000

    def test_constants(self) -> None:
        self.assertEqual(ITERATIONS, 100_000)
        self.assertEqual(SALT_BYTES, 16)

    def test_hash_fast_known_vectors(self) -> None:
        # Standard SHA-256 test vectors specified in requirements
        self.assertEqual(
            hash_fast("abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )
        self.assertEqual(
            hash_fast(""),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )

    def test_hash_fast_invalid_type(self) -> None:
        for bad_input in (123, None, ["abc"], {"a": "b"}, True):
            with self.subTest(bad=bad_input):
                with self.assertRaises(ValueError) as ctx:
                    hash_fast(bad_input)  # type: ignore[arg-type]
                self.assertEqual(str(ctx.exception), "Password must be a string.")

    def test_generate_salt(self) -> None:
        s1 = generate_salt(16)
        s2 = generate_salt(16)
        self.assertEqual(len(s1), 16)
        self.assertEqual(len(s2), 16)
        self.assertNotEqual(s1, s2)
        with self.assertRaises(ValueError):
            generate_salt(0)
        with self.assertRaises(ValueError):
            generate_salt(-1)
        with self.assertRaises(ValueError):
            generate_salt(True)  # type: ignore[arg-type]

    def test_compare_hashes(self) -> None:
        self.assertTrue(compare_hashes("abcdef", "abcdef"))
        self.assertFalse(compare_hashes("abcdef", "abcdeg"))
        self.assertFalse(compare_hashes("abcdef", "abcde"))

    def test_round_trip_and_wrong_password(self) -> None:
        record = hash_protected("3214", iterations=self.FAST_ITERATIONS)
        self.assertTrue(verify_protected("3214", record))
        self.assertFalse(verify_protected("1111", record))

    def test_multiple_round_trips(self) -> None:
        for pw, wrong in (("abcd", "Ab56"), ("Abc123", "secret"), ("jK+73*Dd", "Pass1234")):
            with self.subTest(password=pw):
                record = hash_protected(pw, iterations=self.FAST_ITERATIONS)
                self.assertTrue(verify_protected(pw, record))
                self.assertFalse(verify_protected(wrong, record))

    def test_unique_salts_and_hashes(self) -> None:
        r1 = hash_protected("3214", iterations=self.FAST_ITERATIONS)
        r2 = hash_protected("3214", iterations=self.FAST_ITERATIONS)
        self.assertNotEqual(r1["salt"], r2["salt"])
        self.assertNotEqual(r1["hash"], r2["hash"])

    def test_tampered_and_malformed_records(self) -> None:
        record = hash_protected("101", iterations=self.FAST_ITERATIONS)

        tampered_hash = dict(record)
        orig_hash = str(record["hash"])
        flipped = ("0" if orig_hash[0] != "0" else "1") + orig_hash[1:]
        tampered_hash["hash"] = flipped
        self.assertFalse(verify_protected("101", tampered_hash))

        tampered_salt = dict(record)
        orig_salt = str(record["salt"])
        tampered_salt["salt"] = ("0" if orig_salt[0] != "0" else "1") + orig_salt[1:]
        self.assertFalse(verify_protected("101", tampered_salt))

        malformed_records = [
            "not a dict",
            {},
            {"salt": record["salt"], "iterations": self.FAST_ITERATIONS},
            {"salt": "", "iterations": self.FAST_ITERATIONS, "hash": record["hash"]},
            {"salt": "zz", "iterations": self.FAST_ITERATIONS, "hash": record["hash"]},
            {"salt": record["salt"], "iterations": 0, "hash": record["hash"]},
            {"salt": record["salt"], "iterations": -5, "hash": record["hash"]},
            {"salt": record["salt"], "iterations": True, "hash": record["hash"]},
            {"salt": record["salt"], "iterations": self.FAST_ITERATIONS, "hash": "short"},
            {"salt": record["salt"], "iterations": self.FAST_ITERATIONS, "hash": "g" * 64},
        ]
        for bad in malformed_records:
            with self.subTest(record=bad):
                with self.assertRaises(ValueError) as ctx:
                    verify_protected("101", bad)  # type: ignore[arg-type]
                self.assertEqual(str(ctx.exception), "Malformed record.")

    def test_parse_record(self) -> None:
        record = hash_protected("pass", iterations=100)
        salt_bytes, iters, hash_hex = parse_record(record)
        self.assertEqual(len(salt_bytes), SALT_BYTES)
        self.assertEqual(iters, 100)
        self.assertEqual(len(hash_hex), 64)

    def test_estimate_slowdown(self) -> None:
        self.assertEqual(estimate_slowdown(1000, rate=500.0), 2.0)
        self.assertEqual(estimate_slowdown(1000, rate=500.0, factor=2.5), 5.0)
        self.assertEqual(estimate_slowdown(1000, rate=0.0), float("inf"))


class TestDataIntegrity(unittest.TestCase):
    """Tests for hash_data / verify_data (message integrity)."""

    def test_hash_data_known_vector(self) -> None:
        self.assertEqual(
            hash_data("abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )

    def test_intact_message(self) -> None:
        message = "Rendez-vous demain devant la bibliotheque"
        self.assertTrue(verify_data(message, hash_data(message)))

    def test_modified_message(self) -> None:
        digest = hash_data("bonjour")
        self.assertFalse(verify_data("bonjouR", digest))
        self.assertFalse(verify_data("bonjour ", digest))
        self.assertFalse(verify_data("", digest))

    def test_invalid_inputs(self) -> None:
        for bad_digest in ("", "abc", "z" * 64, None):
            with self.subTest(digest=bad_digest):
                with self.assertRaises(ValueError):
                    verify_data("abc", bad_digest)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            hash_data(None)  # type: ignore[arg-type]


class TestFileDigest(unittest.TestCase):
    """Tests for hash_file (chunked SHA-256 of a file)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def _write(self, name: str, content: bytes) -> Path:
        path = self.dir / name
        path.write_bytes(content)
        return path

    def test_known_vectors(self) -> None:
        self.assertEqual(hash_file(self._write("abc.txt", b"abc")), ABC_SHA256)
        self.assertEqual(hash_file(self._write("empty.txt", b"")), EMPTY_SHA256)

    def test_chunked_equals_whole(self) -> None:
        content = bytes(range(256)) * 50  # 12 800 bytes
        path = self._write("data.bin", content)
        expected = hashlib.sha256(content).hexdigest()
        for chunk_size in (1, 7, 4096, 1_000_000):
            with self.subTest(chunk_size=chunk_size):
                self.assertEqual(hash_file(path, chunk_size=chunk_size), expected)

    def test_str_and_path_accepted(self) -> None:
        path = self._write("abc.txt", b"abc")
        self.assertEqual(hash_file(str(path)), ABC_SHA256)
        self.assertEqual(hash_file(path), ABC_SHA256)

    def test_one_byte_changed(self) -> None:
        original = self._write("a.bin", b"Virement de 100 euros")
        modified = self._write("b.bin", b"Virement de 900 euros")
        self.assertNotEqual(hash_file(original), hash_file(modified))

    def test_file_matches_text_digest(self) -> None:
        path = self._write("msg.txt", "été à 15h".encode("utf-8"))
        self.assertEqual(hash_file(path), hash_data("été à 15h"))

    def test_unreadable_or_invalid(self) -> None:
        with self.assertRaises(ValueError):
            hash_file(self.dir / "missing.txt")
        with self.assertRaises(ValueError):
            hash_file(self.dir)  # a folder, not a file
        for bad_path in (None, 123, b"abc"):
            with self.subTest(path=bad_path):
                with self.assertRaises(ValueError):
                    hash_file(bad_path)  # type: ignore[arg-type]
        path = self._write("abc.txt", b"abc")
        for bad_size in (0, -1, True, "10", 1.5):
            with self.subTest(chunk_size=bad_size):
                with self.assertRaises(ValueError):
                    hash_file(path, chunk_size=bad_size)  # type: ignore[arg-type]


class TestVerifyDigest(unittest.TestCase):
    """Tests for verify_digest (text, bytes or file)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "doc.txt"
        self.path.write_bytes(b"abc")

    def test_text(self) -> None:
        self.assertTrue(verify_digest("abc", ABC_SHA256))
        self.assertFalse(verify_digest("abd", ABC_SHA256))
        self.assertTrue(verify_digest("", EMPTY_SHA256))

    def test_bytes(self) -> None:
        self.assertTrue(verify_digest(b"abc", ABC_SHA256))
        self.assertTrue(verify_digest(bytearray(b"abc"), ABC_SHA256))
        self.assertFalse(verify_digest(b"abC", ABC_SHA256))

    def test_file_with_path_object(self) -> None:
        self.assertTrue(verify_digest(self.path, ABC_SHA256))
        self.path.write_bytes(b"abd")
        self.assertFalse(verify_digest(self.path, ABC_SHA256))

    def test_str_is_text_unless_is_path(self) -> None:
        # The text "<path>" is not mistaken for a file name by default.
        self.assertFalse(verify_digest(str(self.path), ABC_SHA256))
        self.assertTrue(verify_digest(str(self.path), ABC_SHA256, is_path=True))

    def test_uppercase_digest_accepted(self) -> None:
        self.assertTrue(verify_digest("abc", ABC_SHA256.upper()))

    def test_invalid_inputs(self) -> None:
        for bad_digest in ("", "abc", "z" * 64, " " + ABC_SHA256[1:], "0x" + ABC_SHA256[2:], None, 42):
            with self.subTest(digest=bad_digest):
                with self.assertRaises(ValueError):
                    verify_digest("abc", bad_digest)  # type: ignore[arg-type]
        for bad_data in (None, 123, ["abc"]):
            with self.subTest(data=bad_data):
                with self.assertRaises(ValueError):
                    verify_digest(bad_data, ABC_SHA256)
        with self.assertRaises(ValueError):
            verify_digest("abc", ABC_SHA256, is_path="yes")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            verify_digest(Path(self.tmp.name) / "missing.txt", ABC_SHA256)


class TestHmac(unittest.TestCase):
    """Tests for hmac_sha256 / verify_hmac (authenticity)."""

    # RFC 4231 test vectors for HMAC-SHA-256
    RFC_CASES = (
        (b"\x0b" * 20, b"Hi There",
         "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7"),
        (b"Jefe", b"what do ya want for nothing?",
         "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"),
    )

    def test_rfc_4231_vectors(self) -> None:
        for key, message, expected in self.RFC_CASES:
            with self.subTest(key=key):
                self.assertEqual(hmac_sha256(key, message), expected)
                self.assertTrue(verify_hmac(key, message, expected))

    def test_str_and_bytes_equivalent(self) -> None:
        self.assertEqual(
            hmac_sha256("Jefe", "what do ya want for nothing?"),
            hmac_sha256(b"Jefe", b"what do ya want for nothing?"),
        )

    def test_format_and_determinism(self) -> None:
        tag = hmac_sha256("secret", "bonjour")
        self.assertEqual(len(tag), 64)
        self.assertEqual(tag, tag.lower())
        self.assertEqual(tag, hmac_sha256("secret", "bonjour"))

    def test_differs_from_plain_digest(self) -> None:
        self.assertNotEqual(hmac_sha256("secret", "abc"), hash_data("abc"))

    def test_key_changes_tag(self) -> None:
        self.assertNotEqual(hmac_sha256("key1", "abc"), hmac_sha256("key2", "abc"))

    def test_valid_message(self) -> None:
        tag = hmac_sha256("shared-secret", "Virement de 100 euros a Meriem")
        self.assertTrue(verify_hmac("shared-secret", "Virement de 100 euros a Meriem", tag))

    def test_one_character_change_breaks_tag(self) -> None:
        tag = hmac_sha256("shared-secret", "Virement de 100 euros a Meriem")
        self.assertFalse(verify_hmac("shared-secret", "Virement de 900 euros a Meriem", tag))
        self.assertFalse(verify_hmac("shared-secret", "Virement de 100 euros a Meriem ", tag))

    def test_wrong_key_fails(self) -> None:
        tag = hmac_sha256("shared-secret", "bonjour")
        self.assertFalse(verify_hmac("wrong-secret", "bonjour", tag))

    def test_attacker_cannot_forge_with_plain_hash(self) -> None:
        # An attacker who edits the message and recomputes a plain SHA-256
        # digest does NOT obtain a valid HMAC tag.
        forged_message = "Virement de 900 euros a Meriem"
        forged_tag = hash_data(forged_message)
        self.assertFalse(verify_hmac("shared-secret", forged_message, forged_tag))

    def test_uppercase_tag_accepted(self) -> None:
        tag = hmac_sha256("k", "m")
        self.assertTrue(verify_hmac("k", "m", tag.upper()))

    def test_invalid_inputs(self) -> None:
        tag = hmac_sha256("k", "m")
        for bad_tag in ("", "abc", "z" * 64, tag[:-1], tag + "0", None, 42):
            with self.subTest(tag=bad_tag):
                with self.assertRaises(ValueError):
                    verify_hmac("k", "m", bad_tag)  # type: ignore[arg-type]
        for bad_key in ("", b"", None, 123):
            with self.subTest(key=bad_key):
                with self.assertRaises(ValueError):
                    hmac_sha256(bad_key, "m")  # type: ignore[arg-type]
        for bad_message in (None, 123, ["m"]):
            with self.subTest(message=bad_message):
                with self.assertRaises(ValueError):
                    hmac_sha256("k", bad_message)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()