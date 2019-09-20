import py_trees

def test_injector():
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

  B1 = py_trees.decorators.CoverageCounter(py_trees.composites.Sequence(children=[N1a,N2a,N3a,N4a,N5a],name='demo'))

  T = py_trees.trees.BehaviourTree(B1)

  V1 = py_trees.visitors.SnapshotVisitor()
  T.visitors.append(V1)

  V2 = py_trees.visitors.CoverageVisitor()
  T.visitors.append(V2)

  T.tick()
  # initially runs due to blocking N3
  assert(T.root.status==py_trees.common.Status.RUNNING)

  # prepare N3 for test but don't enable - still running
  N3a.set_override(py_trees.common.Status.SUCCESS)
  T.tick()
  assert(T.root.status==py_trees.common.Status.RUNNING)

  # enable - should now fail at N4
  N1a.global_enable()
  T.tick()
  assert(T.root.status==py_trees.common.Status.FAILURE)

  # inject success at N4 and should succeed
  N4a.set_override(py_trees.common.Status.SUCCESS)
  T.tick()
  assert(T.root.status==py_trees.common.Status.SUCCESS)

  # inject running at N2 and should block with running
  N2a.set_override(py_trees.common.Status.RUNNING)
  T.tick()
  assert(T.root.status==py_trees.common.Status.RUNNING)

  # inject failure at N1 and should still block at N2
  N1a.set_override(py_trees.common.Status.FAILURE)
  T.tick()
  assert(T.root.status==py_trees.common.Status.RUNNING)

  # clear N2 and should fail at N1 on repeat
  N2a.clear_override()
  T.tick()
  assert(T.root.status==py_trees.common.Status.SUCCESS)
  T.tick()
  assert(T.root.status==py_trees.common.Status.FAILURE)

  # disable the tests and should be running again
  N5a.global_disable()
  T.tick()
  assert(T.root.status==py_trees.common.Status.RUNNING)

if __name__=="__main__":
  test_injector()
