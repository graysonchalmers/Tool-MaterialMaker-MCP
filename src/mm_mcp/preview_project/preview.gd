extends Node3D

# Fixed preview rig for mm_mcp's render_preview tool: a sphere, a rounded-bevel
# cube (turned 45deg), and a lathed chess rook, resting on a tiled
# ground plane that runs off into a fogged distance. Lit by a soft-shadowed key,
# a boosted shadow-casting rim/kick, and a low bounce fill, over procedural-sky
# ambient + reflections and screen-space AO, with a touch of depth of field,
# screenshotted headfully and quit.
# Args (after --): --albedo=<path> --normal=<path> --orm=<path>
# --tile=<float, default 0.45>  Triplanar UV scale, applied uniformly to every
#   object (sphere, cube, ground, rook), so all of them tile at the same
#   world-space density. Raise it for a finer/smaller physical tile, lower it
#   for a coarser one.
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
const CUBE_BEVEL := 0.14  # fillet radius on the cube's edges (modeled, not a shader)
const CUBE_BEVEL_SEGMENTS := 6  # arc segments across the fillet -> smooth, not a single facet
# Ground plane extent. The old 60x60 plane's far edge sat only ~30 units from
# the camera, where exponential fog (density 0.07) reaches just ~88% -- so the
# ground's hard geometric edge stayed faintly visible against the background as
# a horizon seam. At 400 units the edge is ~200 units out, where fog is
# effectively 100%: the ground has fully dissolved into BG_COLOR before its edge
# is ever reached, so there is no seam left to see. Tile density is now uniform
# world-space via triplanar, independent of this value.
const GROUND_SIZE := 400.0

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

	var tile := 0.45
	if args.has("tile"):
		tile = args["tile"].to_float()

	# Opt-in preview-only clearcoat lobe (car-paint-style showcase garnish).
	# Material Maker itself cannot export a clearcoat lobe, so this never
	# reaches the real render() output -- it only affects this preview
	# composite. Defaults to 0.0, a true no-op: _make_material only enables
	# the feature flag when clearcoat > 0.
	var clearcoat := 0.0
	if args.has("clearcoat"):
		clearcoat = args["clearcoat"].to_float()
	var clearcoat_roughness := 0.5
	if args.has("clearcoat-roughness"):
		clearcoat_roughness = args["clearcoat-roughness"].to_float()

	var albedo_tex := _load_tex(args["albedo"])
	var normal_tex := _load_normal_tex(args["normal"])
	var orm_tex := _load_tex(args["orm"])
	if albedo_tex == null or normal_tex == null or orm_tex == null:
		push_error("one or more textures failed to load, aborting instead of rendering a broken preview")
		get_tree().quit(1)
		return

	# One TRIPLANAR material for every object, so the texture tiles at a single
	# consistent world-space density across the sphere, cube, ground and rook.
	# Triplanar projects by position and blends by normal instead of using each
	# mesh's own UVs -- the old rig gave the sphere (one wrap) and ground (8x
	# multiplier) different tile scales. It also wraps seamlessly across the
	# cube's faces and rounded edges and up the rook's turned profile.
	var mat := _make_material(albedo_tex, normal_tex, orm_tex, tile, clearcoat, clearcoat_roughness)
	mat.uv1_triplanar = true

	var ground := MeshInstance3D.new()
	ground.mesh = PlaneMesh.new()
	ground.mesh.size = Vector2(GROUND_SIZE, GROUND_SIZE)
	ground.mesh.subdivide_width = 1
	ground.mesh.subdivide_depth = 1
	ground.position = Vector3(0, -OBJECT_RADIUS, 0)
	ground.set_surface_override_material(0, mat)
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

	# Rounded-bevel cube. The modeled fillet (see _rounded_box) plus the shared
	# triplanar material means the texture tiles continuously across the faces
	# AND over the rounded edges, at the same density as every other object.
	var cube := MeshInstance3D.new()
	cube.mesh = _rounded_box(OBJECT_RADIUS * 2, CUBE_BEVEL, CUBE_BEVEL_SEGMENTS)
	cube.position = Vector3(0, 0, 0)
	cube.rotation_degrees = Vector3(0, 45, 0)
	cube.set_surface_override_material(0, mat)
	add_child(cube)

	# Chess rook: a lathed (surface-of-revolution) body with a bold molding
	# silhouette (Catmull-Rom profile, smooth normals) and a plain circular top.
	# Sized to the cube's height (2*OBJECT_RADIUS), base resting on the ground.
	var rook := Node3D.new()
	rook.position = Vector3(2.0, 0, 0)
	# Cull-disabled clone of the shared material: the lathe is a hand-built mesh,
	# so double-sided sidesteps any triangle-winding mistake showing as holes.
	var rook_mat := mat.duplicate()
	rook_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	# Profile: Vector2(radius, y), bottom to top; r==0 endpoints cap the axis.
	# y spans -OBJECT_RADIUS (base on the ground) to +0.72*OBJECT_RADIUS (crown
	# platform); the merlons carry the silhouette up to the cube height.
	# Control points for a bold molding silhouette (r, y). A Catmull-Rom spline
	# is threaded through these and sampled densely, so the outline FLOWS through
	# its curves (ogee/cove/ovolo, like a cornice) instead of faceting at each
	# turn -- combined with the lathe's smooth vertex normals, the whole profile
	# reads soft. Bold base torus + big crown cornice for a strong silhouette.
	var yb := -OBJECT_RADIUS
	var ctrl := PackedVector2Array([
		Vector2(0.00, yb),          # bottom center (cap)
		Vector2(0.56, yb),          # foot outer (wide, strong base)
		Vector2(0.58, yb + 0.09),   # base torus bulge (rolls out)
		Vector2(0.50, yb + 0.20),   # ovolo rolls back in
		Vector2(0.42, yb + 0.30),   # down into the shaft
		Vector2(0.35, yb + 0.48),   # cove neck
		Vector2(0.34, yb + 0.82),   # shaft body
		Vector2(0.37, yb + 1.02),   # gentle swell
		Vector2(0.40, yb + 1.13),   # rise
		Vector2(0.36, yb + 1.19),   # small cove (detail)
		Vector2(0.44, yb + 1.26),   # astragal bead out (detail)
		Vector2(0.39, yb + 1.31),   # fillet back in (detail)
		Vector2(0.53, yb + 1.41),   # cornice bulge (big crown molding)
		Vector2(0.47, yb + 1.47),   # cove back in
		Vector2(0.58, yb + 1.56),   # crown rim (widest, top)
		Vector2(0.58, yb + 1.61),   # crown top edge
		Vector2(0.46, yb + 1.65),   # soft roll onto the top
		Vector2(0.00, yb + 1.66),   # circular flat top (cap) -- no merlons
	])
	var profile := _catmull_profile(ctrl, 12)
	var body := MeshInstance3D.new()
	body.mesh = _lathe(profile, 64)
	body.set_surface_override_material(0, rook_mat)
	rook.add_child(body)
	add_child(rook)

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

	# Reflection-only "sun": contributes ONLY to the procedural sky's sun disc
	# (sky_mode = SKY_ONLY means it casts no direct light/shadow on any object,
	# so matte diffuse shading is completely untouched). Aimed near the key's
	# direction so the highlight it produces on smooth metal reads as the same
	# light source, just with enough radiance to survive the roughness blur of
	# the environment-reflection convolution. This is the "concentrated bright
	# region" the sky reflects -- kept off the key/rim/fill so it cannot leak
	# into direct lighting no matter how bright it is tuned.
	var reflection_sun := DirectionalLight3D.new()
	reflection_sun.rotation_degrees = Vector3(-35, 60, 0)
	reflection_sun.light_energy = 26.0
	reflection_sun.light_color = Color(1.0, 0.98, 0.94)
	reflection_sun.sky_mode = DirectionalLight3D.SKY_MODE_SKY_ONLY
	add_child(reflection_sun)

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
	# Localized bright spot instead of raising sky energy globally: a wide-ish
	# but still bounded sun disc (not the ~100deg default, which blends into
	# the whole-hemisphere gradient) that the reflection_sun above lights up.
	# Wide enough to survive scratched_steel's rough (~0.6) GGX blur as a
	# visible reflection catch; still bounded enough that rough matte
	# materials (near-zero specular response) barely move.
	sky_mat.sun_angle_max = 45.0
	sky_mat.sun_curve = 0.2
	var sky := Sky.new()
	sky.sky_material = sky_mat
	env.sky = sky
	# Ambient is pinned to an explicit color (matched to what the sky above
	# derived) so enriching the reflection sky (below / next change) does NOT
	# re-light the matte materials. Reflection still reads the sky.
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.4, 0.42, 0.46)
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
	# Screen-space reflections: objects reflect each OTHER and the ground
	# reflects them, on top of the sky-only image-based reflection above.
	# Roughness-weighted by the renderer, so rough matte materials barely
	# pick it up; only smooth/metal surfaces show a visible object reflection.
	env.ssr_enabled = true
	env.ssr_max_steps = 64
	env.ssr_fade_in = 0.15
	env.ssr_fade_out = 2.0
	env.ssr_depth_tolerance = 0.2
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


