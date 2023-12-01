@tool
extends CodeHighlighter


func _init() -> void:
	add_color_region("#", "", Color.DIM_GRAY)
	
	for k in ["'", '"', "'''", '"""']:
		add_color_region(k, k, Color.YELLOW, true)
	
	for k in [
		"def",
		"class",
		"if"
	]:
		add_keyword_color(k, Color.RED)
	
	number_color = Color.AQUAMARINE


#class Highlighter extends EditorSyntaxHighlighter:
	#var _internal_code_highlighter: CodeHighlighter
	#
	#func _init():
		#var ch := CodeHighlighter.new()
		#
		#pass
		#
		#_internal_code_highlighter = ch
	#
	#func _get_name():
		#return "Python"
	#
	#func _get_supported_languages():
		#return PackedStringArray(["python"])
	#
	#func _get_line_syntax_highlighting(line):
		#return _internal_code_highlighter.get_line_syntax_highlighting(line)
#
#var script_editor := EditorInterface.get_script_editor()
#
#var editors: Array[ScriptEditorBase]
#
#func _on_editor_script_changed(script: Script):
	#for editor in script_editor.get_open_script_editors():
		#print(editor, editor.get_script())
	#

#var highlighter := Highlighter.new()
#
#func setup():
	#EditorInterface.get_script_editor().editor_script_changed\
		#.connect(_on_editor_script_changed)
	#script_editor.register_syntax_highlighter(highlighter)
#
#func cleanup():
	#EditorInterface.get_script_editor().editor_script_changed\
		#.disconnect(_on_editor_script_changed)
	#script_editor.unregister_syntax_highlighter(highlighter)
