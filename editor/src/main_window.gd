extends PanelContainer


func _ready() -> void:
	%LeftSideDockingArea.setup(SideDockingArea.LEFT)
	%RightSideDockingArea.setup(SideDockingArea.RIGHT)
	
	DockingManager.load_layout("res://assets/layout/default_layout.ini")
