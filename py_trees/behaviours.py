#!/usr/bin/env python
#
# License: BSD
#   https://raw.githubusercontent.com/splintered-reality/py_trees/devel/LICENSE
#
##############################################################################
# Documentation
##############################################################################

"""
A library of fundamental behaviours for use.
"""

##############################################################################
# Imports
##############################################################################

import operator
import typing

from . import behaviour
from . import blackboard
from . import common
from . import meta

##############################################################################
# Function Behaviours
##############################################################################


def success(self):
    self.logger.debug("%s.update()" % self.__class__.__name__)
    self.feedback_message = "success"
    return common.Status.SUCCESS


def failure(self):
    self.logger.debug("%s.update()" % self.__class__.__name__)
    self.feedback_message = "failure"
    return common.Status.FAILURE


def running(self):
    self.logger.debug("%s.update()" % self.__class__.__name__)
    self.feedback_message = "running"
    return common.Status.RUNNING


def dummy(self):
    self.logger.debug("%s.update()" % self.__class__.__name__)
    self.feedback_message = "crash test dummy"
    return common.Status.RUNNING


Success = meta.create_behaviour_from_function(success)
"""
Do nothing but tick over with :data:`~py_trees.common.Status.SUCCESS`.
"""

Failure = meta.create_behaviour_from_function(failure)
"""
Do nothing but tick over with :data:`~py_trees.common.Status.FAILURE`.
"""

Running = meta.create_behaviour_from_function(running)
"""
Do nothing but tick over with :data:`~py_trees.common.Status.RUNNING`.
"""

Dummy = meta.create_behaviour_from_function(dummy)
"""
Crash test dummy used for anything dangerous.
"""

##############################################################################
# Standalone Behaviours
##############################################################################


class Periodic(behaviour.Behaviour):
    """
    Simply periodically rotates it's status over the
    :data:`~py_trees.common.Status.RUNNING`, :data:`~py_trees.common.Status.SUCCESS`,
    :data:`~py_trees.common.Status.FAILURE` states.
    That is, :data:`~py_trees.common.Status.RUNNING` for N ticks,
    :data:`~py_trees.common.Status.SUCCESS` for N ticks,
    :data:`~py_trees.common.Status.FAILURE` for N ticks...

    Args:
        name (:obj:`str`): name of the behaviour
        n (:obj:`int`): period value (in ticks)

    .. note:: It does not reset the count when initialising.
    """
    def __init__(self, name, n):
        super(Periodic, self).__init__(name)
        self.count = 0
        self.period = n
        self.response = common.Status.RUNNING

    def update(self):
        self.count += 1
        if self.count > self.period:
            if self.response == common.Status.FAILURE:
                self.feedback_message = "flip to running"
                self.response = common.Status.RUNNING
            elif self.response == common.Status.RUNNING:
                self.feedback_message = "flip to success"
                self.response = common.Status.SUCCESS
            else:
                self.feedback_message = "flip to failure"
                self.response = common.Status.FAILURE
            self.count = 0
        else:
            self.feedback_message = "constant"
        return self.response


class SuccessEveryN(behaviour.Behaviour):
    """
    This behaviour updates it's status with :data:`~py_trees.common.Status.SUCCESS`
    once every N ticks, :data:`~py_trees.common.Status.FAILURE` otherwise.

    Args:
        name (:obj:`str`): name of the behaviour
        n (:obj:`int`): trigger success on every n'th tick

    .. tip::
       Use with decorators to change the status value as desired, e.g.
       :meth:`py_trees.decorators.FailureIsRunning`
    """
    def __init__(self, name, n):
        super(SuccessEveryN, self).__init__(name)
        self.count = 0
        self.every_n = n

    def update(self):
        self.count += 1
        self.logger.debug("%s.update()][%s]" % (self.__class__.__name__, self.count))
        if self.count % self.every_n == 0:
            self.feedback_message = "now"
            return common.Status.SUCCESS
        else:
            self.feedback_message = "not yet"
            return common.Status.FAILURE


