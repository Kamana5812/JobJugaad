def calculate_readiness_score(student):
    """
    Readiness Score = 30% Tech + 20% Proj + 15% Acad + 15% Apt + 10% Comm + 10% Interview
    Returns: dict with score, band, breakdown, explanation
    """
    # 1. Tech score (from skills)
    if not student.skills:
        tech_score = 0.0
    else:
        tech_score = sum(s.proficiency for s in student.skills) / len(student.skills)
        
    # 2. Project score (from projects)
    if not student.projects:
        proj_score = 0.0
    else:
        proj_score = min(100.0, len(student.projects) * 35.0)
        
    # 3. Academics (from cgpa) - map CGPA 0-10 to 0-100
    acad_score = (student.cgpa / 10.0) * 100.0 if student.cgpa else 0.0
    
    # 4. Aptitude, Comm, Interview are mock scores directly from the model
    apt_score = student.aptitude_score or 0.0
    comm_score = student.communication_score or 0.0
    int_score = student.interview_score or 0.0

    # Calculate weighted sum
    breakdown = {
        "Technical Skills (30%)": round(tech_score, 1),
        "Projects (20%)": round(proj_score, 1),
        "Academics (15%)": round(acad_score, 1),
        "Aptitude (15%)": round(apt_score, 1),
        "Communication (10%)": round(comm_score, 1),
        "Interview (10%)": round(int_score, 1)
    }
    
    total_score = (
        (tech_score * 0.30) +
        (proj_score * 0.20) +
        (acad_score * 0.15) +
        (apt_score * 0.15) +
        (comm_score * 0.10) +
        (int_score * 0.10)
    )
    total_score = round(total_score, 1)
    
    # Determine band
    if total_score <= 40:
        band = "Not Ready"
    elif total_score <= 65:
        band = "Developing"
    elif total_score <= 85:
        band = "Ready"
    else:
        band = "Highly Employable"
        
    # Generate explanation
    sorted_factors = sorted(breakdown.items(), key=lambda x: x[1])
    lowest_factor = sorted_factors[0][0].split(" ")[0]
    highest_factor = sorted_factors[-1][0].split(" ")[0]
    
    explanation = (
        f"Your overall readiness is {band}. "
        f"You show strong potential in {highest_factor}, but "
        f"you should focus on improving your {lowest_factor} to boost your employability."
    )
    
    return {
        "score": total_score,
        "band": band,
        "breakdown": breakdown,
        "explanation": explanation
    }
