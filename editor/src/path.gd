@tool
extends Node3D


@export var a: Node3D:
	set(value):
		a = value
		update()
@export var b: Node3D:
	set(value):
		b = value
		update()


func _ready() -> void:
	if Engine.is_editor_hint():
		$MeshInstance3D.owner = get_tree().edited_scene_root
	update()

func update() -> void:
	#if Engine.is_editor_hint():
	if is_node_ready():
		if a != null and b != null:
			var ap: Vector3 = a.position
			var bp: Vector3 = b.position
			position = (ap + bp) * 0.5
			$MeshInstance3D.scale.y = ap.distance_to(bp)
			look_at(ap)
			#$Decal.size = Vector3(0.1, 0.001, ap.distance_to(bp))
			#$Decal.look_at(ap)
