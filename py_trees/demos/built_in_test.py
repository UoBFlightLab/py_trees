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

# the Success/Failure/Running leaf nodes
# would be replaced by the drone interface
chk_mode = TestInjector(Success('check_mode'))
arm_cmd = Success(name='arm')
is_armed = TestInjector(Success(name='is_armed'))
take_off = Success(name='take_off')
at_alt = TestInjector(Success(name='at_alt'))
to_climb = Sequence('to_climb',[FailureIsRunning(chk_mode),
                                arm_cmd,
                                FailureIsRunning(is_armed),
                                take_off,
                                FailureIsRunning(at_alt)])

upld_cmd = Success('upload')
chk_upld = FailureIsRunning(TestInjector(Success('check_upload')))
strt_mis = Success('start_mission')
wait_arr = FailureIsRunning(TestInjector(Success('check_arrived')))
do_move = Sequence('do_move',[upld_cmd,
                              chk_upld,
                              strt_mis,
                              wait_arr])

move_land = Sequence('move_land',[FailureIsSuccess(do_move),Success('land')])

flight = AssertNever(child=Sequence('operation',[to_climb,move_land]),
                     status=Status.FAILURE)

#tree = BehaviourTree(OneShot(Sequence('operation',[to_climb,move_land])))
tree = BehaviourTree(flight)

cov_vis = CoverageVisitor()
snp_vis = SnapshotVisitor()
tree.add_visitor(cov_vis)
tree.add_visitor(snp_vis)

# by default, testing off
chk_mode.global_disable()

def random_test():
  # set all testers to random
  [node.set_override() for node in tree.root.iterate() if isinstance(node,TestInjector)]
  chk_mode.global_enable()
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
  nominal_test()
