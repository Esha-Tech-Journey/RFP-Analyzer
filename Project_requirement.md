RFP Insight & Risk Analyzer
Overview
You are building a small internal tool used by pre-sales teams to quickly evaluate incoming RFPs
(Request for Proposals). The goal is to reduce the time spent manually reading long documents and
help teams decide whether to proceed with an opportunity.
What the system should do
• Allow a user to submit an RFP (title and description)
• Process the request in the background
• Provide structured insights once processing is complete
• Allow users to track the status of submitted requests
Expected outputs for each RFP
• Short summary (4–5 bullet points)
• List of key requirements
• Risk level (Low / Medium / High) with reasons
• Effort estimate (Small / Medium / Large)
• Recommendation (Go / No-Go / Needs Discussion)
User flow
• User submits RFP details
• System returns a job ID immediately
• User can check status using the job ID
• Once complete, user can view the analysis
Backend expectations
• Expose APIs to submit, fetch, and list jobs
• Use background processing for analysis
• Persist job data and results
• Handle failure scenarios gracefully
Tech stack (mandatory)
• FastAPI for API layer
• Celery for background jobs
• Redis as message broker
• PostgreSQL as database
• SQLAlchemy for ORM
• Alembic for migrations
• Docker for running all services
• uv for dependency management
Frontend expectations
• Simple React UI
• Form to submit RFP
• List view of submitted jobs
• Detail view with results
• Polling to update job status
Notes
• Keep UI simple, focus more on backend design
• Business logic can be rule-based
• No authentication required
• Prioritize clarity and working flow over perfectio