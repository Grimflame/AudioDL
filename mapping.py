def map_tag_to_bucket(tag_name: str, category: int) -> str:
    t = tag_name.lower()
    if category == 4:  # character
        return "subject"
    if any(x in t for x in ("girl","boy","man","woman","creature","dragon","android","mecha")):
        return "subject"
    if any(x in t for x in ("hair","eyes","uniform","armor","kimono","scarf","gloves","earrings","hoodie","ribbon")):
        return "subject_detail"
    if any(x in t for x in ("view","angle","pose","portrait","bust","upper_body","full_body","close-up","looking_at_viewer","profile","three-quarter_view")):
        return "pose_frame"
    if any(x in t for x in ("lighting","light","painterly","watercolor","digital_painting","illustration","high_detail","sharp_focus","dramatic","serene","melancholy","neon","golden_hour","rim_light","backlighting","volumetric_light","night","sunset")):
        return "mood_light_style"
    if any(x in t for x in ("forest","beach","snow","mountain","cityscape","classroom","shrine","market_street","indoor","outdoor")):
        return "environment"
    if any(x in t for x in ("bokeh","lens_flare","light_trails","motion_blur","particles","spellcasting","sword_draw","explosion","wind_swept_hair")):
        return "fx_action"
    return "subject_detail"