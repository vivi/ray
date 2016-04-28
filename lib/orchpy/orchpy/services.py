import subprocess32 as subprocess
import os
import atexit
import time

import orchpy
import orchpy.worker as worker

_services_path = os.path.dirname(os.path.abspath(__file__))

all_processes = []
drivers = []

IP_ADDRESS = "127.0.0.1"
TIMEOUT_SECONDS = 5

def address(host, port):
  return host + ":" + str(port)

scheduler_port_counter = 0
def new_scheduler_port():
  global scheduler_port_counter
  scheduler_port_counter += 1
  return 10000 + scheduler_port_counter

worker_port_counter = 0
def new_worker_port():
  global worker_port_counter
  worker_port_counter += 1
  return 40000 + worker_port_counter

objstore_port_counter = 0
def new_objstore_port():
  global objstore_port_counter
  objstore_port_counter += 1
  return 20000 + objstore_port_counter

def cleanup():
  global all_processes
  for p, address in all_processes:
    if p.poll() is not None: # process has already terminated
      print "Process at address " + address + " has already terminated."
      continue
    print "Attempting to kill process at address " + address + "."
    p.kill()
    time.sleep(0.05) # is this necessary?
    if p.poll() is not None:
      print "Successfully killed process at address " + address + "."
      continue
    print "Kill attempt failed, attempting to terminate process at address " + address + "."
    p.terminate()
    time.sleep(0.05) # is this necessary?
    if p.poll is not None:
      print "Successfully terminated process at address " + address + "."
      continue
    print "Termination attempt failed, giving up."
  all_processes = []

  global drivers
  for driver in drivers:
    orchpy.disconnect(driver)
  if len(drivers) == 0:
    orchpy.disconnect()
  drivers = []

# atexit.register(cleanup)

def start_scheduler(scheduler_address):
  p = subprocess.Popen([os.path.join(_services_path, "scheduler"), scheduler_address])
  all_processes.append((p, scheduler_address))

def start_objstore(scheduler_address, objstore_address):
  p = subprocess.Popen([os.path.join(_services_path, "objstore"), scheduler_address, objstore_address])
  all_processes.append((p, objstore_address))

def start_worker(test_path, scheduler_address, objstore_address, worker_address):
  p = subprocess.Popen(["python",
                        test_path,
                        "--scheduler-address=" + scheduler_address,
                        "--objstore-address=" + objstore_address,
                        "--worker-address=" + worker_address])
  all_processes.append((p, worker_address))

def start_node(scheduler_address, node_ip_address, num_workers, worker_path=None):
  """
  Start an object store and associated workers that will be part of a larger cluster.
    Assumes the scheduler has already been started.

  :param scheduler_address: ip address and port of the scheduler (which typically runs on a different node)
  :param node_ip_address: ip address (without port) of the node this function is run on
  :param num_workers: the number of workers to be started on this node
  :worker_path: path of the source code that will be run on the worker
  """
  objstore_address = address(node_ip_address, new_objstore_port())
  start_objstore(scheduler_address, objstore_address)
  time.sleep(0.2)
  for _ in range(num_workers_per_objstore):
    start_worker(worker_path, scheduler_address, objstore_address, address(node_ip_address, new_worker_port()))
  time.sleep(0.3)
  orchpy.connect(scheduler_address, objstore_address, address(node_ip_address, new_worker_port()))
  time.sleep(0.5)

def start_cluster(scheduler_address=None, objstore_address=None, return_drivers=False, num_objstores=1, num_workers_per_objstore=0, worker_path=None):
  global drivers
  if num_workers_per_objstore > 0 and worker_path is None:
    raise Exception("Attempting to start a cluster with {} workers per object store, but `worker_path` is None.".format(num_workers_per_objstore))
  if num_workers_per_objstore > 0 and num_objstores < 1:
    raise Exception("Attempting to start a cluster with {} workers per object store, but `num_objstores` is {}.".format(num_objstores))
  if scheduler_address is None:
    # Then start a scheduler
    scheduler_address = address(IP_ADDRESS, new_scheduler_port())
    start_scheduler(scheduler_address)
  time.sleep(0.1)
  objstore_addresses = []
  # create objstores
  for i in range(num_objstores):
    objstore_address = address(IP_ADDRESS, new_objstore_port())
    objstore_addresses.append(objstore_address)
    start_objstore(scheduler_address, objstore_address)
    time.sleep(0.2)
    for _ in range(num_workers_per_objstore):
      start_worker(worker_path, scheduler_address, objstore_address, address(IP_ADDRESS, new_worker_port()))
    time.sleep(0.3)
  # create drivers
  if return_drivers:
    driver_workers = []
    for i in range(num_objstores):
      driver_worker = worker.Worker()
      orchpy.connect(scheduler_address, objstore_address, address(IP_ADDRESS, new_worker_port()), driver_worker)
      driver_workers.append(driver_worker)
      drivers.append(driver_worker)
    time.sleep(0.5)
    return driver_workers
  else:
    orchpy.connect(scheduler_address, objstore_addresses[0], address(IP_ADDRESS, new_worker_port()))
    time.sleep(0.5)
