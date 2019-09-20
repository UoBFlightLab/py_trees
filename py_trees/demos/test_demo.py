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

N1b = py_trees.decorators.AssertNever(N1a, py_trees.common.Status.FAILURE, py_trees.common.Status.RUNNING)
N3b = py_trees.decorators.AssertNever(N3a,py_trees.common.Status.FAILURE)

B1 = py_trees.decorators.CoverageCounter(py_trees.composites.Sequence(children=[N1b,N2a,N3a,N4a,N5a],name='demo'))

T = py_trees.trees.BehaviourTree(B1)

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

print(py_trees.display.coverage_summary(T.root,V2))

# set random tests on rest
N1a.set_override()
N2a.set_override()
# note missing N3 so not expecting 100%
N4a.set_override()
N5a.set_override()

for ii in range(100):
  T.tick()
  #print(py_trees.display.ascii_tree(T.root,visited=V1.visited,
  #                                  previously_visited=V1.previously_visited))

print(py_trees.display.coverage_summary(T.root,V2))

# set random tests on rest
N1a.clear_override()
N2a.clear_override()
N3a.set_override()

for ii in range(100):
  T.tick()
  #print(py_trees.display.ascii_tree(T.root,visited=V1.visited,
  #                                  previously_visited=V1.previously_visited))

print(py_trees.display.coverage_summary(T.root,V2))
