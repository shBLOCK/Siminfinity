class_name SideDockingArea extends HSplitContainer


enum { LEFT, RIGHT }

func setup(side: int) -> Node:
	var prefix = "LEFT" if side == LEFT else "RIGHT"
	%LeftTop.setup(DockPos.get_instance(prefix + "_LEFT_TOP"))
	%LeftBottom.setup(DockPos.get_instance(prefix + "_LEFT_BOTTOM"))
	%RightTop.setup(DockPos.get_instance(prefix + "_RIGHT_TOP"))
	%RightBottom.setup(DockPos.get_instance(prefix + "_RIGHT_BOTTOM"))
	return self

func load_layout() -> void:
	pass

func save_layout() -> void:
	pass

func _on_region_active_state_changed(_active: bool) -> void:
	%LeftArea.visible = %LeftTop.active or %LeftBottom.active
	%RightArea.visible = %RightTop.active or %RightBottom.active
	self.visible = %LeftArea.visible or %RightArea.visible
