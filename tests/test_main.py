import pytest

import main


def run_cli(monkeypatch, capsys, inputs):
    responses = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))
    main.main()
    return capsys.readouterr().out


def test_cli_keeps_existing_calculator_features(monkeypatch, capsys):
    output = run_cli(
        monkeypatch,
        capsys,
        [
            "1", "2 3 4",
            "5", "sin(pi / 2) + √25",
            "6", "x^2 - 5x + 6 = 0",
            "7", "(x + 2)^3",
            "0",
        ],
    )

    assert "Result: 9.0" in output
    assert "Result: 6.0" in output
    assert "x1 = 2.0" in output
    assert "x2 = 3.0" in output
    assert "Expansion: x^3 + 6x^2 + 12x + 8" in output
    assert "Goodbye!" in output


def test_cli_reports_calculation_errors_without_crashing(monkeypatch, capsys):
    output = run_cli(
        monkeypatch,
        capsys,
        ["4", "10 0", "5", "2 / 0", "0"],
    )

    assert "Error: Cannot divide by zero." in output
    assert "Error:" in output
    assert "Goodbye!" in output


def test_cli_handles_invalid_numeric_input(monkeypatch, capsys):
    output = run_cli(monkeypatch, capsys, ["1", "not-a-number 2", "0"])

    assert "Error: Please enter valid numbers." in output
    assert "Goodbye!" in output


def test_cli_handles_invalid_menu_choice(monkeypatch, capsys):
    output = run_cli(monkeypatch, capsys, ["99", "0"])

    assert "Invalid choice." in output
    assert "Goodbye!" in output
