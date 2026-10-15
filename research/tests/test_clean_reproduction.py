from xiangji.clean_reproduction import COMMANDS, DETERMINISTIC_OUTPUTS


def test_clean_reproduction_covers_lock_tests_and_cycle6_outputs() -> None:
    flat = [" ".join(command) for command in COMMANDS]
    assert any("sync --frozen" in command for command in flat)
    assert any("pytest -q" in command for command in flat)
    assert "experiments/cycle6_stress_tests.json" in DETERMINISTIC_OUTPUTS
    assert "figures/fig6_stress_tests.svg" in DETERMINISTIC_OUTPUTS
    assert "manuscript/registries/claims.csv" in DETERMINISTIC_OUTPUTS
