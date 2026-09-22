"""Deterministic proficiency comparison; thresholds are proposed assumptions."""

def normalize_skill(value):
    return " ".join(value.lower().split())


def skill_gaps(skills, requirements):
    recorded = {}
    for skill in skills:
        name = normalize_skill(skill.skill_name)
        # Older profiles may contain whitespace variants: use their maximum.
        recorded[name] = max(recorded.get(name, 0), skill.proficiency)
    result = []
    for requirement in requirements:
        name, target = requirement["skill_name"], requirement["min_proficiency"]
        actual = recorded.get(name, 0)
        status = "on-track" if actual >= target else "critical" if actual < target / 2 else "gap"
        result.append(dict(skill_name=name, proficiency=actual, required=target,
            shortfall=round(max(0, target - actual), 2), status=status,
            explanation=f"{name}: recorded proficiency {actual:g}/100; role target {target:g}/100."
                + (" No recorded skill evidence; treated as zero." if name not in recorded else " Self-reported, not independently verified."),
            next_step=f"Add a practical {name} project and review proficiency against {target:g}/100."
                if status != "on-track" else f"Keep {name} evidence current for recruiter review."))
    return result
