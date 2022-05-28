"""This module contains the implementation of an abstract definition
of an optimizer that can be used to optimize `Chromosome`'s constants.
"""

from abc import ABCMeta, abstractmethod


class OptimizerBase(metaclass=ABCMeta):
    """An abstract base class for optimizing `Chromosome`'s constants.
    """
    @property
    @abstractmethod
    def objective_fn(self):
        """function to minimize, must take a `Chromosome` as input
        and return a number"""
        raise NotImplementedError

    @objective_fn.setter
    @abstractmethod
    def objective_fn(self, value):
        raise NotImplementedError

    @property
    @abstractmethod
    def options(self):
        """dict : optimizer's options"""
        raise NotImplementedError

    @options.setter
    @abstractmethod
    def options(self, value):
        raise NotImplementedError

    @abstractmethod
    def __call__(self, individual):
        """Performs local optimization of the individual's constants
        based on minimizing this object's objective_fn.

        Parameters
        ----------
        individual : `Chromosome`
            The individual whose constants will be optimized.
        """
        raise NotImplementedError
