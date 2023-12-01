@tool
extends Node3D


@export var point: Node3D


func _process(delta: float) -> void:
	if Engine.is_editor_hint():
		if point != null:
			transform = point.global_transform