class Count(behaviour.Behaviour):
    """
    A counting behaviour that updates its status at each tick depending on
    the value of the counter. The status will move through the states in order -
    :data:`~py_trees.common.Status.FAILURE`, :data:`~py_trees.common.Status.RUNNING`,
    :data:`~py_trees.common.Status.SUCCESS`.

    This behaviour is useful for simple testing and demo scenarios.

    Args:
        name (:obj:`str`): name of the behaviour
        fail_until (:obj:`int`): set status to :data:`~py_trees.common.Status.FAILURE` until the counter reaches this value
        running_until (:obj:`int`): set status to :data:`~py_trees.common.Status.RUNNING` until the counter reaches this value
        success_until (:obj:`int`): set status to :data:`~py_trees.common.Status.SUCCESS` until the counter reaches this value
        reset (:obj:`bool`): whenever invalidated (usually by a sequence reinitialising, or higher priority interrupting)

    Attributes:
        count (:obj:`int`): a simple counter which increments every tick
    """
    def __init__(self, name="Count", fail_until=3, running_until=5, success_until=6, reset=True):
        super(Count, self).__init__(name)
        self.count = 0
        self.fail_until = fail_until
        self.running_until = running_until
        self.success_until = success_until
        self.number_count_resets = 0
        self.number_updated = 0
        self.reset = reset

    def terminate(self, new_status):
        self.logger.debug("%s.terminate(%s->%s)" % (self.__class__.__name__, self.status, new_status))
        # reset only if udpate got us into an invalid state
        if new_status == common.Status.INVALID and self.reset:
            self.count = 0
            self.number_count_resets += 1
        self.feedback_message = ""

    def update(self):
        self.number_updated += 1
        self.count += 1
        if self.count <= self.fail_until:
            self.logger.debug("%s.update()[%s: failure]" % (self.__class__.__name__, self.count))
            self.feedback_message = "failing"
            return common.Status.FAILURE
        elif self.count <= self.running_until:
            self.logger.debug("%s.update()[%s: running]" % (self.__class__.__name__, self.count))
            self.feedback_message = "running"
            return common.Status.RUNNING
        elif self.count <= self.success_until:
            self.logger.debug("%s.update()[%s: success]" % (self.__class__.__name__, self.count))
            self.feedback_message = "success"
            return common.Status.SUCCESS
        else:
            self.logger.debug("%s.update()[%s: failure]" % (self.__class__.__name__, self.count))
            self.feedback_message = "failing forever more"
            return common.Status.FAILURE

    def __repr__(self):
        """
        Simple string representation of the object.

        Returns:
            :obj:`str`: string representation
        """
        s = "%s\n" % self.name
        s += "  Status : %s\n" % self.status
        s += "  Count  : %s\n" % self.count
        s += "  Resets : %s\n" % self.number_count_resets
        s += "  Updates: %s\n" % self.number_updated
        return s

##############################################################################
# Blackboard Behaviours
##############################################################################


class ClearBlackboardVariable(Success):
    """
    Clear the specified value from the blackboard.

    Args:
        name: name of the behaviour
        variable_name: name of the variable to clear
    """
    def __init__(self,
                 name: str=common.Name.AUTO_GENERATED,
                 variable_name: str="dummy",
                 ):
        super(ClearBlackboardVariable, self).__init__(
            name=name,
            blackboard_write={variable_name}
        )
        self.variable_name = variable_name

    def initialise(self):
        """
        Delete the variable from the blackboard.
        """
        self.blackboard.unset(self.variable_name)


class SetBlackboardVariable(Success):
    """
    Set the specified variable on the blackboard.
    Usually we set variables from inside other behaviours, but can
    be convenient to set them from a behaviour of their own sometimes so you
    don't get blackboard logic mixed up with more atomic behaviours.

    Args:
        name: name of the behaviour
        variable_name: name of the variable to set
        variable_value: value of the variable to set

    .. todo:: overwrite option, leading to possible failure/success logic.
    """
    def __init__(self,
                 name: str=common.Name.AUTO_GENERATED,
                 variable_name: str="dummy",
                 variable_value: typing.Any=None
                 ):
        """
        :param name: name of the behaviour
        :param variable_name: name of the variable to set
        :param value_name: value of the variable to set
        """
        super(SetBlackboardVariable, self).__init__(
            name=name,
            blackboard_write={variable_name}
        )
        self.variable_name = variable_name
        self.variable_value = variable_value

    def initialise(self):
        self.blackboard.set(self.variable_name, self.variable_value, overwrite=True)


