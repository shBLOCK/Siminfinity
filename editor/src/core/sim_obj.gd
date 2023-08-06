class_name SimObj extends Node3D


var position_2d: Vector2:
	get:
		return transform_2d.origin
	set(value):
		var t := transform_2d
		t.origin = value
		transform_2d = t

var transform_2d: Transform2D:
	get:
		var axis_x := Vector3.AXIS_X * transform
		var axis_y := Vector3.AXIS_Z * transform
		return Transform2D(axis_x, axis_y, )

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


func _notification(what: int) -> void:
	pass
