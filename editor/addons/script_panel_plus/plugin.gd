@tool
extends EditorPlugin

const project_settings_category := "script_panel_plus/panel_settings/"
const config_path := "res://addons/script_panel_plus/configs/config.cfg"
const defaults_path := "res://addons/script_panel_plus/configs/defaults.cfg"
const scene := preload("res://addons/script_panel_plus/script_panel/script_panel.tscn")

var config: ConfigFile
var defaults: ConfigFile

var engine_editor_interface:   EditorInterface
var engine_script_editor:      ScriptEditor
var engine_script_vbox:        VSplitContainer
var engine_script_list:        ItemList
var engine_screen_select_button: Control

var script_panel: Control
var top_bar: Control
var top_bar_parent: Control

var settings := {}


## PLUGIN

func _enter_tree() -> void:
	while _scripts_are_loading(): 
		await get_tree().process_frame
	load_config()
	load_engine_nodes()
	create_script_panel()
	update()
	project_settings_changed.connect(update)
	script_panel.current_script_changed.connect(check_current_bottom_bar_visibility)
	script_panel.load_last_session()
	script_panel.update_tabs()

func _exit_tree() -> void:
	hide_screen_select_button()
	script_panel.save_last_session()
	close_config()
	script_panel.show_panel()
	script_panel.queue_free()
	show_engine_script_vbox()
	show_top_bar()
	show_all_bottom_bars()


## SETTINGS

func update() -> void:
	load_settings()
	hide_engine_script_vbox()
	script_panel.toggle_hide_button()
	script_panel.update_tabs()
	
	check_top_bar_visibility()
	check_current_bottom_bar_visibility()
	check_current_screen_button_visibility()
	check_search_bar_visibility()
	
	if settings["list_multiple_columns"]:
		script_panel.script_list.max_columns = 0
	else:
		script_panel.script_list.max_columns = 1


## CONFIG

func load_config() -> void:
	if not config: config = ConfigFile.new()
	if not defaults: defaults = ConfigFile.new()
	
	var err := config.load(config_path)
	var err2 := defaults.load(defaults_path)
	
	if err: push_error(err)
	if err2: push_error(err2)
	load_project_settings()
	set_defaults()

func close_config() -> void:
	save_project_settings()
	unload_project_settings()
	config = null
	defaults = null

func load_settings():
	settings.clear()
	for section in config.get_sections():
		for key in config.get_section_keys(section):
			var path := project_settings_category + key
			var default_value = defaults.get_value(section, key)
			var value = ProjectSettings.get_setting(path, default_value)
			settings[key] = value
	script_panel.settings = settings

func load_project_settings() -> void:
	for section in config.get_sections():
		for key in config.get_section_keys(section):
			var value = config.get_value(section, key)
			var path := project_settings_category + key
			ProjectSettings.set_setting(path, value)
	
	ProjectSettings.save()

func save_project_settings() -> void:
	for section in config.get_sections():
		for key in config.get_section_keys(section):
			var path := project_settings_category + key
			config.set_value(section, key, ProjectSettings.get_setting(path))
	config.save(config_path)

func unload_project_settings() -> void:
	for section in config.get_sections():
		for key in config.get_section_keys(section):
			var path := project_settings_category + key
			ProjectSettings.set_setting(path, null)
	ProjectSettings.save()

func set_defaults() -> void:
	for section in defaults.get_sections():
		for key in defaults.get_section_keys(section):
			var value = defaults.get_value(section, key)
			var path := project_settings_category + key
			ProjectSettings.set_initial_value(path, value)
	ProjectSettings.save()


## SHOW / HIDE

func check_top_bar_visibility() -> void:
	if not top_bar: return
	
	if settings["show_top_bar"]:
		show_top_bar()
	else:
		hide_top_bar()

func check_current_screen_button_visibility() -> void:
	if settings["show_screen_select_button"] and not settings["show_top_bar"]:
		show_screen_select_button()
	else:
		hide_screen_select_button()

func check_current_bottom_bar_visibility() -> void:
	if settings["show_bottom_bar"]: 
		show_current_bottom_bar()
	else: 
		hide_current_bottom_bar()

func check_search_bar_visibility() -> void:
	var search_bar := script_panel.search_line.get_parent() as Control
	search_bar.visible = settings["show_search_line"]

