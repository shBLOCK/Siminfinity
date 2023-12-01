extends Node


const DOCK_POS_META := "dock_pos"
const LAST_DOCK_POS_META := "last_dock_pos"
var DEFAULT_PANEL_DOCK_POS := DockPos.get_instance("LEFT_RIGHT_TOP")
@onready var _MainWindow := get_window()
var PanelDockWindow_Scene := preload("res://src/layout/panel_dock_window.tscn")

var PanelDocks := {}

var PanelDockWindows := {}

@onready var Panels := {
	PROPERTIES = preload("res://src/panels/properties/properties_panel.tscn").instantiate(),
	PROJECT = preload("res://src/panels/project/project_panel.tscn").instantiate(),
	AGENT = preload("res://src/panels/agent/agent_panel.tscn").instantiate(),
	PALETTE = preload("res://src/panels/palette/palette_panel.tscn").instantiate(),
}

func _ready():
	Panels.make_read_only()

func _add_panel_dock_region(region: PanelDockRegion, dock_pos: DockPos) -> void:
	PanelDocks[dock_pos] = region

func _remove_panel_dock_region(dock_pos: DockPos) -> void:
	PanelDocks.erase(dock_pos)

func _next_panel_dock_window_id() -> int:
	var id := 0
	var keys := PanelDockWindows.keys()
	keys.sort()
	for i in keys:
		if i != id:
			break
		id += 1
	
	return id

func _add_panel_dock_window(window: PanelDockWindow, id: int) -> void:
	PanelDockWindows[id] = window

func _remove_panel_dock_window(window: PanelDockWindow) -> void:
	var id: int = PanelDockWindows.find_key(window)
	assert(id != null)
	PanelDockWindows.erase(id)
	PanelDocks.erase(PanelDocks.find_key(window.region.dock_pos))

func create_panel_dock_window(original: PanelDockRegion = null) -> DockPos:
	var window: PanelDockWindow = PanelDockWindow_Scene.instantiate()
	if original != null:
		window.position = Vector2i(original.global_position) + original.get_window().position
		window.size = original.size
	else:
		window.position = _MainWindow.position + _MainWindow.size / 2 - window.size / 2
	var id := _next_panel_dock_window_id()
	add_child(window)
	window.setup(id)
	return window.region.dock_pos

func get_dock_window(dock_pos: DockPos) -> PanelDockWindow:
	assert(dock_pos.windowed)
	return PanelDockWindows.get(dock_pos.id)

func get_dock_pos(panel: Control) -> DockPos:
		return panel.get_meta(DOCK_POS_META) if panel.has_meta(DOCK_POS_META) else null

func get_last_dock_pos(panel: Control) -> DockPos:
	return panel.get_meta(LAST_DOCK_POS_META) if panel.has_meta(LAST_DOCK_POS_META) else null

func _set_last_dock_pos(panel: Control, dock_pos: DockPos) -> void:
	panel.set_meta(LAST_DOCK_POS_META, dock_pos)

func dock_panel(panel: Control, dock_pos: DockPos) -> void:
	if panel.get_parent() != null:
		panel.get_parent().remove_child(panel)
	if panel.has_meta(DOCK_POS_META):
		panel.set_meta(LAST_DOCK_POS_META, panel.get_meta(DOCK_POS_META))
	panel.set_meta(DOCK_POS_META, dock_pos)
	PanelDocks[dock_pos]._add_panel(panel)

func get_panel_tr_key(panel_type: String) -> String:
	return "PANEL_%s" % panel_type

