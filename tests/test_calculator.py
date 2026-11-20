"""Automatic tests for the calculator logic.

Run from the project root::

    python -m unittest -v
"""

import unittest

from calculator import CalculatorEngine


class EngineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.calc = CalculatorEngine()

    def press(self, *keys: str) -> None:
        """Type a sequence of keys: digits, '.', operators or '='."""
        for key in keys:
            if key in "+-*/":
                self.calc.set_operator(key)
            elif key == "=":
                self.calc.equals()
            elif key == ".":
                self.calc.input_dot()
            else:
                self.calc.input_digit(key)


class TestInitialState(EngineTestCase):
    def test_starts_with_zero(self):
        self.assertEqual(self.calc.display, "0")
        self.assertFalse(self.calc.has_error)

    def test_leading_zero_is_replaced(self):
        self.press("0", "0", "7")
        self.assertEqual(self.calc.display, "7")


class TestTyping(EngineTestCase):
    def test_digits_are_appended(self):
        self.press("1", "2", "3")
        self.assertEqual(self.calc.display, "123")

    def test_decimal_point(self):
        self.press("3", ".", "1", "4")
        self.assertEqual(self.calc.display, "3.14")

    def test_only_one_decimal_point(self):
        self.press("3", ".", ".", "5")
        self.assertEqual(self.calc.display, "3.5")

    def test_decimal_point_after_operator(self):
        self.press("2", "+", ".")
        self.assertEqual(self.calc.display, "0.")

    def test_digit_limit(self):
        for _ in range(CalculatorEngine.MAX_DIGITS + 5):
            self.calc.input_digit("9")
        self.assertEqual(len(self.calc.display), CalculatorEngine.MAX_DIGITS)

    def test_backspace_removes_last_digit(self):
        self.press("4", "5", "6")
        self.calc.backspace()
        self.assertEqual(self.calc.display, "45")

    def test_backspace_to_zero(self):
        self.press("8")
        self.calc.backspace()
        self.assertEqual(self.calc.display, "0")

    def test_sign_toggle(self):
        self.press("5")
        self.calc.toggle_sign()
        self.assertEqual(self.calc.display, "-5")
        self.calc.toggle_sign()
        self.assertEqual(self.calc.display, "5")


class TestOperations(EngineTestCase):
    def test_addition(self):
        self.press("2", "+", "3", "=")
        self.assertEqual(self.calc.display, "5")

    def test_subtraction(self):
        self.press("1", "0", "-", "4", "=")
        self.assertEqual(self.calc.display, "6")

    def test_multiplication(self):
        self.press("6", "*", "7", "=")
        self.assertEqual(self.calc.display, "42")

    def test_division(self):
        self.press("8", "/", "2", "=")
        self.assertEqual(self.calc.display, "4")

    def test_decimal_result_is_rounded_for_display(self):
        self.press("0", ".", "1", "+", "0", ".", "2", "=")
        self.assertEqual(self.calc.display, "0.3")

    def test_negative_result(self):
        self.press("3", "-", "9", "=")
        self.assertEqual(self.calc.display, "-6")

    def test_chained_operations_are_left_to_right(self):
        # 2 + 3 * 4 is evaluated as (2 + 3) * 4 = 20, like a pocket calculator.
        self.press("2", "+", "3", "*", "4", "=")
        self.assertEqual(self.calc.display, "20")

    def test_operator_can_be_replaced(self):
        self.press("5", "+", "*", "3", "=")
        self.assertEqual(self.calc.display, "15")

    def test_equals_without_operator_keeps_value(self):
        self.press("7", "=")
        self.assertEqual(self.calc.display, "7")

    def test_equals_twice_does_not_repeat_operation(self):
        self.press("2", "+", "2", "=", "=")
        self.assertEqual(self.calc.display, "4")


class TestErrors(EngineTestCase):
    def test_division_by_zero(self):
        self.press("5", "/", "0", "=")
        self.assertEqual(self.calc.display, "Error")
        self.assertTrue(self.calc.has_error)

    def test_division_by_zero_while_chaining(self):
        self.press("5", "/", "0", "+")
        self.assertEqual(self.calc.display, "Error")
        self.assertTrue(self.calc.has_error)

    def test_typing_after_error_starts_new_number(self):
        self.press("5", "/", "0", "=")
        self.press("9")
        self.assertEqual(self.calc.display, "9")
        self.assertFalse(self.calc.has_error)

    def test_clear_resets_everything(self):
        self.press("5", "/", "0", "=")
        self.calc.clear()
        self.assertEqual(self.calc.display, "0")
        self.assertFalse(self.calc.has_error)

    def test_unknown_operator_is_rejected(self):
        with self.assertRaises(ValueError):
            self.calc.set_operator("^")


if __name__ == "__main__":
    unittest.main()
