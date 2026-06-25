from django.test import TestCase

from ocr.eval_metrics import normalize_tokens, word_recall


class NormalizeTokensTest(TestCase):
    def test_strips_accents_and_lowercases(self):
        self.assertEqual(
            normalize_tokens("Comisión Directiva"), ["comision", "directiva"]
        )

    def test_drops_short_tokens(self):
        # "de", "la" (< 3 chars) se descartan; "art" se conserva
        self.assertEqual(normalize_tokens("de la art 17"), ["art"])

    def test_splits_on_punctuation(self):
        self.assertEqual(normalize_tokens("Fiorito, Zamora."), ["fiorito", "zamora"])


class WordRecallTest(TestCase):
    def test_perfect_match(self):
        m = word_recall("Comisión Directiva", "comision directiva")
        self.assertEqual(m["recall"], 1.0)
        self.assertEqual(m["precision"], 1.0)
        self.assertEqual(m["f1"], 1.0)

    def test_partial_recall(self):
        # GT tiene 2 palabras; el OCR recupera 1 → recall 0.5
        m = word_recall("comision", "comision directiva")
        self.assertEqual(m["recall"], 0.5)
        self.assertEqual(m["matched"], 1)
        self.assertEqual(m["gt_total"], 2)

    def test_extra_words_lower_precision_not_recall(self):
        m = word_recall("comision directiva extra ruido", "comision directiva")
        self.assertEqual(m["recall"], 1.0)
        self.assertLess(m["precision"], 1.0)

    def test_empty_extraction(self):
        m = word_recall("", "comision directiva")
        self.assertEqual(m["recall"], 0.0)
        self.assertEqual(m["f1"], 0.0)

    def test_empty_ground_truth_is_safe(self):
        m = word_recall("algo", "")
        self.assertEqual(m["recall"], 0.0)
        self.assertEqual(m["precision"], 0.0)
