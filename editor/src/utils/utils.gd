class_name Utils

static func is_main(node: Node) -> bool:
	## Returns whether the node is the current "main scene".
	## This is true if the node is the main scene and the project is ran normaly,
	## or it is the "current scene" when running in F6 mode.
	return node.get_tree().root == node.get_parent()
