class_name LayeredBuildingOccluder
extends Area2D

@export_range(0.2, 0.9, 0.05) var fade_alpha := 0.45
@export_range(0.0, 1.0, 0.01) var fade_seconds := 0.14
@export var accepted_group := "local_view_actors"
@export var visual_path: NodePath

var _visual: CanvasItem
var _covered_actor_ids: Dictionary = {}
var _fade_tween: Tween
var _cleanup_elapsed := 0.0
var _original_alpha := 1.0

const CLEANUP_INTERVAL_SECONDS := 0.5


func _ready() -> void:
	_visual = get_node_or_null(visual_path) as CanvasItem
	if _visual:
		_original_alpha = _visual.modulate.a
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)


func _exit_tree() -> void:
	if is_instance_valid(_fade_tween):
		_fade_tween.kill()


func _process(delta: float) -> void:
	if _covered_actor_ids.is_empty():
		return
	_cleanup_elapsed += delta
	if _cleanup_elapsed < CLEANUP_INTERVAL_SECONDS:
		return
	_cleanup_elapsed = 0.0
	_remove_invalid_actors()
	if _covered_actor_ids.is_empty():
		_set_occluded(false)


func _on_body_entered(body: Node2D) -> void:
	if not body.is_in_group(accepted_group):
		return
	_covered_actor_ids[body.get_instance_id()] = weakref(body)
	_set_occluded(true)


func _on_body_exited(body: Node2D) -> void:
	_covered_actor_ids.erase(body.get_instance_id())
	_remove_invalid_actors()
	if _covered_actor_ids.is_empty():
		_set_occluded(false)


func _remove_invalid_actors() -> void:
	for actor_id: int in _covered_actor_ids.keys():
		var actor_ref: WeakRef = _covered_actor_ids[actor_id] as WeakRef
		if actor_ref == null or actor_ref.get_ref() == null:
			_covered_actor_ids.erase(actor_id)


func _set_occluded(occluded: bool) -> void:
	if _visual == null:
		return
	var target_alpha := fade_alpha if occluded else _original_alpha
	if is_instance_valid(_fade_tween):
		_fade_tween.kill()
	_fade_tween = create_tween()
	_fade_tween.tween_property(_visual, "modulate:a", target_alpha, fade_seconds)
