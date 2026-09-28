"""Проверки words.json. Запуск: python3 -m unittest -v test_words"""

import json
import re
import unittest
from collections import Counter
from pathlib import Path

WORDS_PATH = Path(__file__).with_name("words.json")
GEORGIAN = re.compile(r"[Ⴀ-ჿᲐ-Ჿⴀ-⴯]")

# Схема транскрипции: придыхательные без знака (თ t, ფ p, ქ k, ჩ ch, ც ts),
# смычные с прямым апострофом (ტ t', პ p', კ k', ჭ ch', წ ts', ყ q'), ხ — kh, ღ — gh.
TRANSLIT = {
    "ა": "a", "ბ": "b", "გ": "g", "დ": "d", "ე": "e", "ვ": "v", "ზ": "z", "თ": "t",
    "ი": "i", "კ": "k'", "ლ": "l", "მ": "m", "ნ": "n", "ო": "o", "პ": "p'", "ჟ": "zh",
    "რ": "r", "ს": "s", "ტ": "t'", "უ": "u", "ფ": "p", "ქ": "k", "ღ": "gh", "ყ": "q'",
    "შ": "sh", "ჩ": "ch", "ც": "ts", "ძ": "dz", "წ": "ts'", "ჭ": "ch'", "ხ": "kh",
    "ჯ": "j", "ჰ": "h",
}


def translit(ka):
    return "".join(TRANSLIT.get(c, c) for c in ka)


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

    def test_tr_follows_scheme(self):
        for w in self.words:
            with self.subTest(entry=w):
                self.assertEqual(w["tr"], translit(w["ka"]))

    def test_page_uses_same_scheme(self):
        # Автозаполнение в index.html должно давать ту же транскрипцию, что проверяет тест выше.
        html = WORDS_PATH.with_name("index.html").read_text(encoding="utf-8")
        block = re.search(r"const TRANSLIT = \{(.*?)\};", html, re.S).group(1)
        page = {k: a or b for k, a, b in re.findall(r"""'(.)':(?:'([^']*)'|"([^"]*)")""", block)}
        self.assertEqual(page, TRANSLIT)

    def test_ru_has_no_trailing_separator(self):
        for w in self.words:
            with self.subTest(entry=w):
                self.assertNotRegex(w["ru"], r"[;,]$")

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
