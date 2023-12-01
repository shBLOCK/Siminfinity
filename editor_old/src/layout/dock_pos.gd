class_name DockPos extends Node


var id: Variant
var window: PanelDockWindow
var windowed: bool:
	get:
		return window != null

static var _instances: Array[DockPos] = []

@warning_ignore("shadowed_variable")
static func get_instance(id: Variant, window: PanelDockWindow = null) -> DockPos:
	## Use this instead of new()!!!
	## This is a singleton implementation.
	for i in DockPos._instances:
		if is_same(i.id, id) and i.window == window:
			return i
	
	var inst := new()
	inst.id = id
	inst.window = window
	DockPos._instances.append(inst)
	return inst

func _to_string() -> String:
	if not windowed:
		return str(id)
	else:
		return "WINDOW_%s" % str(id)

@warning_ignore("shadowed_variable")
static func from_string(string: String) -> DockPos:
	var _windowed := string.begins_with("WINDOW_")
	@warning_ignore("incompatible_ternary")
	var id: Variant = int(string.substr(7)) if _windowed else string
	var window: PanelDockWindow = LayoutManager.PanelDockWindows[id] if _windowed else null
	return DockPos.get_instance(id, window)
