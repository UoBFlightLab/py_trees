#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# License: BSD
#   https://raw.githubusercontent.com/splintered-reality/py_trees/devel/LICENSE
#
##############################################################################
# Documentation
##############################################################################

"""
Key-value storage for trees.
"""

##############################################################################
# Imports
##############################################################################

import enum
import re
import operator
import typing
import uuid

from . import behaviour
from . import behaviours
from . import common
from . import console

##############################################################################
# Classes
##############################################################################


class KeyMetaData(object):

    def __init__(self):
        self.read = []
        self.write = []


class ActivityStream(object):

    def __init__(self):
        pass


class Operation(enum.Enum):
    """An enumerator representing the operation on a blackboard variable"""

    READ = "READ"
    """Behaviour check has passed, or execution of its action has finished with a successful result."""
    WRITE = "WRITE"
    """Behaviour check has failed, or execution of its action finished with a failed result."""
    VALUE = "RUNNING"
    """Behaviour is in the middle of executing some action, result still pending."""
    INVALID = "INVALID"
    """Behaviour is uninitialised and inactive, i.e. this is the status before first entry, and after a higher priority switch has occurred."""


class ActivityItem(object):

    def __init__(self):
        self.key = None
        self.who = None
        self.operation = None
        self.value_previous = None
        self.value_new = None


