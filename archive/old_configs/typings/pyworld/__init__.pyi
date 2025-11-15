from typing import Any, List, Tuple, Union
import numpy as np
from numpy.typing import NDArray

def wav2world(x: NDArray[np.float64],
             fs: int,
             frame_period: float = 5.0
             ) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Convert waveform to f0, spectral envelope and aperiodicity."""
    ...

def synthesize(f0: NDArray[np.float64],
               spectrogram: NDArray[np.float64],
               aperiodicity: NDArray[np.float64],
               fs: int,
               frame_period: float = 5.0
               ) -> NDArray[np.float64]:
    """Synthesize waveform from f0, spectral envelope and aperiodicity."""
    ...

def dio(x: NDArray[np.float64],
        fs: int,
        f0_floor: float = 71.0,
        f0_ceil: float = 800.0,
        channels_in_octave: float = 2.0,
        frame_period: float = 5.0,
        speed: int = 1
        ) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Extract F0 contour using DIO."""
    ...

def stonemask(x: NDArray[np.float64],
              f0: NDArray[np.float64],
              temporal_positions: NDArray[np.float64],
              fs: int
              ) -> NDArray[np.float64]:
    """Refine F0 contour using STONEMASK."""
    ...

def cheaptrick(x: NDArray[np.float64],
               f0: NDArray[np.float64],
               temporal_positions: NDArray[np.float64],
               fs: int,
               q1: float = -0.15
               ) -> NDArray[np.float64]:
    """Extract spectral envelope using CheapTrick."""
    ...

def d4c(x: NDArray[np.float64],
        f0: NDArray[np.float64],
        temporal_positions: NDArray[np.float64],
        fs: int,
        threshold: float = 0.85
        ) -> NDArray[np.float64]:
    """Extract aperiodicity using D4C."""
    ...