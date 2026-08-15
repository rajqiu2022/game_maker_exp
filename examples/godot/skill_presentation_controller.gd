class_name ExampleSkillPresentationController
extends Node

var _profiles: Dictionary = {}
var _processed_event_ids: Dictionary = {}
var _processed_event_order: Array[String] = []
var _warned_profile_ids: Dictionary = {}

const MAX_REMEMBERED_EVENT_IDS := 256


func configure(profiles: Dictionary) -> void:
	_profiles = profiles.duplicate(true)


func play_event(event: Dictionary) -> void:
	var event_id := str(event.get("event_id", ""))
	if event_id.is_empty() or _processed_event_ids.has(event_id):
		return
	_remember_event_id(event_id)

	var presentation_id := str(event.get("presentation_id", ""))
	if not _profiles.has(presentation_id):
		_warn_missing_once(presentation_id)

	# This example intentionally delegates VFX/SFX spawning to project adapters.
	# Presentation code must never deduct resources or apply gameplay effects.
	var phase := str(event.get("phase", "cast"))
	var phase_profile := _resolve_phase_profile(presentation_id, phase)
	if phase_profile.is_empty():
		return
	spawn_vfx(phase_profile, event)
	play_sfx(phase_profile, event)


func spawn_vfx(_phase_profile: Dictionary, _event: Dictionary) -> void:
	pass


func play_sfx(_phase_profile: Dictionary, _event: Dictionary) -> void:
	pass


func _resolve_phase_profile(presentation_id: String, phase: String) -> Dictionary:
	var current_id := presentation_id
	var visited: Dictionary = {}
	while not current_id.is_empty():
		if visited.has(current_id):
			return {}
		visited[current_id] = true
		var profile: Dictionary = _profiles.get(current_id, {}) as Dictionary
		if profile.is_empty():
			if current_id == "fallback.default":
				return {}
			current_id = "fallback.default"
			continue
		var phase_profile: Dictionary = profile.get(phase, {}) as Dictionary
		if not phase_profile.is_empty():
			return phase_profile
		var fallback_id := str(profile.get("fallback_profile", ""))
		if fallback_id.is_empty() and current_id != "fallback.default":
			fallback_id = "fallback.default"
		current_id = fallback_id
	return {}


func _warn_missing_once(presentation_id: String) -> void:
	if _warned_profile_ids.has(presentation_id):
		return
	_warned_profile_ids[presentation_id] = true
	push_warning("Missing skill presentation profile: %s" % presentation_id)


func _remember_event_id(event_id: String) -> void:
	_processed_event_ids[event_id] = true
	_processed_event_order.append(event_id)
	if _processed_event_order.size() <= MAX_REMEMBERED_EVENT_IDS:
		return
	var expired_event_id: String = _processed_event_order.pop_front()
	_processed_event_ids.erase(expired_event_id)
