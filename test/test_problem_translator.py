import unittest

from services.problem_translator import translate_problem


class ProblemTranslatorTests(unittest.TestCase):
    def test_translates_known_problem(self):
        self.assertEqual(
            translate_problem("High swap space usage (less than 50% free)"),
            "Memori Cadangan (Swap) mulai menipis (kurang dari 50%)",
        )

    def test_preserves_unknown_problem(self):
        problem = "A new Zabbix problem without translation"
        self.assertEqual(translate_problem(problem), problem)


if __name__ == "__main__":
    unittest.main()