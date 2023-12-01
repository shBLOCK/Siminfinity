extends SimRoot


var connection: WebSocketPeer
var opened := false


func _ready() -> void:
	connection = WebSocketPeer.new()

func _input(event: InputEvent) -> void:
	if Input.is_action_just_pressed("speed_up"):
		connection.send_text("speed_up")
	if Input.is_action_just_pressed("slow_down"):
		connection.send_text("slow_down")
	if Input.is_action_just_pressed("toggle_pause"):
		connection.send_text("toggle_pause")
	if Input.is_key_pressed(KEY_K):
		get_window().size.x = 1920*4
		get_window().size.y = 1080*4
		print("Screenshot...")
		get_viewport().get_texture().get_image().save_png("res://movie/render.png")
		print("Screenshot saved!")

func _process(delta: float) -> void:
	connection.poll()
	
	if connection.get_ready_state() == WebSocketPeer.STATE_OPEN:
		if not opened:
			print("Connected to server!")
		opened = true
		
		for _p in connection.get_available_packet_count():
			var msg = connection.get_var()
			#print(msg)
			_process_message(msg)
	elif connection.get_ready_state() == WebSocketPeer.STATE_CLOSED:
		opened = false
		connection.connect_to_url("ws://127.0.0.1:31415")

func _process_message(msg) -> void:
	if not msg is Dictionary:
		#print("Invalid message!", msg)
		return
	
	var agv_transform = msg["agv_transforms"]
	var agvs = $AGVs.get_children()
	for i in len(agv_transform):
		agvs[i].transform = agv_transform[i]
	
	var shelf_transform = msg["shelf_transforms"]
	var shelves = $Shelves.get_children()
	for i in len(shelf_transform):
		shelves[i].transform = shelf_transform[i]
