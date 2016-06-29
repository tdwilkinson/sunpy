from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

__author__ = "Tessa D. Wilkinson"

"""
AIA response functions by integrating ChiantiPy

    - analyze AIA instrument response that tells efficiency of channel using instrument properties
    - then output a wavelength response
    - use spectral model (synthetic spectra) - to get ion emissivities as a function of temp/density
    - obtain temperature response based on chianti spectral contribution functions (emissivity)

AIA ccd's do not provide spectroscopic information, so there is no way to directly apply a wavlength-dependent calibration to the data.

other important variables:
effective area
ion emissivity
electron density
temperature array

utilize sunpy/instr/tests/test_aia.py


    for units use:
    @u.quantity_input(wave=u.m)

"""

import numpy as np
import pandas as pd
from astropy.table import Table
import astropy.units as u

import os

import sunpy
import sunpy.data.test as test


class Response():
    """
    class description here!

    Parameters
    ----------

    Attributes
    ----------

    dataframe: table
        The property information stored in a table after being imported from SSW .genx files

    Notes:

    Feedback/ Thoughts are always welcome! -Thanks!
    """

    def __init__(self, dataframe, channel = 'all', **kwargs): #data_table,

        # #data_table = kwargs.get('data_table', '')
        #
        # if channel == 'all':
        #     self.data_dictionary = data_table.columns
        # else:
        #     self.channel_data = data_table[str(channel)]
        #
        # self.properties = data_table['properties']
        # self.wavelength_range = kwargs.get('wavelength_range', np.array(data_table['94'][8]))


        #The code above is for testing the table structure. The code below is for using dataframe to carry on until I finish testing the Table structure.


        self.channel = channel

        if channel == 'all':
            self.dataframe = dataframe
        else:
            self.channel_data = dataframe[str(channel)]

        # wavelength range is calculated here: (for plotting)
        self.wavelength_range = np.arange(0, float(self.channel_data['wavenumsteps']))*float((self.channel_data['wavestep']))+ float(self.channel_data['wavemin'])

        # only for comparing to paper - inside functions
        self.channel_list = kwargs.get('channel_list', [])



    def effective_area(self, compare_genx=False, compare_table=False):
        """
        AIA instrument response / effective area
        - contains information about the efficiency of the telescope optics.
        - trying to reformat effective area structure, convert to DN units

        Effective Area = Geo_Area * Reflectance of Primary and Secondary Mirrors * Transmission Efficiency of filters * Quantum Efficiency of CCD * Correction for time-varying contamination

        A_{eff}=A_{geo}R_p(\lambda)R_S(\lambda)T_E(\lambda)T_F(\lambda)D(\lambda,t)Q(\lambda)
        site github ^^^     @

        Parameters
        ----------
        wavelength: int
            the wavelength center of the channel of interest

        Variables:
        ----------
        Reflectance = The combined reflectance of the primary and secondary mirrors
        Transmission_efficiency = for the focal plane and entrence filters

        Returns
        -------
        effective_area: np.array
            if compare is True: returns the effective area loaded in from the ssw genx file.
            if compare is False: returns the calculations here from Boerner


        """

        var = self.channel_data

        if compare_genx:
            self.eff_area = var['effarea']
        elif compare_table:
            self.eff_area = [0.312, 1.172, 2.881, 1.188, 1.206, 0.063, 0.045, 0.0192, 0.0389][
                self.channel_list.index(self.channel)]
        else:
            # variables:
            wavelength = self.wavelength_range
            reflectance = var['primary'] * var['secondary']
            transmission_efficiency = var['fp_filter'] * var['ent_filter']  # these appear to be the same... not sure

            # equation:
            eff_area = var['geoarea'] * reflectance * transmission_efficiency * wavelength * var['contam']* var['ccd']

            self.eff_area = eff_area[self.channel]

        return self.eff_area

    def wavelength_response(self, compare_genx=False, compare_table = False):
        """

        Describes the instrument (AIA) response per wavelength by calculating effective area vs wavelength of the strongest emission lines present in the solar feature.
            R(\lambda)=A_{eff}(\lambda,t)G(\lambda)

        effective area A_{eff}=A_{geo}R_p(\lambda)R_S(\lambda)T_E(\lambda)T_F(\lambda)D(\lambda,t)Q(\lambda)
        gain of the CCD-camera system, G(\lambda)=(12398/\lambda/3.65)g
        flat field function F(\mathbf{x})

           Wavelength response functions: calculate the amount of flux per wavelength
         R_i(\lambda) which is equivalent to \eta_i as expressed above.


        Parameters
        ----------
        :keyword

        photon_to_dn?
            may need a photon-to-DN unit conversion   # digital number = counts on detector

        output: float
            outfile of instrument response per channel

        Returns
        -------
        :return: float, array describing the response per wavelength of effective area (wavelength response)
                want units cm^2 DN phot^-1
        """

        # TODO: fix doc string here! ^^^
        # TODO: WIP!!   work with values / conversions to get the right number out from this function
        gu = u.count / u.photon
        gain_table = {94: 2.128 * gu, 131: 1.523 * gu, 171: 1.168 * gu, 195: 1.024 * gu, 211: 0.946 * gu,
                      304: 0.658 * gu, 335: 0.596 * gu, 1600: 0.125 * gu, 1700: 0.118 * gu}

        var = self.channel_data

        if compare_genx:
            # gives Table 2 values for instruement response
            index = self.channel_list.index(self.channel)
            self.inst_response = [0.664, 1.785, 3.365, 1.217, 1.14, 0.041, 0.027, 0.0024, 0.0046][index]
        elif compare_table:
            # calculations of G from Boerner Table 12
            for key, gain in gain_table.iteritems():
                if str(key) == str(self.channel):
                    eff_area = self.effective_area()
                    inst_response = eff_area * gain # / wavelength
                    self.inst_response = inst_response[self.channel]
        else:
            # Calculations of G from Boerner formulas * work in progress*
            for key, gain in ccd_gain.iteritems():
                if str(key) == str(wavelength):
                    eff_area = self.effective_area(key)
                    Gain = 12398.0 / (var['wave'] * var['elecperev']) / var['elecperdn']  # < gain
                    instr_response = (eff_area ) * Gain ** (u.electron / u.ct)
                    # want: dn/photon

        return self.inst_response

        # NOTES:      ^^^ get the same values as the table when using all table values: self.effective_area(compare_table=True)
        #                 get one of the same values (171) when calculating it with center wavelength - fix


def emissivity():
    """

    - Use  chianti.core.mspectrum.intensityratio to get spectral line intensities and show relative emissivity per line.
        chianti.core.continuum has places to access freebound and freefree emissions
    - create a line list  to show line intensities

    input:


    :return: generates chianti object - continuum - chianti model with line list
    """
    pass


def spectrum():
    """
    generate a spectral model for various solar features to be used in modules

    - develop an emissivity (chianti) spectral structure based on plasma  properties (line intensities?/ emissivity?)
    - want to read values of physical parameters to determine feature
    - elemental abundances:  chianti.core.Spectrum.chianti.data.Abundance
        chianti.core.continuum has places to access freebound and freefree emissions

    input:

    :return:
    """
    pass


def temperature_response():
    """
    calculates temperature for various features using ChiantiPy
     - Will need to use the spectral contribution function in Chiantipy
            G(\lambda,T)
    input: string, data file

    channel: string, indicates channels used


    :return:

    outfile: giving temperature response per channel

    """
    pass