class Blackboard(object):
    """
    Key-value store for sharing amongst behaviours.

    Examples:
        You can instantiate the blackboard from anywhere in your program. Even
        disconnected calls will get access to the same data store. For example:

        .. code-block:: python

            def check_foo():
                blackboard = Blackboard()
                assert(blackboard.foo, "bar")

            if __name__ == '__main__':
                blackboard = Blackboard()
                blackboard.foo = "bar"
                check_foo()

        If the key value you are interested in is only known at runtime, then
        you can set/get from the blackboard without the convenient variable style
        access:

        .. code-block:: python

            blackboard = Blackboard()
            result = blackboard.set("foo", "bar")
            foo = blackboard.get("foo")

        The blackboard can also be converted and printed (with highlighting)
        as a string. This is useful for logging and debugging.

        .. code-block:: python

            print(Blackboard())


    .. warning::

       Be careful of key collisions. This implementation leaves this management up to the user.

    Args:
        name: client's not nec. unique, but convenient identifier (stringifies the uuid if None)
        unique_identifier: client's unique identifier for tracking (auto-generates if None)
        read: list of keys this client has permission to read
        write: list of keys this client has permission to write

    .. note::

       Initialisation is not handled in construction, merely registration for tracking
       purposes (and incidentally, access permissions).

    Raises:
        TypeError: if the provided name/unique identifier is not of type str/uuid.UUID
        ValueError: if the unique identifier has already been registered

    Attributes:
        Blackboard.storage: key-value storage
        Blackboard.read: # typing.Dict[str, typing.List[uuid.UUID]]  / key : [unique identifier]
        Blackboard.write: # typing.Dict[str, typing.List[uuid.UUID]]  / key : [unique identifier]
        name: client's, not necessarily unique, identifier for tracking
        unique_identifier: client's unique identifier for tracking
        read: # typing.List[str] / [key]: list of keys this client has permission to read
        write: # typing.List[str] / [key]: list of keys this client has permission to write

    .. seealso::
       * :ref:`Blackboards and Blackboard Behaviours <py-trees-demo-blackboard-program>`
    """
    storage = {}  # Dict[str, Any] / key-value storage
    metadata = {}  # Dict[ str, KeyMetaData ] / key-metadata information
    clients = {}   # Dict[ uuid.UUID, Blackboard] / id-client information

    def __init__(
            self, *,
            name: str=None,
            unique_identifier: uuid.UUID=None,
            read: typing.List[str]=[],
            write: typing.List[str]=[]):
        # print("__init__")
        if unique_identifier is None:
            unique_identifier = uuid.uuid4()
        if type(unique_identifier) != uuid.UUID:
            raise TypeError("provided unique identifier is not of type uuid.UUID")
        if name is None or not name:
            name = str(unique_identifier)
        if not isinstance(name, str):
            raise TypeError("provided name is not of type str [{}]".format(type(name)))
        super().__setattr__("unique_identifier", unique_identifier)
        super().__setattr__("name", name)
        super().__setattr__("read", read)
        for key in read:
            Blackboard.metadata.setdefault(key, KeyMetaData())
            Blackboard.metadata[key].read.append(
                super().__getattribute__("unique_identifier")
            )
        super().__setattr__("write", write)
        for key in write:
            Blackboard.metadata.setdefault(key, KeyMetaData())
            Blackboard.metadata[key].write.append(
                super().__getattribute__("unique_identifier")
            )
        Blackboard.clients[
            super().__getattribute__("unique_identifier")
        ] = self

    def __setattr__(self, name, value):
        """
        Convenience attribute style referencing with checking against
        permissions.

        Raises:
            ValueError: if the client does not have write access to the variable
        """
        # print("__setattr__ [{}][{}]".format(name, value))
        if name not in super().__getattribute__("write"):
            raise ValueError("client '{}' does not have write access to '{}'".format(self.name, name))
        Blackboard.storage[name] = value

    def __getattr__(self, name):
        """
        Convenience attribute style referencing with checking against
        permissions.

        Raises:
            ValueError: if the client does not have read access to the variable
            AttributeError: if the variable does not yet exist on the blackboard
        """
        # print("__getattr__ [{}]".format(name))
        try:
            value = Blackboard.storage[name]
            if name not in super().__getattribute__("read"):
                raise ValueError("client '{}' does not have read access to '{}'".format(self.name, name))
            return value
        except KeyError as e:
            raise AttributeError("variable '{}' does not yet exist on the blackboard".format(name)) from e

    @staticmethod
    def introspect_blackboard():
        print("-----------------")
        print("Introspect")
        print("-----------------")
        print("  Blackboard.storage:\n{}".format(Blackboard.storage))
        print("  Blackboard.metadata:\n{}".format(Blackboard.metadata))
        # print("  Blackboard.write:\n{}".format(Blackboard.write))

    def set(self, name: str, value: typing.Any, overwrite: bool=True):
        """
        Set, conditionally depending on whether the variable already exists or otherwise.

        This is most useful when initialising variables and multiple elements
        seek to do so. A good policy to adopt for your applications in these situations is
        a first come, first served policy. Ensure global configuration has the first
        opportunity followed by higher priority behaviours in the tree and so forth.
        Lower priority behaviours would use this to respect the pre-configured
        setting and at most, just validate that it is acceptable to the functionality
        of it's own behaviour.

        Args:
            name: name of the variable to set
            value: value of the variable to set
            overwrite: do not set if the variable already exists on the blackboard

        Raises:
            ValueError: if the client does not have write access to the variable
            AttributeError: if overwrite was not requested and the variable already exists
        """
        if name not in super().__getattribute__("write"):
            raise ValueError("client does not have write access to '{}'".format(name))
        if not overwrite:
            if name in Blackboard.storage:
                raise AttributeError("variable already exists and overwriting was not requested")
        setattr(self, name, value)
        return True

    def get(self, name):
        """
        Method based accessor to the blackboard variables (as opposed to simply using
        '.<name>').

        Args:
            name: name of the variable to get

        Raises:
            ValueError: if the client does not have read access to the variable
            AttributeError: if the variable does not yet exist on the blackboard
        """
        return getattr(self, name)

    def unset(self, name: str):
        """
        For when you need to unset a blackboard variable, this provides a
        convenient helper method. This is particularly useful for unit
        testing behaviours.

        Args:
            name: name of the variable to unset

        Raises:
            AttributeError: if the variable does not yet exist
        """
        delattr(self, name)

    def __str__(self):
        indent = "  "
        s = console.green + type(self).__name__ + console.reset + "\n"
        s += console.white + indent + "Client Data" + console.reset + "\n"
        keys = ["name", "unique_identifier", "read", "write"]
        s += self.stringify_key_value_pairs(keys, self.__dict__, 2 * indent)
        s += console.white + indent + "Variables" + console.reset + "\n"
        keys = list(dict.fromkeys(self.read + self.write))  # unique list, https://www.peterbe.com/plog/fastest-way-to-uniquify-a-list-in-python-3.6
        s += self.stringify_key_value_pairs(keys, Blackboard.storage, 2 * indent)
        return s

    def stringify_key_value_pairs(self, keys, key_value_dict, indent):
        s = ""
        max_length = 0
        for key in keys:
            max_length = len(key) if len(key) > max_length else max_length
        for key in keys:
            try:
                value = key_value_dict[key]
                lines = ('{0}'.format(value)).split('\n')
                if len(lines) > 1:
                    s += console.cyan + indent + '{0: <{1}}'.format(key, max_length + 1) + console.reset + ":\n"
                    for line in lines:
                        s += console.yellow + indent + "  {0}\n".format(line) + console.reset
                else:
                    s += console.cyan + indent + '{0: <{1}}'.format(key, max_length + 1) + console.reset + ": " + console.yellow + '{0}\n'.format(value) + console.reset
            except KeyError:
                s += console.cyan + indent + '{0: <{1}}'.format(key, max_length + 1) + console.reset + ": " + console.yellow + "-\n" + console.reset
        s += console.reset
        return s

    def unregister(self, clear=True):
        """
        Unregister this blackboard and if requested, clear key-value pairs if this
        client is the last user of those variables.
        """
        for key in self.read:
            Blackboard.metadata[key].read.remove(super().__getattribute__("unique_identifier"))
        for key in self.write:
            Blackboard.metadata[key].write.remove(super().__getattribute__("unique_identifier"))
        if clear:
            for key in (set(self.read) | set(self.write)):
                if not (set(Blackboard.metadata[key].read) | set(Blackboard.metadata[key].write)):
                    Blackboard.storage.pop(key, None)

    @staticmethod
    def keys() -> typing.Set[str]:
        """
        Get the set of blackboard keys.

        Returns:
            the complete set of keys registered by clients
        """
        # return registered keys, those on the blackboard are not
        # necessarily written to yet
        return Blackboard.metadata.keys()

    @staticmethod
    def keys_filtered_by_regex(regex: str) -> typing.Set[str]:
        """
        Get the set of blackboard keys filtered by regex.

        Args:
            regex: a python regex string

        Returns:
            subset of keys that have been registered and match the pattern
        """
        pattern = re.compile(regex)
        return [key for key in Blackboard.metadata.keys() if pattern.search(key) is not None]

    @staticmethod
    def keys_filtered_by_clients(client_ids: typing.Union[typing.List[str], typing.Set[str]]) -> typing.Set[str]:
        """
        Get the set of blackboard keys filtered by client ids.

        Args:
            client_ids: set of client uuid's.

        Returns:
            subset of keys that have been registered by the specified clients
        """
        # convenience for users
        if type(client_ids) == list:
            client_ids = set(client_ids)
        keys = set()
        for key in Blackboard.metadata.keys():
            # for sets, | is union, & is intersection
            key_clients = set(Blackboard.metadata[key].read) | set(Blackboard.metadata[key].write)
            if key_clients & client_ids:
                keys.add(key)
        return keys

