import py_trees
import random

class CoverageCounter(py_trees.decorators.Decorator):
    def __init__(self,child):
        self.times_ticked = 0
        self.times_success = 0
        self.times_running = 0
        self.times_failure = 0
        super(CoverageCounter, self).__init__(child=child, name=self.coverage_report())

    def coverage_report(self):
        report_message = 'T:{} S:{} R:{} F:{}'.format(self.times_ticked,
                                                      self.times_success,
                                                      self.times_running,
                                                      self.times_failure)
        return(report_message)

    def update(self):
        self.times_ticked = self.times_ticked + 1
        if self.decorated.status == py_trees.common.Status.SUCCESS:
          self.times_success = self.times_success + 1
        if self.decorated.status == py_trees.common.Status.RUNNING:
          self.times_running = self.times_running + 1
        if self.decorated.status == py_trees.common.Status.FAILURE:
          self.times_failure = self.times_failure + 1
        report_message = self.coverage_report()
        #self.feedback_message = report_message
        self.name = report_message
        return self.decorated.status


class TestInjector(py_trees.decorators.Decorator):
    def __init__(self,child):
        super(TestInjector, self).__init__(child=child)
        self._fixed_override = None
        self._random_override = False

    def set_override(self,status=None):
        if status:
            self._fixed_override = status
            self._random_override = False
        else:
            self._fixed_override = None
            self._random_override = True
        if self.override_enabled():
            print('OVERRIDE SET UP AND ACTIVE')
        else:
            print('OVERRIDE SET UP.  INACTIVE UNTIL GLOBAL OVERRIDE ON')

    def disable_override(self):
        self._fixed_override = None
        self._random_override = False

    def global_enable(self):
        bb = py_trees.blackboard.Blackboard()
        bb.ENABLE_TEST_INJECT = True
        print('TEST INJECTION ENABLED: BEHAVIOURS WILL BE OVERRIDEN')

    def global_disable(self):
        bb = py_trees.blackboard.Blackboard()
        bb.ENABLE_TEST_INJECT = False
        print('TEST INJECTION DISABLED: ALL BEHAVIOURS ACTIVE')

    def override_enabled(self):
        bb = py_trees.blackboard.Blackboard()
        global_enable = bb.get('ENABLE_TEST_INJECT')
        if global_enable is None:
            return False
        elif not global_enable==True:
            return False
        if self._fixed_override:
            return True
        elif self._random_override:
            return True
        else:
            return False

    def update(self):
        """
        Bounce if test injection enabled
        """
        if self.override_enabled():
            if self._fixed_override:
                self.logger.debug("{}.update()[bouncing]".format(self.__class__.__name__))
                status = self._fixed_override
            elif self._random_override:
                self.logger.debug("{}.update()[bouncing]".format(self.__class__.__name__))
                r = 3*random.random()
                if r<=1:
                    status = py_trees.common.Status.SUCCESS
                elif r<=2:
                    status = py_trees.common.Status.RUNNING
                else:
                    status = py_trees.common.Status.FAILURE
            self.feedback_message = 'Test injects {}'.format(status.name)
            return status
        self.feedback_message = 'Injection disabled'
        return self.decorated.status
    
    def tick(self):
        """
        Select between decorator (single child) and behaviour (no children) style
        ticks depending on whether or not the underlying child has been ticked
        successfully to completion previously.
        """
        if self.override_enabled():
            # ignore the child
            for node in py_trees.behaviour.Behaviour.tick(self):
                yield node
        else:
            # tick the child
            for node in py_trees.decorators.Decorator.tick(self):
                yield node

class CoverageVisitor(py_trees.visitors.VisitorBase):

    def __init__(self):
        super(CoverageVisitor, self).__init__(full=False)
        self.times_ticked = {}
        self.has_returned = {}
        self.has_returned[py_trees.common.Status.RUNNING]={}
        self.has_returned[py_trees.common.Status.SUCCESS]={}
        self.has_returned[py_trees.common.Status.FAILURE]={}

    def run(self, behaviour):
        if behaviour.id in self.times_ticked.keys():
            self.times_ticked[behaviour.id] = self.times_ticked[behaviour.id] + 1
        else:
            self.times_ticked[behaviour.id] = 1
        if behaviour.status in self.has_returned.keys():
            self.has_returned[behaviour.status][behaviour.id]=True

    def report(self):
        for id in self.times_ticked.keys():
            has_s = (id in self.has_returned[py_trees.common.Status.SUCCESS].keys())
            has_r = (id in self.has_returned[py_trees.common.Status.RUNNING].keys())
            has_f = (id in self.has_returned[py_trees.common.Status.FAILURE].keys())
            print('Node {} ticked {} times. Succeeded: {}; Running: {}; Failed: {}; '.format(id,self.times_ticked[id],has_s,has_r,has_f))

N1 = CoverageCounter(py_trees.behaviours.Success(name='S1'))
N2 = CoverageCounter(py_trees.behaviours.Success(name='S2'))
Q1 = TestInjector(py_trees.behaviours.Running(name='R1'))
N3 = CoverageCounter(Q1)

B1 = CoverageCounter(py_trees.composites.Sequence(children=[N1,N2,N3],name='demo'))

T = py_trees.trees.BehaviourTree(B1)
V1 = py_trees.visitors.SnapshotVisitor()
T.visitors.append(V1)
V2 = CoverageVisitor()
T.visitors.append(V2)

Q1.global_enable()

for ii in range(20):
  if ii==3:
    Q1.set_override(py_trees.common.Status.FAILURE)
  if ii==5:
    Q1.set_override(py_trees.common.Status.SUCCESS)
  if ii==7:
    Q1.set_override()
  if ii==9:
    Q1.disable_override()
  T.tick()
  print(py_trees.display.ascii_tree(T.root,visited=V1.visited,
                                    previously_visited=V1.previously_visited))

V2.report()
