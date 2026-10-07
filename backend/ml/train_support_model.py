import os
import sys
import joblib
import pandas as pd
from datetime import datetime, timedelta, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sqlalchemy import select

# Add parent dir to path so we can import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import tenant_session
from models import Student, StudentSkill, Interview, Job, RiskPrediction
from engines.skill_gap import skill_gaps

def extract_features(session):
    print("Extracting features from synthetic database...")
    # Get a representative job to calculate skill gaps against
    job = session.scalar(select(Job).order_by(Job.id).limit(1))
    if not job:
        print("No jobs found in database.")
        return pd.DataFrame()
    
    # We will compute features for all students in this college
    students = session.scalars(select(Student)).all()
    
    now = datetime.now(timezone.utc)
    
    dataset = []
    for student in students:
        # 1. Skill gaps (Technical Support Indicator)
        skills = session.scalars(select(StudentSkill).where(StudentSkill.student_id == student.id)).all()
        gaps = [g for g in skill_gaps(skills, job.required_skills) if g["status"] != "on-track"]
        num_gaps = len(gaps)
        
        # 2. Interview score (Interview Preparation Indicator)
        # Impute missing mock interview scores with a neutral 50.0
        interview_score = student.interview_score if student.interview_score is not None else 50.0 
        
        # 3. Activity (Recorded Participation Indicator)
        activity = session.query(Interview).filter(
            Interview.student_id == student.id,
            Interview.event_type == 'interview',
            Interview.status.in_(["completed", "selected", "rejected"]),
            Interview.end_time >= now - timedelta(days=30),
            Interview.end_time <= now
        ).count()
        
        # Target: For demonstration, we use the existing rule-based `flagged` status 
        # from risk_predictions as our proxy ground-truth. 
        risk_pred = session.scalar(select(RiskPrediction).where(RiskPrediction.student_id == student.id).order_by(RiskPrediction.id.desc()).limit(1))
        target = 1 if (risk_pred and risk_pred.flagged) else 0

        dataset.append({
            "student_id": student.id,
            "num_skill_gaps": num_gaps,
            "interview_score": interview_score,
            "recent_activity": activity,
            "support_needed": target
        })
    return pd.DataFrame(dataset)

def train_model():
    college_id = 10219 # Default demo college tenant ID
    try:
        with tenant_session(college_id) as session:
            df = extract_features(session)
    except Exception as e:
        print(f"Database connection error: {e}")
        return
        
    if df.empty:
        print("No data extracted.")
        return
        
    print(f"Extracted {len(df)} records.")
    print("Class distribution:")
    print(df['support_needed'].value_counts())

    X = df[['num_skill_gaps', 'interview_score', 'recent_activity']]
    y = df['support_needed']

    # Train/test split with stratification
    stratify_target = y if len(y.unique()) > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=stratify_target)

    # Train a Random Forest with class_weight='balanced' to handle class imbalance
    # This fulfills the PRD methodological requirement in ARCHITECTURE.md 
    print("\nTraining Random Forest with class_weight='balanced'...")
    model = RandomForestClassifier(class_weight='balanced', max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    print("\nEvaluating model:")
    y_pred = model.predict(X_test)
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Feature importances to satisfy explainability constraints (factor breakdowns)
    print("\nFeature Importances (Explainability Constraints):")
    importances = model.feature_importances_
    features = X.columns
    for f, imp in zip(features, importances):
        print(f" - {f}: {imp:.4f}")

    # The prediction output will now be based on these feature importances.
    # In production, predict_proba can be used alongside these importances 
    # to form the JSON factor_breakdown dynamically per student.
    
    # Save model artifact
    save_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(save_dir, exist_ok=True)
    model_path = os.path.join(save_dir, "support_model.joblib")
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")

if __name__ == "__main__":
    train_model()
