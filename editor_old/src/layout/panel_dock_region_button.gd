extends VBoxContainer


signal pressed(Node)

var dock_pos: DockPos


func _on_resized() -> void:
	self.custom_minimum_size.y = self.size.x * 1.3

func _on_draw() -> void:
	for child in %Tabs.get_children():
		child.free()
	var dock: PanelDockRegion = LayoutManager.PanelDocks[dock_pos]
	%Button.self_modulate.a = 1.0 if dock.active else 0.5
	
	var current := dock.current_panel_id
	for i in range(dock.panel_count):
		var tab := Panel.new()
		tab.custom_minimum_size = Vector2(6, 3)
		var style_box := StyleBoxFlat.new()
		style_box.set_corner_radius_all(0)
		style_box.anti_aliasing = false
		style_box.bg_color = Color.WHITE if i == current else Color.WHITE * 0.7
		tab.add_theme_stylebox_override("panel", style_box)
		%Tabs.add_child(tab)

func _on_button_pressed() -> void:
	pressed.emit(self)
