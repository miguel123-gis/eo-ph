from dask_gateway import Gateway

def set_up_dask(enabled=False, num_workers=4, min_workers=4, max_workers=50):
    if enabled:
        # Set up dask
        gateway = Gateway("http://127.0.0.1:8000")
        gateway.list_clusters()

        # Create a cluster
        cluster = gateway.new_cluster()
        cluster.scale(num_workers)

        # Autoscale the clusters
        client = cluster.get_client()
        cluster.adapt(minimum=min_workers, maximum=max_workers)