"""Shared, explicit EEG preprocessing choices."""


def prepare_eeg_raw(raw):
    raw.pick("eeg")
    raw.set_eeg_reference("average", projection=False, verbose="ERROR")
    raw.filter(1.0, 40.0, picks="eeg", verbose="ERROR")
    return raw
