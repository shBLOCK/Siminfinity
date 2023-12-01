extends PropWidget


func _ready() -> void:
	$SpinBox.get_child(0, true).add_theme_stylebox_override("normal", get_theme_stylebox("child_bg", "EditorProperty"))
