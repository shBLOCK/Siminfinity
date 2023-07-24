class_name MenuItem extends Node


signal focused
signal pressed


@export var is_separator := false:
	set(value):
		print("set")
		is_separator = value
		_on_property_changed()

@export var text: String = ""

@export_multiline var tooltip := "":
	set(value):
		tooltip = value
		_on_property_changed()

@export var accelerator_key: Key:
	set(value):
		accelerator_key = value
		_on_property_changed()
@export_flags("Cmd or Ctrl:16777216", "Shift:33554432", "Alt:67108864", "Meta:134217728", "Ctrl:268435456", "Keypad:536870912", "Group Switch:1073741824")
var accelerator_mods := 0:
	set(value):
		accelerator_mods = value
		_on_property_changed()

@export var disabled := false:
	set(value):
		disabled = value
		_on_property_changed()

@export var indent := 0:
	set(value):
		indent = value
		_on_property_changed()

@export_group("Check Mode")
enum CheckableMode { NONE, BOX, RADIO }
@export var checkable_mode: CheckableMode:
	set(value):
		checkable_mode = value
		_on_property_changed()
@export var checked := false:
	set(value):
		checked = value
		_on_property_changed()
@export var toggle_on_press := true:
	set(value):
		toggle_on_press = value
		_on_property_changed()

@export_group("Icon")
@export var icon: Texture2D:
	set(value):
		icon = value
		_on_property_changed()
@export var icon_max_width := 0:
	set(value):
		icon_max_width = value
		_on_property_changed()
@export var icon_modulate := Color.WHITE:
	set(value):
		icon_modulate = value
		_on_property_changed()

@export_group("Short Cut")
@export var shortcut: Shortcut:
	set(value):
		shortcut = value
		_on_property_changed()
@export var shortcut_global := false:
	set(value):
		shortcut_global = value
		_on_property_changed()
@export var shortcut_disabled := false:
	set(value):
		shortcut_disabled = value
		_on_property_changed()

@export_group("")


@warning_ignore("unused_private_class_variable")
var _id: int
@warning_ignore("unused_private_class_variable")
var _menu: PopupMenu
@warning_ignore("unused_private_class_variable")
var _index: int
@warning_ignore("unused_private_class_variable")
var _smart_menu: SmartPopupMenu
@warning_ignore("unused_private_class_variable")
var _sub_menu: PopupMenu


func _on_child_order_changed() -> void:
	if _smart_menu != null:
		_smart_menu._on_item_rearranged()

func _on_tree_entered():
	var parent := get_parent()
	if parent is SmartPopupMenu:
		parent._on_item_rearranged()

var _old_parent: Node = null

func _on_tree_exiting():
	_old_parent = get_parent()

func _on_tree_exited():
	if _old_parent is SmartPopupMenu:
		_old_parent._on_item_rearranged()

func _on_property_changed() -> void:
	if _smart_menu != null:
		_smart_menu.update_item(self)

# prevent infinite recursion
#var _in_get_prop_list_func := false
#func _get_property_list() -> Array[Dictionary]:
#	if _in_get_prop_list_func:
#		return []
#	_in_get_prop_list_func = true
#
#	var props := get_property_list()
#
#	var is_my_prop := false
#	for prop in props:
#		print(prop)
#		if prop.name == "menu_item.gd":
#			is_my_prop = true
#		if not is_my_prop:
#			continue
#
#		if is_separator and prop.name != "is_separator":
#			prop.usage = PROPERTY_USAGE_READ_ONLY
#
#	_in_get_prop_list_func = false
#
#	return props
