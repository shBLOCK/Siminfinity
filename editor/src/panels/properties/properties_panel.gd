class_name PropertiesPanel extends VBoxContainer


@onready var PropertiesContainer := %PropertiesContainer

var SectionLabel_Scene := preload("res://src/panels/properties/section_label.tscn")
var PropertiesGroup_Scene := preload("res://src/panels/properties/properties_group.tscn")

var _group_stack: Array[PropertiesGroup] = []

func begin_section(section_name: String, icon: Texture2D) -> void:
	var sec = SectionLabel_Scene.instantiate().setup(section_name, icon)
	PropertiesContainer.add_child(sec)

func add_property(prop: PropWidget) -> void:
	if _group_stack.is_empty():
		PropertiesContainer.add_child(prop)
	else:
		_group_stack[-1].add_sub(prop)

func push_group(group_name: String) -> void:
	var group: PropertiesGroup = PropertiesGroup_Scene.instantiate()
	group.text = group_name
	group.expanded = false
	if _group_stack.is_empty():
		PropertiesContainer.add_child(group)
	else:
		_group_stack[-1].add_sub(group)
	_group_stack.append(group)

func pop_group(layers := 1) -> void:
	for i in range(layers):
		if _group_stack.pop_back() == null:
			push_error("Properties Panel: group stack underflow")

func next_group(group_name: String) -> void:
	## pop push
	pop_group()
	push_group(group_name)

func end() -> void:
	## Must be called when all the widgets has been added.
	if not _group_stack.is_empty():
		push_error("Properties Panel: group stack push/pop mismatch")

func clear() -> void:
	for prop in PropertiesContainer.get_children():
		prop.queue_free()

##############################
func _ready() -> void:
	_demo()
	if Utils.is_main(self):
		_demo()

func _demo() -> void:
	print("Properties Panel: Running demo...")
	
	var prop: PropWidget
	
	begin_section("Section 1", load("res://icon.svg"))
	
	push_group("Group 1")
	prop = preload("res://src/panels/properties/types/prop_spin_box.tscn").instantiate().setup("Prop 1")
	add_property(prop)
	pop_group()
	
	const nested_layers := 5
	for i in range(nested_layers):
		push_group("Nested %d" % i)
	prop = preload("res://src/panels/properties/types/prop_spin_box.tscn").instantiate().setup("Prop 1")
	add_property(prop)
	pop_group(nested_layers)
	
	end()
