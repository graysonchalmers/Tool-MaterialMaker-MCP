extends Node3D

# Fixed preview rig for mm_mcp's render_preview tool: a sphere and a cube
# under raking key + rim lighting, screenshotted headfully and quit. Args
# (after --): --albedo=<path> --normal=<path> --orm=<path> --out=<path>

func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		var parts = a.split("=", true, 1)
		if parts.size() == 2:
			args[parts[0].trim_prefix("--")] = parts[1]

	if not args.has("albedo") or not args.has("normal") or not args.has("orm") or not args.has("out"):
		push_error("usage: --albedo=path --normal=path --orm=path --out=path")
		get_tree().quit(1)
		return

	var albedo_tex := _load_tex(args["albedo"])
	var normal_tex := _load_tex(args["normal"])
	var orm_tex := _load_tex(args["orm"])
	if albedo_tex == null or normal_tex == null or orm_tex == null:
		push_error("one or more textures failed to load, aborting instead of rendering a broken preview")
		get_tree().quit(1)
		return

	var mat := ORMMaterial3D.new()
	mat.albedo_texture = albedo_tex
	mat.normal_enabled = true
	mat.normal_texture = normal_tex
	mat.orm_texture = orm_tex

	var sphere := MeshInstance3D.new()
	sphere.mesh = SphereMesh.new()
	sphere.mesh.radial_segments = 48
	sphere.mesh.rings = 24
	sphere.position = Vector3(-1.3, 0, 0)
	sphere.set_surface_override_material(0, mat)
	add_child(sphere)

	var cube := MeshInstance3D.new()
	cube.mesh = BoxMesh.new()
	cube.mesh.size = Vector3(1.7, 1.7, 1.7)
	cube.position = Vector3(1.3, 0, 0)
	cube.set_surface_override_material(0, mat)
	add_child(cube)

	var cam := Camera3D.new()
	cam.position = Vector3(0, 0.5, 5.2)
	cam.fov = 40
	add_child(cam)
	cam.look_at(Vector3(0, 0, 0), Vector3.UP)
	cam.current = true

	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-25, 60, 0)
	key.light_energy = 1.3
	key.light_color = Color(1.0, 0.96, 0.9)
	add_child(key)

	var rim := DirectionalLight3D.new()
	rim.rotation_degrees = Vector3(-15, -130, 0)
	rim.light_energy = 0.55
	rim.light_color = Color(0.85, 0.9, 1.0)
	add_child(rim)

	var env_node := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.11, 0.11, 0.12)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(1, 1, 1)
	env.ambient_light_energy = 0.25
	env_node.environment = env
	add_child(env_node)

	for i in range(6):
		await get_tree().process_frame

	var img := get_viewport().get_texture().get_image()
	var err := img.save_png(args["out"])
	if err != OK:
		push_error("save_png failed: %s" % err)
		get_tree().quit(1)
		return

	print("PREVIEW OK: wrote %s" % args["out"])
	get_tree().quit(0)


func _load_tex(path: String) -> ImageTexture:
	var img := Image.load_from_file(path)
	if img == null:
		return null
	return ImageTexture.create_from_image(img)
