"""Python Calculator - a small desktop calculator built with Tkinter.

The module is split into two parts:

* ``CalculatorEngine`` - pure calculation logic, no GUI, easy to test.
* ``CalculatorApp``   - Tkinter window that renders the engine state.

Run the app with::

    python calculator.py
"""

from __future__ import annotations

import tkinter as tk

OPERATORS = ("+", "-", "*", "/")

# --- Look and feel ---------------------------------------------------------

WINDOW_BG = "#1f2430"
DISPLAY_BG = "#161a22"
TEXT_COLOR = "#f5f7fa"
MUTED_COLOR = "#8b93a7"
BUTTON_BG = "#2c3340"
BUTTON_ACTIVE_BG = "#3a4354"
OPERATOR_BG = "#3b6ea5"
OPERATOR_ACTIVE_BG = "#4a83c0"
EQUALS_BG = "#2f9e6b"
EQUALS_ACTIVE_BG = "#38b87c"


class CalculatorEngine:
    """State machine behind the calculator.

    The engine keeps the current entry as a string so the display can show
    exactly what the user typed (including a trailing decimal point).
    """

    MAX_DIGITS = 12

    def __init__(self) -> None:
        self.clear()

    # -- public API ---------------------------------------------------------

    def clear(self) -> None:
        """Reset everything, as if the calculator was just switched on."""
        self._entry = "0"
        self._stored: float | None = None
        self._operator: str | None = None
        self._fresh = True  # next digit starts a brand new number
        self._error = False

    @property
    def display(self) -> str:
        """Text that should be visible on the screen."""
        return self._entry

    @property
    def has_error(self) -> bool:
        return self._error

    def input_digit(self, digit: str) -> None:
        if self._error:
            self.clear()
        if not (len(digit) == 1 and digit.isdigit()):
            raise ValueError(f"not a digit: {digit!r}")

        if self._fresh:
            self._entry = digit
            self._fresh = False
        elif self._entry == "0":
            self._entry = digit
        elif self._digit_count() < self.MAX_DIGITS:
            self._entry += digit

    def input_dot(self) -> None:
        if self._error:
            self.clear()
        if self._fresh:
            self._entry = "0."
            self._fresh = False
        elif "." not in self._entry:
            self._entry += "."

    def toggle_sign(self) -> None:
        if self._error:
            return
        if self._entry.startswith("-"):
            self._entry = self._entry[1:]
        elif self._entry != "0":
            self._entry = "-" + self._entry

    def backspace(self) -> None:
        if self._error:
            self.clear()
            return
        if self._fresh:
            return
        self._entry = self._entry[:-1]
        if self._entry in ("", "-"):
            self._entry = "0"
            self._fresh = True

    def set_operator(self, operator: str) -> None:
        """Store the left operand and remember which operation to apply."""
        if operator not in OPERATORS:
            raise ValueError(f"unknown operator: {operator!r}")
        if self._error:
            return

        # Pressing two operators in a row just replaces the pending one.
        if self._operator is not None and not self._fresh:
            self._apply_pending()
            if self._error:
                return

        self._stored = self._as_float(self._entry)
        self._operator = operator
        self._fresh = True

    def equals(self) -> None:
        """Apply the pending operation, if there is one."""
        if self._error or self._operator is None:
            self._fresh = True
            return

        try:
            result = self._compute(self._stored, self._as_float(self._entry), self._operator)
        except ZeroDivisionError:
            self._show_error()
            return

        self._entry = self._format(result)
        self._stored = None
        self._operator = None
        self._fresh = True

    # -- internals ----------------------------------------------------------

    def _apply_pending(self) -> None:
        try:
            result = self._compute(self._stored, self._as_float(self._entry), self._operator)
        except ZeroDivisionError:
            self._show_error()
            return
        self._stored = result
        self._entry = self._format(result)

    def _show_error(self) -> None:
        self._entry = "Error"
        self._error = True
        self._stored = None
        self._operator = None
        self._fresh = True

    def _digit_count(self) -> int:
        return len(self._entry.replace("-", "").replace(".", ""))

    @staticmethod
    def _as_float(text: str) -> float:
        return float(text.rstrip("."))

    @staticmethod
    def _compute(left: float | None, right: float, operator: str | None) -> float:
        if left is None or operator is None:
            return right
        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            if right == 0:
                raise ZeroDivisionError("division by zero")
            return left / right
        raise ValueError(f"unknown operator: {operator!r}")

    @staticmethod
    def _format(value: float) -> str:
        if value != value or value in (float("inf"), float("-inf")):
            return "Error"
        return f"{value:.10g}"


