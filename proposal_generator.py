"""Honest, reviewable proposal drafts. No unverifiable claims or automatic sending."""
from job_fit import score_job, load_profile

def generate_rule_based_proposal(title: str, snippet: str, client_info: str = '', skills: list = None) -> str:
    return draft_proposal({'title': title, 'snippet': snippet, 'client_info': client_info})

def draft_proposal(job_data: dict) -> str:
    profile = load_profile()
    fit = score_job(job_data, profile)
    title = ' '.join(str(job_data.get('title') or 'your project').split())[:180]
    track = fit['track']
    scopes = {
        'short_video': ('a short-form video workflow', 'Review your script, footage and style reference; agree on the aspect ratio, captions, duration and delivery format.'),
        'automation': ('a small automation workflow', 'Map the inputs and outputs, build one agreed workflow, then test retries and failure handling using sample data.'),
        'website': ('a focused website workflow', 'Confirm the pages and form fields, build the agreed flow, then test mobile layout, validation and access to stored data.'),
    }
    angle, scope = scopes.get(track, ('the project scope', 'Review the requirements together and confirm which deliverables I can take on before committing.'))
    lines = [f'Hi, I read your post about "{title}".', '', f'I would like to discuss {angle} for this project.', '', 'Proposed first step:', scope, '', 'Could you share a reference, the material you already have, and your expected deadline? I would also like to confirm the deliverables, budget and revision limit before agreeing to the work.']
    portfolio = str(profile.get('portfolio_url') or '').strip()
    if portfolio.startswith('https://'):
        lines += ['', f'Relevant work to review: {portfolio}']
    lines += ['', 'If the scope is a fit, we can agree on a small paid milestone with clear acceptance criteria.', '', 'Thanks,', profile.get('name', 'Johnny')]
    return '\n'.join(lines)
