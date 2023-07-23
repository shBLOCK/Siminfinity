class_name PropWidget extends BoxContainer


var readonly := false:
	set(value):
		%Name.add_theme_color_override(
			"font_color",
			get_theme_color("readonly_color" if readonly else "property_color", "EditorProperty")
		)
		readonly = value

@warning_ignore("shadowed_variable")
func setup(text: String, readonly := false) -> PropWidget:
	%Name.text = text
	self.readonly = readonly
	return self
