class_name PropertiesGroup extends VBoxContainer


var text: String:
	get:
		return %Button.text
	set(value):
		%Button.text = value

var expanded: bool:
	get:
		return %MarginContainer.visible
	set(value):
		%MarginContainer.visible = value
		_update_button_icon()

func add_sub(sub: Control) -> void:
	%SubPropertiesContainer.add_child(sub)

func get_sub(index: int) -> Control:
	return %SubPropertiesContainer.get_child(index) as Control

func get_all_sub() -> Array[Control]:
	return %SubPropertiesContainer.get_children() as Array[Control]

func remove_sub(sub: Control) -> void:
	%SubPropertiesContainer.remove_child(sub)


func _update_button_icon() -> void:
	%Button.icon = get_theme_icon(
		"arrow" if %MarginContainer.visible else "arrow_collapsed",
		"Tree"
	)

func _ready() -> void:
	_update_button_icon()

func _on_button_pressed() -> void:
	self.expanded = not self.expanded