class CheckBlackboardVariable(behaviour.Behaviour):
    """
    Check the blackboard to see if it has a specific variable
    and optionally whether that variable has an expected value.
    It is a binary behaviour, always updating it's status
    with either :data:`~py_trees.common.Status.SUCCESS` or
    :data:`~py_trees.common.Status.FAILURE` at each tick.
    """
    def __init__(self,
                 name: str=common.Name.AUTO_GENERATED,
                 variable_name: str="dummy",
                 expected_value: typing.Any=None,
                 comparison_operator: typing.Any=operator.eq,
                 clearing_policy: common.ClearingPolicy=common.ClearingPolicy.ON_INITIALISE,
                 debug_feedback_message: bool=False
                 ):
        """
        Initialise the behaviour. It's worth noting that there are a few
        combinations to the configuration that serve different use cases.

        Args:
            name: name of the behaviour
            variable_name: name of the variable to set
            expected_value: expected value to find (if `None`, check for existence only)
            comparison_operator: one from the python `operator module`_
            clearing_policy: when to clear the match result, see :py:class:`~py_trees.common.ClearingPolicy`
            debug_feedback_message: provide additional detail in behaviour feedback messages for debugging

        .. tip::
            If just checking for existence, use the default argument
            on construction, `expected_value=None`.

        .. tip::
            There are times when you want to get the expected match once and then save
            that result thereafter. For example, to flag once a system has reached a
            subgoal. Use the :data:`~py_trees.common.ClearingPolicy.NEVER` flag to do this.
        """
        super(CheckBlackboardVariable, self).__init__(
            name=name,
            blackboard_read={variable_name}
        )

        name_components = variable_name.split('.')
        self.variable_name = name_components[0]
        self.nested_name = '.'.join(name_components[1:])  # empty string if no other parts

        self.blackboard = blackboard.Blackboard(
            name=self.name,
            unique_identifier=self.id,
            read={self.variable_name}
        )
        self.expected_value = expected_value
        self.comparison_operator = comparison_operator
        self.matching_result = None
        self.clearing_policy = clearing_policy
        self.debug_feedback_message = debug_feedback_message

    def initialise(self):
        """
        Clears the internally stored message ready for a new run
        if ``old_data_is_valid`` wasn't set.
        """
        self.logger.debug("%s.initialise()" % self.__class__.__name__)
        if self.clearing_policy == common.ClearingPolicy.ON_INITIALISE:
            self.matching_result = None

    def update(self):
        """
        Check for existence, or the appropriate match on the expected value.

        Returns:
             :class:`~py_trees.common.Status`: :data:`~py_trees.common.Status.FAILURE` if not matched, :data:`~py_trees.common.Status.SUCCESS` otherwise.
        """
        self.logger.debug("%s.update()" % self.__class__.__name__)
        if self.matching_result is not None:
            return self.matching_result

        result = None

        try:
            # value = check_attr(self.blackboard)
            value = self.blackboard.get(self.variable_name)
            if self.nested_name:
                try:
                    value = operator.attrgetter(self.nested_name)(value)
                except AttributeError:
                    raise KeyError()
            # if existence check required only
            if self.expected_value is None:
                self.feedback_message = "'%s' exists on the blackboard (as required)" % self.variable_name
                result = common.Status.SUCCESS
        except KeyError:
            name = "{}.{}".format(self.variable_name, self.nested_name) if self.nested_name else self.variable_name
            self.feedback_message = 'blackboard variable {0} did not exist'.format(name)
            result = common.Status.FAILURE

        if result is None:
            # expected value matching
            # value = getattr(self.blackboard, self.variable_name)
            success = self.comparison_operator(value, self.expected_value)

            if success:
                if self.debug_feedback_message:  # costly
                    self.feedback_message = "'%s' comparison succeeded [v: %s][e: %s]" % (self.variable_name, value, self.expected_value)
                else:
                    self.feedback_message = "'%s' comparison succeeded" % (self.variable_name)
                result = common.Status.SUCCESS
            else:
                if self.debug_feedback_message:  # costly
                    self.feedback_message = "'%s' comparison failed [v: %s][e: %s]" % (self.variable_name, value, self.expected_value)
                else:
                    self.feedback_message = "'%s' comparison failed" % (self.variable_name)
                result = common.Status.FAILURE

        if result == common.Status.SUCCESS and self.clearing_policy == common.ClearingPolicy.ON_SUCCESS:
            self.matching_result = None
        else:
            self.matching_result = result
        return result

    def terminate(self, new_status):
        """
        Always discard the matching result if it was invalidated by a parent or
        higher priority interrupt.
        """
        self.logger.debug("%s.terminate(%s)" % (self.__class__.__name__, "%s->%s" % (self.status, new_status) if self.status != new_status else "%s" % new_status))
        if new_status == common.Status.INVALID:
            self.matching_result = None


