@tool
class_name ThemeIconTexture extends ImageTexture


@export var theme_type: String = "EditorIcons":
	set(value):
		theme_type = value
		update_icon()
@export var theme_name: String:
	set(value):
		theme_name = value
		update_icon()

func _init() -> void:
	self.changed.connect(self._on_changed)

var _updating := false

func update_icon() -> void:
	_updating = true
	set_image(ThemeDB.get_project_theme().get_icon(theme_name, theme_type).get_image())
	_updating = false

func _on_changed() -> void:
	if not _updating:
		update_icon()
