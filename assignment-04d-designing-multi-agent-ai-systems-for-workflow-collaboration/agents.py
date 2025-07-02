from crewai import Agent

resume_screener = Agent(
    role='Resume Screener',
    goal='Shortlist candidates based on skills and experience.',
    backstory='You specialize in quickly analyzing resumes.',
    verbose=True
)

interview_designer = Agent(
    role='Interview Designer',
    goal='Generate tailored interview questions.',
    backstory='You excel in designing relevant and insightful interviews.',
    verbose=True
)

culture_fit_assessor = Agent(
    role='Culture Fit Assessor',
    goal='Evaluate cultural alignment of candidates.',
    backstory='Expert in assessing soft skills and organizational fit.',
    verbose=True
)
