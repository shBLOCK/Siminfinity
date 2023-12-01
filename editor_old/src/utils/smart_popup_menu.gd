class_name SmartPopupMenu extends PopupMenu


@export var menubar_title := "":
	set(value):
		menubar_title = value
		_update_menubar()
@export var menubar_tooltip := "":
	set(value):
		menubar_tooltip = value
		_update_menubar()
@export var menubar_disabled := false:
	set(value):
		menubar_disabled = value
		_update_menubar()
@export var menubar_hidden := false:
	set(value):
		menubar_hidden = value
		_update_menubar()

var _current_id := 0
var _id_item_map: Dictionary

func get_item_from_id(id: int) -> MenuItem:
	return _id_item_map.get(id)

var _building := false

func build() -> void:
	_building = true
	
	# Clearing
	_id_item_map = {}
	self.clear()
	for child in get_children(true):
		if child is PopupMenu:
			remove_child(child)
	
	# Building
	for child in get_children():
		_do_build(child as MenuItem, self)
	
	_building = false

func _do_build(item: MenuItem, menu: PopupMenu) -> void:
	item._menu = menu
	item._id = _current_id
	item._index = menu.item_count
	menu.add_item(item.text, _current_id)
	_id_item_map[_current_id] = item
	_current_id += 1
	
	if item.get_child_count() > 0:
		item._sub_menu = PopupMenu.new()
		# the submenu's name is set in undate_item()
		menu.add_child(item._sub_menu)
	else:
		item._sub_menu = null
	
	update_item(item)
	
	if not menu.id_focused.is_connected(self._on_menu_id_focused):
		menu.id_focused.connect(self._on_menu_id_focused)
	if not menu.id_pressed.is_connected(self._on_menu_id_pressed):
		menu.id_pressed.connect(self._on_menu_id_pressed)
	
	if item.get_child_count() > 0:
		for child in item.get_children():
			_do_build(child, item._sub_menu)

func update_item(item: MenuItem) -> void:
	var menu := item._menu
	var index := item._index
	menu.set_item_as_separator(index, item.is_separator)
	menu.set_item_text(index, item.text)
	if item._sub_menu != null:
		var sub_menu_name := "_sub_menu_" + item.text
		menu.set_item_submenu(index, sub_menu_name)
		item._sub_menu.name = sub_menu_name
	else:
		menu.set_item_submenu(index, "")
	menu.set_item_tooltip(index, item.tooltip)
	menu.set_item_accelerator(index, item.accelerator_key | item.accelerator_mods)
	match item.checkable_mode:
		MenuItem.CheckableMode.NONE:
			menu.set_item_as_checkable(index, false)
		MenuItem.CheckableMode.BOX:
			menu.set_item_as_checkable(index, true)
		MenuItem.CheckableMode.RADIO:
			menu.set_item_as_radio_checkable(index, true)
	menu.set_item_checked(index, item.checked)
	menu.set_item_disabled(index, item.disabled)
	menu.set_item_indent(index, item.indent)
	menu.set_item_icon(index, item.icon)
	menu.set_item_icon_max_width(index, item.icon_max_width)
	menu.set_item_icon_modulate(index, item.icon_modulate)
	menu.set_item_shortcut(index, item.shortcut, item.shortcut_global)
	menu.set_item_shortcut_disabled(index, item.shortcut_disabled)


func _on_menu_id_focused(id: int) -> void:
	get_item_from_id(id).focused.emit()

func _on_menu_id_pressed(id: int) -> void:
	var item := get_item_from_id(id)
	if item.checkable_mode != MenuItem.CheckableMode.NONE and item.toggle_on_press:
		item.checked = not item.checked
	item.pressed.emit()


func _on_item_rearranged() -> void:
	if not is_node_ready():
		return
	if _building:
		return
	self.call_deferred("build")

func _ready() -> void:
	build()

func _enter_tree():
	_update_menubar()

func _update_menubar() -> void:
	if not get_parent() is MenuBar:
		return
	var menubar: MenuBar = get_parent() as MenuBar
	var index := menubar.get_children().find(self)
	menubar.set_menu_title(index, menubar_title)
	menubar.set_menu_tooltip(index, menubar_tooltip)
	menubar.set_menu_disabled(index, menubar_disabled)
	menubar.set_menu_hidden(index, menubar_hidden)
