extends Node3D

# Fixed preview rig for mm_mcp's render_preview tool: a sphere, a cube (turned
# 45deg), and a cutaway ball (revealing an inner core), resting on a tiled
# ground plane that runs off into a fogged distance, under raking key + rim
# lighting with shadows and a touch of depth of field, screenshotted headfully
# and quit.
# Args (after --): --albedo=<path> --normal=<path> --orm=<path> --out=<path>
# --tile=<float, default 1.0>  UV repeat count on the sphere/cube/cutaway ball;
#   the ground plane always tiles at 8x that so its own repeat is visible at a
#   glance, and the cutaway ball's inner core tiles at CORE_RADIUS_FRACTION x
#   that so its brick density visually matches the rest.

const OBJECT_RADIUS := 0.85  # half-height of the cube / sphere radius, for ground placement
const GROUND_TILE_MULTIPLIER := 8.0
const CORE_RADIUS_FRACTION := 0.55  # cutaway ball's inner core, relative to OBJECT_RADIUS
# 240 (top-down/Y-axis spin) is the locked-in cutaway-ball orientation after
# visual review comparing multiple rotation angles.
const CUTAWAY_ROTATION_DEGREES := 240.0

func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		var parts = a.split("=", true, 1)
		if parts.size() == 2:
			args[parts[0].trim_prefix("--")] = parts[1]

	if not args.has("albedo") or not args.has("normal") or not args.has("orm") or not args.has("out"):
		push_error("usage: --albedo=path --normal=path --orm=path --out=path [--tile=1.0]")
		get_tree().quit(1)
		return

	var tile := 1.0
	if args.has("tile"):
		tile = args["tile"].to_float()

	var albedo_tex := _load_tex(args["albedo"])
	var normal_tex := _load_tex(args["normal"])
	var orm_tex := _load_tex(args["orm"])
	if albedo_tex == null or normal_tex == null or orm_tex == null:
		push_error("one or more textures failed to load, aborting instead of rendering a broken preview")
		get_tree().quit(1)
		return

	var mat := _make_material(albedo_tex, normal_tex, orm_tex, tile)
	var ground_mat := _make_material(albedo_tex, normal_tex, orm_tex, tile * GROUND_TILE_MULTIPLIER)
	# Same physical brick size as the outer shell, not the same repeat count:
	# a smaller sphere needs fewer repeats to read at a matching density.
	var core_mat := _make_material(albedo_tex, normal_tex, orm_tex, tile * CORE_RADIUS_FRACTION)

	var ground := MeshInstance3D.new()
	ground.mesh = PlaneMesh.new()
	ground.mesh.size = Vector2(60, 60)
	ground.mesh.subdivide_width = 1
	ground.mesh.subdivide_depth = 1
	ground.position = Vector3(0, -OBJECT_RADIUS, 0)
	ground.set_surface_override_material(0, ground_mat)
	add_child(ground)

	var sphere := MeshInstance3D.new()
	sphere.mesh = SphereMesh.new()
	sphere.mesh.radius = OBJECT_RADIUS
	sphere.mesh.height = OBJECT_RADIUS * 2
	sphere.mesh.radial_segments = 48
	sphere.mesh.rings = 24
	sphere.position = Vector3(-2.0, 0, 0)
	sphere.set_surface_override_material(0, mat)
	add_child(sphere)

	var cube := MeshInstance3D.new()
	cube.mesh = BoxMesh.new()
	cube.mesh.size = Vector3(OBJECT_RADIUS * 2, OBJECT_RADIUS * 2, OBJECT_RADIUS * 2)
	cube.position = Vector3(0, 0, 0)
	cube.rotation_degrees = Vector3(0, 45, 0)
	cube.set_surface_override_material(0, mat)
	add_child(cube)

	# Cutaway ball: a wedge subtracted from a sphere, revealing an inner core.
	# An honest approximation of a studio material-test ball, not a true
	# beveled asset (Godot's CSG booleans cut sharp edges; real bevels would
	# need a modeled mesh, see the preview_project README note).
	var cutaway := CSGCombiner3D.new()
	cutaway.position = Vector3(2.0, 0, 0)
	cutaway.rotation_degrees = Vector3(0, CUTAWAY_ROTATION_DEGREES, 0)
	var outer := CSGSphere3D.new()
	outer.radius = OBJECT_RADIUS
	outer.radial_segments = 48
	outer.rings = 24
	outer.material = mat
	outer.smooth_faces = true
	cutaway.add_child(outer)
	var wedge := CSGBox3D.new()
	wedge.size = Vector3(OBJECT_RADIUS * 2.2, OBJECT_RADIUS * 2.2, OBJECT_RADIUS * 2.2)
	wedge.operation = CSGShape3D.OPERATION_SUBTRACTION
	wedge.position = Vector3(OBJECT_RADIUS * 0.75, OBJECT_RADIUS * 0.75, 0)
	wedge.rotation_degrees = Vector3(0, 45, 0)
	# Without a material, the flat faces this subtraction exposes render as
	# plain white (no UVs assigned) instead of picking up the shell's texture.
	wedge.material = mat
	cutaway.add_child(wedge)
	var core := CSGSphere3D.new()
	core.radius = OBJECT_RADIUS * CORE_RADIUS_FRACTION
	core.radial_segments = 32
	core.rings = 16
	core.material = core_mat
	core.smooth_faces = true
	cutaway.add_child(core)
	add_child(cutaway)

	var cam := Camera3D.new()
	cam.position = Vector3(0, 1.4, 6.5)
	cam.fov = 36
	var cam_attrs := CameraAttributesPractical.new()
	cam_attrs.dof_blur_far_enabled = true
	cam_attrs.dof_blur_far_distance = 9.0
	cam_attrs.dof_blur_far_transition = 6.0
	cam_attrs.dof_blur_amount = 0.04
	cam.attributes = cam_attrs
	add_child(cam)
	cam.look_at(Vector3(0, 0, 0), Vector3.UP)
	cam.current = true

	# Belt-and-suspenders with project.godot's anti_aliasing/quality settings:
	# set it on the actual viewport too, in case a project-setting default
	# doesn't apply cleanly to a scene built entirely from script.
	get_viewport().msaa_3d = Viewport.MSAA_8X
	get_viewport().screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA

	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, 60, 0)
	key.light_energy = 1.3
	key.light_color = Color(1.0, 0.96, 0.9)
	key.shadow_enabled = true
	add_child(key)

	var rim := DirectionalLight3D.new()
	rim.rotation_degrees = Vector3(-15, -130, 0)
	rim.light_energy = 0.55
	rim.light_color = Color(0.85, 0.9, 1.0)
	add_child(rim)

	var env_node := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.05, 0.05, 0.06)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(1, 1, 1)
	env.ambient_light_energy = 0.25
	env.fog_enabled = true
	env.fog_light_color = Color(0.05, 0.05, 0.06)
	env.fog_light_energy = 1.0
	env.fog_density = 0.07
	env.fog_sky_affect = 1.0
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
	var tex := ImageTexture.create_from_image(img)
	return tex


func _make_material(albedo_tex: ImageTexture, normal_tex: ImageTexture,
		orm_tex: ImageTexture, tile: float) -> ORMMaterial3D:
	var mat := ORMMaterial3D.new()
	mat.albedo_texture = albedo_tex
	mat.normal_enabled = true
	mat.normal_texture = normal_tex
	mat.orm_texture = orm_tex
	mat.uv1_scale = Vector3(tile, tile, 1)
	mat.texture_repeat = true
	return mat