const CFG_SEC_PANELS := "Panels"
const CFG_SEC_WINDOW_PREFIX := "Window."
const CFG_PANEL_DOCK_WINDOW_NAME_PREFIX := "panel_dock_window_"
const CFG_MAIN_WINDOW_NAME := "main"
#TODO: save each panel in it's own section, and save their sizes
func load_layout(path: String):
	var cfg := ConfigFile.new()
	var err := cfg.load(path)
	if err != OK:
		push_error("[LayoutManager] Failed to load layout config file at %s : %s" % [path, error_string(err)])
		return
	
	# Load main window settings
	_load_window_layout(cfg, CFG_MAIN_WINDOW_NAME, _MainWindow)
	
	# Clear current windows
	for window in PanelDockWindows:
		window.close()
	
	# Create dock windows
	var id_window_map := {}
	for section in cfg.get_sections():
		if not section.begins_with(CFG_SEC_WINDOW_PREFIX):
			continue
		var window_name: String = section.substr(len(CFG_SEC_WINDOW_PREFIX))
		if not window_name.begins_with(CFG_PANEL_DOCK_WINDOW_NAME_PREFIX):
			continue
		var mapping_id := int(window_name.substr(len(CFG_PANEL_DOCK_WINDOW_NAME_PREFIX)))
		
		var dock_pos := create_panel_dock_window()
		var window = get_dock_window(dock_pos)
		id_window_map[mapping_id] = window
		_load_window_layout(cfg, window_name, window)
		
	# Reset panels to default dock
	for panel in Panels.values():
		dock_panel(panel, DEFAULT_PANEL_DOCK_POS)
	
	# Dock panels
	for panel_type in cfg.get_section_keys(CFG_SEC_PANELS):
		if not Panels.has(panel_type):
			push_warning("[LayoutManager] Invalid panel type in layout file: %s" % panel_type)
			continue
		var pos_str = cfg.get_value(CFG_SEC_PANELS, panel_type)
		var dock_pos = DockPos.from_string(pos_str)
		if dock_pos.windowed:
			var window: PanelDockWindow = id_window_map[dock_pos.id]
			dock_pos = DockPos.get_instance(window.id, window)
		if not dock_pos in PanelDocks:
			push_warning("[LayoutManager] Invalid panel docking position: %s" % pos_str)
			continue
		dock_panel(Panels[panel_type], dock_pos)

func _load_window_layout(cfg: ConfigFile, win_name: String, window: Window) -> Window:
	var section := CFG_SEC_WINDOW_PREFIX + win_name
	window.current_screen = min(
		cfg.get_value(section, "screen", DisplayServer.get_primary_screen()),
		DisplayServer.get_screen_count() - 1
	)
	window.mode = cfg.get_value(section, "mode", 0)
	if window.mode == Window.MODE_WINDOWED:
		window.size = cfg.get_value(section, "size", window.size)
		var default_pos := \
			DisplayServer.screen_get_position() +\
			DisplayServer.screen_get_size() / 2 -\
			window.size / 2
		window.position = cfg.get_value(section, "position", default_pos)
	
	return window

func save_layout(path: String):
	var cfg := ConfigFile.new()
	
	var err := cfg.save(path)
	if err != OK:
		push_error("[LayoutManager] Failed to save layout config file at %s : %s" %[path, error_string(err)])
	
	# Save panels
	for panel_name in Panels:
		var panel: Control = Panels[panel_name]
		if panel.has_meta(DOCK_POS_META):
			var dock_pos: DockPos = panel.get_meta(DOCK_POS_META)
			cfg.set_value(CFG_SEC_PANELS, panel_name, str(dock_pos))
	
	# Save dock windows
	for id in PanelDockWindows:
		var window: Window = PanelDockWindows[id]
		_save_window_layout(cfg, CFG_PANEL_DOCK_WINDOW_NAME_PREFIX + id, window)
	
	# Save main window
	_save_window_layout(cfg, CFG_MAIN_WINDOW_NAME, _MainWindow)

func _save_window_layout(cfg: ConfigFile, win_name: String, window: Window) -> void:
	var section := CFG_SEC_WINDOW_PREFIX + win_name
	
	if window.current_screen != DisplayServer.get_primary_screen():
		cfg.set_value(section, "screen", window.current_screen)
	cfg.set_value(section, "mode", window.mode)
	cfg.set_value(section, "position", window.position)
	cfg.set_value(section, "size", window.size)
