# # -*- coding: utf-8 -*-

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


def _detrend_transmission(del_freq, s21, detrend_mode, detrend_points_init,
                          detrend_points_final):

    # First detrending for the delay
    # This is done by detrending the phase using the initial points and the final points

    mag, phas = np.abs(s21), np.angle(s21)

    fit_delay_init = linregress(x=np.hstack(
        (del_freq[:detrend_points_init], del_freq[-detrend_points_final:])),
                                y=np.hstack((phas[:detrend_points_init],
                                             phas[-detrend_points_final:])))

    phas = (phas - fit_delay_init.slope * del_freq + np.pi) % (2. *
                                                               np.pi) - np.pi

    # Done detrending for delay and phase

    # Now detrending the magnitude
    fit_poly_mag = linregress(x=np.hstack(
        (del_freq[:detrend_points_init], del_freq[-detrend_points_final:])),
                              y=np.hstack((mag[:detrend_points_init],
                                           mag[-detrend_points_final:])))

    mag = mag - fit_poly_mag.slope * del_freq

    return mag * np.exp(1.0j * phas), fit_delay_init, fit_poly_mag


def _retrend_transmission(del_freq, s21, fit_delay_init, fit_poly_mag):

    mag, phas = np.abs(s21), np.angle(s21)
    mag = mag + fit_poly_mag.slope * del_freq

    phas = np.remainder((phas + fit_delay_init.slope * del_freq + np.pi),
                        (2. * np.pi)) - np.pi

    return mag, phas


def _circle_residual(params, s21):
    return np.sum(
        np.square(
            np.abs(s21 - params[0] - 1.0j * params[1]) - params[2] * params[2]))


def _circle_jacobian(params, s21):
    # diff = params[0] + 1.0j * params[1] - s21
    return 2. * np.sum(params[0] - np.real(s21)), 2. * np.sum(
        params[1] - np.imag(s21)), -2. * params[2] * len(s21)


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
    radius = np.sqrt(
        np.average(np.square(x - x_center) + np.square(y - y_center)))

    # Rough fitting done

    # Someone might want to implement an improvement to this Kasa fit later, but this works for most intents and purposes

    return x_center, y_center, radius


def _rotate_and_translate_to_origin(s21, center):
    s21 = (center - s21) * np.exp(-1.0j * np.angle(center))
    return s21


def _phase_function_loss(params, freq, phas):
    theta, Qr, fr = params[0], params[1], params[2]
    return (2. * np.arctan(2. * Qr * (1. - (freq / fr))) - theta - phas +
            np.pi) % (2. * np.pi) - np.pi


def _fit_phase_func(freq, phas, theta, Qr, fr):
    phase_fit_result, _, _, mesg, stat = leastsq(_phase_function_loss,
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
                                                 full_output=True)

    if stat > 0:
        return phase_fit_result[0], phase_fit_result[1], phase_fit_result[
            2]  #, phase_fit_cov
    else:
        raise Exception(mesg)