class CalculatorApp(tk.Tk):
    """Tkinter window wired to :class:`CalculatorEngine`."""

    # (label, engine action) pairs for the 4x5 button grid
    LAYOUT = (
        (("C", "clear"), ("\u232b", "backspace"), ("\u00b1", "sign"), ("\u00f7", "/")),
        (("7", "7"), ("8", "8"), ("9", "9"), ("\u00d7", "*")),
        (("4", "4"), ("5", "5"), ("6", "6"), ("\u2212", "-")),
        (("1", "1"), ("2", "2"), ("3", "3"), ("+", "+")),
        (("0", "0"), (".", "dot"), ("=", "equals")),
    )

    def __init__(self) -> None:
        super().__init__()
        self.engine = CalculatorEngine()

        self.title("Python Calculator")
        self.configure(bg=WINDOW_BG)
        self.resizable(False, False)

        self._build_display()
        self._build_buttons()
        self._bind_keys()
        self._center_window()
        self._refresh()

    # -- construction -------------------------------------------------------

    def _build_display(self) -> None:
        frame = tk.Frame(self, bg=DISPLAY_BG, padx=16, pady=14)
        frame.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=(10, 4))

        self._display_var = tk.StringVar(value="0")
        self._display = tk.Label(
            frame,
            textvariable=self._display_var,
            bg=DISPLAY_BG,
            fg=TEXT_COLOR,
            font=("Segoe UI", 28),
            anchor="e",
            width=14,
        )
        self._display.pack(fill="x")

        self._hint = tk.Label(
            self,
            text="Клавиатура: цифры, + - * /, Enter, Backspace, Esc",
            bg=WINDOW_BG,
            fg=MUTED_COLOR,
            font=("Segoe UI", 8),
        )
        self._hint.grid(row=1, column=0, columnspan=4, pady=(0, 6))

    def _build_buttons(self) -> None:
        for column in range(4):
            self.grid_columnconfigure(column, weight=1)

        for row_index, row in enumerate(self.LAYOUT, start=2):
            for column, (label, action) in enumerate(row):
                if row_index == 6 and label == "0":
                    # "0" spans two columns in the last row
                    button = self._make_button(label, action, width=9)
                    button.grid(row=row_index, column=column, columnspan=2, sticky="nsew", padx=5, pady=5)
                    continue
                if row_index == 6 and label == ".":
                    button = self._make_button(label, action)
                    button.grid(row=row_index, column=3, sticky="nsew", padx=5, pady=5)
                    continue
                button = self._make_button(label, action)
                button.grid(row=row_index, column=column, sticky="nsew", padx=5, pady=5)

    def _make_button(self, label: str, action: str, width: int = 4) -> tk.Button:
        if action in OPERATORS:
            background, active_background = OPERATOR_BG, OPERATOR_ACTIVE_BG
        elif action == "equals":
            background, active_background = EQUALS_BG, EQUALS_ACTIVE_BG
        else:
            background, active_background = BUTTON_BG, BUTTON_ACTIVE_BG

        return tk.Button(
            self,
            text=label,
            width=width,
            font=("Segoe UI", 15),
            bg=background,
            fg=TEXT_COLOR,
            activebackground=active_background,
            activeforeground=TEXT_COLOR,
            relief="flat",
            bd=0,
            highlightthickness=0,
            takefocus=0,
            cursor="hand2",
            command=lambda: self._run(action),
        )

    def _bind_keys(self) -> None:
        self.bind("<Key>", self._on_key)
        # Keep button clicks from stealing keyboard focus.
        self.bind_all("<Button-1>", lambda event: self.focus_set(), add="+")

    # -- behaviour ----------------------------------------------------------

    def _run(self, action: str) -> None:
        engine = self.engine
        if action in "0123456789":
            engine.input_digit(action)
        elif action == "dot":
            engine.input_dot()
        elif action in OPERATORS:
            engine.set_operator(action)
        elif action == "equals":
            engine.equals()
        elif action == "clear":
            engine.clear()
        elif action == "backspace":
            engine.backspace()
        elif action == "sign":
            engine.toggle_sign()
        else:  # pragma: no cover - guarded by LAYOUT
            raise ValueError(f"unknown action: {action!r}")
        self._refresh()

    def _on_key(self, event: tk.Event) -> None:
        char = event.char
        keysym = event.keysym

        if char.isdigit():
            self._run(char)
        elif char in (".", ","):
            self._run("dot")
        elif char in OPERATORS:
            self._run(char)
        elif keysym in ("Return", "KP_Enter") or char == "=":
            self._run("equals")
        elif keysym == "BackSpace":
            self._run("backspace")
        elif keysym == "Escape":
            self._run("clear")
        elif keysym == "Delete":
            self._run("clear")

    def _refresh(self) -> None:
        self._display_var.set(self.engine.display)

    def _center_window(self) -> None:
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 3
        self.geometry(f"+{x}+{y}")


def main() -> None:
    app = CalculatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
