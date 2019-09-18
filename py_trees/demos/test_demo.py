import py_trees

N1 = py_trees.decorators.CoverageCounter(py_trees.behaviours.Success(name='S1'))
N2 = py_trees.decorators.CoverageCounter(py_trees.behaviours.Success(name='S2'))
Q1 = py_trees.decorators.TestInjector(py_trees.behaviours.Running(name='R1'))
N3 = py_trees.decorators.CoverageCounter(Q1)
N4 = py_trees.decorators.CoverageCounter(py_trees.behaviours.Failure(name='F1'))
# this next one can never be ticked, as the preceding failure will block it
N5 = py_trees.decorators.CoverageCounter(py_trees.behaviours.Success(name='S3'))

B1 = py_trees.decorators.CoverageCounter(py_trees.composites.Sequence(children=[N1,N2,N3,N4,N5],name='demo'))

T = py_trees.trees.BehaviourTree(B1)

V1 = py_trees.visitors.SnapshotVisitor()
T.visitors.append(V1)

V2 = py_trees.visitors.CoverageVisitor()
T.visitors.append(V2)

Q1.global_enable()

for ii in range(12):
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

print(py_trees.display.coverage_summary(T.root,V2))