def _lorentz_func(freq, amplitude_complex_mag, amplitude_complex_arg, Qr, Qc,
                  fr, phi0, delay):
    freq_ = freq[:len(freq) // 2]
    # Because one cannot fit complex functions with scipy.optimize.curve_fit
    s21 = amplitude_complex_mag * np.exp(
        1.0j * (amplitude_complex_arg - 2. * np.pi * freq_ * delay)) * (1 - (
            (Qr / Qc) * np.exp(1.0j * phi0)) / (1 + 2.0j * Qr *
                                                (freq_ - fr) / fr))

    return np.hstack((np.real(s21), np.imag(s21)))


def _lorentz_jacob(freq, amplitude_complex_mag, amplitude_complex_arg, Qr, Qc,
                   fr, phi0, delay):

    freq_ = freq[:len(freq) // 2]
    temp = np.exp(1.0j *
                  (amplitude_complex_arg - 2. * np.pi * freq_ * delay)) * (
                      (Qr / Qc) * np.exp(1.0j * phi0)) / (1 + 2.0j * Qr *
                                                          (freq_ - fr) / fr)
    jac1 = np.exp(1.0j *
                  (amplitude_complex_arg - 2. * np.pi * freq_ * delay)) - temp
    jac2 = 1.0j * amplitude_complex_mag * jac1  # arg(A)
    jac3 = -temp / (Qr * (1 + 2.0j * Qr * (freq_ - fr) / fr))  # Qr
    jac4 = temp / Qc  # Qc
    jac5 = jac3 * 2.0j * freq_ * (Qr / fr) * (Qr / fr)  #fr
    jac6 = -1.0j * temp  # phi0
    jac7 = -2. * np.pi * freq_ * jac2  # delay

    jac1 = np.hstack((np.real(jac1), np.imag(jac1)))
    jac2 = np.hstack((np.real(jac2), np.imag(jac2)))
    jac3 = np.hstack((np.real(jac3), np.imag(jac3)))
    jac4 = np.hstack((np.real(jac4), np.imag(jac4)))
    jac5 = np.hstack((np.real(jac5), np.imag(jac5)))
    jac6 = np.hstack((np.real(jac6), np.imag(jac6)))
    jac7 = np.hstack((np.real(jac7), np.imag(jac7)))

    return np.vstack((jac1, jac2, jac3, jac4, jac5, jac6, jac7)).T

    #return np.stack((np.real(jac), np.imag(jac)), axis=2)


def _fit_lorentzian(freq, s21, amplitude_complex_mag, amplitude_complex_arg, Qr,
                    Qc, fr, phi0, delay):

    lorentz_fit_result, lorentz_fit_cov = curve_fit(
        _lorentz_func,
        np.hstack((freq, freq)),
        np.hstack((np.real(s21), np.imag(s21))),
        p0=[
            amplitude_complex_mag, amplitude_complex_arg, Qr, Qc, fr, phi0,
            delay
        ],
        jac=_lorentz_jacob,
        bounds=([
            0., -np.inf, Qr / 2., Qc / 2., fr * (1 - 2. / Qr), -np.inf, -np.inf
        ], [
            np.inf, np.inf, Qr * 2., Qc * 2., fr * (1 + 2. / Qr), np.inf, np.inf
        ]),
        ftol=1e-15,
        gtol=1e-15,
        xtol=1e-15,
        method='trf',
        max_nfev=1e6)
    return lorentz_fit_result, lorentz_fit_cov


def fit_transmission(freq,
                     s21,
                     detrend=True,
                     detrend_order=True,
                     detrend_points_init=1,
                     detrend_points_final=1,
                     plot=True,
                     full_output=False):
    """Fits the S21 data provided to this using the φ-RM method. Returns the fitting parameters and plots the fit.

    Args:
        freq (array): The frequencies corresponding to the S21
        s21 (complex array): The complex S21 to be fit
        detrend (bool): If True, performs a linear detrending of the data before fitting it. Otherwise, uses the data as is. (defaults to True)
        detrend_order (int): The order of polynomial to use when detrending the magnitude (As of now, only accepts value = 1) (defaults to 1)
        detrend_points_init (int): Number of points from the beginning of the array to use for detrending. Make sure that the resonance is at some distance from the beginning of the array (defaults to 1)
        detrend_points_final (int): Number of points from the end of the array to use for detrending. Make sure that the resonance is at some distance from the end of the array (defaults to 1)
        plot (bool): If True, plots the fits. If not, does not plot the fits (defaults to True)
        full_output (bool): If False, the function only returns the best fit parameters as a dictionary and the plots. If True, the function returns the fit output with the covariance matrix in the order [amplitude_complex_mag, amplitude_complex_arg, Qr, Qc, fr, phi0, delay] alongside the previous outputs. (defaults to False)

    Returns:
        dict: Returns a dictionary with the best fit parameters as key-value pairs. The key list is [amplitude_complex, Qr, Qc, fr, phi0, delay]
        list: Returns a list of figure and axes of the plotted plots (Empty if plot = False)
        ndarray: (Optional) Returns the best fit parameters as a numpy array in the order described in Args
        ndarray: (Optional) Returns the covariance matrix associated with the best fit as a numpy array with the rows and columns corresponding to te order described in Args
    """

    del_freq = freq - freq[0]

    fit_delay_init, fit_poly_mag = None, None
    if detrend == True:
        s21_detrended, fit_delay_init, fit_poly_mag = _detrend_transmission(
            del_freq, s21, detrend_order, detrend_points_init,
            detrend_points_final)
    else:
        s21_detrended = s21.copy()

    amplitude_complex = s21_detrended[0]
    s21_new = s21_detrended / amplitude_complex

    mag = np.abs(s21_new)

    # Generating some initial guesses
    index_reso = np.argmin(mag)
    fr_init = freq[index_reso]
    band_rough = freq[mag < (mag[index_reso] + np.ptp(mag) * 0.7)]
    Qr_init = 2. * fr_init / np.ptp(band_rough)

    x_center, y_center, radius = _fit_circle_to_data(s21_new)

    s21_new = _rotate_and_translate_to_origin(s21_new,
                                              x_center + 1.0j * y_center)

    theta_init = np.angle(x_center + 1.0j * y_center) - np.arcsin(
        y_center / radius)

    theta_init, Qr_init, fr_init = _fit_phase_func(freq, np.angle(s21_new),
                                                   theta_init, Qr_init, fr_init)

    Qc_init = Qr_init / (2. * radius)

    phi0_init = np.angle(x_center + 1.0j * y_center) - theta_init

    lorentz_fit_result, lorentz_fit_cov = _fit_lorentzian(
        freq, s21_detrended, np.abs(amplitude_complex),
        np.angle(amplitude_complex), Qr_init, Qc_init, fr_init, phi0_init, 0.)

    amplitude_complex_mag, amplitude_complex_arg, Qr, Qc, fr, phi0, delay = lorentz_fit_result

    plots = []

    if plot == True:
        # Generating the fit values
        fit_s21 = _lorentz_func(np.hstack((freq, freq)), amplitude_complex_mag,
                                amplitude_complex_arg, Qr, Qc, fr, phi0, delay)

        fit_s21 = fit_s21[:len(freq)] + 1.0j * fit_s21[len(freq):]

        if detrend == True:
            fit_s21_mag, fit_s21_phas = _retrend_transmission(
                del_freq, fit_s21, fit_delay_init, fit_poly_mag)
        else:
            fit_s21_mag, fit_s21_phas = np.abs(fit_s21), np.angle(fit_s21)

        fig, ax = plt.subplots(1, 3)
        ax[0].scatter(freq, np.abs(s21), label="raw")
        ax[0].plot(freq, fit_s21_mag, label="fit", color='red')
        ax[0].legend()
        ax[0].set_xlabel("Freq (Hz)")
        ax[0].set_ylabel("|S21|")
        ax[0].set_box_aspect(1.)
        ax[1].scatter(freq, np.angle(s21), label="raw")
        ax[1].plot(freq, fit_s21_phas, label="fit", color='red')
        ax[1].legend()
        ax[1].set_xlabel("Freq (Hz)")
        ax[1].set_ylabel("arg(S21)")
        ax[1].set_box_aspect(1.)
        ax[2].scatter(np.real(s21), np.imag(s21), label="raw")
        ax[2].plot(fit_s21_mag * np.cos(fit_s21_phas),
                   fit_s21_mag * np.sin(fit_s21_phas),
                   label="fit",
                   color='red')
        ax[2].legend()
        ax[2].set_xlabel("Re(S21)")
        ax[2].set_ylabel("Im(S21)")
        ax[2].set_box_aspect(1.)
        fig.set_dpi(200)
        fig.tight_layout()
        #plt.savefig('test.png')
        #print('plotted')
        plots = plots + [fig, ax]
        plt.show()

    # Returning the results with post-processing
    amplitude_complex = amplitude_complex_mag * np.exp(
        1.0j * amplitude_complex_arg)
    delay -= (fit_delay_init.slope) / (2. * np.pi)

    # amplitude_complex_mag, amplitude_complex_arg, Qr, Qc, fr, phi0, delay

    fit_values = np.hstack(
        ([amplitude_complex], lorentz_fit_result[2:-1], [delay]))

    if full_output:
        return fit_values, plots, lorentz_fit_result, lorentz_fit_cov
    else:
        return dict(amplitude_complex=amplitude_complex,
                    Qr=Qr,
                    Qc=Qc,
                    fr=fr,
                    phi0=phi0,
                    delay=delay), plots


# %%
