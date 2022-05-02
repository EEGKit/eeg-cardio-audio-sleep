from typing import Optional, Tuple

import numpy as np
from mne.preprocessing.bads import _find_outliers
from numpy.typing import ArrayLike, NDArray

from .. import logger
from ._checks import _check_type


def generate_async_timings(
    sequence_timings: ArrayLike,
    zscore: float = 4.0,
    valid_perc: float = 60,
) -> Tuple[Optional[NDArray[float]], bool]:
    """
    Given the sequence of timings of a synchronous block, generate the sequence
    of timings for the future asynchronous block(s).
    Outliers are removed based on Denis Engemann iterative Z-score method, and
    the asynchronous timing sequence is generated by randomizing the
    synchornous inter-stimuli timings.

    Parameters
    ----------
    sequence_timings : list
        List of timings at which an R-peak occured.
    zscore : float
        The value above which a feature is classified as outlier.
    valid_perc : float
        Float between 0 and 100 representing the minimum percent of total peaks
        from sequence_timings that have to be valid.

    Returns
    -------
    sequence_timings : array | None
        List of timings at which a stimuli occurs for the asynchronous blocks.
        None is returned if the sequence could not be generated.
    valid : bool
        True if the number of valid inter-stimulus delay is above the
        valid_perc threshold.
    """
    _check_type(
        sequence_timings, (list, tuple, np.ndarray), "sequence_timings"
    )
    _check_type(zscore, ("numeric",), "zscore")
    _check_type(valid_perc, ("numeric",), "valid_perc")
    if valid_perc < 0 or 100 < valid_perc:
        raise ValueError(
            "Argument 'valid_perc' should represent a percentage "
            f"between 0 and 100. Provided '{valid_perc}'% is not "
            "valid."
        )

    n = len(sequence_timings)
    diff = np.diff(sequence_timings)
    outliers = _find_outliers(diff, threshold=zscore, max_iter=3)
    valids = diff[~outliers]
    if valids.size == 0:  # should never happen
        return None, False
    valid = 100 * valids.size / (n - 1) < valid_perc
    if not valid:
        logger.warning(
            "Asynchronous timing sequence generation has dropped %s / %s "
            "inter-stimulus delays, dropping below the %s threshold.",
            valids.size,
            n - 1,
            valid_perc,
        )
    # generate sequence of 'n-1' valid inter-stimulus delays
    delays = np.random.choice(valids, size=n - 1, replace=True)
    timings = np.zeros((n,))
    for k, delay in enumerate(delays):
        timings[k + 1] = timings[-1] + delay
    return timings, valid
