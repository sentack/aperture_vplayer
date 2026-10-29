"""Playback and subtitle preferences for the settings panel, exposed to QML as `prefs`.

Theme and accent live on ThemeController (`appearance`), which reads the same Settings.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from aperture.core import RATES
from aperture.settings import LAST_RATE, RESUME_MODES, SUBTITLE_SIZES, Settings


def _rate_key(rate: object) -> str:
    return LAST_RATE if rate == LAST_RATE else f"{rate:g}"


class PreferencesController(QObject):
    changed = Signal()
    # After reset(): listeners holding derived state (the theme) re-read Settings.
    resetDone = Signal()
    # A fixed speed was picked in Settings: it applies to what is playing now, too.
    rateSelected = Signal(float)

    def __init__(self, settings: Settings, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = settings

    def _commit(self) -> None:
        self._settings.save()
        self.changed.emit()

    def _get_volume(self) -> float:
        return self._settings.default_volume

    def _set_volume(self, value: float) -> None:
        value = round(min(1.0, max(0.0, value)), 2)
        if value != self._settings.default_volume:
            self._settings.default_volume = value
            self._commit()

    defaultVolume = Property(float, _get_volume, _set_volume, notify=changed)

    def _get_rate(self) -> str:
        return _rate_key(self._settings.default_rate)

    def _set_rate(self, key: str) -> None:
        """`"last"` or a preset such as `"1.25"`; anything else is ignored."""
        if key == LAST_RATE:
            value: object = LAST_RATE
        else:
            try:
                value = float(key)
            except ValueError:
                return
            if value not in RATES:
                return
        if value != self._settings.default_rate:
            self._settings.default_rate = value
            self._commit()
        if value != LAST_RATE:
            self.rateSelected.emit(value)

    defaultRate = Property(str, _get_rate, _set_rate, notify=changed)

    @Property(list, constant=True)
    def rateOptions(self) -> list[str]:
        return [LAST_RATE, *(_rate_key(rate) for rate in RATES)]

    def _get_subtitles_auto(self) -> bool:
        return self._settings.subtitles_auto

    def _set_subtitles_auto(self, value: bool) -> None:
        if value != self._settings.subtitles_auto:
            self._settings.subtitles_auto = bool(value)
            self._commit()

    subtitlesAuto = Property(bool, _get_subtitles_auto, _set_subtitles_auto, notify=changed)

    def _get_subtitle_size(self) -> str:
        return self._settings.subtitle_size

    def _set_subtitle_size(self, value: str) -> None:
        if value in SUBTITLE_SIZES and value != self._settings.subtitle_size:
            self._settings.subtitle_size = value
            self._commit()

    subtitleSize = Property(str, _get_subtitle_size, _set_subtitle_size, notify=changed)

    @Property(float, notify=changed)
    def subtitleScale(self) -> float:
        return self._settings.subtitle_scale

    @Property(list, constant=True)
    def subtitleSizes(self) -> list[str]:
        return list(SUBTITLE_SIZES)

    def _get_resume_mode(self) -> str:
        return self._settings.resume_mode

    def _set_resume_mode(self, value: str) -> None:
        if value in RESUME_MODES and value != self._settings.resume_mode:
            self._settings.resume_mode = value
            self._commit()

    resumeMode = Property(str, _get_resume_mode, _set_resume_mode, notify=changed)

    @Property(list, constant=True)
    def resumeModes(self) -> list[str]:
        return list(RESUME_MODES)

    @Slot()
    def reset(self) -> None:
        self._settings.reset()
        self._commit()
        self.resetDone.emit()

    def remember_rate(self, rate: float) -> None:
        """Track the speed in use, for sessions that start at the last used speed."""
        rate = min(RATES[-1], max(RATES[0], rate))
        if rate != self._settings.last_rate:
            self._settings.last_rate = rate
            self._settings.save()
