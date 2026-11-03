"""Deterministic triage against demonstrated project tracks, no API or auto-apply."""
import json
import html
import re
from pathlib import Path
from red_flags import scan_red_flags
PROFILE_PATH = Path(__file__).with_name('freelance_profile.json')

def load_profile():
    return json.loads(PROFILE_PATH.read_text(encoding='utf-8'))

def has(text, pattern):
    return bool(re.search(pattern, text, re.I))

def score_job(job, profile=None):
    profile = profile if profile is not None else load_profile()
    title = html.unescape(str(job.get('title') or ''))
    snippet = html.unescape(re.sub(r'<[^>]*>', '', str(job.get('snippet') or '')))
    text = f'{title} {snippet}'.lower()
    tracks = set(profile.get('tracks', []))
    video = has(text, r'\b(video|editor|editing|reels?|shorts?|tiktok|remotion)\b')
    automation = has(text, r'\b(automation|automate|webhook|workflow|scraping|scraper|n8n|zapier)\b')
    website = has(text, r'\b(website|landing page|web app|dashboard|next\.?js|react)\b')
    # A manufacturing workflow is not a software automation brief.
    engineering = has(text, r'\b(cad|solidworks|nc1|sheet metal|mechanical engineer\w*|enclosure design)\b')
    if engineering:
        automation = False
        video = False
        website = False
    reasons, gaps, questions = [], [], []
    if engineering:
        gaps.append('CAD/cơ khí ngoài phạm vi demo automation phần mềm hiện có.')

    score, track = 10, None
    if video and 'short_video' in tracks:
        track, score = 'short_video', 42
        reasons.append('Có demo video dọc để đối chiếu yêu cầu.')
        if has(text, r'\b(short[- ]?form|reels?|youtube shorts|tiktok|vertical)\b|9:16'):
            score += 15
            reasons.append('Đúng định dạng video ngắn/dọc.')
        else:
            gaps.append('Chưa rõ có phù hợp quy trình video dọc hiện có.')
        if has(text, r'\b(crypto|bitcoin|trading|finance|financial|forex|stock)\b'):
            score += 10
            reasons.append('Nội dung gần ngách video thị trường đang làm.')
        if has(text, r'\b(long[- ]form|documentary|feature film)\b'):
            score -= 15
            gaps.append('Video dài cần kiểm tra portfolio và khối lượng riêng.')
    elif automation and 'automation' in tracks:
        track, score = 'automation', 52
        reasons.append('Gần các luồng form/email → dữ liệu → Telegram đang có demo.')
        if has(text, r'\b(python|telegram|sqlite|csv|form|email|webhook)\b'):
            score += 15
            reasons.append('Có thành phần tương tự hệ thống đang vận hành.')
    elif website and 'website' in tracks:
        track, score = 'website', 46
        reasons.append('Có demo form và trang quản lý để tham khảo.')
        if has(text, r'\b(form|landing page|dashboard|small business)\b'):
            score += 12
            reasons.append('Phạm vi gần demo website nhỏ.')
    else:
        gaps.append('Chưa có tài sản demo phù hợp; không ưu tiên chỉ vì có từ crypto/AI.')
    truncated = '…' in title or '...' in title or '…' in snippet or '...' in snippet
    if truncated:
        gaps.append('Email chứa mô tả/tiêu đề bị cắt; chưa xác minh trang job gốc.')
    if len(snippet.strip()) >= 160 and not truncated:
        score += 6
        reasons.append('Có mô tả đủ dài để bắt đầu đánh giá phạm vi.')
    else:
        gaps.append('Mô tả còn thiếu; cần đọc trang job gốc.')
    budget = str(job.get('budget') or '').strip()
    if re.search(r'\d', budget):
        score += 5
        reasons.append('Có thông tin ngân sách để đối chiếu chi phí.')
    else:
        questions.append('Ngân sách cho toàn bộ phạm vi là bao nhiêu?')
    if has(text, r'premiere|after effects|\.aep\b|\.prproj\b'):
        score -= 20
        gaps.append('Yêu cầu Adobe chưa có năng lực/file nguồn được xác minh trong hồ sơ.')
    if has(text, r'\b(capcut|davinci resolve|avid)\b'):
        score -= 20
        gaps.append('Chưa xác minh khả năng giao bằng phần mềm biên tập được yêu cầu; demo hiện có dùng Remotion.')
    if has(text, r'\b(3d|blender|unreal|houdini|cinema 4d)\b'):
        score -= 25
        gaps.append('Chưa có demo 3D tương ứng.')
    if has(text, r'\b(translat\w*|native speaker|certified)\b'):
        score -= 20
        gaps.append('Chưa xác minh năng lực dịch thuật/chứng chỉ được yêu cầu.')
    amount_match = re.search(r'(?:fixed[^\d]*|\$)([\d,]+(?:\.\d+)?)', budget, re.I)
    if 'fixed' in budget.lower() and amount_match and float(amount_match.group(1).replace(',', '')) <= 15:
        score -= 15
        gaps.append('Ngân sách fixed rất nhỏ; cần biết số đầu ra và thời gian thực hiện trước khi cân nhắc.')
    flags = scan_red_flags(text)
    score -= min(35, len(flags) * 10)
    questions.append('Đầu vào, đầu ra, deadline và số vòng chỉnh sửa cụ thể là gì?')
    score = max(0, min(100, score))
    if not track:
        score = min(score, 30)
    label = 'Nên đọc kỹ' if score >= 65 else 'Cần làm rõ' if score >= 40 else 'Ưu tiên thấp'
    evidence = profile.get('evidence', {}).get(track, '') if track else ''
    return dict(score=score, label=label, track=track, confidence='limited' if truncated or len(snippet.strip()) < 160 else 'description_only', reasons=reasons, gaps=gaps, questions=questions, flags=flags, evidence=evidence)

def rank_jobs(jobs, limit=5, profile=None):
    profile = profile if profile is not None else load_profile()
    eligible = [j for j in jobs if j.get('email_type') in ('job_alert', 'brief', 'invitation', 'offer')]
    ranked = [dict(job=j, fit=score_job(j, profile)) for j in eligible]
    ranked = [item for item in ranked if item['fit']['track'] is not None]
    return sorted(ranked, key=lambda x:(x['fit']['score'], x['job'].get('id', 0)), reverse=True)[:limit]

def format_fit(fit):
    lines = [f"{fit['score']}/100 · {fit['label']} (độ khớp với demo, không phải xác suất trúng)"]
    lines += ['+ '+s for s in fit['reasons']]
    lines += ['Cần kiểm tra: '+s for s in fit['gaps']]
    lines += ['Rủi ro: '+s for s in fit['flags']]
    lines += ['Hỏi khách: '+s for s in fit['questions']]
    if fit['evidence']:
        lines.append('Tài sản để đối chiếu: '+fit['evidence'])
    return '\n'.join(lines)
