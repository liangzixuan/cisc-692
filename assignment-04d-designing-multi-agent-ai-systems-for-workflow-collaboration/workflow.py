from crewai import Crew
from tasks import task_screen_resumes, task_design_interview, task_culture_fit

hiring_crew = Crew(
    tasks=[task_screen_resumes, task_design_interview, task_culture_fit],
    verbose=True
)

# Execute Workflow
result = hiring_crew.kickoff()
print(result)
