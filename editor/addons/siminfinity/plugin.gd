@tool
extends EditorPlugin


const CustomTypes := {
	SimRoot = preload("res://addons/siminfinity/types/sim_root.gd")
}


func _enter_tree() -> void:
	get_editor_interface().get_script_editor()
	add_custom_type("SimRoot", "SimRoot", CustomTypes.SimRoot, preload("res://icon.svg"))


func _exit_tree() -> void:
	remove_custom_type("SimRoot")