##############################################################################
# Blackboard Behaviours
##############################################################################


class ClearBlackboardVariable(behaviours.Success):
    """
    Clear the specified value from the blackboard.

    Args:
        name (:obj:`str`): name of the behaviour
        variable_name (:obj:`str`): name of the variable to clear
    """
    def __init__(self,
                 name="Clear Blackboard Variable",
                 variable_name="dummy",
                 ):
        super(ClearBlackboardVariable, self).__init__(name)
        self.variable_name = variable_name
        self.blackboard = Blackboard(
            name=self.name,
            write={self.variable_name}
        )

    def initialise(self):
        """
        Delete the variable from the blackboard.
        """
        self.blackboard.unset(self.variable_name)


class SetBlackboardVariable(behaviours.Success):
    """
    Set the specified variable on the blackboard.
    Usually we set variables from inside other behaviours, but can
    be convenient to set them from a behaviour of their own sometimes so you
    don't get blackboard logic mixed up with more atomic behaviours.

    Args:
        name (:obj:`str`): name of the behaviour
        variable_name (:obj:`str`): name of the variable to set
        variable_value (:obj:`any`): value of the variable to set

    .. todo:: overwrite option, leading to possible failure/success logic.
    """
    def __init__(self,
                 name="Set Blackboard Variable",
                 variable_name="dummy",
                 variable_value=None
                 ):
        """
        :param name: name of the behaviour
        :param variable_name: name of the variable to set
        :param value_name: value of the variable to set
        """
        super(SetBlackboardVariable, self).__init__(name)
        self.variable_name = variable_name
        self.variable_value = variable_value

    def initialise(self):
        self.blackboard = Blackboard(
            name=self.name,
            unique_identifier=self.id,
            write={self.variable_name}
        )
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
                 name,
                 variable_name="dummy",
                 expected_value=None,
                 comparison_operator=operator.eq,
                 clearing_policy=common.ClearingPolicy.ON_INITIALISE,
                 debug_feedback_message=False
                 ):
        """
        Initialise the behaviour. It's worth noting that there are a few
        combinations to the configuration that serve different use cases.

        Args:
            name (:obj:`str`): name of the behaviour
            variable_name (:obj:`str`): name of the variable to set
            expected_value (:obj:`any`): expected value to find (if `None`, check for existence only)
            comparison_operator (:obj:`func`): one from the python `operator module`_
            clearing_policy (:obj:`any`): when to clear the match result, see :py:class:`~py_trees.common.ClearingPolicy`
            debug_feedback_message (:obj:`bool`): provide additional detail in behaviour feedback messages for debugging

        .. tip::
            If just checking for existence, use the default argument
            on construction, `expected_value=None`.

        .. tip::
            There are times when you want to get the expected match once and then save
            that result thereafter. For example, to flag once a system has reached a
            subgoal. Use the :data:`~py_trees.common.ClearingPolicy.NEVER` flag to do this.
        """
        super(CheckBlackboardVariable, self).__init__(name)
        self.variable_name = variable_name
        self.blackboard = Blackboard(
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
        check_attr = operator.attrgetter(self.variable_name)

        try:
            value = check_attr(self.blackboard)
            # if existence check required only
            if self.expected_value is None:
                self.feedback_message = "'%s' exists on the blackboard (as required)" % self.variable_name
                result = common.Status.SUCCESS
        except AttributeError:
            self.feedback_message = 'blackboard variable {0} did not exist'.format(self.variable_name)
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
                 name,
                 variable_name="dummy",
                 expected_value=None,
                 comparison_operator=operator.eq,
                 clearing_policy=common.ClearingPolicy.ON_INITIALISE
                 ):
        super(WaitForBlackboardVariable, self).__init__(name)
        self.variable_name = variable_name
        self.blackboard = Blackboard(
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
            value = self.check_attr(self.blackboard)
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
        except AttributeError:
            self.feedback_message = 'blackboard variable {0} did not exist'.format(self.variable_name)
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


##############################################################################
# Main
##############################################################################


def main():
    bb2 = Blackboard(
        name="Bob's Board",
        unique_identifier=uuid.uuid4(),
        read=['foo', 'bar'],
        write=['foo', 'dude'],
    )
    bb2.foo = "more bar"
    bb2.dude = "bob"
    unused_myfoo = bb2.foo
    bb2.introspect_blackboard()
    print("-----------------")
    print("{}".format(str(bb2)))
    print("-----------------")
    print(console.green + "Exceptions\n" + console.reset)
    try:
        print(console.green + "  get(<key>): doesn't exist on the blackboard" + console.reset)
        print("bar: {}".format(bb2.get('bar')))
    except Exception as e:
        print("    {}: {}".format(type(e), str(e)))
    try:
        print(console.green + "  get(<key>): doesn't have read access..." + console.reset)
        print("dude: {}".format(bb2.get('dude')))
    except Exception as e:
        print("    {}: {}".format(type(e), str(e)))
    try:
        print(console.green + "  .<key>: doesn't exist on the blackboard" + console.reset)
        print("bar: {}".format(bb2.bar))
    except Exception as e:
        print("    {}: {}".format(type(e), str(e)))
    try:
        print(console.green + "  .<key>: doesn't have read access..." + console.reset)
        print("dude: {}".format(bb2.dude))
    except Exception as e:
        print("    {}: {}".format(type(e), str(e)))
    # set
    try:
        print(console.green + "  set(<key>): doesn't have write permissions" + console.reset)
        bb2.set('foobar', 3)
    except Exception as e:
        print("    {}: {}".format(type(e), str(e)))
    try:
        print(console.green + "  set(<key>): could not overwrite existing variable" + console.reset)
        bb2.set('foo', 3, overwrite=False)
    except Exception as e:
        print("    {}: {}".format(type(e), str(e)))
    try:
        print(console.green + "  .<key>=...: doesn't have write permissions" + console.reset)
        bb2.foobar = 3
    except Exception as e:
        print("    {}: {}".format(type(e), str(e)))