"""Local optimization using scipy

Specifies `ScipyOptimizer` which is a class for local optimization of
`Chromosome`s using scipy's minimize or root methods. Also
specifies ROOT_SET, a set of methods that will use scipy's root method;
MINIMIZE_SET, a set of methods that will use scipy's minimize method;
and JACOBIAN_SET, a set of methods that will use jacobian information.
"""

import numpy as np
from scipy import optimize

from .optimizer import OptimizerBase
from ..evaluation.gradient_mixin import GradientMixin, VectorGradientMixin

ROOT_SET = {
    # "hybr",
    "lm"
    # "broyden1",
    # "broyden2",
    # "anderson",
    # "linearmixing",
    # "diagbroyden",
    # "excitingmixing",
    # "krylov",
    # "df-sane"
}

MINIMIZE_SET = {
    "Nelder-Mead",
    "Powell",
    "CG",
    "BFGS",
    # "Newton-CG",
    "L-BFGS-B",
    "TNC",
    # "COBYLA",
    "SLSQP"
    # "trust-constr"
    # "dogleg",
    # "trust-ncg",
    # "trust-exact",
    # "trust-krylov"
}

JACOBIAN_SET = {
    "CG",
    "BFGS",
    # "Newton-CG",
    "L-BFGS-B",
    "TNC",
    "SLSQP",
    # "trust-constr"
    # "dogleg",
    # "trust-ncg",
    # "trust-exact",
    # "trust-krylov",
    # "hybr",
    "lm"
}


