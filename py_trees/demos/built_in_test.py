import py_trees

#TODO document
#TODO encapsulate the tree in a class so each test re-builds it anew

from py_trees.decorators import TestInjector, OneShot, FailureIsRunning, FailureIsSuccess, RunningIsFailure, AssertNever
from py_trees.behaviours import Success, Running, Failure
from py_trees.composites import Sequence, Selector
from py_trees.trees import BehaviourTree
from py_trees.visitors import SnapshotVisitor, CoverageVisitor
from py_trees.display import ascii_tree, ascii_tree_coverage, coverage_summary
from py_trees.common import Status

class FlightTree(BehaviourTree):

  def __init__(self):
    # the Success/Failure/Running leaf nodes
    # would be replaced by the drone interface
    self.chk_mode = TestInjector(Success('check_mode'))
    self.arm_cmd = Success(name='arm')
    self.is_armed = TestInjector(Success(name='is_armed'))
    self.take_off = Success(name='take_off')
    self.at_alt = TestInjector(Success(name='at_alt'))
    self.to_climb = Sequence('to_climb',[FailureIsRunning(self.chk_mode),
                                self.arm_cmd,
                                FailureIsRunning(self.is_armed),
                                self.take_off,
                                FailureIsRunning(self.at_alt)])

    self.upld_cmd = Success('upload')
    self.chk_upld = FailureIsRunning(TestInjector(Success('check_upload')))
    self.strt_mis = Success('start_mission')
    self.wait_arr = FailureIsRunning(TestInjector(Success('check_arrived')))
    self.do_move = Sequence('do_move',[self.upld_cmd,
                                       self.chk_upld,
                                       self.strt_mis,
                                       self.wait_arr])

    self.move_land = Sequence('move_land',[FailureIsSuccess(self.do_move),Success('land')])

    self.flight = AssertNever(child=Sequence('operation',[self.to_climb,self.move_land]),
                         status=Status.FAILURE)
    super().__init__(self.flight)

tree = FlightTree()
py_trees.display.render_dot_tree(tree.root)

cov_vis = CoverageVisitor()
snp_vis = SnapshotVisitor()
tree.add_visitor(cov_vis)
tree.add_visitor(snp_vis)

# by default, testing off
tree.chk_mode.global_disable()

def random_test():
  # set all testers to random
  [node.set_override() for node in tree.root.iterate() if isinstance(node,TestInjector)]
  tree.chk_mode.global_enable()
  for ii in range(100):
    tree.tick()
    print(ascii_tree(tree.root,
                     visited = snp_vis.visited,previously_visited = snp_vis.previously_visited))
  print(ascii_tree_coverage(tree.root,cov_vis))
  print(coverage_summary(tree.root,cov_vis))

def nominal_test():
  for ii in range(20):
    tree.tick()
    print(ascii_tree(tree.root,
                     visited = snp_vis.visited,previously_visited = snp_vis.previously_visited))
  print(ascii_tree_coverage(tree.root,cov_vis))
  print(coverage_summary(tree.root,cov_vis))

if __name__=='__main__':
  random_test()
