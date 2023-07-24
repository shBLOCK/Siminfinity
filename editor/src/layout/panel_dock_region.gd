class_name PanelDockRegion extends PanelContainer


signal active_state_changed(active: bool)
signal current_panel_changed(panel: Control)

var active := false:
	set(value):
		visible = value
		active = value
		active_state_changed.emit(value)

var dock_pos: DockPos

@onready var Tabs: TabContainer = $TabContainer

@warning_ignore("shadowed_variable")
func setup(dock_pos: DockPos) -> PanelDockRegion:
	self.dock_pos = dock_pos
	LayoutManager._add_panel_dock_region(self, dock_pos)
	$DockOptionsPopup.setup(self)
	return self

func _add_panel(panel: Control) -> void:
	active = true
	if panel.get_parent() != null:
		panel.get_parent().remove_child(panel)
	Tabs.add_child(panel)
	var tab_id = Tabs.get_tab_idx_from_control(panel)
	Tabs.set_tab_title(
		tab_id,
		LayoutManager.get_panel_tr_key(
			LayoutManager.Panels.find_key(panel)
		)
	)
	Tabs.current_tab = tab_id
	
	# hacky workaround to a strange issue
	Tabs.tabs_visible = false
	Tabs.tabs_visible = true

var panel_count: int:
	get:
		return Tabs.get_tab_count()

var panels: Array[Control]:
	get:
		var p: Array[Control] = []
		for i in range(Tabs.get_tab_count()):
			p.append(Tabs.get_tab_control(i))
		return p

var current_panel: Control:
	get:
		return null if panels.is_empty() else panels[Tabs.current_tab]

var current_panel_id: int:
	get:
		return Tabs.current_tab

func _ready() -> void:
	Tabs.set_popup($DockOptionsPopup) 
	active = false

func _on_tab_container_child_exiting_tree(node: Node) -> void:
	if Tabs.get_tab_count() == 1 and node == Tabs.get_current_tab_control():
		active = false

func _on_tab_container_tab_changed(tab: int):
	current_panel_changed.emit($TabContainer.get_tab_control(tab))