class ScipyOptimizer(OptimizerBase):
    """An optimizer that uses scipy.minimize or scipy.root
    for local optimization

    A class for optimizing the parameters of a `Chromosome` using
    either scipy.minimize or scipy.root depending on the method
    specified.

    Parameters
    ----------
    objective_fn
        A function to minimize which can be evaluated by passing in a
        `Chromosome`.
    options : dict, optional
        Additional arguments for optimization.
        e.g. (..., tol=1e-8, options={"maxiter": 1000})

        e.g. param_init_bounds: iterable
           [low, high) bounds that are used to initialize params,
           formatted as an iterable
           defaults to [-10000, 10000)

        e.g. method: string
            method to use for optimization (e.g. BFGS, lm, etc.)
            defaults to BFGS

        e.g. tol: float
            tolerance used for method
            defaults to 1e-6

        e.g. options : dict
            method-specific options (e.g. maxiter, ftol, etc.)

    Attributes
    ----------
    objective_fn
        A function to minimize which can be evaluated by passing in a
        `Chromosome`
    options : dict
        Additional arguments for clo options

    Raises
    ------
    KeyError
        `method` must be a method supported by scipy
    TypeError
        `objective_function` must suit the specified method
    """
    def __init__(self, objective_fn, **options):
        self.options = options
        self.objective_fn = objective_fn

    @property
    def objective_fn(self):
        """function to minimize, must take a `Chromosome` as input
        and return a number"""
        return self._objective_fn

    @objective_fn.setter
    def objective_fn(self, obj_fn):
        self._jacobian_capable = isinstance(obj_fn, VectorGradientMixin)
        self._gradient_capable = isinstance(obj_fn, GradientMixin)
        self._objective_fn = obj_fn
        self._verify_objective_fn(obj_fn, self.options["method"])

    @staticmethod
    def _verify_objective_fn(objective_fn, method):
        if method in ROOT_SET and not hasattr(objective_fn,
                                              "evaluate_fitness_vector"):
            raise TypeError("{} requires VectorBasedFunction \
                            as a fitness function".format(method))

    @property
    def options(self):
        """dict : optimizer options (e.g. param_init_bounds, method,
        tol, options, etc.)"""
        return self._options

    @options.setter
    def options(self, kwargs):
        self._options = kwargs

        # set default param init bounds to [-10000, 10000) if not included
        if "param_init_bounds" not in self._options.keys():
            self._options["param_init_bounds"] = [-10000, 10000]

        # set default method to BFGS if not included
        if "method" not in self._options.keys():
            self._options["method"] = "BFGS"
        self._verify_method(self._options["method"])

        # set default tol to 1e-6 if not included
        if "tol" not in self._options.keys():
            self._options["tol"] = 1e-6

        # scipy_options = normal options w/o param_init_bounds
        self._scipy_options = {k: v for k, v in self._options.items() if
                               k != "param_init_bounds"}

    @staticmethod
    def _verify_method(method):
        if method not in ROOT_SET and method not in MINIMIZE_SET:
            raise KeyError("{} is not a listed method".format(method))

    def __call__(self, individual):
        """Performs local optimization of the individual's constants
        based on minimizing this object's objective_fn.

        Parameters
        ----------
        individual : `Chromosome`
            The individual whose constants will be optimized.
        """
        num_params = individual.get_number_local_optimization_params()
        c_0 = np.random.uniform(*self.options["param_init_bounds"], num_params)
        params = self._run_method_for_optimization(
            self._sub_routine_for_obj_fn, individual, c_0)
        individual.set_local_optimization_params(params)

    def _sub_routine_for_obj_fn(self, params, individual):
        """Sets the individual's parameters to params and returns
        the objective_fn's evaluation of the individual after doing so.

        Parameters
        ----------
        params : iterable of float
            Parameters to set within the individual.
        individual : `Chromosome`
            The individual whose constants we want to optimize.

        Returns
        -------
        float or iterable of float
            The objective function's evaluation of the individual
            after its parameters are set to params
        """
        individual.set_local_optimization_params(params)

        if self.options["method"] in ROOT_SET:
            return self.objective_fn.evaluate_fitness_vector(individual)
        return self.objective_fn(individual)

    def _run_method_for_optimization(self, sub_routine, individual, params):
        """Run scipy optimization on the provided individual using
        this object's settings.

        Parameters
        ----------
        sub_routine
            The function that will be evaluated during optimization,
            see _sub_routine_for_obj_fn for more details.
        individual : `Chromosome`
            The individual whose constants we want to optimize.
        params : iterable of float
            Initial guess of the optimal parameters.

        Returns
        -------
        params: iterable of float
            The best found params for the provided individual
        """
        backend, jacobian = self._get_backend_and_jacobian()
        try:
            optimize_result = backend(
                sub_routine,
                params,
                args=individual,
                jac=jacobian,
                **self._scipy_options
            )
            return optimize_result.x
        except TypeError:  # issue with too many constants using root method
            old_method = self.options["method"]

            self.options["method"] = "BFGS"  # use minimize method instead
            self._scipy_options["method"] = "BFGS"

            backend, jacobian = self._get_backend_and_jacobian()
            optimize_result = backend(
                sub_routine,
                params,
                args=individual,
                jac=jacobian,
                **self._scipy_options
            )
            self.options["method"] = old_method  # reset to old method
            self._scipy_options["method"] = old_method
            return optimize_result.x

    def _get_backend_and_jacobian(self):
        """Returns scipy.minimize or scipy.root depending on the set method
        along with a jacobian function of the objective_fn if one can be found,
        otherwise returns False for the jacobian function.

        Returns
        -------
        backend
            scipy.minimize or scipy.root depending on the set method
        jacobian
            A function used to evaluate the jacobian of the objective_fn
            if one can be found, otherwise False
        """
        backend = optimize.minimize
        jacobian = False

        jacobian_method = self.options["method"] in JACOBIAN_SET

        if self.options["method"] in ROOT_SET:
            backend = optimize.root
            if jacobian_method and self._jacobian_capable:
                jacobian = lambda x, indv: \
                    self.objective_fn.get_fitness_vector_and_jacobian(indv)[1]

        else:  # MINIMIZE_SET
            if jacobian_method and self._gradient_capable:
                jacobian = lambda x, indv: \
                    self.objective_fn.get_fitness_and_gradient(indv)[1]

        return backend, jacobian
