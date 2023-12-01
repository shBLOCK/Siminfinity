class_name PanelDockWindow extends Window


var id: int
var region: PanelDockRegion

var _setup_done := false

func _ready() -> void:
	region = $PanelDockRegion
	call_deferred("show")

@warning_ignore("shadowed_variable")
func setup(id: int) -> void:
	self.id = id
	region.setup(DockPos.get_instance(id, self))
	LayoutManager._add_panel_dock_window(self, id)
	_setup_done = true

var _closed := false

func close():
	if _closed:
		return
	_closed = true
	for panel in region.panels:
		var pos := LayoutManager.get_last_dock_pos(panel)
		if pos == null:
			pos = LayoutManager.DEFAULT_PANEL_DOCK_POS
		LayoutManager.dock_panel(panel, pos)
	LayoutManager._remove_panel_dock_window(self)
	queue_free()
	

func _on_close_requested():
	close()

func _on_panel_dock_region_active_state_changed(active):
	if not _setup_done:
		return
	if active == false:
		close()

func _on_current_panel_changed(panel):
	var panel_name := tr(LayoutManager.get_panel_tr_key(LayoutManager.Panels.find_key(panel)))
	title = "%s - %s" % [panel_name, ProjectSettings.get_setting("application/config/name")]
