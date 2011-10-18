============
QDamarisView
============

Introduction
------------

This program is written for easy analysis of HDF5 files written by DAMARIS, the 
DArmstadt MAgnetic Resonance Instrumentation Software from the Fujara group of the 
Technical University Darmstad, Germany.
Specifically, it is made for extraction of simple NMR timesignal features, i.e. amplitude from 
typical NMR experiments like saturation recovery, stimulated echo experiments, etc.


Usage
-----

Select HDF5 file with Cmd+L, then select the nodes you want to extract information from [1]_ . 
Then right-click on the selection and select the feature you want to extract: 

Get amplitudes:
A widget will pop up where you can choose a reference signal. Here you can fix the phase of the signal and 
choose the integration window. The phase correction will be applied to all selected datasets.

Fitting
-------

not yet implemented

.. [1] Currently only signal amplitudes are implemented.
