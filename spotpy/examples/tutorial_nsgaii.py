#!/usr/bin/env python
# coding: utf-8


from __future__ import division, print_function
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

try:
    import spotpy
except ImportError:
    import sys

    sys.path.append(".")
    import spotpy

import spotpy.algorithms
from spotpy.examples.hymod_python.hymod import hymod
import os
import unittest


class spot_setup(object):
    def __init__(self):
        # Transform [mm/day] into [l s-1], where 1.783 is the catchment area
        self.Factor = 1.783 * 1000 * 1000 / (60 * 60 * 24)
        # Load Observation data from file
        self.PET, self.Precip = [], []
        self.date, self.trueObs = [], []
        self.owd = os.path.dirname(os.path.realpath(__file__))
        self.hymod_path = self.owd + os.sep + 'hymod_python'
        climatefile = open(self.hymod_path + os.sep + 'hymod_input.csv', 'r')
        headerline = climatefile.readline()[:-1]

        if ';' in headerline:
            self.delimiter = ';'
        else:
            self.delimiter = ','
        self.header = headerline.split(self.delimiter)
        for line in climatefile:
            values = line.strip().split(self.delimiter)
            self.date.append(str(values[0]))
            self.Precip.append(float(values[1]))
            self.PET.append(float(values[2]))
            self.trueObs.append(float(values[3]))

        climatefile.close()
        self.params = [spotpy.parameter.Uniform('cmax', low=1.0, high=500, optguess=412.33),
                       spotpy.parameter.Uniform('bexp', low=0.1, high=2.0, optguess=0.1725),
                       spotpy.parameter.Uniform('alpha', low=0.1, high=0.99, optguess=0.8127),
                       spotpy.parameter.Uniform('Ks', low=0.0, high=0.10, optguess=0.0404),
                       spotpy.parameter.Uniform('Kq', low=0.1, high=0.99, optguess=0.5592),
                       spotpy.parameter.Uniform('fake1', low=0.1, high=10, optguess=0.5592),
                       spotpy.parameter.Uniform('fake2', low=0.1, high=10, optguess=0.5592)]

    def parameters(self):
        return spotpy.parameter.generate(self.params)

    def simulation(self, x):
        data = hymod(self.Precip, self.PET, x[0], x[1], x[2], x[3], x[4])
        sim = []
        for val in data:
            sim.append(val * self.Factor)
        return sim[366:]

    def evaluation(self):
        return self.trueObs[366:]

    def objectivefunction(self, simulation, evaluation, params=None):
        # like = spotpy.likelihoods.gaussianLikelihoodMeasErrorOut(evaluation,simulation)
        # return -like
        # like1 = spotpy.signatures.getSkewness(evaluation, simulation)
        like1 = spotpy.objectivefunctions.agreementindex(evaluation, simulation)
        like2 = spotpy.objectivefunctions.rmse(evaluation, simulation)
        like3 = spotpy.signatures.getCoeffVariation(evaluation, simulation)
        return [like1, like2, like3]



class Test_NSGAII(unittest.TestCase):
    def setUp(self):
        self.sp_setup = spot_setup()
        self.sampler = spotpy.algorithms.NSGAII(self.sp_setup, dbname='NSGA2', dbformat="csv")

        self.sampler.sample(generations=5, paramsamp=40)

    def test_sampler_output(self):
        self.assertGreaterEqual(400, len(self.sampler.getdata()))
        self.assertLessEqual(300, len(self.sampler.getdata()))
