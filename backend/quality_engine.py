def calculate_quality_score(
    *,
    avg_complexity: float,
    warning_count: int,
    loc: int,
    globals_: int,
    random_calls: int,
    mem_allocs: int,
    threads: int,
    locks: int,
    infinite_loops: int,
    danger_score: int
):
    """
    Returns:
      score (0–100),
      grade (Excellent / Good / Fair / Poor),
      reasons (list[str])
    """

    score = 100
    reasons = []

    # -----------------------
    # Complexity penalty
    # -----------------------
    if avg_complexity > 8:
        score -= 20
        reasons.append("High average cyclomatic complexity")
    elif avg_complexity > 5:
        score -= 10
        reasons.append("Moderate cyclomatic complexity")

    # -----------------------
    # Warnings penalty
    # -----------------------
    if warning_count >= 5:
        score -= 15
        reasons.append("Many static warnings detected")
    elif warning_count >= 2:
        score -= 8
        reasons.append("Some static warnings detected")

    # -----------------------
    # Code size penalty
    # -----------------------
    if loc > 500:
        score -= 10
        reasons.append("Very large codebase")
    elif loc > 250:
        score -= 5
        reasons.append("Moderately large codebase")

    # -----------------------
    # Architecture risks
    # -----------------------
    if globals_ >= 3:
        score -= 10
        reasons.append("Heavy global mutable state")

    if random_calls >= 5:
        score -= 8
        reasons.append("High nondeterminism")

    if mem_allocs > 0:
        score -= 10
        reasons.append("Manual memory allocation detected")

    if threads >= 4 and locks >= 2:
        score -= 10
        reasons.append("Complex concurrency design")

    if infinite_loops > 0:
        score -= 6
        reasons.append("Infinite loops reduce predictability")

    # -----------------------
    # Risk model penalty
    # -----------------------
    score -= danger_score * 4

    # Clamp score
    score = max(0, min(100, score))

    # -----------------------
    # Grade mapping
    # -----------------------
    if score >= 85:
        grade = "Excellent 🟢"
    elif score >= 70:
        grade = "Good 🟡"
    elif score >= 50:
        grade = "Fair 🟠"
    else:
        grade = "Poor 🔴"

    return round(score, 1), grade, reasons
