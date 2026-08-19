from pathlib import Path

from factorysoftware.state import append_log, generate_board, write_board


def test_generate_board_no_events(tmp_path: Path):
    board = generate_board(tmp_path)
    assert "Tablero de la Fábrica" in board
    assert "no editar a mano" in board


def test_generate_board_shows_phase_gate_status(tmp_path: Path):
    append_log(tmp_path, "phase_gate", {"phase": "requirements", "result": "approved", "iterations": 1})
    board = generate_board(tmp_path)
    assert "Requerimientos" in board
    assert "✅" in board


def test_generate_board_shows_epic_table(tmp_path: Path):
    append_log(
        tmp_path,
        "pipeline_step",
        {"phase": "construction", "step_id": "task_execution", "scope": "EPIC-1", "estado": "iniciado"},
    )
    append_log(
        tmp_path,
        "pipeline_step",
        {"phase": "construction", "step_id": "pr_gate", "scope": "EPIC-2", "estado": "completado"},
    )
    board = generate_board(tmp_path)
    assert "EPIC-1" in board
    assert "EPIC-2" in board
    assert "task_execution" in board


def test_write_board_creates_file_and_overwrites(tmp_path: Path):
    write_board(tmp_path)
    board_path = tmp_path / ".factory" / "board.md"
    assert board_path.exists()
    board_path.write_text("edición manual del usuario", encoding="utf-8")
    write_board(tmp_path)
    assert "edición manual" not in board_path.read_text(encoding="utf-8")
