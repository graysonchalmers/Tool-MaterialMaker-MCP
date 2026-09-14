extends Node3D

# Fixed preview rig for mm_mcp's render_preview tool: a sphere, a cube (turned
# 45deg), and a cutaway ball (revealing an inner core), resting on a tiled
# ground plane that runs off into a fogged distance. Lit by a soft-shadowed key,
# a boosted shadow-casting rim/kick, and a low bounce fill, over procedural-sky
# ambient + reflections and screen-space AO, with a touch of depth of field,
# screenshotted headfully and quit.
# Args (after --): --albedo=<path> --normal=<path> --orm=<path>
# --tile=<float, default 1.0>  UV repeat count on the sphere/cube/cutaway ball;
#   the ground plane always tiles at 8x that so its own repeat is visible at a
#   glance, and the cutaway ball's inner core tiles at CORE_RADIUS_FRACTION x
#   that so its brick density visually matches the rest.
#
# Two output modes, same rig either way:
# --out=<path>  Single static frame (render_preview).
# --sweep-outdir=<path> --sweep-frames=<int> [--sweep-kind=precess|azimuth]
#   [--cone=<deg>]  Animate the key light, writing one frame_NNN.png per step to
#   sweep-outdir instead of a single --out (render_preview_sweep -- the caller
#   assembles the frames into a GIF). Default 'precess' wobbles the key's aim in
#   a small cone (default 18deg) so highlights circle the relief without going
#   backlit; 'azimuth' is the old full 360-degree orbit. Rim/fill stay fixed.

