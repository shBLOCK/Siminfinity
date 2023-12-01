extends Node


class _SerializationSettings:
	var cls: StringName
	var id: StringName
	var properties: PackedStringArray
	var has_serializer: bool
	var parent: _SerializationSettings


var _registry: Dictionary


func register(cls: StringName, id: StringName, params: PackedStringArray ) -> void:
	pass
