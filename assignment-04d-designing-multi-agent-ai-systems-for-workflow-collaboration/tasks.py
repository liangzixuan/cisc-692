from crewai import Task
from agents import resume_screener, interview_designer, culture_fit_assessor

task_screen_resumes = Task(
    description='Screen resumes and shortlist top 5 candidates.',
    agent=resume_screener,
    expected_output='A JSON list with names and key qualifications of the top 5 shortlisted candidates.'
)

task_design_interview = Task(
    description='Create specific interview questions for shortlisted candidates.',
    agent=interview_designer,
    context=[task_screen_resumes],
    expected_output='A JSON document with tailored interview questions for each shortlisted candidate.'
)

task_culture_fit = Task(
    description='Evaluate candidates’ responses for culture fit.',
    agent=culture_fit_assessor,
    context=[task_design_interview],
    expected_output='A JSON report assessing each candidate’s culture fit score and rationale.'
)
