extends PopupPanel


var region: PanelDockRegion

@warning_ignore("shadowed_variable")
func setup(region: PanelDockRegion) -> void:
	self.region = region

func _ready() -> void:
	%LLT.dock_pos = DockPos.get_instance("LEFT_LEFT_TOP")
	%LLB.dock_pos = DockPos.get_instance("LEFT_LEFT_BOTTOM")
	%LRT.dock_pos = DockPos.get_instance("LEFT_RIGHT_TOP")
	%LRB.dock_pos = DockPos.get_instance("LEFT_RIGHT_BOTTOM")
	%RLT.dock_pos = DockPos.get_instance("RIGHT_LEFT_TOP")
	%RLB.dock_pos = DockPos.get_instance("RIGHT_LEFT_BOTTOM")
	%RRT.dock_pos = DockPos.get_instance("RIGHT_RIGHT_TOP")
	%RRB.dock_pos = DockPos.get_instance("RIGHT_RIGHT_BOTTOM")

func _on_button_make_floating_theme_changed() -> void:
	%ButtonMakeFloating.icon = %ButtonMakeFloating.get_theme_icon("MakeFloating", "EditorIcons")

func _on_dock_region_button_pressed(button: Control) -> void:
	DockingManager.dock_panel(region.current_panel, button.dock_pos)
	self.hide()

func _on_button_make_floating_pressed() -> void:
	var panel := region.current_panel
	if panel == null:
		self.hide()
		return
	var dock_pos := DockingManager.create_panel_dock_window(region)
	DockingManager.dock_panel(panel, dock_pos)
	self.hide()
