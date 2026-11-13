import json

import pytest

from tzar_widescreen.manifest import FILE, DamagedManifest, Manifest


def test_save_and_load(tmp_path):
    manifest = Manifest(version="0.2.0", width=1368, tzar_ini={"VIDEO/DIRECTXDEVICE": "-1", "X/Y": None},
                        moved_aside=["ddraw.dll"])
    manifest.save(tmp_path)
    assert Manifest.load(tmp_path) == manifest


def test_no_manifest_means_not_installed(tmp_path):
    assert Manifest.load(tmp_path) is None


def test_manifest_from_0_1_0_has_no_width(tmp_path):
    (tmp_path / FILE).write_text(json.dumps({"version": "0.1.0", "tzar_ini": {}, "moved_aside": []}))
    manifest = Manifest.load(tmp_path)
    assert manifest.width == 1832  # the only width 0.1.0 used


def test_unknown_keys_are_ignored(tmp_path):
    (tmp_path / FILE).write_text(json.dumps({"version": "9.0.0", "width": 1500, "from_the_future": True}))
    assert Manifest.load(tmp_path).width == 1500


@pytest.mark.parametrize("content", [
    '{"version": "0.2.0"',                            # cut off
    "[]",                                             # not an object
    '{"width": 1832}',                                # no version
    '{"version": "0.2.0", "width": "wide"}',          # wrong type
    '{"version": "0.2.0", "moved_aside": "ddraw"}',   # wrong type
    '{"version": "0.2.0", "tzar_ini": {"A/B": 1}}',   # wrong type
])
def test_damaged_manifest_is_reported(tmp_path, content):
    (tmp_path / FILE).write_text(content)
    with pytest.raises(DamagedManifest):
        Manifest.load(tmp_path)