const OBJECT_RADIUS := 0.85  # half-height of the cube / sphere radius, for ground placement
const GROUND_TILE_MULTIPLIER := 8.0
# Ground plane extent. The old 60x60 plane's far edge sat only ~30 units from
# the camera, where exponential fog (density 0.07) reaches just ~88% -- so the
# ground's hard geometric edge stayed faintly visible against the background as
# a horizon seam. At 400 units the edge is ~200 units out, where fog is
# effectively 100%: the ground has fully dissolved into BG_COLOR before its edge
# is ever reached, so there is no seam left to see. Reference size for keeping
# the tile density constant regardless of this value.
const GROUND_SIZE := 400.0
const GROUND_SIZE_REFERENCE := 60.0
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

	var sweep_mode := args.has("sweep-outdir") and args.has("sweep-frames")
	var usage := "usage: --albedo=path --normal=path --orm=path --out=path [--tile=1.0] OR --albedo=path --normal=path --orm=path --sweep-outdir=path --sweep-frames=N [--tile=1.0]"
	if not args.has("albedo") or not args.has("normal") or not args.has("orm"):
		push_error(usage)
		get_tree().quit(1)
		return
	if not sweep_mode and not args.has("out"):
		push_error(usage)
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
	# Scale the UV repeat with the plane so a bigger plane keeps the same
	# physical tile size near the camera -- otherwise enlarging the plane would
	# stretch each tile and change the tuned look.
	var ground_tile := tile * GROUND_TILE_MULTIPLIER * (GROUND_SIZE / GROUND_SIZE_REFERENCE)
	var ground_mat := _make_material(albedo_tex, normal_tex, orm_tex, ground_tile)
	# Same physical brick size as the outer shell, not the same repeat count:
	# a smaller sphere needs fewer repeats to read at a matching density.
	var core_mat := _make_material(albedo_tex, normal_tex, orm_tex, tile * CORE_RADIUS_FRACTION)

	var ground := MeshInstance3D.new()
	ground.mesh = PlaneMesh.new()
	ground.mesh.size = Vector2(GROUND_SIZE, GROUND_SIZE)
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

	# Soft-shadow filter quality high enough that the wide key penumbra
	# (light_angular_distance) reads as a smooth falloff, not banding. Global
	# RenderingServer setting: applies to every static frame and sweep frame.
	RenderingServer.directional_soft_shadow_filter_set_quality(
		RenderingServer.SHADOW_QUALITY_SOFT_ULTRA)

	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, 60, 0)
	key.light_energy = 1.3
	key.light_color = Color(1.0, 0.96, 0.9)
	key.shadow_enabled = true
	# Distance-based penumbra: crisp where the shadow meets the object, blurring
	# as it falls away. Higher = softer-with-distance.
	key.light_angular_distance = 5.0
	add_child(key)

	# Rim / kick from behind, boosted to a real edge light that separates the
	# objects from the dark backdrop. It DELIBERATELY casts a soft shadow: that
	# cast is load-bearing, it stops the rim's own spill from washing out the
	# contact grounding under the objects. This is not the usual "a rim never
	# casts" case -- do not disable the shadow. The soft angular distance keeps
	# that shadow from reading as a hard, cheap edge.
	var rim := DirectionalLight3D.new()
	rim.rotation_degrees = Vector3(-20, -150, 0)
	rim.light_energy = 2.0
	rim.light_color = Color(0.8, 0.88, 1.0)
	rim.shadow_enabled = true
	rim.light_angular_distance = 4.0
	add_child(rim)

	# Fill / bounce card: a low, cool directional from the shadow side, tinted
	# toward the ground so it reads as light bouncing off the plane.
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(25, -60, 0)
	fill.light_energy = 0.35
	fill.light_color = Color(0.6, 0.62, 0.7)
	add_child(fill)

	var env_node := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.05, 0.05, 0.06)
	# A procedural sky drives ambient + reflections WITHOUT ever being drawn
	# (the background stays the tuned dark color): this is the soft image-based
	# bounce, and it is also what keeps metals from reading dead-black.
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.35, 0.42, 0.55)
	sky_mat.sky_horizon_color = Color(0.55, 0.55, 0.58)
	sky_mat.ground_bottom_color = Color(0.22, 0.20, 0.18)
	sky_mat.ground_horizon_color = Color(0.4, 0.4, 0.42)
	sky_mat.sky_energy_multiplier = 1.0
	var sky := Sky.new()
	sky.sky_material = sky_mat
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 1.0
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.fog_enabled = true
	env.fog_light_color = Color(0.05, 0.05, 0.06)
	env.fog_light_energy = 1.0
	env.fog_density = 0.07
	env.fog_sky_affect = 1.0
	# Screen-space AO: renderer-level contact darkening in creases and where
	# objects meet the ground. Tight radius + high power for crisp contacts that
	# hold up under the boosted rim/fill; light_affect lets it bite under the
	# direct key, ao_channel_affect blends it with the material's baked AO.
	env.ssao_enabled = true
	env.ssao_radius = 0.25
	env.ssao_intensity = 5.0
	env.ssao_power = 3.5
	env.ssao_detail = 0.4
	env.ssao_horizon = 0.02
	env.ssao_light_affect = 0.7
	env.ssao_ao_channel_affect = 1.0
	env_node.environment = env
	add_child(env_node)

	for i in range(6):
		await get_tree().process_frame

	if sweep_mode:
		var frame_count: int = args["sweep-frames"].to_int()
		var sweep_dir: String = args["sweep-outdir"]
		# Default sweep is a PRECESSION: the key stays aimed at the object and its
		# aim traces a small cone (radius = --cone degrees, default 18) around the
		# light-to-object axis, so highlights circle the relief without the shot
		# ever going backlit. The rim/fill are held still. --sweep-kind=azimuth
		# restores the old full 360-degree orbit of the key.
		var kind := "precess"
		if args.has("sweep-kind"):
			kind = args["sweep-kind"]
		var cone := 18.0
		if args.has("cone"):
			cone = args["cone"].to_float()
		DirAccess.make_dir_recursive_absolute(sweep_dir)
		var base_pitch := key.rotation_degrees.x
		var base_yaw := key.rotation_degrees.y
		for i in range(frame_count):
			var phase := TAU * float(i) / float(frame_count)
			if kind == "azimuth":
				key.rotation_degrees = Vector3(base_pitch, 360.0 * float(i) / float(frame_count), 0)
			else:
				key.rotation_degrees = Vector3(
					base_pitch + cone * sin(phase),
					base_yaw + cone * cos(phase),
					0)
			for f in range(6):
				await get_tree().process_frame
			var frame_img := get_viewport().get_texture().get_image()
			var frame_path := sweep_dir.path_join("frame_%03d.png" % i)
			var frame_err := frame_img.save_png(frame_path)
			if frame_err != OK:
				push_error("save_png failed for frame %d: %s" % [i, frame_err])
				get_tree().quit(1)
				return
		print("PREVIEW SWEEP OK [%s]: wrote %d frames to %s" % [kind, frame_count, sweep_dir])
		get_tree().quit(0)
		return

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
