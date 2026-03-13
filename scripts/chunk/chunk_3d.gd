# chunk_3d.gd
# 3D chunk for detach/recall. Spawned by PlayerController3D with an initial
# linear_velocity (lob); RigidBody3D gravity gives the arc. Starts frozen; controller unfreezes on detach.

extends RigidBody3D
