from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

from benchmarks import _data  # noqa: E402

REFERENCE_DIR = Path(__file__).parent / "data"
REFERENCE_NAME = "uniform_n1000_t1000_s20240419"
# numpy of eras 0, A, B, C
REFERENCE_WRITERS = ["1.16", "1.20", "1.26", "2.3"]


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(_data, "DATA_DIR", tmp_path)
    return tmp_path


def test_generated_then_loaded_data_are_identical(data_dir):
    """The first call writes a verified .npy file; the second reads the same array from it."""
    first = _data.uniform_events(1000, 1000)
    assert (data_dir / (REFERENCE_NAME + ".npy")).exists()
    second = _data.uniform_events(1000, 1000)
    np.testing.assert_array_equal(first, second)


def test_corrupted_file_is_rejected(data_dir):
    """A stored file whose content differs from the registered checksum raises an error."""
    _data.uniform_events(1000, 1000)
    path = data_dir / (REFERENCE_NAME + ".npy")
    arr = np.load(str(path))
    arr[0] += 1
    np.save(str(path), arr)
    with pytest.raises(RuntimeError):
        _data.uniform_events(1000, 1000)


@pytest.mark.parametrize("writer", REFERENCE_WRITERS)
def test_files_written_by_every_era_numpy_load_here(writer):
    """Reference files written by each era's numpy load in this numpy with the registered checksum."""
    arr = np.load(str(REFERENCE_DIR / "{}-numpy{}.npy".format(REFERENCE_NAME, writer)), allow_pickle=False)
    assert _data.checksum(arr) == _data.CHECKSUMS[REFERENCE_NAME]
