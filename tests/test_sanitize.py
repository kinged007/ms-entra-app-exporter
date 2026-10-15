
from utils.dict import dict_walk, filter_dict, merge_dicts
from utils.time import nice_time
from utils.validate import redact_value


def test_merge_dicts_shallow():
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 3, "c": 4}
    merge_dicts(d1, d2)
    assert d1 == {"a": 1, "b": 3, "c": 4}


def test_merge_dicts_nested():
    d1 = {"a": {"x": 1, "y": 2}}
    d2 = {"a": {"y": 99, "z": 3}}
    merge_dicts(d1, d2)
    assert d1 == {"a": {"x": 1, "y": 99, "z": 3}}


def test_filter_dict_exclude():
    data = {
        "password": "secret",
        "displayName": "hello",
        "nested": {"password": "x", "keep": "y"},
    }
    out = filter_dict(data, "password", exclude=True)
    assert "password" not in out
    assert out["displayName"] == "hello"
    assert "password" not in out["nested"]
    assert out["nested"]["keep"] == "y"


def test_filter_dict_include():
    data = {"password": "secret", "displayName": "hello"}
    out = filter_dict(data, "password", exclude=False)
    assert "password" in out
    assert "displayName" not in out


def test_dict_walk_replaces_strings():
    data = {
        "a": "hello world",
        "b": {"c": "hello world"},
        "d": ["hello world", {"e": "hello"}],
    }

    def replacer(_k, v):
        if isinstance(v, str):
            return v.replace("hello", "hi")
        return v

    out = dict_walk(data, replacer)
    assert out["a"] == "hi world"
    assert out["b"]["c"] == "hi world"


def test_redact_value_replaces_appid():
    data = {"appId": "abc-123", "nested": {"value": "prefix abc-123 suffix"}}
    redact_value(data, "abc-123", "__REDACTED__")
    assert data["appId"] == "__REDACTED__"
    assert data["nested"]["value"] == "prefix __REDACTED__ suffix"


def test_nice_time_format():
    t = nice_time()
    # "YYYY-MM-DD HH.MM.SS"
    assert len(t) == 19
    assert t[4] == "-" and t[7] == "-"
    assert t[10] == " " and t[13] == "." and t[16] == "."


def test_sanitize_app_data_application():
    from utils.validate import sanitize_app_data

    # ApplicationModel intentionally excludes appId (read-only Graph field)
    # so the test verifies sanitization redacts values before model construction
    apps = [{"displayName": "Test App", "appId": "111-222", "notes": "refs 111-222"}]
    result = sanitize_app_data(apps, "Application")
    assert len(result) == 1
    assert result[0].displayName == "Test App"
    # notes field should have appId redacted
    assert "__APPID_REDACTED__" in (result[0].notes or "")


def test_sanitize_app_data_service_principal():
    from utils.validate import sanitize_app_data

    sps = [{"displayName": "SP One", "appId": "999-888"}]
    result = sanitize_app_data(sps, "Service Principal")
    assert len(result) == 1
    assert result[0].displayName == "SP One"
