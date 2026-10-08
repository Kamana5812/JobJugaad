import os
from groq import Groq
from sqlalchemy import select
from models import Job, StudentSkill, Project
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from engines.matching import calculate_match

# Initialize Groq client
api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

def get_rag_context(session, college_id, query):
    """Retrieve campus placement history (jobs) matching the query."""
    jobs = session.scalars(select(Job).where(Job.college_id == college_id)).all()
    if not jobs:
        return "No historical placement data found."
    
    # Create document corpus from jobs
    docs = []
    for j in jobs:
        docs.append(
            f"Role: {j.title} | CTC: {j.ctc} LPA | Min CGPA: {j.min_cgpa} | "
            f"Skills: {', '.join(j.required_skills)} | Desc: {j.description}"
        )
    
    # Simple TF-IDF retrieval
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform(docs)
        query_vec = vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
        
        # Get top 3 most relevant historical records
        top_indices = similarities.argsort()[-3:][::-1]
        relevant_docs = [docs[i] for i in top_indices if similarities[i] > 0.1]
        
        if relevant_docs:
            return "Relevant Campus Placement History:\n- " + "\n- ".join(relevant_docs)
        return "No highly relevant placement history matched the query."
    except Exception as e:
        return f"Error retrieving history: {str(e)}"

def generate_chat_response(session, user, student, job, message):
    if not client:
        return "Error: GROQ_API_KEY is missing from the .env file. Please add it to enable the AI features."
        
    context = []
    
    # Context 1: Student Profile
    context.append(f"Student Name: {student.name}")
    context.append(f"Branch: {student.branch}, CGPA: {student.cgpa}")
    
    student_skills = session.scalars(select(StudentSkill).where(StudentSkill.student_id == student.id)).all()
    projects = session.scalars(select(Project).where(Project.student_id == student.id)).all()
    
    skill_str = ", ".join([f"{s.skill_name} ({s.proficiency}%)" for s in student_skills])
    context.append(f"Skills: {skill_str}")
    project_str = ", ".join([p.title for p in projects])
    context.append(f"Projects: {project_str}")

    # Context 2: Current Job Context (if provided)
    if job:
        context.append(f"\nCurrent Target Role: {job.title} (CTC: {job.ctc} LPA)")
        context.append(f"Requirements: Min CGPA {job.min_cgpa}, Skills: {', '.join(job.required_skills)}")
        # Pre-calculate match score using existing engine logic
        match_info = calculate_match(student, student_skills, projects, [], job)
        context.append(f"Match Score: {match_info.match_score}/100, Eligible: {match_info.eligible}")
        context.append(f"System Explanation: {match_info.explanation}")

    # Context 3: Placement History (RAG)
    rag_context = get_rag_context(session, user.college_id, message)
    context.append(f"\n{rag_context}")

    prompt = f"""You are 'Jugaad Dost', a friendly, encouraging, and highly practical placement copilot for college students. 
You provide structured, highly actionable advice. Be concise.

--- STUDENT CONTEXT ---
{chr(10).join(context)}

--- STUDENT MESSAGE ---
{message}

Please respond to the student directly."""

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "system", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Dost is currently facing technical issues: {str(e)}"
