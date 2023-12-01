class_name SectionLabel extends PanelContainer


func setup(label: String, icon: Texture2D) -> SectionLabel:
	%Name.text = label
	%Icon.texture = icon
	return self
