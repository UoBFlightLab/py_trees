import py_trees

N1 = py_trees.behaviours.Success(name='S1')
N2 = py_trees.behaviours.Success(name='S2')
N3 = py_trees.behaviours.Running(name='R1')
N4 = py_trees.behaviours.Failure(name='F1')
# this next one can never be ticked, as the preceding failure will block it
N5 = py_trees.behaviours.Success(name='S3')

N1a = py_trees.decorators.TestInjector(N1)
N2a = py_trees.decorators.TestInjector(N2)
N3a = py_trees.decorators.TestInjector(N3)
N4a = py_trees.decorators.TestInjector(N4)
N5a = py_trees.decorators.TestInjector(N5)

B1 = py_trees.composites.Sequence(children=[N1a,N2a,N3a,N4a,N5a],name='demo')

B1w = py_trees.decorators.FailureIsRunning(B1)

B1a = py_trees.decorators.AssertNever(B1w,py_trees.common.Status.FAILURE)

T = py_trees.trees.BehaviourTree(B1a)

V1 = py_trees.visitors.SnapshotVisitor()
T.visitors.append(V1)

V2 = py_trees.visitors.CoverageVisitor()
T.visitors.append(V2)

# turn on test injection
N3a.global_enable()

for ii in range(12):
  if ii==6:
    N3a.set_override(py_trees.common.Status.SUCCESS)
  T.tick()
  print(py_trees.display.ascii_tree(T.root,visited=V1.visited,
                                    previously_visited=V1.previously_visited))

print(py_trees.display.ascii_tree_coverage(T.root,V2))
print(py_trees.display.coverage_summary(T.root,V2))

# set random tests on rest
N1a.set_override()
N2a.set_override()
# note missing N3 so not expecting 100%
N4a.set_override()
N5a.set_override()

for ii in range(100):
  try:
    T.tick()
  except AssertionError:
    print("ASSERTION ERROR")
  #print(py_trees.display.ascii_tree(T.root,visited=V1.visited,
  #                                  previously_visited=V1.previously_visited))

print(py_trees.display.ascii_tree_coverage(T.root,V2))
print(py_trees.display.coverage_summary(T.root,V2))

# set random tests on rest
N1a.clear_override()
N2a.clear_override()
N3a.set_override()

for ii in range(100):
  T.tick()
  #print(py_trees.display.ascii_tree(T.root,visited=V1.visited,
  #                                  previously_visited=V1.previously_visited))

print(py_trees.display.ascii_tree_coverage(T.root,V2))
print(py_trees.display.coverage_summary(T.root,V2))