func _load_normal_tex(path: String) -> ImageTexture:
	# WORKAROUND (preview-only): Godot's uv1_triplanar normal path reads the
	# green channel opposite its standard-UV path, so Material Maker's OpenGL
	# normals render with INVERTED relief under the triplanar rig (grooves become
	# ridges). Flip green here so relief is correct. The exported maps are untouched.
	var img := Image.load_from_file(path)
	if img == null:
		return null
	img.convert(Image.FORMAT_RGBA8)
	var w := img.get_width()
	var h := img.get_height()
	var data := img.get_data()
	for i in range(w * h):
		data[i * 4 + 1] = 255 - data[i * 4 + 1]
	var flipped := Image.create_from_data(w, h, false, Image.FORMAT_RGBA8, data)
	return ImageTexture.create_from_image(flipped)


func _make_material(albedo_tex: ImageTexture, normal_tex: ImageTexture,
		orm_tex: ImageTexture, tile: float, clearcoat: float = 0.0,
		clearcoat_roughness: float = 0.5) -> ORMMaterial3D:
	var mat := ORMMaterial3D.new()
	mat.albedo_texture = albedo_tex
	mat.normal_enabled = true
	mat.normal_texture = normal_tex
	mat.orm_texture = orm_tex
	mat.uv1_scale = Vector3(tile, tile, 1)
	mat.texture_repeat = true
	# Opt-in preview-only clearcoat lobe -- see call site. clearcoat<=0.0 must
	# be a true no-op, so the feature flag itself stays off at the default
	# rather than being enabled with a 0.0 value.
	if clearcoat > 0.0:
		mat.clearcoat_enabled = true
		mat.clearcoat = clearcoat
		mat.clearcoat_roughness = clearcoat_roughness
	return mat