class WaitForBlackboardVariable(behaviour.Behaviour):
    """
    Check the blackboard to see if it has a specific variable
    and optionally whether that variable has a specific value.
    Unlike :py:class:`~py_trees.blackboard.CheckBlackboardVariable`
    this class will be in a :data:`~py_trees.common.Status.RUNNING` state until the variable appears
    and (optionally) is matched.

    Args:
        name (:obj:`str`): name of the behaviour
        variable_name (:obj:`str`): name of the variable to check
        expected_value (:obj:`any`): expected value to find (if `None`, check for existence only)
        comparison_operator (:obj:`func`): one from the python `operator module`_
        clearing_policy (:obj:`any`): when to clear the match result, see :py:class:`~py_trees.common.ClearingPolicy`

    .. tip::
        There are times when you want to get the expected match once and then save
        that result thereafter. For example, to flag once a system has reached a
        subgoal. Use the :data:`~py_trees.common.ClearingPolicy.NEVER` flag to do this.

    .. seealso:: :class:`~py_trees.blackboard.CheckBlackboardVariable`

    .. include:: weblinks.rst
    """
    def __init__(self,
                 name=common.Name.AUTO_GENERATED,
                 variable_name="dummy",
                 expected_value=None,
                 comparison_operator=operator.eq,
                 clearing_policy=common.ClearingPolicy.ON_INITIALISE
                 ):
        super(WaitForBlackboardVariable, self).__init__(name)
        name_components = variable_name.split('.')
        self.variable_name = name_components[0]
        self.nested_name = '.'.join(name_components[1:])  # empty string if no other parts
        self.blackboard = blackboard.Blackboard(
            name=self.name,
            unique_identifier=self.id,
            read={self.variable_name}
        )
        self.expected_value = expected_value
        self.comparison_operator = comparison_operator
        self.clearing_policy = clearing_policy
        self.matching_result = None

    def initialise(self):
        """
        Clears the internally stored message ready for a new run
        if ``old_data_is_valid`` wasn't set.
        """
        self.logger.debug("%s.initialise()" % self.__class__.__name__)
        if self.clearing_policy == common.ClearingPolicy.ON_INITIALISE:
            self.matching_result = None
        self.check_attr = operator.attrgetter(self.variable_name)

    def update(self):
        """
        Check for existence, or the appropriate match on the expected value.

        Returns:
             :class:`~py_trees.common.Status`: :data:`~py_trees.common.Status.FAILURE` if not matched, :data:`~py_trees.common.Status.SUCCESS` otherwise.
        """
        self.logger.debug("%s.update()" % self.__class__.__name__)
        if self.matching_result is not None:
            return self.matching_result

        # existence failure check
        try:
            value = self.blackboard.get(self.variable_name)
            if self.nested_name:
                try:
                    value = operator.attrgetter(self.nested_name)(value)
                except AttributeError:
                    raise KeyError()  # type raised when no variable exists, caught below
            # if existence check required only
            if self.expected_value is None:
                self.feedback_message = "'%s' exists on the blackboard (as required)" % self.variable_name
                result = common.Status.SUCCESS
            # expected value matching
            else:
                success = self.comparison_operator(value, self.expected_value)
                if success:
                    self.feedback_message = "'%s' comparison succeeded [v: %s][e: %s]" % (self.variable_name, value, self.expected_value)
                    result = common.Status.SUCCESS
                else:
                    self.feedback_message = "'%s' comparison failed [v: %s][e: %s]" % (self.variable_name, value, self.expected_value)
                    result = common.Status.RUNNING
        except KeyError:
            name = "{}.{}".format(self.variable_name, self.nested_name) if self.nested_name else self.variable_name
            self.feedback_message = 'variable {0} did not exist'.format(name)
            result = common.Status.RUNNING

        if result == common.Status.SUCCESS and self.clearing_policy == common.ClearingPolicy.ON_SUCCESS:
            self.matching_result = None
        elif result != common.Status.RUNNING:  # will fall in here if clearing ON_INITIALISE, or NEVER
            self.matching_result = result
        return result

    def terminate(self, new_status):
        """
        Always discard the matching result if it was invalidated by a parent or
        higher priority interrupt.
        """
        self.logger.debug("%s.terminate(%s)" % (self.__class__.__name__, "%s->%s" % (self.status, new_status) if self.status != new_status else "%s" % new_status))
        if new_status == common.Status.INVALID:
            self.matching_result = None
