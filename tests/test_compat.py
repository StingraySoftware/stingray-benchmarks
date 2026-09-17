from benchmarks import _compat


class _Events:
    def __init__(self, name):
        self.name = name

    def to_lc(self, dt):
        return ("lc", self.name, dt)


class _NewSpectrum:
    def __init__(self, *data, dt=None, segment_size=None, gti=None):
        self.args = (data, dt, segment_size, gti)


class _OldSpectrum:
    def __init__(self, lc1=None, lc2=None, segment_size=None, gti=None):
        self.args = ((lc1, lc2), segment_size, gti)


def test_spectrum_from_events_passes_events_when_supported():
    """Versions whose spectra take ``dt`` receive the event lists directly."""
    spec = _compat.averaged_spectrum_from_events(
        _NewSpectrum, _Events("a"), _Events("b"), dt=0.1, segment_size=10, gti="g"
    )
    data, dt, segment_size, gti = spec.args
    assert [ev.name for ev in data] == ["a", "b"] and (dt, segment_size, gti) == (0.1, 10, "g")


def test_spectrum_from_events_bins_first_on_v01():
    """Versions without ``dt`` (Stingray v0.1) receive light curves binned with that dt."""
    spec = _compat.averaged_spectrum_from_events(
        _OldSpectrum, _Events("a"), _Events("b"), dt=0.1, segment_size=10, gti="g"
    )
    assert spec.args == ((("lc", "a", 0.1), ("lc", "b", 0.1)), 10, "g")
