class_name SimObj extends Node3D


var transform_2d: Transform2D:
	get:
		var basis3 := transform.basis
		var origin3 := transform.origin
		return Transform2D(
			Vector2(basis3.x.x, basis3.x.z),
			Vector2(basis3.z.x, basis3.z.z),
			Vector2(origin3.x, origin3.z)
		)
	set(value):
		transform.basis.x.x = value.x.x
		transform.basis.x.z = value.x.y
		transform.basis.z.x = value.y.x
		transform.basis.z.z = value.y.y
		transform.origin.x = value.origin.x
		transform.origin.z = value.origin.y

var position_2d: Vector2:
	get:
		return transform_2d.origin
	set(value):
		var t := transform_2d
		t.origin = value
		transform_2d = t

var rotation_2d: float:
	get:
		return transform_2d.get_rotation()
	set(value):
		transform_2d = transform_2d.rotated(transform_2d.get_rotation() - value)

var scale_2d: Vector2:
	get:
		return Vector2(transform_2d.get_scale())
	set(value):
		transform_2d = transform_2d.scaled_local(value)
