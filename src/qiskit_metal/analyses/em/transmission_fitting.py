# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""For fitting the S21 for notch-type resonators.

@author: Samarth Hawaldar

Key References:

M. S. Khalil, M. J. A. Stoutimore, F. C. Wellstood, and K. D. Osborn
, "An analysis method for asymmetric resonator transmission applied to superconducting devices", Journal of Applied Physics 111, 054510 (2012)
https://doi.org/10.1063/1.3692073

Gao, J. (2008). The physics of superconducting microwave resonators (thesis). The Physics of Superconducting Microwave Resonators .
https://web.physics.ucsb.edu/~bmazin/Papers/2008/Gao/Caltech%20Thesis%202008%20Gao.pdf.

Circle Fitting adapted from http://www.cs.bsu.edu/homepages/kjones/kjones/circles.pdf
"""

import numpy as np
from scipy.optimize import leastsq
from scipy.stats import linregress
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt


def _detrend_transmission(
    del_freq, s21, detrend_mode, detrend_points_init, detrend_points_final
):

    # First detrending for the delay
    # This is done by detrending the phase using the initial points and the final points

    mag, phas = np.abs(s21), np.unwrap(np.angle(s21))

    fit_delay_init = linregress(
        x=np.hstack((del_freq[:detrend_points_init], del_freq[-detrend_points_final:])),
        y=np.hstack((phas[:detrend_points_init], phas[-detrend_points_final:])),
    )

    phas = (phas - fit_delay_init.slope * del_freq + np.pi) % (2.0 * np.pi) - np.pi

    # Done detrending for delay and phase

    # Now detrending the magnitude
    fit_poly_mag = linregress(
        x=np.hstack((del_freq[:detrend_points_init], del_freq[-detrend_points_final:])),
        y=np.hstack((mag[:detrend_points_init], mag[-detrend_points_final:])),
    )

    mag = mag - fit_poly_mag.slope * del_freq

    return mag * np.exp(1.0j * phas), fit_delay_init, fit_poly_mag


def _circle_residual(params, s21):
    return np.sum(
        np.square(np.abs(s21 - params[0] - 1.0j * params[1]) - params[2] * params[2])
    )


def _circle_jacobian(params, s21):
    # diff = params[0] + 1.0j * params[1] - s21
    return (
        2.0 * np.sum(params[0] - np.real(s21)),
        2.0 * np.sum(params[1] - np.imag(s21)),
        -2.0 * params[2] * len(s21),
    )


def _fit_circle_to_data(s21):
    # Performing a rough fit initially using a Kasa fit. Someone might want to change this to a Taubin fit, but this works mostly

    n = len(s21)
    x = np.real(s21)
    y = np.imag(s21)
    x2 = np.square(x)
    y2 = np.square(y)
    x3 = x2 * x
    y3 = y2 * y

    sx = np.sum(x)
    sy = np.sum(y)
    sx2 = np.sum(x2)
    sy2 = np.sum(y2)
    sxy = np.sum(x * y)
    sx3 = np.sum(x3)
    sy3 = np.sum(y3)
    sxy2 = np.sum(x * y2)
    sx2y = np.sum(x2 * y)

    A = n * sx2 - sx * sx
    B = n * sxy - sx * sy
    C = n * sy2 - sy * sy
    D = 0.5 * (n * sxy2 - sx * sy2 + n * sx3 - sx * sx2)
    E = 0.5 * (n * sx2y - sy * sx2 + n * sy3 - sy * sy2)

    x_center = (D * C - B * E) / (A * C - B * B)
    y_center = (A * E - B * D) / (A * C - B * B)
    radius = np.sqrt(np.average(np.square(x - x_center) + np.square(y - y_center)))

    # Rough fitting done

    # Someone might want to implement an improvement to this Kasa fit later, but this works for most intents and purposes

    return x_center, y_center, radius


def _rotate_and_translate_to_origin(s21, center):
    s21 = (center - s21) * np.exp(-1.0j * np.angle(center))
    return s21


def _phase_function_loss(params, freq, phas):
    theta, Qr, fr = params[0], params[1], params[2]
    return (2.0 * np.arctan(2.0 * Qr * (1.0 - (freq / fr))) - theta - phas + np.pi) % (
        2.0 * np.pi
    ) - np.pi


def _fit_phase_func(freq, phas, theta, Qr, fr):
    phase_fit_result, _, _, mesg, stat = leastsq(
        _phase_function_loss,
        np.array([theta, Qr, fr]),
        args=(
            freq,
            phas,
        ),
        ftol=1e-16,
        xtol=1e-16,
        gtol=1e-16,
        maxfev=10000,
        epsfcn=1e-16,
        full_output=True,
    )

    if stat > 0:
        return (
            phase_fit_result[0],
            phase_fit_result[1],
            phase_fit_result[2],
        )  # , phase_fit_cov
    else:
        raise Exception(mesg)


def _lorentz_func(
    freq,
    amplitude_complex_mag,
    amplitude_complex_arg,
    Qr,
    Qc,
    fr,
    phi0,
    delay,
    *slope,
    freq_ref=0.0,
    slope_ref=0.0,
):
    # The cable delay acts on freq - freq_ref; amplitude_complex_arg is the
    # phase of the off-resonant transmission at freq_ref. An optional eighth
    # parameter is a real, relative baseline slope:
    # S21 -> S21 * (1 + slope * (freq - slope_ref)).
    freq_ = freq[: len(freq) // 2]
    # Because one cannot fit complex functions with scipy.optimize.curve_fit
    s21 = (
        amplitude_complex_mag
        * np.exp(
            1.0j * (amplitude_complex_arg - 2.0 * np.pi * (freq_ - freq_ref) * delay)
        )
        * (1 - ((Qr / Qc) * np.exp(1.0j * phi0)) / (1 + 2.0j * Qr * (freq_ - fr) / fr))
    )
    if slope:
        s21 = s21 * (1.0 + slope[0] * (freq_ - slope_ref))

    return np.hstack((np.real(s21), np.imag(s21)))


def _lorentz_jacob(
    freq,
    amplitude_complex_mag,
    amplitude_complex_arg,
    Qr,
    Qc,
    fr,
    phi0,
    delay,
    *slope,
    freq_ref=0.0,
    slope_ref=0.0,
):

    freq_ = freq[: len(freq) // 2]
    background = np.exp(
        1.0j * (amplitude_complex_arg - 2.0 * np.pi * (freq_ - freq_ref) * delay)
    )
    denom = 1 + 2.0j * Qr * (freq_ - fr) / fr
    temp = background * ((Qr / Qc) * np.exp(1.0j * phi0)) / denom
    jac1 = background - temp  # |A|
    jac2 = 1.0j * amplitude_complex_mag * jac1  # arg(A)
    jac3 = -amplitude_complex_mag * temp / (Qr * denom)  # Qr
    jac4 = amplitude_complex_mag * temp / Qc  # Qc
    jac5 = jac3 * 2.0j * freq_ * (Qr / fr) * (Qr / fr)  # fr
    jac6 = -1.0j * amplitude_complex_mag * temp  # phi0
    jac7 = -2.0 * np.pi * (freq_ - freq_ref) * jac2  # delay

    jacs = (jac1, jac2, jac3, jac4, jac5, jac6, jac7)
    if slope:
        # The baseline multiplies every derivative; d/dslope is the
        # slope-free model times (freq - slope_ref).
        baseline = 1.0 + slope[0] * (freq_ - slope_ref)
        jacs = tuple(j * baseline for j in jacs) + (
            amplitude_complex_mag * jac1 * (freq_ - slope_ref),
        )
    return np.vstack([np.hstack((np.real(j), np.imag(j))) for j in jacs]).T


def _fit_lorentzian(
    freq,
    s21,
    amplitude_complex_mag,
    amplitude_complex_arg,
    Qr,
    Qc,
    fr,
    phi0,
    delay,
    *slope,
    freq_ref=0.0,
):
    # With a slope, it is referenced to freq_ref as well (fixed, so the
    # Jacobian stays simple); fit_transmission re-references it to fr.
    kw = dict(freq_ref=freq_ref, slope_ref=freq_ref)
    n_extra = len(slope)
    lorentz_fit_result, lorentz_fit_cov = curve_fit(
        lambda f, *p: _lorentz_func(f, *p, **kw),
        np.hstack((freq, freq)),
        np.hstack((np.real(s21), np.imag(s21))),
        p0=[amplitude_complex_mag, amplitude_complex_arg, Qr, Qc, fr, phi0, delay]
        + list(slope),
        jac=lambda f, *p: _lorentz_jacob(f, *p, **kw),
        x_scale="jac",
        bounds=(
            [0.0, -np.inf, Qr / 2.0, Qc / 2.0, fr * (1 - 2.0 / Qr), -np.inf, -np.inf]
            + [-np.inf] * n_extra,
            [np.inf, np.inf, Qr * 2.0, Qc * 2.0, fr * (1 + 2.0 / Qr), np.inf, np.inf]
            + [np.inf] * n_extra,
        ),
        ftol=1e-15,
        gtol=1e-15,
        xtol=1e-15,
        method="trf",
        max_nfev=1e6,
    )
    return lorentz_fit_result, lorentz_fit_cov


def fit_transmission(
    freq,
    s21,
    detrend=True,
    detrend_order=True,
    detrend_points_init=1,
    detrend_points_final=1,
    plot=True,
    full_output=False,
    baseline_slope=False,
):
    """Fits the S21 data provided to this using the φ-RM method. Returns the fitting parameters and plots the fit.

    Args:
        freq (array): The frequencies corresponding to the S21
        s21 (complex array): The complex S21 to be fit
        detrend (bool): If True, estimates the cable delay (slope of the unwrapped phase) and a linear magnitude slope from the end points and uses the detrended data for the starting values. The final fit always runs on the data as given, with the delay as a free parameter; a magnitude slope is not part of the model. If False, the starting values come from the data as is, with zero delay. (defaults to True)
        detrend_order (int): The order of polynomial to use when detrending the magnitude (As of now, only accepts value = 1) (defaults to 1)
        detrend_points_init (int): Number of points from the beginning of the array to use for detrending. Make sure that the resonance is at some distance from the beginning of the array (defaults to 1)
        detrend_points_final (int): Number of points from the end of the array to use for detrending. Make sure that the resonance is at some distance from the end of the array (defaults to 1)
        plot (bool): If True, plots the fits. If not, does not plot the fits (defaults to True)
        full_output (bool): If False, the function only returns the best fit parameters as a dictionary and the plots. If True, the function returns the fit output with the covariance matrix in the order [amplitude_complex_mag, amplitude_complex_arg, Qr, Qc, fr, phi0, delay] alongside the previous outputs; with ``baseline_slope=True`` the order is [amplitude_complex_mag, amplitude_complex_arg, Qr, Qc, fr, phi0, delay, baseline_slope]. (defaults to False)
        baseline_slope (bool): If True, the model gets a real, linear baseline slope ``k`` (in 1/Hz): the model below is multiplied by ``(1 + k (f - fr))``, so ``|A|`` is the off-resonant level at ``fr``. The starting value is the magnitude slope of the detrend (zero with ``detrend=False``). Use it when the measured |S21| baseline is tilted across the span; without it a tilt biases Q (about +0.25 % on Qr and Qc for a 2 % tilt across the span). The slope is real only, because an imaginary part would duplicate the cable delay to first order. The dictionary gets a ``baseline_slope`` key and the first ``full_output`` array gets the slope as its last element. (defaults to False; the default output is unchanged)

    The model (Khalil et al. 2012, with a cable delay) is
    ``S21(f) = A exp(-2 pi i f delay) (1 - (Qr/Qc) exp(i phi0) / (1 + 2 i Qr (f - fr)/fr))``
    with absolute frequency ``f``; the returned ``amplitude_complex`` and
    ``delay`` reproduce the data when inserted in it. This is the model of
    Probst et al., Rev. Sci. Instrum. 86, 024706 (2015), which has no
    baseline slope; ``baseline_slope=True`` adds the factor
    ``(1 + baseline_slope (f - fr))``.

    Returns:
        dict: Returns a dictionary with the best fit parameters as key-value pairs. The key list is [amplitude_complex, Qr, Qc, fr, phi0, delay], plus baseline_slope with ``baseline_slope=True``
        list: Returns a list of figure and axes of the plotted plots (Empty if plot = False)
        ndarray: (Optional) Returns the best fit parameters as a numpy array in the order described in Args
        ndarray: (Optional) Returns the covariance matrix associated with the best fit as a numpy array with the rows and columns corresponding to te order described in Args
    """

    freq = np.asarray(freq, dtype=float)
    s21 = np.asarray(s21, dtype=complex)
    del_freq = freq - freq[0]
    # The final fit references the cable delay to the centre of the span,
    # which decorrelates delay and arg(A); the result is converted back to
    # the absolute-frequency model of the docstring at the end.
    freq_ref = 0.5 * (freq[0] + freq[-1])

    # The detrended data only provide starting values. The final fit runs on
    # the raw data, so the returned parameters are those of the model.
    if detrend:
        s21_detrended, fit_delay_init, fit_mag_init = _detrend_transmission(
            del_freq, s21, detrend_order, detrend_points_init, detrend_points_final
        )
        delay_init = -fit_delay_init.slope / (2.0 * np.pi)
        mag_slope_init = fit_mag_init.slope
    else:
        s21_detrended = s21.copy()
        delay_init = 0.0
        mag_slope_init = 0.0

    amplitude_complex = s21_detrended[0]
    s21_new = s21_detrended / amplitude_complex

    mag = np.abs(s21_new)

    # Generating some initial guesses
    index_reso = np.argmin(mag)
    fr_init = freq[index_reso]
    band_rough = freq[mag < (mag[index_reso] + np.ptp(mag) * 0.7)]
    Qr_init = 2.0 * fr_init / np.ptp(band_rough)

    x_center, y_center, radius = _fit_circle_to_data(s21_new)

    s21_new = _rotate_and_translate_to_origin(s21_new, x_center + 1.0j * y_center)

    theta_init = np.angle(x_center + 1.0j * y_center) - np.arcsin(y_center / radius)

    theta_init, Qr_init, fr_init = _fit_phase_func(
        freq, np.angle(s21_new), theta_init, Qr_init, fr_init
    )

    Qc_init = Qr_init / (2.0 * radius)

    phi0_init = np.angle(x_center + 1.0j * y_center) - theta_init

    # Off-resonant transmission at freq_ref, from the detrended first point
    amplitude_ref = amplitude_complex * np.exp(
        -2.0j * np.pi * (freq_ref - freq[0]) * delay_init
    )
    slope_init = []
    if baseline_slope:
        # The detrend subtracted the magnitude slope, so the detrended first
        # point is the baseline at freq[0]; move it to freq_ref and express
        # the slope relative to it.
        baseline_ref = np.abs(amplitude_ref) + mag_slope_init * (freq_ref - freq[0])
        amplitude_ref = baseline_ref * np.exp(1.0j * np.angle(amplitude_ref))
        slope_init = [mag_slope_init / baseline_ref]

    lorentz_fit_result, lorentz_fit_cov = _fit_lorentzian(
        freq,
        s21,
        np.abs(amplitude_ref),
        np.angle(amplitude_ref),
        Qr_init,
        Qc_init,
        fr_init,
        phi0_init,
        delay_init,
        *slope_init,
        freq_ref=freq_ref,
    )

    # Back to the model with absolute frequency, exp(-2 pi i f delay)
    lorentz_fit_result = np.array(lorentz_fit_result, dtype=float)
    n_par = len(lorentz_fit_result)
    delay = lorentz_fit_result[6]
    lorentz_fit_result[1] = np.angle(
        np.exp(1.0j * (lorentz_fit_result[1] + 2.0 * np.pi * freq_ref * delay))
    )
    to_absolute = np.eye(n_par)
    to_absolute[1, 6] = 2.0 * np.pi * freq_ref
    if baseline_slope:
        # A (1 + k (f - freq_ref)) = A u (1 + (k / u) (f - fr)),
        # u = 1 + k (fr - freq_ref): re-reference the slope to fr.
        mag_c, fr_c, k_c = (lorentz_fit_result[i] for i in (0, 4, 7))
        u = 1.0 + k_c * (fr_c - freq_ref)
        lorentz_fit_result[0] = mag_c * u
        lorentz_fit_result[7] = k_c / u
        to_absolute[0, 0] = u
        to_absolute[0, 4] = mag_c * k_c
        to_absolute[0, 7] = mag_c * (fr_c - freq_ref)
        to_absolute[7, 7] = 1.0 / u**2
        to_absolute[7, 4] = -((k_c / u) ** 2)
    lorentz_fit_cov = to_absolute @ lorentz_fit_cov @ to_absolute.T

    amplitude_complex_mag, amplitude_complex_arg, Qr, Qc, fr, phi0, delay = (
        lorentz_fit_result[:7]
    )
    slope_fit = list(lorentz_fit_result[7:])

    plots = []

    if plot:
        # Generating the fit values
        fit_s21 = _lorentz_func(
            np.hstack((freq, freq)),
            amplitude_complex_mag,
            amplitude_complex_arg,
            Qr,
            Qc,
            fr,
            phi0,
            delay,
            *slope_fit,
            slope_ref=fr,
        )

        fit_s21 = fit_s21[: len(freq)] + 1.0j * fit_s21[len(freq) :]

        fig, ax = plt.subplots(1, 3)
        ax[0].scatter(freq, np.abs(s21), label="raw")
        ax[0].plot(freq, np.abs(fit_s21), label="fit", color="red")
        ax[0].legend()
        ax[0].set_xlabel("Freq (Hz)")
        ax[0].set_ylabel("|S21|")
        ax[0].set_box_aspect(1.0)
        ax[1].scatter(freq, np.angle(s21), label="raw")
        ax[1].plot(freq, np.angle(fit_s21), label="fit", color="red")
        ax[1].legend()
        ax[1].set_xlabel("Freq (Hz)")
        ax[1].set_ylabel("arg(S21)")
        ax[1].set_box_aspect(1.0)
        ax[2].scatter(np.real(s21), np.imag(s21), label="raw")
        ax[2].plot(np.real(fit_s21), np.imag(fit_s21), label="fit", color="red")
        ax[2].legend()
        ax[2].set_xlabel("Re(S21)")
        ax[2].set_ylabel("Im(S21)")
        ax[2].set_box_aspect(1.0)
        fig.set_dpi(200)
        fig.tight_layout()
        plots = plots + [fig, ax]
        plt.show()

    # Returning the results with post-processing
    amplitude_complex = amplitude_complex_mag * np.exp(1.0j * amplitude_complex_arg)

    # amplitude_complex_mag, amplitude_complex_arg, Qr, Qc, fr, phi0, delay

    fit_values = np.hstack(
        ([amplitude_complex], lorentz_fit_result[2:6], [delay], slope_fit)
    )

    if full_output:
        return fit_values, plots, lorentz_fit_result, lorentz_fit_cov
    else:
        result = dict(
            amplitude_complex=amplitude_complex,
            Qr=Qr,
            Qc=Qc,
            fr=fr,
            phi0=phi0,
            delay=delay,
        )
        if baseline_slope:
            result["baseline_slope"] = slope_fit[0]
        return result, plots


# %%