func _rounded_box(size: float, radius: float, segments: int) -> ArrayMesh:
	# A cube with smoothly ROUNDED (filleted) edges, not a single-facet chamfer.
	# Method: take a densely-subdivided cube surface and push each vertex onto
	# the Minkowski sum of a box (half-extent `inner`) and a sphere (`radius`):
	#   core = clamp(p, -inner, inner);  surface = core + radius * normalize(p-core)
	# The surface normal is exactly normalize(p-core), so it is analytic and
	# smooth -- flat faces stay flat (core == p there), edges/corners bulge into
	# arcs. Adjacent faces' shared edge verts map to the same arc points, so the
	# fillet is seamless. No UVs (the cube material is triplanar). `segments` is
	# how many grid cells fall inside the `radius` band -> arc smoothness.
	var h := size * 0.5
	var inner := maxf(h - radius, 0.0)
	var subdiv := int(ceil(segments * size / maxf(radius, 1e-3)))
	var box := BoxMesh.new()
	box.size = Vector3(size, size, size)
	box.subdivide_width = subdiv
	box.subdivide_height = subdiv
	box.subdivide_depth = subdiv
	var arrays := box.surface_get_arrays(0)
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var normals := PackedVector3Array()
	normals.resize(verts.size())
	for i in verts.size():
		var p: Vector3 = verts[i]
		var core := Vector3(
			clampf(p.x, -inner, inner),
			clampf(p.y, -inner, inner),
			clampf(p.z, -inner, inner))
		var d := p - core
		var dl := d.length()
		var n := d / dl if dl > 1e-6 else p.normalized()
		verts[i] = core + n * radius
		normals[i] = n
	# Weld coincident vertices. BoxMesh emits each face separately, so the shared
	# box edges carry duplicate verts -- fine to render, but non-manifold, which
	# makes this mesh unusable as a CSG boolean cutter (the subtraction silently
	# does nothing). Merging exact-coincident positions closes it into a manifold.
	# Only cross-face edge duplicates coincide (identical position AND normal), so
	# the visible result is unchanged; it just becomes watertight.
	var old_index: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
	var key_to_idx := {}
	var w_verts := PackedVector3Array()
	var w_norms := PackedVector3Array()
	var remap := PackedInt32Array()
	remap.resize(verts.size())
	for i in verts.size():
		var v: Vector3 = verts[i]
		var key := Vector3i(roundi(v.x * 100000), roundi(v.y * 100000), roundi(v.z * 100000))
		if key_to_idx.has(key):
			remap[i] = key_to_idx[key]
		else:
			var ni := w_verts.size()
			key_to_idx[key] = ni
			remap[i] = ni
			w_verts.append(v)
			w_norms.append(normals[i])
	var new_index := PackedInt32Array()
	new_index.resize(old_index.size())
	for i in old_index.size():
		new_index[i] = remap[old_index[i]]
	var out := []
	out.resize(Mesh.ARRAY_MAX)
	out[Mesh.ARRAY_VERTEX] = w_verts
	out[Mesh.ARRAY_NORMAL] = w_norms
	out[Mesh.ARRAY_INDEX] = new_index
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, out)
	return mesh


