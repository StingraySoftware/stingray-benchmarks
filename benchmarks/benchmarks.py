"""Stingray benchmarks, written to run unchanged from v0.3 to main.

All data come from a fixed seed with numpy's legacy RandomState, whose
stream is identical in every numpy version, so all eras see the same data.
Stingray objects are built in ``setup``, so an API problem only affects the
benchmarks that depend on it. Set STINGRAY_BENCH_SMALL=1 to shrink all data
(used by the test suite).
"""

import os

import numpy as np

from . import _compat

SMALL = bool(os.environ.get("STINGRAY_BENCH_SMALL"))
SEED = 20240419


def uniform_events(n, tmax, seed=SEED):
    """Sorted, uniformly distributed event times in [0, tmax)."""
    return np.sort(np.random.RandomState(seed).uniform(0, tmax, n))


class EventListSuite:
    """Creation of an EventList from event times.

    Before Stingray v2.0 there were no checks to skip, so the two benchmarks
    time the same code there.
    """

    params = [1_000, 10_000] if SMALL else [1_000_000, 10_000_000]
    param_names = ["n_events"]

    def setup(self, n):
        self.gti = np.array([[0, 1000]])
        self.times = uniform_events(n, 1000)

    def time_create_with_checks(self, n):
        _compat.make_eventlist(self.times, gti=self.gti, skip_checks=False)

    def time_create_no_checks(self, n):
        _compat.make_eventlist(self.times, gti=self.gti, skip_checks=True)


class LightcurveFromEventsSuite:
    """Binning event times into a light curve with 1 s bins."""

    params = [1_000, 10_000] if SMALL else [1_000_000, 10_000_000]
    param_names = ["n_events"]

    def setup(self, n):
        from stingray.lightcurve import Lightcurve

        self.Lightcurve = Lightcurve
        self.gti = np.array([[0, 1000]])
        self.times = uniform_events(n, 1000)

    def time_make_lightcurve(self, n):
        self.Lightcurve.make_lightcurve(self.times, dt=1, gti=self.gti)

    def time_make_lightcurve_no_gti(self, n):
        self.Lightcurve.make_lightcurve(self.times, dt=1)


class LightcurveSuite:
    """Creation of an evenly sampled light curve from binned counts."""

    params = [1_000, 10_000] if SMALL else [1_000_000, 10_000_000]
    param_names = ["n_bins"]

    def setup(self, n):
        self.dt = 1.0e-4
        self.times = (np.arange(n) + 0.5) * self.dt
        self.gti = np.array([[0, n * self.dt]])
        self.counts = np.random.RandomState(SEED).poisson(100, size=n)

    def time_create_with_checks(self, n):
        _compat.make_lightcurve(
            self.times, self.counts, dt=self.dt, gti=self.gti, skip_checks=False
        )

    def time_create_no_checks(self, n):
        _compat.make_lightcurve(
            self.times, self.counts, dt=self.dt, gti=self.gti, skip_checks=True
        )


# Two regimes of averaged spectra: few long segments, or many short ones.
SPECTRUM_CASES = {
    "few_long_segments": dict(n_events=10_000_000, tmax=1000, dt=0.1, segment_size=100),
    "many_short_segments": dict(n_events=1_000_000, tmax=3000, dt=0.001, segment_size=3),
}
if SMALL:
    SPECTRUM_CASES = {
        "few_long_segments": dict(n_events=2_000, tmax=100, dt=0.1, segment_size=10),
        "many_short_segments": dict(n_events=2_000, tmax=30, dt=0.01, segment_size=1),
    }


class AveragedSpectrumSuite:
    """Averaged power and cross spectra, from event lists and light curves."""

    params = list(SPECTRUM_CASES)
    param_names = ["case"]
    timeout = 900

    def setup(self, case):
        from stingray.events import EventList

        cfg = SPECTRUM_CASES[case]
        self.dt = cfg["dt"]
        self.segment_size = cfg["segment_size"]
        self.gti = np.array([[0, cfg["tmax"]]])

        times0 = uniform_events(cfg["n_events"], cfg["tmax"], seed=SEED)
        times1 = uniform_events(cfg["n_events"], cfg["tmax"], seed=SEED + 1)
        times = np.sort(np.concatenate([times0, times1]))

        self.events0 = EventList(times0, gti=self.gti)
        self.events1 = EventList(times1, gti=self.gti)
        self.events = EventList(times, gti=self.gti)
        self.lc0 = self.events0.to_lc(dt=self.dt)
        self.lc1 = self.events1.to_lc(dt=self.dt)
        self.lc = self.events.to_lc(dt=self.dt)

    def time_powerspectrum_from_events(self, case):
        from stingray.powerspectrum import AveragedPowerspectrum

        AveragedPowerspectrum(self.events, dt=self.dt, segment_size=self.segment_size)

    def time_crossspectrum_from_events(self, case):
        from stingray.crossspectrum import AveragedCrossspectrum

        AveragedCrossspectrum(
            self.events0,
            self.events1,
            dt=self.dt,
            gti=self.gti,
            segment_size=self.segment_size,
        )

    def time_powerspectrum_from_lc(self, case):
        from stingray.powerspectrum import AveragedPowerspectrum

        AveragedPowerspectrum(self.lc, segment_size=self.segment_size)

    def time_crossspectrum_from_lc(self, case):
        from stingray.crossspectrum import AveragedCrossspectrum

        AveragedCrossspectrum(self.lc0, self.lc1, segment_size=self.segment_size)
