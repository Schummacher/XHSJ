from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DICT = ROOT / "xhsj.dict.yaml"
SCHEMA = ROOT / "xhsj.schema.yaml"


def read_import_tables():
    in_imports = False
    tables = []
    for line in DICT.read_text(encoding="utf-8").splitlines():
        if line.strip() == "import_tables:":
            in_imports = True
            continue
        if in_imports:
            match = re.match(r"^\s{2}-\s+([A-Za-z0-9_.]+)\s*$", line)
            if match:
                tables.append(match.group(1))
                continue
            if line and not line.startswith("  ") and not line.startswith("#"):
                break
    return tables


def read_entries(path):
    entries = []
    body = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line == "...":
            body = True
            continue
        if not body or not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) >= 2:
            entries.append((fields[0], fields[1].split()[0]))
    return entries


def test_import_tables_exist():
    tables = read_import_tables()
    assert tables, "主词典没有 import_tables"
    missing = [table for table in tables if not (ROOT / f"{table}.dict.yaml").is_file()]
    assert not missing, f"主词典引用了不存在的词库：{missing}"


def test_missing_xhsj_ow_is_removed():
    assert "xhsj.ow" not in read_import_tables()


def test_experimental_tables_are_not_imported():
    experimental = {
        "xhsj.dj",
        "xhsj.jmma2",
        "xhsj.jmma3",
        "xhsj.jmma4",
        "xhsj.qrma1",
        "xhsj.qrma2",
        "xhsj.qrma3",
        "xhsj.qrma4",
        "xhsj.qrma5",
    }
    assert not experimental.intersection(read_import_tables())


def test_schema_declares_auto_select_and_auto_select_is_safe_value():
    text = SCHEMA.read_text(encoding="utf-8")
    assert "dictionary: xhsj" in text
    assert "auto_select: true" in text


def test_imported_dict_entries_have_codes():
    tables = read_import_tables()
    for table in tables:
        path = ROOT / f"{table}.dict.yaml"
        for text, code in read_entries(path):
            assert text.strip(), f"{path.name} 存在空文本词条"
            assert code.strip(), f"{path.name} 中 {text!r} 缺少编码"


def test_fixed_coverage_entries():
    coverage = [
        ("xhsj.erma.dict.yaml", "阿", "a"),
        ("xhsj.sima.dict.yaml", "方案", "fhan"),
        ("xhsj.sjma.dict.yaml", "条形码", "txm"),
    ]
    for filename, text, code in coverage:
        entries = read_entries(ROOT / filename)
        assert (text, code) in entries, f"{filename} 缺少固定词条 {text}\t{code}"


if __name__ == "__main__":
    tests = [
        value
        for name, value in globals().items()
        if name.startswith("test_") and callable(value)
    ]
    failed = []
    for test in tests:
        try:
            test()
            print(f"[PASS] {test.__name__}")
        except Exception as exc:
            failed.append((test.__name__, str(exc)))
            print(f"[FAIL] {test.__name__}: {exc}")
    if failed:
        raise SystemExit(1)
