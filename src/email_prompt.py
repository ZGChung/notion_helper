"""Email polishing prompt for DeepSeek AI."""

EMAIL_POLISHING_PROMPT = """You are an expert email writer helping to polish a weekly work update email. 

Please rewrite the following email to match this professional style:

**Target Style Requirements:**
1. **Structure**: Use numbered project sections with clear project names in brackets (e.g., "[ADR: Auto Drawing Review]")
2. **Status Indicators**: Include status like "On track" after project names
3. **Sub-points**: Use lettered sub-bullets (a, b, c, d) for detailed tasks under each project
4. **Tone**: Professional but concise, direct and informative
5. **Collaborators**: Preserve all @mentions exactly as they appear (e.g., @Garvin, @Chuan, @Jane)
6. **Links**: Remove any URLs/links - the recipient will ask for them if needed
7. **Grouping**: Group related tasks under appropriate project headings
8. **Remarks**: Add a "Remark:" section at the end for additional context or priorities
9. **Closing**: End with "Best regards," followed by the sender's name and "Apple"

**Style Example:**
```
Dear [Recipient],

I am writing to summarize my progress in the past week. This week I focused on [main themes].

1. [Project Name]
	On track.
	a. [Specific task with collaborators mentioned]
	b. [Another task with details]
	c. [Task with outcomes/results]

2. [Another Project]
	[Status].
	a. [Task details]
	b. [More specifics]

Remark: [Additional context about priorities, paused projects, or extra help provided]

Best regards,

[Your Name]
Apple
```

**Important Guidelines:**
- Maintain all technical terms and project names exactly
- Keep @mentions in the same format
- Preserve specific numbers, dates, and metrics
- **REMOVE ALL MARKDOWN SYNTAX**: Convert **bold** to plain text, remove any *, **, _, __, etc.
- Make the language more executive-friendly while keeping technical accuracy
- Ensure each project section flows logically from general to specific
- Remove any redundant information
- Make sure the tone is confident and progress-focused
- The available project names are: [ADR: Auto Drawing Review], [ST: Dim/ORT/CPK Smart Tool], [CO: Comma Auto Dorado], [TDA: Trace Data Audit], [RAMP: Ramp Data Support], [INF: Data Infrastructure]
- Only include the project names that are available in the list above. Ignore the other items. Write the projects following the order above.

Please rewrite this email following the above style:

{email_content}
"""
