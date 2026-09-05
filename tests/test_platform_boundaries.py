from pathlib import Path

from scripts.check_platform_boundaries import COMPANION, RAG, SHARED, check_repository


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_shared_package_may_import_another_shared_package(tmp_path: Path) -> None:
    _write(tmp_path, "packages/fretboard/model.py", "from packages.steel_theory import pitch\n")
    _write(tmp_path, "packages/steel_theory/pitch.py", "VALUE = 1\n")

    violations, scanned = check_repository(tmp_path)

    assert violations == []
    assert scanned == 2


def test_shared_package_may_not_import_an_app(tmp_path: Path) -> None:
    _write(tmp_path, "packages/fretboard/model.py", "from apps.steel_guitar_rag import settings\n")

    violations, _ = check_repository(tmp_path)

    assert len(violations) == 1
    assert violations[0].source_scope == SHARED
    assert violations[0].target_scope == RAG


def test_transitional_products_may_not_import_each_other(tmp_path: Path) -> None:
    _write(tmp_path, "steel_guitar_rag/app.py", "from partner_companions import travis_howdy\n")
    _write(tmp_path, "partner_companions/travis_howdy/release.py", "import steel_guitar_rag.api\n")

    violations, _ = check_repository(tmp_path)

    assert {(item.source_scope, item.target_scope) for item in violations} == {
        (RAG, COMPANION),
        (COMPANION, RAG),
    }


def test_relative_javascript_import_cannot_cross_apps(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "apps/travis-companion/src/howdy.js",
        'import "../../steel-guitar-rag/src/answer.js";\n',
    )
    _write(tmp_path, "apps/steel-guitar-rag/src/answer.js", "export const answer = true;\n")

    violations, _ = check_repository(tmp_path)

    assert len(violations) == 1
    assert violations[0].source_scope == COMPANION
    assert violations[0].target_scope == RAG
