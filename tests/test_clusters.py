from engine import clusters


def test_simple_cluster():
    clusters.clusters.clear()
    clusters.add_edge(1, 2)
    clusters.add_edge(2, 3)
    assert clusters.get_cluster(1) == {1, 2, 3}
    assert clusters.get_cluster(2) == {1, 2, 3}
    assert clusters.get_cluster(4) == {4}


def test_cluster_no_edges():
    clusters.clusters.clear()
    assert clusters.get_cluster(5) == {5}