func _lathe(profile: PackedVector2Array, segments: int) -> ArrayMesh:
	# Surface of revolution: revolve a 2D profile (Vector2(radius, y), bottom to
	# top) around the Y axis. Normals are SMOOTH around the axis but computed
	# per profile SEGMENT (each ring band uses its segment's outward normal), so
	# the profile's corners -- collars, grooves, lip flares -- read as crisp
	# edges instead of being rounded away. r==0 endpoints cap the axis (the ring
	# collapses to an apex, so those bands are triangle fans). Material is
	# double-sided, so winding is not load-bearing.
	var rows := profile.size() - 1
	# Smooth per-vertex profile normals: average the two adjacent segment normals
	# so the revolved surface has no facets along its length (the "flowy" read).
	# The perpendicular sign (-dy, dr) is the outward orientation verified in the
	# render (a plain (dy,-dr) lit the body from the inside -> near black).
	var pnorm := []
	pnorm.resize(profile.size())
	for i in range(profile.size()):
		var acc := Vector2.ZERO
		if i > 0:
			var s := profile[i] - profile[i - 1]
			acc += Vector2(-s.y, s.x).normalized()
		if i < profile.size() - 1:
			var s := profile[i + 1] - profile[i]
			acc += Vector2(-s.y, s.x).normalized()
		pnorm[i] = acc.normalized()
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for k in range(rows):
		var p0 := profile[k]
		var p1 := profile[k + 1]
		var pn0: Vector2 = pnorm[k]
		var pn1: Vector2 = pnorm[k + 1]
		var vy0 := float(k) / rows
		var vy1 := float(k + 1) / rows
		for j in range(segments):
			var a0 := TAU * j / segments
			var a1 := TAU * (j + 1) / segments
			var u0 := float(j) / segments
			var u1 := float(j + 1) / segments
			var c0 := cos(a0); var s0 := sin(a0)
			var c1 := cos(a1); var s1 := sin(a1)
			var v00 := Vector3(p0.x * c0, p0.y, p0.x * s0)
			var v01 := Vector3(p0.x * c1, p0.y, p0.x * s1)
			var v10 := Vector3(p1.x * c0, p1.y, p1.x * s0)
			var v11 := Vector3(p1.x * c1, p1.y, p1.x * s1)
			var n00 := Vector3(pn0.x * c0, pn0.y, pn0.x * s0)
			var n01 := Vector3(pn0.x * c1, pn0.y, pn0.x * s1)
			var n10 := Vector3(pn1.x * c0, pn1.y, pn1.x * s0)
			var n11 := Vector3(pn1.x * c1, pn1.y, pn1.x * s1)
			# UVs (u = angle, v = height) exist only so generate_tangents() can
			# build a tangent basis -- the triplanar material samples by position,
			# not these UVs, but its normal mapping needs the tangents.
			if p0.x <= 1e-6:
				st.set_normal(n10); st.set_uv(Vector2(u0, vy1)); st.add_vertex(v10)
				st.set_normal(n11); st.set_uv(Vector2(u1, vy1)); st.add_vertex(v11)
				st.set_normal(n00); st.set_uv(Vector2(u0, vy0)); st.add_vertex(v00)
			elif p1.x <= 1e-6:
				st.set_normal(n00); st.set_uv(Vector2(u0, vy0)); st.add_vertex(v00)
				st.set_normal(n01); st.set_uv(Vector2(u1, vy0)); st.add_vertex(v01)
				st.set_normal(n10); st.set_uv(Vector2(u0, vy1)); st.add_vertex(v10)
			else:
				st.set_normal(n00); st.set_uv(Vector2(u0, vy0)); st.add_vertex(v00)
				st.set_normal(n10); st.set_uv(Vector2(u0, vy1)); st.add_vertex(v10)
				st.set_normal(n11); st.set_uv(Vector2(u1, vy1)); st.add_vertex(v11)
				st.set_normal(n00); st.set_uv(Vector2(u0, vy0)); st.add_vertex(v00)
				st.set_normal(n11); st.set_uv(Vector2(u1, vy1)); st.add_vertex(v11)
				st.set_normal(n01); st.set_uv(Vector2(u1, vy0)); st.add_vertex(v01)
	st.generate_tangents()
	return st.commit()


func _catmull_pt(p0: Vector2, p1: Vector2, p2: Vector2, p3: Vector2, t: float) -> Vector2:
	var t2 := t * t
	var t3 := t2 * t
	return 0.5 * ((2.0 * p1) + (-p0 + p2) * t
		+ (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
		+ (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3)


func _catmull_profile(ctrl: PackedVector2Array, steps: int) -> PackedVector2Array:
	# Catmull-Rom spline through the control points, sampled `steps` per span, so
	# the lathe profile is a smooth flowing curve instead of straight facets.
	var out := PackedVector2Array()
	var n := ctrl.size()
	for i in range(n - 1):
		var p0: Vector2 = ctrl[maxi(i - 1, 0)]
		var p1: Vector2 = ctrl[i]
		var p2: Vector2 = ctrl[i + 1]
		var p3: Vector2 = ctrl[mini(i + 2, n - 1)]
		for s in range(steps):
			out.append(_catmull_pt(p0, p1, p2, p3, float(s) / steps))
	out.append(ctrl[n - 1])
	return out
