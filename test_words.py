"""Проверки words.json. Запуск: python3 -m unittest -v test_words"""

import json
import re
import unittest
from collections import Counter
from pathlib import Path

WORDS_PATH = Path(__file__).with_name("words.json")
GEORGIAN = re.compile(r"[Ⴀ-ჿᲐ-Ჿⴀ-⴯]")


class WordsJsonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = WORDS_PATH.read_text(encoding="utf-8")
        cls.words = json.loads(cls.raw)

    def test_top_level_is_list(self):
        self.assertIsInstance(self.words, list)
        self.assertGreater(len(self.words), 0)

    def test_entries_have_exact_keys(self):
        for i, w in enumerate(self.words):
            with self.subTest(index=i, entry=w):
                self.assertIsInstance(w, dict)
                self.assertEqual(set(w), {"id", "ka", "tr", "ru"})

    def test_ids_are_unique_positive_ints(self):
        # index.html подставляет id в onclick и в id DOM-узла, поэтому нужен целый, уникальный.
        for w in self.words:
            with self.subTest(entry=w):
                self.assertIs(type(w["id"]), int)
                self.assertGreater(w["id"], 0)
        dups = [i for i, n in Counter(w["id"] for w in self.words).items() if n > 1]
        self.assertEqual(dups, [], "повторяющиеся id")

    def test_required_fields_filled_and_trimmed(self):
        # Как в addWord(): ka и ru обязательны, tr может быть пустым, всё без пробелов по краям.
        for w in self.words:
            with self.subTest(entry=w):
                for key in ("ka", "tr", "ru"):
                    self.assertIsInstance(w[key], str)
                    self.assertEqual(w[key], w[key].strip())
                self.assertTrue(w["ka"])
                self.assertTrue(w["ru"])

    def test_ka_contains_georgian(self):
        for w in self.words:
            with self.subTest(entry=w):
                self.assertRegex(w["ka"], GEORGIAN)

    def test_no_exact_duplicates(self):
        # Одно слово с разными переводами (ის — «тот» и «он/она/оно») допустимо, полная копия — нет.
        pairs = Counter((w["ka"], w["ru"]) for w in self.words)
        self.assertEqual([p for p, n in pairs.items() if n > 1], [], "повторяющиеся пары ka + ru")

    def test_formatting(self):
        # Формат indent 2 без \u-экранирования. Страница пишет файл без перевода строки в конце,
        # поэтому он допускается, но не требуется.
        expected = json.dumps(self.words, indent=2, ensure_ascii=False)
        self.assertEqual(self.raw.rstrip("\n"), expected)


if __name__ == "__main__":
    unittest.main()