func hide_top_bar() -> void:
	if not top_bar: return
	
	top_bar.visibility_layer = 0
	
	var new_parent = engine_script_editor
	if new_parent: top_bar.reparent(new_parent, false)
	new_parent.move_child(top_bar, 0)

func show_top_bar() -> void:
	if not top_bar: return
	
	top_bar.reparent(top_bar_parent, false)
	top_bar_parent.move_child(top_bar, 0)
	top_bar.visibility_layer = 1

func hide_engine_script_vbox() -> void:
	engine_script_vbox.set("visible", false)

func show_engine_script_vbox() -> void:
	engine_script_vbox.set("visible", true)

func show_all_bottom_bars() -> void:
	for i in get_all_bottom_bars():
		i.visible = true

func hide_all_bottom_bars() -> void:
	for i in get_all_bottom_bars():
		i.visible = false

func hide_current_bottom_bar() -> void:
	var cur_bottom_bar := get_current_bottom_bar()
	if cur_bottom_bar: cur_bottom_bar.visible = false

func show_current_bottom_bar() -> void:
	var cur_bottom_bar := get_current_bottom_bar()
	if cur_bottom_bar: cur_bottom_bar.visible = true

func show_screen_select_button() -> void:
	var _children: Array[Node] = engine_script_editor.get_child(0).find_children("*", "ScreenSelect", false, false)
	var new_parent :Control = script_panel.line_label.get_parent()
	
	if _children.size() < 1: return
	if not new_parent: return
	
	engine_screen_select_button = _children[0]
	
	if not engine_screen_select_button: return
	
	engine_screen_select_button.reparent(new_parent)
	new_parent.move_child(engine_screen_select_button, -1)

func hide_screen_select_button() -> void:
	if not top_bar: return
	if not engine_screen_select_button: return
	
	engine_screen_select_button.reparent(top_bar)
	top_bar.move_child(engine_screen_select_button, -1)


## GET NODES

func get_current_bottom_bar() -> Control:
	var result: Control
	
	if engine_script_editor.get_current_editor():
		var i = engine_script_editor.get_current_editor().\
		find_children("*", "CodeTextEditor", true, false)[0]
		result = i.get_child(1)
	else:
		if not engine_script_list.is_anything_selected(): return result
		
		var array := engine_script_editor.\
		find_children("*", "EditorHelp", true, false)
		var needed := engine_script_list.\
		get_item_text( engine_script_list.get_selected_items()[0] )
		
		for i in array:
			if i.name == needed: 
				return i.get_child(2)
	
	return result

func get_all_bottom_bars() -> Array[Control]:
	var result: Array[Control]
	# Bottom Bars in Scripts
	for i in get_editor_interface().get_script_editor().\
	find_children("*", "CodeTextEditor", true, false):
		result.append( i.get_child(1) )
	
	# Bottom Bars in Help Docs
	for i in get_editor_interface().get_script_editor().\
	find_children("*", "EditorHelp", true, false):
		result.append( i.get_child(2) )
	
	return result

func load_engine_nodes() -> void:
	engine_editor_interface = get_editor_interface()
	engine_script_editor = engine_editor_interface.get_script_editor()
	engine_script_vbox = engine_script_editor.\
	get_child(0).get_child(1).get_child(0)
	engine_script_list = engine_script_editor.get_child(0).get_child(1)\
	.get_child(0).get_child(0).get_child(1)
	top_bar = engine_script_editor.get_child(0).get_child(0)
	top_bar_parent = top_bar.get_parent()


## SCRIPT PANEL

func create_script_panel() -> void:
	script_panel = scene.instantiate()
	script_panel.plugin_reference = self
	upload_engine_nodes_to_script_panel()
	
	engine_script_editor.get_child(0).get_child(1).add_child(script_panel)
	engine_script_editor.get_child(0).get_child(1).move_child(script_panel, 0)
	
	script_panel.update_all_scripts()
	script_panel.update_script_editor_list()

func upload_engine_nodes_to_script_panel() -> void:
	script_panel.engine_editor_interface = engine_editor_interface
	script_panel.engine_script_editor = engine_script_editor
	script_panel.engine_script_list = engine_script_list


## MISC

func _scripts_are_loading() -> bool:
	return get_editor_interface().get_script_editor().\
	get_child(0).get_child(0).get_children().size() < 15
