"""Scheduling Engine

Deterministic greedy constraint-checker for scheduling interviews.
Checks for overlap with student schedules, venue bookings, and panel availability.
Proposes the next available slot on conflict.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from backend import models

def propose_schedule(
    job_id: str,
    student_id: str,
    preferred_start: datetime,
    duration_minutes: int,
    venue: str,
    panel: str,
    db: Session
) -> tuple[datetime, datetime]:
    """Finds the next available interview slot that satisfies all constraints.
    
    If the preferred_start conflicts, it pushes the time forward by 30-minute
    increments until a clear slot is found.
    """
    current_start = preferred_start
    
    # Hard safety break to prevent infinite loops (e.g., if checking an entire year)
    max_attempts = 48 * 7  # up to 7 days ahead in 30-min increments
    attempts = 0
    
    while attempts < max_attempts:
        current_end = current_start + timedelta(minutes=duration_minutes)
        
        # Check for any overlapping interviews (start < new_end AND end > new_start)
        # that share the same student, venue, or panel.
        overlapping = db.query(models.Interview).filter(
            and_(
                models.Interview.start_time < current_end,
                models.Interview.end_time > current_start,
                or_(
                    models.Interview.student_id == student_id,
                    models.Interview.venue == venue,
                    models.Interview.panel == panel
                )
            )
        ).first()
        
        if not overlapping:
            return current_start, current_end
            
        # Conflict found. Push forward by 30 minutes and try again.
        current_start += timedelta(minutes=30)
        attempts += 1
        
    raise ValueError("Could not find a free slot within the next 7 days.")
