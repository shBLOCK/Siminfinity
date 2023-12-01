@tool
extends Node3D


@export
var generate: bool:
	get:
		return false
	set(value):
		if value:
			_gen()

@export var size := Vector2i(12, 12)
@export var spacing := Vector2(1, 1)

var Point := preload("res://src/point.tscn")
var Path := preload("res://src/path.tscn")
var AGV := preload("res://src/agv.tscn")
var Shelf := preload("res://src/shelf.tscn")


func _path(a, b):
	var path = Path.instantiate()
	path.a = a
	path.b = b
	add_child(path)
	path.owner = get_tree().edited_scene_root

func _gen():
	if not Engine.is_editor_hint():
		return
	
	for c in get_children():
		remove_child(c)
	
	var points := {}
	
	for x in size.x:
		for y in size.y:
			var point := Point.instantiate()
			point.name = "Point(%d,%d)" % [x, y]
			point.position = Vector3(spacing.x * x, 0, spacing.y * y)
			points[Vector2i(x, y)] = point
			add_child(point)
			point.owner = get_tree().edited_scene_root
	
	for x in size.x:
		
		for y in size.y:
			if x < size.x-1:
				_path(points[Vector2i(x, y)], points[Vector2i(x+1, y)])
				_path(points[Vector2i(x+1, y)], points[Vector2i(x, y)])
			if y < size.y-1:
				_path(points[Vector2i(x, y)], points[Vector2i(x, y+1)])
				_path(points[Vector2i(x, y+1)], points[Vector2i(x, y)])
	
	for point in points.keys():
		if point.x == 0:
			var agv = AGV.instantiate()
			agv.point = points[point]
			for c in get_node("../AGVs").get_children():
				get_node("../AGVs").remove_child(c)
			get_node("../AGVs").add_child(agv)
			agv.owner = get_tree().edited_scene_root
	
	for c in get_node("../AGVs").get_children():
		get_node("../AGVs").remove_child(c)
	for point in points.keys():
		if point.x == 0:
			var agv = AGV.instantiate()
			agv.point = points[point]
			
			get_node("../AGVs").add_child(agv)
			agv.owner = get_tree().edited_scene_root
	
	for c in get_node("../Shelves").get_children():
		get_node("../Shelves").remove_child(c)
	for point in points.keys():
		if not (2 <= point.x and point.x <= 8):
			continue
		if not point.y % 3 in [1, 2]:
			continue
		
		var shelf = Shelf.instantiate()
		shelf.point = points[point]
		get_node("../Shelves").add_child(shelf)
		shelf.owner = get_tree().edited_scene_root
